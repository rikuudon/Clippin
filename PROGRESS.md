# Project Progress: Clippin

## Current Status: Stage 4 Web Review Dashboard Live & Operational (Next.js Studio)

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
- [x] Built Stage 4: Next.js Review Dashboard (`/dashboard`) using App Router, TypeScript, and rich Vanilla CSS design tokens.
- [x] Connected dashboard to Supabase Cloud backend with server-side pre-signed video streaming & attachment download URLs.
- [x] Implemented full clip curation workflow: live 9:16 video players, virality score badges, hook breakdowns, one-click "Copy Caption" & "Copy Hashtags" buttons, instant "Approve" / "Reject" toggles with optimistic state updates, and an interactive full-screen Theater Modal.
- [x] Created `dashboard/.env.example` and secured production credentials in `.env.local`.

---

### Tested & Verified
- [x] **Local Clipper Pipeline**: Tested on 25-minute YouTube video (`lGcH3n7bfl4`), successfully generating 6 candidate clips.
- [x] **Metadata Validation (`clips.json`)**: Verified all required fields are present (`start`, `end`, `score`, `hook`, `title`, `reason`, `post_caption`, `hashtags`, `credit_line`).
- [x] **Stage 2 Dynamic Camera & Multi-Speaker Centering**: Verified on all 6 clips. Kyle centered in clip_05; Nick DiGiovanni, Bayashi, and Max each centered when speaking in clip_06.
- [x] **Viral Subtitle Verification**: Verified punchy 2-word Hormozi-style subtitles with Arial Black, heavy outline, and neon yellow pop.
- [x] **Codec Validation**: Verified output clips use H.264 video codec (1080x1920) and AAC audio codec via `ffprobe`.
- [x] **Stage 3 Supabase Integration**: Verified end-to-end sync with user's Supabase project (`nlbfnrodgwtfhdswkubt`). Video record inserted, all 6 clips uploaded to `clips` bucket, and rows inserted in `public.clips`.
- [x] **Stage 4 Next.js Build**: Production build (`npm run build`) compiled successfully with Turbopack and zero TypeScript errors.
- [x] **Stage 4 API Routes**:
  - `GET /api/clips`: Successfully fetches videos and clips, signs private bucket storage URLs, and computes real-time statistics.
  - `PATCH /api/clips/[id]`: Verified bidirectional status updates (`ready` -> `approved` -> `ready`) directly syncing to Supabase.
- [x] **Stage 4 Live Dev Server**: Next.js server actively running on `http://localhost:3000`.

---

### Ready for Next Action
- The Review Dashboard is running and ready for you to preview, play, approve, and download clips at `http://localhost:3000`.
