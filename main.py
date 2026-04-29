import os
import uuid
import subprocess
import asyncio
import re
from pathlib import Path
from urllib.parse import urlparse

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

app = FastAPI(title="Delfo Studio 95 API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

TMP_DIR = Path("/tmp/delfo")
TMP_DIR.mkdir(parents=True, exist_ok=True)

MAX_DURATION_SECONDS = 600


class ConvertRequest(BaseModel):
    url: str


def validate_url(url: str) -> None:
    url = url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="URL is required.")
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            raise ValueError("scheme")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid URL format.")
    allowed = {"youtube.com", "youtu.be", "tiktok.com", "instagram.com", "m.youtube.com"}
    if not any(d in parsed.netloc.lower() for d in allowed):
        raise HTTPException(status_code=400, detail="Unsupported platform. Supported: YouTube, TikTok, Instagram Reels.")


async def get_video_duration(url: str) -> float:
    proc = await asyncio.create_subprocess_exec(
        "yt-dlp",
        "--no-playlist",
        "--extractor-args", "youtube:player_client=tv_embedded",
        "--print", "%(duration)s",
        url,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30)
    if proc.returncode != 0:
        err = stderr.decode(errors="replace").strip()
        if "private" in err.lower() or "unavailable" in err.lower():
            raise HTTPException(status_code=422, detail="Video is private or unavailable.")
        raise HTTPException(status_code=422, detail=f"Could not fetch video info: {err[:200]}")
    raw = stdout.decode().strip()
    try:
        return float(raw)
    except ValueError:
        raise HTTPException(status_code=422, detail="Could not determine video duration. Live streams are not supported.")


async def download_audio(url: str, output_path: Path) -> None:
    proc = await asyncio.create_subprocess_exec(
        "yt-dlp",
        "--no-playlist",
        "--extractor-args", "youtube:player_client=tv_embedded",
        "--extract-audio",
        "--audio-format", "mp3",
        "--audio-quality", "192K",
        "--output", str(output_path),
        "--no-progress",
        "--quiet",
        url,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=120)
    except asyncio.TimeoutError:
        proc.kill()
        raise HTTPException(status_code=504, detail="Conversion timed out. Try a shorter video.")
    if proc.returncode != 0:
        err = stderr.decode(errors="replace").strip()
        if "private" in err.lower():
            raise HTTPException(status_code=422, detail="Video is private or unavailable.")
        if "deleted" in err.lower() or "removed" in err.lower():
            raise HTTPException(status_code=422, detail="This video has been deleted or removed.")
        if "ffmpeg" in err.lower():
            raise HTTPException(status_code=500, detail="FFmpeg failed to process the audio. Please try again.")
        if "no such format" in err.lower() or "not available" in err.lower():
            raise HTTPException(status_code=422, detail="Audio format not available for this video.")
        raise HTTPException(status_code=500, detail=f"Download failed: {err[:300]}")


def sanitize_filename(name: str, max_len: int = 60) -> str:
    name = re.sub(r'[^\w\s\-_.]', '', name)
    name = re.sub(r'\s+', '_', name).strip('._')
    return name[:max_len] or "audio"


async def get_video_title(url: str) -> str:
    proc = await asyncio.create_subprocess_exec(
        "yt-dlp",
        "--no-playlist",
        "--extractor-args", "youtube:player_client=tv_embedded",
        "--print", "%(title)s",
        url,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=20)
        title = stdout.decode(errors="replace").strip()
        return sanitize_filename(title) if title else "audio"
    except Exception:
        return "audio"


@app.get("/")
def health():
    return {"status": "ok", "service": "Delfo Studio 95 API", "version": "1.0.0"}

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/api/convert")
async def convert(req: ConvertRequest):
    url = req.url.strip()
    validate_url(url)

    duration = await get_video_duration(url)
    if duration > MAX_DURATION_SECONDS:
        mins = int(duration // 60)
        raise HTTPException(status_code=422, detail=f"Video is too long ({mins} min). Maximum allowed: {MAX_DURATION_SECONDS // 60} minutes.")

    title = await get_video_title(url)
    job_id = uuid.uuid4().hex[:8]
    base_path = TMP_DIR / f"{job_id}_{title}"
    mp3_path = Path(str(base_path) + ".mp3")

    await download_audio(url, base_path)

    if not mp3_path.exists():
        candidates = list(TMP_DIR.glob(f"{job_id}_*.mp3"))
        if not candidates:
            raise HTTPException(status_code=500, detail="Conversion produced no output file.")
        mp3_path = candidates[0]

    filename = mp3_path.name

    async def cleanup():
        try:
            if mp3_path.exists():
                mp3_path.unlink()
        except Exception:
            pass

    from starlette.background import BackgroundTask
    response = FileResponse(
        path=str(mp3_path),
        media_type="audio/mpeg",
        filename=filename,
        background=None,
    )
    response.background = BackgroundTask(cleanup)
    return response
