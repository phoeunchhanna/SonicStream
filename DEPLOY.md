# Deployment Guide for SonicStream

This project is ready to be deployed to the cloud. Because it uses **FFmpeg**, the easiest way to deploy it is using **Docker** or a platform that supports buildpacks.

We recommend **Render.com** (easiest free tier with Docker) or **Heroku**.

---

## Option 1: Render.com (Recommended)

Render is great because it can build directly from the `Dockerfile` we just created.

1.  **Push your code to GitHub**.
    - Create a repository on GitHub.
    - Push this entire `video-tool` folder to it.
2.  **Sign up/Login to [dashboard.render.com](https://dashboard.render.com/)**.
3.  Click **New +** -> **Web Service**.
4.  Connect your GitHub repository.
5.  **Settings**:
    - **Name**: `sonicstream` (or whatever you like)
    - **Region**: Choose closest to you.
    - **Runtime**: Select **Docker**.
    - **Instance Type**: Free.
6.  Click **Create Web Service**.

Render will detect the `Dockerfile` at the root, build the image (installing Python + FFmpeg), and deploy it. It usually takes 2-3 minutes.

---

## Option 2: Heroku

Heroku requires "Buildpacks" to install FFmpeg.

1.  **Install Heroku CLI** and login (`heroku login`).
2.  **Create App**:
    ```bash
    heroku create sonicstream-app
    ```
3.  **Add Buildpacks** (Order matters!):
    - First, the FFmpeg buildpack:
      ```bash
      heroku buildpacks:add https://github.com/jonathanong/heroku-buildpack-ffmpeg-latest.git
      ```
    - Second, the Python buildpack:
      ```bash
      heroku buildpacks:add heroku/python
      ```
4.  **Deploy**:
    ```bash
    git push heroku main
    ```

---

## Verify Deployment

Once deployed, your app will be available at your-app-name.onrender.com or herokuapp.com.

- You do **not** need to configure anything else; the `Procfile` and `Dockerfile` handle the rest.
- **Note**: On free tiers, the server might "sleep" after inactivity. The first request might take 30 seconds to wake it up.
