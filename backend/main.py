import os
import uuid
import glob
import shutil
import subprocess
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl

APP_DIR = Path(__file__).resolve().parent
OUT_DIR = APP_DIR / "outputs"
OUT_DIR.mkdir(exist_ok=True)

# --- Safety checks (optional but helpful) ---
def _which(cmd: str) -> Optional[str]:
    return shutil.which(cmd)

def _require_bin(cmd: str):
    if not _which(cmd):
        raise RuntimeError(f"Missing required binary: {cmd}")

# check at startup (Render logs will show clearly)
try:
    _require_bin("yt-dlp")
    _require_bin("ffmpeg")
    # node is optional if you want to rely on deno, but we require node for reliability
    _require_bin("node")
except Exception as e:
    print(f"[startup] dependency warning: {e}")

# cleanup old files at startup
try:
    for f in OUT_DIR.glob("*"):
        f.unlink(missing_ok=True)
    print("[startup] cleaned outputs/")
except Exception as e:
    print(f"[startup] cleanup warning: {e}")

app = FastAPI()

# If frontend & backend are same domain, CORS not needed, but keep it safe
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # change to your domain if you want stricter security
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class URLRequest(BaseModel):
    url: HttpUrl

@app.get("/", response_class=HTMLResponse)
def home():
    html_path = APP_DIR / "index.html"
    if not html_path.exists():
        return HTMLResponse("<h3>index.html not found</h3>", status_code=404)
    return HTMLResponse(html_path.read_text(encoding="utf-8"))

@app.get("/health")
def health():
    return {"ok": True}

def _cleanup_job(job_id: str):
    pattern = str(OUT_DIR / f"{job_id}*")
    for path in glob.glob(pattern):
        try:
            os.remove(path)
        except:
            pass

@app.post("/convert/url")
def convert_url(payload: URLRequest):
    url = str(payload.url)
    job_id = str(uuid.uuid4())

    out_template = str(OUT_DIR / f"{job_id}.%(ext)s")
    # final expected filename:
    mp3_path = OUT_DIR / f"{job_id}.mp3"

    # yt-dlp command:
    cmd = [
        "yt-dlp",
        "--no-playlist",
        "--extract-audio",
        "--audio-format", "mp3",
        "--audio-quality", "0",
        "--js-runtime", "node",  # <-- IMPORTANT for YouTube
        "-o", out_template,
        url,
    ]

    try:
        # run yt-dlp
        p = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=180,  # increase if needed
        )

        if p.returncode != 0:
            _cleanup_job(job_id)
            err = (p.stderr or p.stdout or "Unknown yt-dlp error").strip()
            raise HTTPException(status_code=500, detail=f"Download failed: {err}")

        # Sometimes yt-dlp may output .webm/.m4a if ffmpeg conversion fails.
        # Ensure mp3 exists:
        if not mp3_path.exists():
            # try to find any output file and convert manually
            candidates = list(OUT_DIR.glob(f"{job_id}.*"))
            if not candidates:
                _cleanup_job(job_id)
                raise HTTPException(status_code=500, detail="No output file generated.")
            src = candidates[0]
            # manual ffmpeg convert:
            ffmpeg_cmd = ["ffmpeg", "-y", "-i", str(src), str(mp3_path)]
            fp = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
            if fp.returncode != 0 or not mp3_path.exists():
                _cleanup_job(job_id)
                raise HTTPException(status_code=500, detail=f"FFmpeg convert failed: {(fp.stderr or fp.stdout).strip()}")

        # return mp3 file
        return FileResponse(
            path=str(mp3_path),
            media_type="audio/mpeg",
            filename="audio.mp3",
        )

    except subprocess.TimeoutExpired:
        _cleanup_job(job_id)
        raise HTTPException(status_code=504, detail="Timeout while downloading/converting.")
    except HTTPException:
        raise
    except Exception as e:
        _cleanup_job(job_id)
        raise HTTPException(status_code=500, detail=str(e))
