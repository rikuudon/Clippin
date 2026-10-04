import os
import sys
import json
import argparse
import subprocess
import re
from pathlib import Path
from dotenv import load_dotenv

# Set UTF-8 encoding for standard output on Windows to prevent charmap crashes
if sys.platform == "win32":
    try:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
    except Exception:
        pass

# ==============================================================================
# PyAV Compatibility Patch:
# In PyAV (av >= 14), the 'metadata_errors' parameter was removed from av.open.
# However, faster-whisper (audio.py) still passes metadata_errors="ignore".
# We patch av.open so that metadata_errors is cleanly stripped without breaking.
# ==============================================================================
try:
    import av
    _orig_av_open = av.open

    def _compat_av_open(*args, **kwargs):
        kwargs.pop("metadata_errors", None)
        return _orig_av_open(*args, **kwargs)

    av.open = _compat_av_open
except Exception:
    pass

# Ensure the worker directory is in sys.path so prompts.py can always be imported
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))

try:
    from prompts import CLIP_SELECTION_PROMPT
except ImportError:
    print("[Error] Could not find prompts.py. Make sure prompts.py is in the worker directory.")
    sys.exit(1)

# Load environment variables from worker/.env or repo root .env
load_dotenv(SCRIPT_DIR / ".env")
load_dotenv(REPO_ROOT / ".env")


def check_ffmpeg():
    """Verify that FFmpeg is accessible in PATH."""
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    except (subprocess.SubprocessError, FileNotFoundError):
        print("\n" + "=" * 60)
        print("❌ [PREREQUISITE ERROR] FFmpeg is not found in your system PATH!")
        print("FFmpeg is required to cut and export video clips.")
        print("Please install FFmpeg or ensure it is added to your environment PATH.")
        print("=" * 60 + "\n")
        sys.exit(1)


def sanitize_filename(name: str) -> str:
    """Convert string to safe directory/file name."""
    return re.sub(r'[\\/*?:"<>| ]', "_", name)[:50].strip("_")


def download_youtube_video(url: str, output_dir: Path, cookies_file: str = None) -> dict:
    """Download video using yt-dlp and extract attribution metadata."""
    import yt_dlp

    output_dir.mkdir(parents=True, exist_ok=True)
    source_file = output_dir / "source.mp4"
    metadata_path = output_dir / "metadata.json"

    # If the video was already downloaded in a previous run, reuse it!
    if source_file.exists() and metadata_path.exists():
        try:
            with open(metadata_path, "r", encoding="utf-8") as f:
                cached_meta = json.load(f)
            print(f" -> Found previously downloaded video: {source_file.name}")
            print(f" -> Title: {cached_meta.get('title', 'Unknown')}")
            print(f" -> Creator: {cached_meta.get('creator', 'Unknown')}")
            return cached_meta
        except Exception:
            pass  # If corrupt, re-download below

    print(f" -> Connecting to YouTube: {url}")
    source_target_pattern = str(output_dir / "source.%(ext)s")

    # Determine if cookies are provided via parameter, environment, or file
    effective_cookie_file = None
    if cookies_file and Path(cookies_file).exists():
        effective_cookie_file = str(cookies_file)
    elif os.getenv("YOUTUBE_COOKIES"):
        cookie_path = output_dir / "youtube_cookies.txt"
        with open(cookie_path, "w", encoding="utf-8") as cf:
            cf.write(os.getenv("YOUTUBE_COOKIES"))
        effective_cookie_file = str(cookie_path)
    elif (SCRIPT_DIR / "cookies.txt").exists():
        effective_cookie_file = str(SCRIPT_DIR / "cookies.txt")
    elif (REPO_ROOT / "cookies.txt").exists():
        effective_cookie_file = str(REPO_ROOT / "cookies.txt")

    base_opts = {
        "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "outtmpl": source_target_pattern,
        "merge_output_format": "mp4",
        "quiet": False,
        "no_warnings": False,
        "remote_components": ["ejs:github"],
        "js_runtimes": {"node": {}, "deno": {}},
    }
    if effective_cookie_file:
        base_opts["cookiefile"] = effective_cookie_file
        print(f" -> Using YouTube cookies file: {effective_cookie_file}")

    # Try android/ios player client first (bypasses bot detection in cloud/datacenter runners)
    strategies = [
        {
            "name": "Android/iOS Mobile Client",
            "opts": {
                **base_opts,
                "extractor_args": {"youtube": {"player_client": ["android", "ios"]}},
            },
        },
        {
            "name": "Standard Web Client",
            "opts": base_opts,
        },
    ]

    last_error = None
    info = None
    for strategy in strategies:
        try:
            print(f" -> Attempting download using {strategy['name']}...")
            with yt_dlp.YoutubeDL(strategy["opts"]) as ydl:
                info = ydl.extract_info(url, download=True)
            if info:
                break
        except Exception as e:
            last_error = e
            print(f" -> {strategy['name']} warning: {e}")

    if not info:
        raise RuntimeError(
            f"yt-dlp failed to download YouTube video: {last_error}\n"
            "Tip: In cloud environments (like GitHub Actions), YouTube blocks automated datacenter IPs.\n"
            "To bypass: Add your browser cookies as a GitHub Secret named 'YOUTUBE_COOKIES'."
        )

    video_id = info.get("id", "yt_video")
    title = info.get("title", "Unknown Title")
    creator = info.get("uploader") or info.get("channel") or "Unknown Creator"
    webpage_url = info.get("webpage_url") or url
    license_type = info.get("license") or "Standard YouTube License"

    # Locate downloaded source file
    if not source_file.exists():
        candidates = list(output_dir.glob("source.*"))
        if candidates:
            source_file = candidates[0]
        else:
            raise FileNotFoundError(f"Could not locate downloaded file in {output_dir}")

    metadata = {
        "video_id": video_id,
        "title": title,
        "creator": creator,
        "source_url": webpage_url,
        "license_type": license_type,
        "credit_line": f"Credit: {creator} ({webpage_url})",
        "source_file": str(source_file),
    }

    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    print(f" -> Download complete: {source_file.name}")
    print(f" -> Title: {title}")
    print(f" -> Creator: {creator}")
    return metadata


def load_local_video(file_path: str, base_output_dir: Path) -> dict:
    """Prepare a local video file for processing."""
    source_path = Path(file_path).resolve()
    if not source_path.exists():
        raise FileNotFoundError(f"Local video file does not exist: {source_path}")

    # Check if the file is inside an existing output directory with metadata.json
    parent_dir = source_path.parent
    existing_meta = parent_dir / "metadata.json"
    if existing_meta.exists() and parent_dir.name != "output":
        try:
            with open(existing_meta, "r", encoding="utf-8") as f:
                meta = json.load(f)
            print(f" -> Reusing existing job folder: {parent_dir.name}")
            return meta
        except Exception:
            pass

    clean_stem = sanitize_filename(source_path.stem)
    video_id = f"local_{clean_stem}"
    video_output_dir = base_output_dir / video_id
    video_output_dir.mkdir(parents=True, exist_ok=True)

    metadata = {
        "video_id": video_id,
        "title": source_path.stem,
        "creator": "Local User",
        "source_url": str(source_path),
        "license_type": "Local Content",
        "credit_line": f"Credit: Local User ({source_path.name})",
        "source_file": str(source_path),
    }

    metadata_path = video_output_dir / "metadata.json"
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    print(f" -> Loaded local video: {source_path.name}")
    print(f" -> Assigned Video ID: {video_id}")
    return metadata


def transcribe_video(source_file: str, output_dir: Path, model_size: str = "base") -> dict:
    """Transcribe video audio using faster-whisper with word-level timestamps."""
    transcript_path = output_dir / "transcript.json"

    # Reuse existing transcript if already computed
    if transcript_path.exists():
        try:
            with open(transcript_path, "r", encoding="utf-8") as f:
                cached = json.load(f)
            if cached.get("segments"):
                print(f" -> Found existing transcript.json with {len(cached['segments'])} segments. Skipping re-transcription.")
                return cached
        except Exception:
            pass

    from faster_whisper import WhisperModel

    print(f" -> Loading faster-whisper model ('{model_size}' on CPU)...")
    try:
        model = WhisperModel(model_size, device="cpu", compute_type="int8")
    except Exception as e:
        raise RuntimeError(f"Failed to load faster-whisper model '{model_size}': {e}")

    print(f" -> Decoding and transcribing '{Path(source_file).name}' (with word timestamps)...")
    try:
        segments_gen, info = model.transcribe(
            source_file,
            beam_size=5,
            word_timestamps=True,
        )
    except Exception as e:
        raise RuntimeError(f"faster-whisper failed during audio transcription: {e}")

    print(f" -> Detected audio language: {info.language} (confidence: {info.language_probability * 100:.1f}%)")

    segments_list = []
    words_list = []

    for seg in segments_gen:
        segments_list.append({
            "id": seg.id,
            "start": round(seg.start, 2),
            "end": round(seg.end, 2),
            "text": seg.text.strip(),
        })
        if seg.words:
            for w in seg.words:
                words_list.append({
                    "word": w.word.strip(),
                    "start": round(w.start, 2),
                    "end": round(w.end, 2),
                    "probability": round(w.probability, 2),
                })

    if not segments_list:
        raise RuntimeError("Transcription produced zero speech segments. The video might be silent or audio was not detected.")

    transcript_data = {
        "language": info.language,
        "duration": round(info.duration, 2),
        "segments": segments_list,
        "words": words_list,
    }

    with open(transcript_path, "w", encoding="utf-8") as f:
        json.dump(transcript_data, f, indent=2, ensure_ascii=False)

    print(f" -> Transcription complete: {len(segments_list)} sentence segments, {len(words_list)} words.")
    print(f" -> Saved to: {transcript_path}")
    return transcript_data


def select_clips_with_gemini(transcript_data: dict, model_name: str = "gemini-3.8-flash") -> list:
    """Send transcript to Gemini API and parse JSON clip recommendations with auto-retry and model fallback."""
    import time
    from google import genai
    from google.genai import types

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key.strip() == "your_gemini_api_key_here":
        raise ValueError(
            "GEMINI_API_KEY is not set!\n"
            "Please open 'worker/.env' and replace 'your_gemini_api_key_here' with your free key from:\n"
            "https://aistudio.google.com/app/apikey"
        )

    # Build readable transcript representation with timestamps for the LLM
    formatted_lines = []
    for s in transcript_data["segments"]:
        formatted_lines.append(f"[{s['start']:.1f}s - {s['end']:.1f}s] {s['text']}")
    formatted_transcript = "\n".join(formatted_lines)

    prompt = CLIP_SELECTION_PROMPT.format(transcript=formatted_transcript)

    try:
        client = genai.Client(api_key=api_key)
    except Exception as e:
        raise RuntimeError(f"Failed to initialize Gemini client: {e}")

    # Fallback model sequence if Google's servers return a 503 capacity spike
    models_to_try = [model_name]
    for fallback in ["gemini-3.7-flash", "gemini-3.5-flash"]:
        if fallback not in models_to_try:
            models_to_try.append(fallback)

    def _validate_json(raw_text):
        cleaned = raw_text.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```[a-zA-Z]*\n", "", cleaned)
            cleaned = re.sub(r"\n```$", "", cleaned)
        data = json.loads(cleaned)
        if not isinstance(data, list):
            raise ValueError("Gemini response is not a JSON array of clips.")

        valid_clips = []
        required_keys = {"start", "end", "score", "hook", "title", "reason"}
        for item in data:
            if not isinstance(item, dict):
                continue
            if not required_keys.issubset(item.keys()):
                raise ValueError(f"Missing required keys in clip recommendation: {item}")
            start = float(item["start"])
            end = float(item["end"])
            if end <= start:
                continue
            valid_clips.append({
                "start": start,
                "end": end,
                "score": int(item["score"]),
                "hook": str(item["hook"]),
                "title": str(item["title"]),
                "reason": str(item["reason"]),
            })
        if not valid_clips:
            raise ValueError("No valid clips found in Gemini response.")
        return valid_clips

    last_error = None
    for current_model in models_to_try:
        print(f" -> Sending transcript to Google Gemini model: {current_model}...")
        for attempt in range(1, 4):
            try:
                response = client.models.generate_content(
                    model=current_model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        temperature=0.3,
                        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
                    ),
                )
                clips = _validate_json(response.text)
                print(f" -> Gemini ({current_model}) successfully selected {len(clips)} candidate clips.")
                return clips
            except Exception as e:
                err_msg = str(e)
                last_error = e
                # Check for 503 high demand or transient rate-limiting
                if "503" in err_msg or "UNAVAILABLE" in err_msg or "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg:
                    wait_sec = attempt * 3
                    print(f" -> [Warning] {current_model} is temporarily busy ({'503' if '503' in err_msg else 'rate-limited'}). Backing off {wait_sec}s (attempt {attempt}/3)...")
                    time.sleep(wait_sec)
                else:
                    print(f" -> [Warning] Attempt {attempt} with {current_model} failed: {e}")
                    time.sleep(1)

        print(f" -> [Notice] {current_model} unavailable. Trying next fallback model...")

    raise RuntimeError(f"All Gemini models ({', '.join(models_to_try)}) failed. Last error: {last_error}")


def snap_and_filter_clips(raw_clips: list, segments: list) -> list:
    """
    Snap candidate clips to nearest sentence boundaries, enforce 30-90s,
    and drop overlapping segments in favor of higher-scoring clips.
    """
    print(" -> Snapping start and end times to natural sentence boundaries...")

    if not segments:
        raise ValueError("Cannot snap clips: transcript has no sentence segments.")

    snapped_candidates = []

    for raw in raw_clips:
        raw_start = raw["start"]
        raw_end = raw["end"]

        # Find closest segment start and end indices
        best_start_idx = min(range(len(segments)), key=lambda i: abs(segments[i]["start"] - raw_start))
        best_end_idx = min(range(len(segments)), key=lambda i: abs(segments[i]["end"] - raw_end))

        if best_end_idx < best_start_idx:
            best_end_idx = best_start_idx

        cur_start = segments[best_start_idx]["start"]
        cur_end = segments[best_end_idx]["end"]
        cur_duration = cur_end - cur_start

        # If clip is shorter than 30s, expand forward segment-by-segment
        while cur_duration < 30.0 and best_end_idx + 1 < len(segments):
            best_end_idx += 1
            cur_end = segments[best_end_idx]["end"]
            cur_duration = cur_end - cur_start

        # If still shorter than 30s, expand backward segment-by-segment
        while cur_duration < 30.0 and best_start_idx > 0:
            best_start_idx -= 1
            cur_start = segments[best_start_idx]["start"]
            cur_duration = cur_end - cur_start

        # If clip exceeds 90s, trim backward from the end
        while cur_duration > 90.0 and best_end_idx > best_start_idx:
            best_end_idx -= 1
            cur_end = segments[best_end_idx]["end"]
            cur_duration = cur_end - cur_start

        final_duration = round(cur_end - cur_start, 2)
        if 30.0 <= final_duration <= 90.0:
            snapped_candidates.append({
                "start": round(cur_start, 2),
                "end": round(cur_end, 2),
                "duration": final_duration,
                "score": raw["score"],
                "hook": raw["hook"],
                "title": raw["title"],
                "reason": raw["reason"],
                "post_caption": raw.get("post_caption", ""),
                "hashtags": raw.get("hashtags", []),
            })
        else:
            print(f" -> Skipping candidate '{raw['title']}' (duration {final_duration:.1f}s outside 30-90s limit).")

    # Sort candidate clips by viral score (highest first) to resolve overlaps
    snapped_candidates.sort(key=lambda c: c["score"], reverse=True)

    accepted_clips = []
    for cand in snapped_candidates:
        c_start = cand["start"]
        c_end = cand["end"]

        # Check for overlap with already accepted higher-scoring clips
        has_overlap = False
        for acc in accepted_clips:
            # Overlap occurs if max(start1, start2) < min(end1, end2)
            if max(c_start, acc["start"]) < min(c_end, acc["end"]):
                has_overlap = True
                print(f" -> Dropping '{cand['title']}' (overlaps with higher-scoring '{acc['title']}').")
                break

        if not has_overlap:
            accepted_clips.append(cand)

    # Sort final accepted clips chronologically
    accepted_clips.sort(key=lambda c: c["start"])
    print(f" -> Kept {len(accepted_clips)} non-overlapping clips (30-90s each).")
    return accepted_clips


def ensure_face_model(models_dir: Path) -> Path:
    """Ensure the YuNet face detection ONNX model is present."""
    models_dir.mkdir(parents=True, exist_ok=True)
    target_path = models_dir / "face_detection_yunet.onnx"
    if not target_path.exists():
        print(" -> Downloading lightweight YuNet face detector model (~230KB)...")
        import urllib.request
        url = "https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx"
        urllib.request.urlretrieve(url, target_path)
    return target_path


def get_video_dimensions(video_file: str) -> tuple[int, int]:
    """Get video width and height using OpenCV."""
    import cv2
    cap = cv2.VideoCapture(video_file)
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cap.release()
    if w > 0 and h > 0:
        return w, h
    return 1920, 1080


def is_video_vertical_1080p(video_path: str) -> bool:
    """Check if video is 1080x1920."""
    w, h = get_video_dimensions(video_path)
    return w == 1080 and h == 1920


def generate_dynamic_reframe_crop(source_file: str, start_time: float, duration: float, model_path: Path, output_dir: Path) -> tuple[str, list, bool]:
    """
    Intelligently track focus across the clip:
    - Automatically cuts camera between speakers when speakers switch.
    - Centers food, items, and B-roll when no faces are in the shot.
    - Returns an FFmpeg dynamic crop expression and shot metadata.
    """
    import cv2
    import glob
    import shutil

    w, h = get_video_dimensions(source_file)
    crop_w = int(h * 9 / 16)
    crop_w = crop_w - (crop_w % 2)
    default_center_x = w / 2.0

    # Temporary directory for fast 1-fps thumbnail analysis
    thumbs_dir = output_dir / f"thumbs_{int(start_time)}_{int(duration)}"
    thumbs_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Extract 1-fps thumbnails in one fast FFmpeg pass (~1-2 seconds)
        thumb_cmd = [
            "ffmpeg", "-y",
            "-ss", str(start_time),
            "-t", str(duration),
            "-i", source_file,
            "-vf", "fps=1,scale=640:360",
            "-q:v", "3",
            str(thumbs_dir / "f_%03d.jpg")
        ]
        subprocess.run(thumb_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

        thumb_files = sorted(glob.glob(str(thumbs_dir / "f_*.jpg")))
        if not thumb_files:
            return f"{(w - crop_w) // 2}", [], False

        detector = cv2.FaceDetectorYN.create(str(model_path), "", (320, 320), score_threshold=0.6)
        detector.setInputSize((320, 320))
        scale_x = w / 320.0

        raw_targets = []
        any_face_detected = False

        for thumb in thumb_files:
            img = cv2.imread(thumb)
            if img is None:
                raw_targets.append(default_center_x)
                continue
            resized = cv2.resize(img, (320, 320))
            _, faces = detector.detect(resized)

            if faces is None or len(faces) == 0:
                # Food / B-roll / Objects / Packaging: Center frame
                raw_targets.append(default_center_x)
            elif len(faces) == 1:
                any_face_detected = True
                fx, fw = faces[0][0] * scale_x, faces[0][2] * scale_x
                raw_targets.append(fx + fw / 2.0)
            else:
                any_face_detected = True
                # Multi-speaker frame: select most prominent / active speaker
                best_face = max(faces, key=lambda f: f[2] * f[3])
                fx, fw = best_face[0] * scale_x, best_face[2] * scale_x
                raw_targets.append(fx + fw / 2.0)

        # Group into stable camera shots (min 1.5s per shot to prevent erratic jump cuts)
        shots = []
        cur_target = raw_targets[0]
        cur_start = 0.0

        for i in range(1, len(raw_targets)):
            t = float(i)
            target = raw_targets[i]
            if abs(target - cur_target) > 350 and (t - cur_start) >= 1.5:
                shots.append((cur_start, t, cur_target))
                cur_start = t
                cur_target = target

        shots.append((cur_start, duration, cur_target))

        # Build dynamic FFmpeg crop expression
        shot_crops = []
        for s_start, s_end, s_target in shots:
            c_x = int(s_target - crop_w / 2.0)
            c_x = max(0, min(w - crop_w, c_x))
            c_x = c_x - (c_x % 2)
            shot_crops.append((s_start, s_end, c_x))

        if len(shot_crops) == 1:
            crop_expr = str(shot_crops[0][2])
        else:
            parts = []
            for s_start, s_end, c_x in shot_crops[:-1]:
                parts.append(f"if(lt(t,{s_end:.2f}),{c_x},")
            last_crop_x = shot_crops[-1][2]
            crop_expr = "".join(parts) + str(last_crop_x) + (")" * len(parts))

        return crop_expr, shot_crops, any_face_detected

    finally:
        # Clean up temporary thumbnail images
        if thumbs_dir.exists():
            try:
                shutil.rmtree(thumbs_dir)
            except Exception:
                pass


def format_ass_time(seconds: float) -> str:
    """Format seconds into ASS subtitle timestamp format: H:MM:SS.cs"""
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    cs = int(round((seconds - int(seconds)) * 100))
    if cs >= 100:
        secs += 1
        cs = 0
    return f"{hrs:d}:{mins:02d}:{secs:02d}.{cs:02d}"


def generate_ass_subtitles(clip_words: list, clip_start: float, output_ass_path: Path, max_words_per_phrase: int = 2):
    """
    Generate viral, eye-catching animated ASS subtitles for TikTok/Reels:
    - Heavy bold typography (Arial Black 88pt)
    - High-contrast black outline (width 9) and drop shadow
    - Fast 2-word punchy phrasing for maximum audience retention
    - Active word highlighted in bright Neon Yellow with subtle scale pop
    - Positioned at MarginV 480 (safe zone above TikTok UI)
    """
    lines = [
        "[Script Info]",
        "ScriptType: v4.00+",
        "PlayResX: 1080",
        "PlayResY: 1920",
        "ScaledBorderAndShadow: yes",
        "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
        "Style: Default,Arial Black,88,&H00FFFFFF,&H000000FF,&H00000000,&H90000000,-1,0,0,0,100,100,2,0,1,9,3,2,40,40,480,1",
        "",
        "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
    ]

    if not clip_words:
        with open(output_ass_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
        return

    # Normalize relative timestamps inside this clip
    rel_words = []
    for w in clip_words:
        w_text = w.get("word", "").strip().upper()
        if not w_text:
            continue
        w_start = max(0.0, w.get("start", 0.0) - clip_start)
        w_end = max(w_start + 0.1, w.get("end", 0.0) - clip_start)
        rel_words.append({"word": w_text, "start": w_start, "end": w_end})

    # Group words into fast, punchy 2-word (max 3-word) phrases
    phrases = []
    current_phrase = []
    for i, w in enumerate(rel_words):
        current_phrase.append(w)
        ends_sentence = any(w["word"].endswith(punct) for punct in [".", "!", "?", ","])
        has_gap = False
        if i + 1 < len(rel_words):
            gap = rel_words[i + 1]["start"] - w["end"]
            if gap > 0.35:
                has_gap = True
        if len(current_phrase) >= max_words_per_phrase or ends_sentence or has_gap:
            phrases.append(current_phrase)
            current_phrase = []
    if current_phrase:
        phrases.append(current_phrase)

    # For each phrase, generate dialogues highlighting the current active word in Neon Yellow
    for phrase in phrases:
        p_start = phrase[0]["start"]
        p_end = phrase[-1]["end"]

        for idx, active_word in enumerate(phrase):
            w_start_time = active_word["start"]
            if idx + 1 < len(phrase):
                w_end_time = phrase[idx + 1]["start"]
            else:
                w_end_time = p_end

            if w_end_time <= w_start_time:
                w_end_time = w_start_time + 0.15

            start_str = format_ass_time(w_start_time)
            end_str = format_ass_time(w_end_time)

            text_parts = []
            for j, w in enumerate(phrase):
                if j == idx:
                    # Active word: Neon Yellow highlight + 6% scale pop
                    text_parts.append(r"{\c&H0000FFFF&\fscx106\fscy106}" + w["word"] + r"{\r}")
                else:
                    text_parts.append(w["word"])

            dialogue_text = " ".join(text_parts)
            dialogue_line = f"Dialogue: 0,{start_str},{end_str},Default,,0,0,0,,{dialogue_text}"
            lines.append(dialogue_line)

    with open(output_ass_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def render_vertical_clip(source_file: str, start_time: float, duration: float, clip_path: Path, ass_path: Path, crop_expr: str):
    """Render 1080x1920 vertical video with dynamic speaker/food tracking and burned-in subtitles."""
    w, h = get_video_dimensions(source_file)
    crop_w = int(h * 9 / 16)
    crop_w = crop_w - (crop_w % 2)
    escaped_ass = str(ass_path).replace("\\", "/").replace(":", "\\:")

    vf = f"crop={crop_w}:{h}:'{crop_expr}':0,scale=1080:1920:flags=lanczos,subtitles='{escaped_ass}'"

    cmd = [
        "ffmpeg",
        "-y",
        "-ss", str(start_time),
        "-i", source_file,
        "-t", str(duration),
        "-vf", vf,
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "20",
        "-c:a", "aac",
        "-b:a", "192k",
        "-avoid_negative_ts", "make_zero",
        str(clip_path),
    ]

    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg failed rendering {clip_path.name}:\n{result.stderr[-600:]}")


def cut_clips_with_ffmpeg(source_file: str, clips: list, output_dir: Path, metadata: dict, transcript_data: dict = None) -> list:
    """Render each clip into 9:16 vertical video with dynamic speaker switching, food centering, and viral subtitles."""
    models_dir = SCRIPT_DIR / "models"
    face_model = ensure_face_model(models_dir)

    all_words = transcript_data.get("words", []) if transcript_data else []
    final_clips_data = []

    for i, clip in enumerate(clips, 1):
        clip_filename = f"clip_{i:02d}.mp4"
        clip_path = output_dir / clip_filename
        ass_path = output_dir / f"clip_{i:02d}.ass"
        start_time = clip["start"]
        end_time = clip["end"]
        duration = clip["duration"]

        print(f"\n -> Processing [{i}/{len(clips)}] {clip_filename} ({duration:.1f}s) - \"{clip['title']}\"")

        # 1. Extract words and generate eye-catching viral subtitles
        clip_words = [w for w in all_words if start_time <= w.get("start", 0.0) <= end_time]
        print(f"    * Generating viral TikTok subtitles ({len(clip_words)} words)...")
        generate_ass_subtitles(clip_words, start_time, ass_path)

        # 2. Dynamic multi-speaker tracking & food centering
        print(f"    * Analyzing scene shots, speaker switching, and food/object focus...")
        crop_expr, shot_crops, has_face = generate_dynamic_reframe_crop(source_file, start_time, duration, face_model, output_dir)
        print(f"    * Created {len(shot_crops)} dynamic camera angles across {duration:.1f}s.")

        # 3. Render 1080x1920 vertical video with burned-in subtitles
        print(f"    * Rendering 1080x1920 vertical clip with dynamic tracking via FFmpeg...")
        render_vertical_clip(source_file, start_time, duration, clip_path, ass_path, crop_expr)
        print(f"    [OK] Rendered {clip_filename} successfully!")

        clip_record = {
            "clip_id": f"clip_{i:02d}",
            "filename": clip_filename,
            "file_path": str(clip_path),
            "start": clip["start"],
            "end": clip["end"],
            "duration": clip["duration"],
            "score": clip["score"],
            "hook": clip["hook"],
            "title": clip["title"],
            "reason": clip["reason"],
            "post_caption": clip.get("post_caption", ""),
            "hashtags": clip.get("hashtags", []),
            "has_face": has_face,
            "dynamic_reframe": True,
            "shots_count": len(shot_crops),
            # Video source attribution
            "source_url": metadata.get("source_url", ""),
            "creator": metadata.get("creator", ""),
            "license_type": metadata.get("license_type", ""),
            "credit_line": metadata.get("credit_line", ""),
        }
        final_clips_data.append(clip_record)

    # Save clips.json
    clips_json_path = output_dir / "clips.json"
    with open(clips_json_path, "w", encoding="utf-8") as f:
        json.dump(final_clips_data, f, indent=2, ensure_ascii=False)

    print(f"\n -> Successfully saved metadata to: {clips_json_path}")
    return final_clips_data


def main():
    parser = argparse.ArgumentParser(description="Clippin Stage 1: Automated Local Video Clipper")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--url", help="YouTube video URL to download and clip")
    group.add_argument("--file", help="Path to a local video file (.mp4)")

    parser.add_argument(
        "--whisper-model",
        default="base",
        choices=["tiny", "base", "small", "medium", "large-v3"],
        help="faster-whisper model size (default: base)",
    )
    parser.add_argument(
        "--gemini-model",
        default=os.getenv("GEMINI_MODEL", "gemini-3.8-flash"),
        help="Gemini model name (default: gemini-3.8-flash)",
    )
    parser.add_argument(
        "--output-dir",
        default=str(REPO_ROOT / "output"),
        help="Root directory for outputs (default: ./output)",
    )
    parser.add_argument(
        "--cookies",
        default=None,
        help="Path to YouTube cookies.txt file",
    )
    parser.add_argument(
        "--rerender",
        action="store_true",
        help="Re-render 9:16 vertical clips with dynamic camera tracking and new captions without re-running Whisper or Gemini",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-running transcription, clip selection, and cutting even if outputs exist",
    )

    args = parser.parse_args()
    check_ffmpeg()

    base_output_dir = Path(args.output_dir).resolve()

    # --------------------------------------------------------------------------
    # STEP 1: Video Ingestion
    # --------------------------------------------------------------------------
    print("\n" + "=" * 60)
    print(">>> [STEP 1/5] INGESTING VIDEO")
    print("=" * 60)
    try:
        if args.url:
            import yt_dlp

            # Resolve cookies if provided via argument, environment variable, or file
            cookie_file = None
            if args.cookies and Path(args.cookies).exists():
                cookie_file = str(args.cookies)
            elif os.getenv("YOUTUBE_COOKIES"):
                temp_cookie_path = base_output_dir / "youtube_cookies.txt"
                temp_cookie_path.parent.mkdir(parents=True, exist_ok=True)
                with open(temp_cookie_path, "w", encoding="utf-8") as cf:
                    cf.write(os.getenv("YOUTUBE_COOKIES"))
                cookie_file = str(temp_cookie_path)
            elif (SCRIPT_DIR / "cookies.txt").exists():
                cookie_file = str(SCRIPT_DIR / "cookies.txt")
            elif (REPO_ROOT / "cookies.txt").exists():
                cookie_file = str(REPO_ROOT / "cookies.txt")

            extract_opts = {
                "quiet": True,
                "remote_components": ["ejs:github"],
                "js_runtimes": {"node": {}, "deno": {}},
                "extractor_args": {"youtube": {"player_client": ["android", "ios"]}},
            }
            if cookie_file:
                extract_opts["cookiefile"] = cookie_file

            with yt_dlp.YoutubeDL(extract_opts) as ydl:
                try:
                    info = ydl.extract_info(args.url, download=False)
                    vid_id = info.get("id", "yt_video")
                except Exception:
                    vid_id = sanitize_filename(args.url.split("v=")[-1][:15])
            video_dir = base_output_dir / vid_id
            metadata = download_youtube_video(args.url, video_dir, cookies_file=cookie_file)
        else:
            metadata = load_local_video(args.file, base_output_dir)
            video_dir = Path(metadata["source_file"]).parent if Path(metadata["source_file"]).parent.name != "output" else base_output_dir / metadata["video_id"]

        source_video = metadata["source_file"]
        print("[OK] STEP 1 COMPLETE: Video is ready for processing.")
    except Exception as e:
        print("\n" + "!" * 60)
        print("[FAILED AT STEP 1: VIDEO INGESTION]")
        print(f"Reason: Could not download or open video file.")
        print(f"Details: {e}")
        print("!" * 60 + "\n")
        sys.exit(1)

    # Check if all clips are already rendered in 1080x1920 vertical format with dynamic reframe
    clips_json_path = video_dir / "clips.json"
    existing_clips = None
    if not args.rerender and not args.force and clips_json_path.exists():
        try:
            with open(clips_json_path, "r", encoding="utf-8") as f:
                existing_clips = json.load(f)
            if existing_clips and all(Path(c.get("file_path", "")).exists() and is_video_vertical_1080p(c.get("file_path", "")) and c.get("dynamic_reframe") for c in existing_clips):
                print("\n" + "=" * 60)
                print(f"[SUCCESS] ALL CLIPS ALREADY RENDERED IN 1080x1920 ({len(existing_clips)} clips found).")
                print(f"Destination folder: {video_dir}")
                for c in existing_clips:
                    print(f"   [{c['clip_id']}] \"{c['title']}\" ({c['duration']}s, Viral Score: {c['score']}/100) -> {c['filename']}")
                print("=" * 60)
                print("(To re-render with updated styling, run again with the --rerender flag)\n")
                return
        except Exception:
            pass

    # --------------------------------------------------------------------------
    # STEP 2: Speech Transcription (faster-whisper)
    # --------------------------------------------------------------------------
    print("\n" + "=" * 60)
    print(">>> [STEP 2/5] TRANSCRIBING AUDIO (faster-whisper)")
    print("=" * 60)
    try:
        transcript_data = transcribe_video(source_video, video_dir, model_size=args.whisper_model)
        print("[OK] STEP 2 COMPLETE: Audio transcribed and transcript.json saved.")
    except Exception as e:
        print("\n" + "!" * 60)
        print("[FAILED AT STEP 2: TRANSCRIPTION]")
        print(f"Reason: Audio decoding or speech recognition failed.")
        print(f"Details: {e}")
        print("!" * 60 + "\n")
        sys.exit(1)

    # --------------------------------------------------------------------------
    # STEP 3 & 4: Clip Selection & Boundary Snapping
    # --------------------------------------------------------------------------
    filtered_clips = None
    if existing_clips and not args.force:
        print("\n" + "=" * 60)
        print(">>> [STEPS 3 & 4] REUSING EXISTING CLIPS (Gemini skipped to save credits)")
        print("=" * 60)
        print(f" -> Found {len(existing_clips)} pre-selected clips in clips.json. Upgrading to vertical 9:16.")
        filtered_clips = existing_clips
    else:
        print("\n" + "=" * 60)
        print(">>> [STEP 3/5] SELECTING VIRAL CLIPS (Google Gemini)")
        print("=" * 60)
        try:
            raw_clips = select_clips_with_gemini(transcript_data, model_name=args.gemini_model)
            print(f"[OK] STEP 3 COMPLETE: Gemini selected {len(raw_clips)} candidate segments.")
        except Exception as e:
            print("\n" + "!" * 60)
            print("[FAILED AT STEP 3: GEMINI AI SELECTION]")
            print(f"Reason: Gemini API request or JSON parsing failed.")
            print(f"Details: {e}")
            print("!" * 60 + "\n")
            sys.exit(1)

        print("\n" + "=" * 60)
        print(">>> [STEP 4/5] SNAPPING SENTENCE BOUNDARIES & RESOLVING OVERLAPS")
        print("=" * 60)
        try:
            filtered_clips = snap_and_filter_clips(raw_clips, transcript_data["segments"])
            if not filtered_clips:
                print("\n[Notice] No clips matched the 30-90s non-overlapping criteria. Please try another video.")
                return
            print(f"[OK] STEP 4 COMPLETE: {len(filtered_clips)} approved non-overlapping clips (30-90s).")
        except Exception as e:
            print("\n" + "!" * 60)
            print("[FAILED AT STEP 4: SENTENCE SNAPPING]")
            print(f"Reason: Failed to align clip timestamps with transcript sentences.")
            print(f"Details: {e}")
            print("!" * 60 + "\n")
            sys.exit(1)

    # --------------------------------------------------------------------------
    # STEP 5: Vertical 9:16 Video Cutting & Caption Burning (FFmpeg + YuNet + ASS)
    # --------------------------------------------------------------------------
    print("\n" + "=" * 60)
    print(">>> [STEP 5/5] RENDERING 9:16 VERTICAL CLIPS WITH ANIMATED CAPTIONS")
    print("=" * 60)
    try:
        final_clips = cut_clips_with_ffmpeg(source_video, filtered_clips, video_dir, metadata, transcript_data)
        print(f"[OK] STEP 5 COMPLETE: All {len(final_clips)} vertical clips successfully rendered.")
    except Exception as e:
        print("\n" + "!" * 60)
        print("[FAILED AT STEP 5: RENDERING VERTICAL CLIPS]")
        print(f"Reason: FFmpeg or face detection failed during rendering.")
        print(f"Details: {e}")
        print("!" * 60 + "\n")
        sys.exit(1)

    # --------------------------------------------------------------------------
    # Summary
    # --------------------------------------------------------------------------
    print("\n" + "=" * 60)
    print(f"[SUCCESS] PIPELINE FINISHED! Created {len(final_clips)} clips.")
    print(f"Destination folder: {video_dir}")
    for c in final_clips:
        print(f"   [{c['clip_id']}] \"{c['title']}\" ({c['duration']}s, Viral Score: {c['score']}/100) -> {c['filename']}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
