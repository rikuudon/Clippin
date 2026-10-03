# Project Progress: Clippin

## Current Status: Stage 1 Verified & Patched (Ready for Supabase Setup & Stage 2)

---

### Done
- [x] Initialized Git repository structure and comprehensive `.gitignore` (safeguarding `.env`, video binaries, and node_modules).
- [x] Configured Google Gemini free-tier integration (`gemini-3.8-flash` via official `google-genai` SDK with multi-model fallback).
- [x] Created `worker/requirements.txt` with dependencies (`google-genai`, `faster-whisper`, `yt-dlp`, `python-dotenv`, `opencv-python`).
- [x] Created `worker/prompts.py` with viral clip selection criteria, title, hook, viral score, post caption, and hashtags.
- [x] Implemented `worker/clipper.py` pipeline (video ingestion, transcription, sentence boundary snapping, cutting, and metadata export).
- [x] Added `post_caption` and `hashtags` fields to `prompts.py`, `clipper.py`, and backfilled `output/lGcH3n7bfl4/clips.json`.
- [x] Prepared Supabase PostgreSQL schema, RLS policies, and private bucket definitions in `supabase/schema.sql`.
- [x] Prepared GitHub Actions manual workflow in `.github/workflows/worker.yml`.
- [x] Updated `worker/.env.example` with all worker and Supabase configuration variables.

---

### Tested
- [x] **Local Clipper Pipeline**: Tested on 25-minute YouTube video (`lGcH3n7bfl4`), successfully generating 6 candidate clips.
- [x] **Metadata Validation (`clips.json`)**: Verified all required fields are present (`start`, `end`, `score`, `hook`, `title`, `reason`, `post_caption`, `hashtags`, `credit_line`).
- [x] **Codec Validation**: Verified output clips use H.264 video codec and AAC audio codec via `ffprobe`.

---

### Untested
- [ ] **Supabase Setup**: Executing `supabase/schema.sql` in Supabase SQL Editor and verifying table/bucket creation.
- [ ] **GitHub Actions Runner**: Running `.github/workflows/worker.yml` on GitHub cloud runners with secrets.
- [ ] **Supabase Storage Upload**: Direct worker upload of rendered `.mp4` clips to the private `"clips"` storage bucket (code not yet integrated into `clipper.py`).
- [ ] **Stage 2 Video Styling**: 9:16 vertical smart cropping (face tracking / background blur) and burned-in word-by-word ASS subtitles.
- [ ] **Stage 5 Web Dashboard**: Next.js App Router review dashboard in `/dashboard` (not yet initialized).

---

### Known Issues
- **Resolution & Subtitles**: Rendered test clips are 3840x2160 (horizontal 16:9 4K) without burned-in captions because Stage 2 video transformation has not yet been implemented in `clipper.py`.
- **Worker Supabase Sync**: The worker currently writes outputs only to the local filesystem (`output/`) and GitHub Actions artifacts; it does not yet write directly to the Supabase database or storage buckets.

---

### Next Step
1. Complete manual Supabase setup (run SQL schema and verify private storage buckets).
2. Add GitHub repository secrets (`GEMINI_API_KEY`, `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`).
3. Implement Stage 2 in `worker/clipper.py` (9:16 vertical cropping + ASS burned-in subtitles).
4. Connect worker directly to Supabase to insert clip rows and upload MP4 files (Stage 3).
