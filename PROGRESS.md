# Project Progress: Clippin

## Current Status: Stage 2 Complete & Tested (Ready for Stage 3 Supabase Integration)

---

### Done
- [x] Initialized Git repository structure and comprehensive `.gitignore` (safeguarding `.env`, video binaries, and node_modules).
- [x] Configured Google Gemini free-tier integration (`gemini-3.8-flash` via official `google-genai` SDK with multi-model fallback).
- [x] Created `worker/requirements.txt` with dependencies (`google-genai`, `faster-whisper`, `yt-dlp`, `python-dotenv`, `opencv-python`).
- [x] Created `worker/prompts.py` with viral clip selection criteria, title, hook, viral score, post caption, and hashtags.
- [x] Implemented `worker/clipper.py` pipeline (video ingestion, transcription, sentence boundary snapping, cutting, and metadata export).
- [x] Added `post_caption` and `hashtags` fields to `prompts.py`, `clipper.py`, and backfilled `output/lGcH3n7bfl4/clips.json`.
- [x] Implemented Stage 2: Face tracking centering via OpenCV YuNet ONNX model (`worker/models/face_detection_yunet.onnx`).
- [x] Implemented Stage 2: Fallback 9:16 layout with blurred background for faceless or screen-recording clips.
- [x] Implemented Stage 2: Animated word-by-word ASS subtitle generation with active word yellow highlighting (`{\c&H0000FFFF&}`).
- [x] Implemented Stage 2: FFmpeg vertical rendering to 1080x1920 H.264/AAC with burned-in subtitles.
- [x] Prepared Supabase PostgreSQL schema, RLS policies, and private bucket definitions in `supabase/schema.sql`.
- [x] Prepared GitHub Actions manual workflow in `.github/workflows/worker.yml`.
- [x] Updated `worker/.env.example` with all worker and Supabase configuration variables.

---

### Tested
- [x] **Local Clipper Pipeline**: Tested on 25-minute YouTube video (`lGcH3n7bfl4`), successfully generating 6 candidate clips.
- [x] **Metadata Validation (`clips.json`)**: Verified all required fields are present (`start`, `end`, `score`, `hook`, `title`, `reason`, `post_caption`, `hashtags`, `credit_line`).
- [x] **Stage 2 Vertical Video & Audio Verification**: Tested with `ffprobe` on `clip_01.mp4` through `clip_06.mp4`. Confirmed 1080x1920 resolution, H.264 video, AAC audio, and burned-in subtitles.
- [x] **Face Tracking Centering**: Verified speaker face detection and horizontal centering via YuNet.

---

### Untested
- [ ] **Supabase Setup**: Executing `supabase/schema.sql` in Supabase SQL Editor and verifying table/bucket creation.
- [ ] **Supabase Storage Upload**: Direct worker upload of rendered `.mp4` clips to the private `"clips"` storage bucket and row insertion in `videos`/`clips` tables.
- [ ] **GitHub Actions Runner**: Running `.github/workflows/worker.yml` on GitHub cloud runners with secrets.
- [ ] **Stage 5 Web Dashboard**: Next.js App Router review dashboard in `/dashboard` (not yet initialized).

---

### Next Step
1. Complete Supabase setup (run SQL schema and get `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY`).
2. Implement Stage 3: Connect worker directly to Supabase (`supabase-py`) to upload rendered clips and insert video/clip records.
3. Initialize Stage 5: Next.js review dashboard in `/dashboard`.
