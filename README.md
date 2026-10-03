# 🎬 Clippin

An automated video clipping engine that converts long-form videos into high-engagement, standalone short clips (30–90 seconds) ready for TikTok, Reels, and YouTube Shorts.

---

## 🚀 Stage 1: Local Clip Engine

The local worker script (`worker/clipper.py`) does the following:
1. **Downloads or loads a video** (via YouTube URL or local `.mp4`).
2. **Transcribes speech** into word-by-word and sentence-level timestamps using `faster-whisper` (on CPU).
3. **Selects the best viral hooks** using Google's free-tier `gemini-3.8-flash` AI model.
4. **Snaps timestamps** to natural sentence boundaries (30–90s duration, no cut-off speech, no overlapping clips).
5. **Cuts clips cleanly** into `clip_01.mp4`, `clip_02.mp4`, etc. using `ffmpeg`.
6. **Saves structured metadata** in `clips.json` (hook, title, viral score, explanation, and creator credit).

---

## 📋 Prerequisites

1. **Python 3.10 or newer** (already verified on your system).
2. **FFmpeg** (already verified on your system).
3. **Google Gemini API Key** (100% Free):
   - Go to [Google AI Studio](https://aistudio.google.com/app/apikey).
   - Sign in with your Google account.
   - Click **"Create API Key"** and copy it.

---

## 🛠️ Step-by-Step Setup

### Step 1: Install Python Dependencies
Open PowerShell or your terminal in this project folder and run:

```powershell
pip install -r worker/requirements.txt
```

### Step 2: Add your Gemini API Key
Create a `.env` file inside the `worker` folder:
1. Duplicate `worker/.env.example` and rename it to `worker/.env`.
2. Open `worker/.env` in your text editor and paste your key:
   ```env
   GEMINI_API_KEY=AIzaSyYourActualKeyHere
   ```
*(Note: `.env` is listed in `.gitignore` so your key will never be uploaded to GitHub.)*

---

## 🎯 How to Run

### Option A: From a YouTube Video URL
```powershell
python worker/clipper.py --url "https://www.youtube.com/watch?v=YOUR_VIDEO_ID"
```

### Option B: From a Local Video File
Place your video file in the project folder and run:
```powershell
python worker/clipper.py --file "my_video.mp4"
```

---

## 📁 Output Structure

All outputs are saved to the `output/<video-id>/` folder:

```text
output/
└── <video-id>/
    ├── source.mp4          # The original downloaded video
    ├── metadata.json       # Video title, creator, license & credit line
    ├── transcript.json     # Word-level and sentence-level timestamps
    ├── clips.json          # Selected clips with hooks, titles, and viral scores
    ├── clip_01.mp4         # Extracted 30-90s video clip
    └── clip_02.mp4         # Extracted 30-90s video clip
```