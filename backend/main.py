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


# ----------------- Check system tools -----------------

def _which(cmd: str) -> Optional[str]:
    return shutil.which(cmd)


def _require_bin(cmd: str):
    if not _which(cmd):
        raise RuntimeError(f"Missing required binary: {cmd}")


try:
    _require_bin("yt-dlp")
    _require_bin("ffmpeg")
    _require_bin("node")
    print("[startup] All dependencies OK")
except Exception as e:
    print(f"[startup] warning: {e}")


# ----------------- Cleanup old files -----------------

try:
    for f in OUT_DIR.glob("*"):
        f.unlink(missing_ok=True)
    print("[startup] outputs cleaned")
except Exception as e:
    print(f"[startup] cleanup warning: {e}")


# ----------------- App -----------------

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class URLRequest(BaseModel):
    url: HttpUrl


# ----------------- Routes -----------------

@app.get("/", response_class=HTMLResponse)
def home():
    html = APP_DIR.parent / "frontend" / "index.html"

    if not html.exists():
        return HTMLResponse("index.html not found", status_code=404)

    return HTMLResponse(html.read_text(encoding="utf-8"))


@app.get("/health")
def health():
    return {"status": "ok"}


def cleanup(job_id: str):
    for f in glob.glob(str(OUT_DIR / f"{job_id}*")):
        try:
            os.remove(f)
        except:
            pass


@app.post("/convert/url")
def convert_url(req: URLRequest):

    url = str(req.url)
    job_id = str(uuid.uuid4())

    out_tpl = str(OUT_DIR / f"{job_id}.%(ext)s")
    mp3_file = OUT_DIR / f"{job_id}.mp3"

    cmd = [
        "yt-dlp",
        "--no-playlist",
        "--extract-audio",
        "--audio-format", "mp3",
        "--audio-quality", "0",
        "--js-runtime", "node",
        "-o", out_tpl,
        url
    ]

    try:
        p = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=180
        )

        if p.returncode != 0:
            cleanup(job_id)
            raise HTTPException(500, p.stderr or p.stdout)

        # Check mp3
        if not mp3_file.exists():

            files = list(OUT_DIR.glob(f"{job_id}.*"))

            if not files:
                cleanup(job_id)
                raise HTTPException(500, "No output file")

            src = files[0]

            ff = subprocess.run(
                ["ffmpeg", "-y", "-i", src, mp3_file],
                capture_output=True,
                text=True
            )

            if ff.returncode != 0:
                cleanup(job_id)
                raise HTTPException(500, ff.stderr)

        return FileResponse(
            mp3_file,
            media_type="audio/mpeg",
            filename="audio.mp3"
        )

    except subprocess.TimeoutExpired:
        cleanup(job_id)
        raise HTTPException(504, "Timeout")

    except Exception as e:
        cleanup(job_id)
        raise HTTPException(500, str(e))
