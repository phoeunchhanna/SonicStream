# Deployment Guide for SonicStream

This project is optimized for **Render.com** using Docker.

We chose Render because it has excellent support for custom system dependencies (like FFmpeg) via Docker, which Vercel struggles with on the free tier.

---

## Deploy to Render.com (Recommended)

1.  **Push your code to GitHub**.
    - Make sure you have pushed all changes to your repository.

2.  **Sign up/Login to [dashboard.render.com](https://dashboard.render.com/)**.

3.  Click **New +** -> **Web Service**.

4.  Connect your GitHub repository.

5.  **Configure Settings**:
    - **Name**: `sonicstream`
    - **Runtime**: Select **Docker**.
    - **Instance Type**: Free.

6.  Click **Create Web Service**.

Render will automatically:

1.  Isolate your app in a container.
2.  Install Python 3.11.
3.  **Install FFmpeg** (crucial for this app).
4.  Run the server.

---

## Troubleshooting

- **Timeout errors**: Unlike Vercel (10s limit), Render allows long-running requests, so downloading large videos will work fine!
- **"Sleeping"**: On the free tier, the first request might take ~50 seconds to wake up the server.

---

## Alternative: Heroku

If you prefer Heroku:

1.  `heroku create`
2.  `heroku buildpacks:add https://github.com/jonathanong/heroku-buildpack-ffmpeg-latest.git`
3.  `heroku buildpacks:add heroku/python`
4.  `git push heroku main`
