# 🎶 Delfo Studio 95

> **Retro Windows 95 / Winamp-inspired web app to convert YouTube, TikTok & Instagram videos to MP3.**

![Delfo Studio 95](https://img.shields.io/badge/style-Windows%2095-blue?style=flat-square)
![License](https://img.shields.io/badge/license-MIT-green?style=flat-square)
![Backend](https://img.shields.io/badge/backend-FastAPI%20%2B%20yt--dlp-orange?style=flat-square)

---

## ✨ Features

- 🎵 Convert YouTube, YouTube Shorts, TikTok, Instagram Reels to MP3
- 🖥️ Retro Windows 95 / Winamp aesthetic
- 🚀 No database required — zero state, files cleaned up after download
- 🆓 Deployable entirely for free
- ⚠️ Full error handling (invalid URL, unsupported platform, too-long video, ffmpeg failures)

## 📁 Structure

```
delfo-studio-95/
├── frontend/
│   └── index.html          # Single-file frontend (HTML + CSS + JS)
├── backend/
│   ├── main.py             # FastAPI app
│   ├── requirements.txt    # Python dependencies
│   ├── build.sh            # Render build script (installs ffmpeg)
│   └── Procfile            # Process definition
├── render.yaml             # Render deploy config
├── README.md
└── .gitignore
```

## 🛠️ Local Development

### Prerequisites
- Python 3.11+
- `ffmpeg` installed (`brew install ffmpeg` / `apt install ffmpeg`)
- `yt-dlp` (installed via pip)

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

API will be available at `http://localhost:8000`

### Frontend

Open `frontend/index.html` directly in your browser, or serve it:

```bash
cd frontend
python -m http.server 3000
# Open http://localhost:3000
```

> The frontend auto-detects `localhost` and points to `http://localhost:8000`.

---

## 🚀 Deploy

### Frontend → GitHub Pages

1. Push repo to GitHub
2. Go to **Settings → Pages**
3. Source: `Deploy from branch` → `main` → `/frontend` folder
4. Your site will be live at `https://yourusername.github.io/delfo-studio-95/`

**OR deploy to Vercel:**
```bash
npx vercel --cwd frontend
```

### Backend → Render

1. Go to [render.com](https://render.com) and create a free account
2. New → **Web Service** → Connect your GitHub repo
3. Configure:
   - **Root Directory:** `backend`
   - **Build Command:** `bash build.sh`
   - **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Environment:** Python 3
4. Deploy!
5. Copy your Render URL (e.g. `https://delfo-studio-95-api.onrender.com`)

### Connect Frontend to Backend

After deploying the backend, edit `frontend/index.html`:

```javascript
// Find this line (around line 200):
: 'https://YOUR-RENDER-APP.onrender.com'; // ← update after deploy

// Replace with your actual URL:
: 'https://delfo-studio-95-api.onrender.com';
```

---

## ⚙️ API Reference

### `POST /api/convert`

Convert a video URL to MP3.

**Request:**
```json
{
  "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
}
```

**Response:** Binary MP3 file stream with headers:
- `Content-Type: audio/mpeg`
- `Content-Disposition: attachment; filename="video_title.mp3"`

**Error responses:**
| Status | Reason |
|--------|--------|
| 400 | Invalid or unsupported URL |
| 422 | Video unavailable, private, or too long |
| 500 | Server / ffmpeg error |
| 504 | Conversion timeout |

---

## ⚠️ Limitations (Free Tier)

| Constraint | Limit |
|------------|-------|
| Max video duration | 10 minutes |
| Request timeout | 120 seconds |
| Render cold start | ~30 seconds (first request) |
| Concurrent conversions | 1 (free tier single instance) |

---

## 🔧 Tech Stack

| Layer | Tech |
|-------|------|
| Frontend | HTML5 + CSS3 + Vanilla JS |
| Backend | Python 3.11 + FastAPI |
| Audio extraction | yt-dlp |
| Audio conversion | ffmpeg |
| Frontend hosting | GitHub Pages / Vercel |
| Backend hosting | Render (free tier) |

---

## 📝 Notes

- Files are **never stored permanently** — deleted immediately after the download stream completes
- yt-dlp is updated regularly; pin versions in `requirements.txt` for stability
- Render free tier **spins down after 15 min of inactivity** — first request may take 30s

---

## 📜 License

MIT © 2025 Delfo Systems Inc.
