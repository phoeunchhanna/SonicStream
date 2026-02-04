FROM python:3.11-slim

# Install system dependencies (ffmpeg is required for yt-dlp)
RUN apt-get update && apt-get install -y ffmpeg nodejs && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project
COPY backend /app/backend
COPY frontend /app/frontend

# Set PYTHONPATH so python can find the 'backend' package
ENV PYTHONPATH=/app

# Run the application
# We use the PORT environment variable if available (for Cloud Run/Heroku), default to 8000
CMD sh -c "uvicorn backend.main:app --host 0.0.0.0 --port \${PORT:-8000}"
