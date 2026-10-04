# Project Progress: Clippin

## Current Status: Refinements Verified & Synced (Ready for Option B: GitHub Actions Cloud Worker)

---

### Current State
1. **Pipeline & Transcription (Stage 1)**: Complete. Whisper transcription snaps on sentence boundaries, cuts clean 30-90s clips, and Gemini AI scores virality with titles, hooks, reasons, captions, and hashtags.
2. **Multi-Speaker Centering & Framing (Stage 2)**: Complete & Verified.
   - **Speaker Tracking**: Calibrated exact horizontal coordinates for Max (Left: $X=1350$), Kyle (Right: $X=2700$), Nick DiGiovanni ($X=880$), Bayashi ($X=2850$), and food/product close-ups ($X=1920$ or $X=1500$ when hand-held).
   - **Fixes Applied**:
     - `clip_01`: Hook now immediately centers on Max speaking (fixed empty middle wall bug).
     - `clip_03`: Waffle ice cream showcase at 0:13 centered on both speaker and product (fixed cut-off bug).
     - `clip_05` & `clip_06`: Confirmed proper framing for Kyle (crispy crust at 0:26), Nick DiGiovanni, and Bayashi.
   - **Subtitle Formatting Overhaul**:
     - Scaled font size from `88pt` to `68pt` Arial Black.
     - Sized safe zone margins to `MarginL: 70`, `MarginR: 70`, `MarginV: 340` with `WrapStyle: 2`.
     - Zero horizontal clipping or edge cutoff.
3. **Supabase Cloud Backend (Stage 3)**: Complete & Verified.
   - PostgreSQL tables (`videos`, `clips`) and private storage bucket (`clips`).
   - All 6 re-rendered vertical clips (16.4MB - 29.3MB each) uploaded with `upsert: true`.
   - Real-time pre-signed streaming & attachment download URLs generated on demand.
4. **Web Review Studio (Stage 4)**: Live & Operational on `http://localhost:3000`.
   - **Native Video Display**: Removed artificial `max-height: 480px` constraint; card grid and theater modal now maintain true 1080x1920 9:16 vertical resolution and orientation.
   - **Mobile Device Viewport**: Redesigned Theater Modal with a high-fidelity phone mockup frame and `1080 × 1920 (9:16 Full HD)` format badges.
   - **Review Workflows**: 1-click caption copy, 1-click hashtag copy, instant optimistic "Approve" / "Reject" toggles, and direct MP4 downloads.

---

### Completed Action Plan
- [x] **1. Studio Video Display Overhaul**:
  - Updated `dashboard/app/globals.css` and `dashboard/app/page.tsx`.
  - Maintained true 9:16 vertical ratio without artificial `max-height` clipping.
  - Used `object-fit: contain` and natural vertical sizing so the entire 1080x1920 frame is 100% visible, uncropped, and sharp.
  - Redesigned Theater Modal with a high-fidelity mobile device viewport frame displaying exact 1080x1920 9:16 orientation and resolution info badge.
- [x] **2. Speaker Framing & Centering Overhaul**:
  - Re-mapped `clip_01` catalog so the intro immediately centers on Max speaking on the left rather than the empty wall.
  - Re-mapped `clip_03` catalog at 0:13 so Max and the waffle ice cream he is holding are centered.
  - Adjusted ASS subtitle styles: decreased font size from 88pt to 68pt with safe horizontal margins (`MarginL: 70`, `MarginR: 70`) and `MarginV: 340` so text never spills off-screen.
- [x] **3. Re-render & Supabase Cloud Sync**:
  - Re-rendered all 6 clips (`clip_01.mp4` through `clip_06.mp4`) with corrected dynamic speaker framing and safe ASS subtitles.
  - Re-uploaded all 6 updated clips to the private `clips` Supabase storage bucket and verified database rows.

---

### Future Plans
- **Stage 5 (Option B - Next Up)**:
  - Configure GitHub Actions Cloud Worker workflow (`.github/workflows/worker.yml`).
  - Test cloud-based automated pipeline with GitHub Secrets (`GEMINI_API_KEY`, `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`).
  - Achieve $0 100% cloud-automated video repurposing without requiring local machine CPU/GPU.
- **Stage 6 (Auto-Publishing / Webhooks)**:
  - Integrate social publishing webhook or one-click export to TikTok / YouTube Shorts / Instagram Reels once clips are marked `approved`.
