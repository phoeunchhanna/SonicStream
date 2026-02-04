# SonicStream - Premium Video to MP3

**SonicStream** is a high-performance, privacy-focused tool to convert YouTube and Facebook videos to MP3.

## Features

- **Premium UI**: Glassmorphism design with ambient glow effects.
- **Direct Download**: Files are streamed directly to your device.
- **Privacy First**: No server storage. Files are automatically deleted immediately after download.
- **Smart Engine**: Powered by `yt-dlp` and `ffmpeg` for high-quality extraction.

## Prerequisites

1.  **Python 3.9+**
2.  **FFmpeg** (Required for conversion)
    - Windows: `winget install Gyan.FFmpeg`
    - Linux/Mac: `sudo apt install ffmpeg` or `brew install ffmpeg`

## Installation & Local Run

1.  **Install Dependencies**:

    ```powershell
    pip install -r requirements.txt
    ```

2.  **Run the Server**:

    ```powershell
    # Run from the root directory
    uvicorn backend.main:app --reload
    ```

    - The server will handle `ffmpeg` detection automatically (on Windows).

3.  **Open the App**:
    - Open `frontend/index.html` in your browser.

## Deployment (Heroku / Render)

This project is configured for deployment.

- **Procfile**: Included for Heroku-like platforms.
- **Command**: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
- **BuildPacks**: Ensure you add `https://github.com/jonathanong/heroku-buildpack-ffmpeg-latest.git` (or equivalent) so FFmpeg is available in the cloud environment.

---

_Built with FastAPI and Vanilla JS._
