
from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os, uuid, subprocess, shutil, time, glob

from fastapi.staticfiles import StaticFiles

# Add Winget path to environment PATH
winget_path = os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WinGet\Links")
if os.path.exists(winget_path) and winget_path not in os.environ["PATH"]:
    os.environ["PATH"] += os.pathsep + winget_path

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


OUT_DIR = "outputs"
os.makedirs(OUT_DIR, exist_ok=True)

# Startup cleanup: Ensure outputs folder is empty when server starts
try:
    for f in os.listdir(OUT_DIR):
        os.remove(os.path.join(OUT_DIR, f))
    print("Startup: Cleaned outputs directory.")
except Exception as e:
    print(f"Startup cleanup warning: {e}")

def remove_job_files(job_id: str):
    """Clean up ALL files related to this job (mp3, webm, part, etc.)"""
    # no sleep needed if we read into memory first
    pattern = os.path.join(OUT_DIR, f"{job_id}*")
    for path in glob.glob(pattern):
        try:
            if os.path.exists(path):
                os.remove(path)
                print(f"Cleaned up: {path}")
        except Exception as e:
            print(f"Error cleaning up {path}: {e}")

@app.get("/health")
def health():
    return {"ok": True}

class URLRequest(BaseModel):
    url: str

@app.post("/convert/url")
async def convert_from_url(body: URLRequest):
    """Download audio from URL, read to memory, delete file, return bytes."""
    url = (body.url or "").strip()
    if not url:
        raise HTTPException(status_code=400, detail="No URL provided")

    job_id = str(uuid.uuid4())
    # Template uses %(ext)s so yt-dlp picks the best audio extension (usually m4a or mp3)
    out_template = os.path.join(OUT_DIR, f"{job_id}.%(ext)s")
    # We promise MP3 to the user, so we force conversion
    final_mp3_path = os.path.join(OUT_DIR, f"{job_id}.mp3")

    if shutil.which("yt-dlp") is None:
        raise HTTPException(status_code=500, detail="yt-dlp missing. Install requirements.")
    if shutil.which("ffmpeg") is None:
        raise HTTPException(status_code=500, detail="ffmpeg missing. Install ffmpeg.")

    # cmd: Extract audio, convert to mp3
    cmd = [
        "yt-dlp",
        "--extract-audio",
        "--audio-format", "mp3",
        "--no-playlist",
        "-o", out_template,
        url,
    ]

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    if proc.returncode != 0 or not os.path.exists(final_mp3_path):
        err = proc.stderr or "Unknown error"
        raise HTTPException(status_code=500, detail=f"Download failed: {err[:400]}")

    # Read into memory
    try:
        with open(final_mp3_path, "rb") as f:
            file_data = f.read()
    except Exception as e:
        remove_job_files(job_id)
        raise HTTPException(status_code=500, detail=f"File read error: {e}")

    # Delete immediately
    remove_job_files(job_id)

    # Return bytes
    return Response(
        content=file_data, 
        media_type="audio/mpeg", 
        headers={"Content-Disposition": "attachment; filename=audio.mp3"}
    )

# Serve Frontend (Place at bottom to allow API routes to take precedence)
frontend_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")
if os.path.exists(frontend_path):
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")
