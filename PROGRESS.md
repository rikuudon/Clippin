# Project Progress: Clippin

## Current Status: Stage 3 Complete & Tested (Ready for Stage 5 Web Dashboard)

---

### Done
- [x] Initialized Git repository structure and comprehensive `.gitignore` (safeguarding `.env`, video binaries, and node_modules).
- [x] Configured Google Gemini free-tier integration (`gemini-3.8-flash` via official `google-genai` SDK with multi-model fallback).
- [x] Created `worker/requirements.txt` with dependencies (`google-genai`, `faster-whisper`, `yt-dlp`, `python-dotenv`, `opencv-python`, `httpx`).
- [x] Created `worker/prompts.py` with viral clip selection criteria, title, hook, viral score, post caption, and hashtags.
- [x] Implemented `worker/clipper.py` pipeline (video ingestion, transcription, sentence boundary snapping, cutting, and metadata export).
- [x] Added `post_caption` and `hashtags` fields to `prompts.py`, `clipper.py`, and backfilled `output/lGcH3n7bfl4/clips.json`.
- [x] Implemented Stage 2: Dynamic multi-shot camera tracking across speaker cuts and focal shifts via OpenCV YuNet ONNX model (`worker/models/face_detection_yunet.onnx`).
- [x] Implemented Stage 2: Multi-speaker centering catalog and speech turn alignment (Kyle at 0:26 in clip_05; Nick, Bayashi, and Max in clip_06).
- [x] Implemented Stage 2: Automatic food, product, and B-roll centering (`X = width / 2`) during object showcase moments.
- [x] Implemented Stage 2: Viral high-retention ASS subtitles (bold Arial Black 88pt, black outline 9, drop shadow 3, fast 2-word punchy phrasing, active word Electric Neon Yellow highlight with 6% scale pop, safe zone MarginV 480).
- [x] Implemented Stage 2: FFmpeg single-pass dynamic evaluation crop expression with Lanczos scaling to 1080x1920 H.264/AAC.
- [x] Prepared Supabase PostgreSQL schema, RLS policies, and private bucket definitions in `supabase/schema.sql`.
- [x] Implemented Stage 3: Direct automated worker sync to Supabase (upserting video record, uploading 9:16 vertical `.mp4` clips to private `clips` storage bucket, and inserting clip records in database).
- [x] Prepared GitHub Actions manual workflow in `.github/workflows/worker.yml`.
- [x] Updated `worker/.env.example` with all worker and Supabase configuration variables.

---

### Tested
- [x] **Local Clipper Pipeline**: Tested on 25-minute YouTube video (`lGcH3n7bfl4`), successfully generating 6 candidate clips.
- [x] **Metadata Validation (`clips.json`)**: Verified all required fields are present (`start`, `end`, `score`, `hook`, `title`, `reason`, `post_caption`, `hashtags`, `credit_line`).
- [x] **Stage 2 Dynamic Camera & Multi-Speaker Centering**: Verified on all 6 clips. Kyle centered in clip_05; Nick DiGiovanni, Bayashi, and Max each centered when speaking in clip_06.
- [x] **Viral Subtitle Verification**: Verified punchy 2-word Hormozi-style subtitles with Arial Black, heavy outline, and neon yellow pop.
- [x] **Codec Validation**: Verified output clips use H.264 video codec (1080x1920) and AAC audio codec via `ffprobe`.
- [x] **Stage 3 Supabase Integration**: Verified end-to-end sync with user's Supabase project (`nlbfnrodgwtfhdswkubt`). Video record inserted, all 6 clips uploaded to `clips` bucket, and rows inserted in `public.clips`.

---

### Untested
- [ ] **GitHub Actions Runner**: Running `.github/workflows/worker.yml` on GitHub cloud runners with secrets.
- [ ] **Stage 5 Web Dashboard**: Next.js App Router review dashboard in `/dashboard` (not yet initialized).

---

### Next Step
1. Initialize Stage 5: Next.js App Router review dashboard in `/dashboard` to preview, play, approve, reject, edit captions, and download viral clips.
