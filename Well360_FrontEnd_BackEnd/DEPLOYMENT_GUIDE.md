
# 🚀 Deployment Guide for Well360 Backend

You can deploy the **Well360 Backend** to the internet easily using platforms like **Render** or **Railway**. 
This guide assumes you want a simple setup with persistent storage (database & uploads safe after restart).

---

## ✅ Prerequisites

1.  **GitHub Account**: You must push your code to a GitHub repository.
2.  **Render Account**: Create a free account at [https://render.com](https://render.com).

---

## 🛠️ Step 1: Push Code to GitHub

1.  Initialize git if you haven't: `git init`
2.  Add files: `git add .`
3.  Commit: `git commit -m "Prepare for deployment"`
4.  Push to your remote repository on GitHub.

---

## ☁️ Step 2: Deploy on Render.com (Recommended)

Render is great because it supports "Disks" (Persistent Volumes) easily.

1.  **New Web Service**:
    *   Go to Dashboard → **New +** → **Web Service**.
    *   Connect your GitHub repository.

2.  **Configuration**:
    *   **Name**: `well360-backend` (or similar)
    *   **Region**: Closest to you (e.g., Singapore/Oregon/Frankfurt).
    *   **Branch**: `main` (or your working branch).
    *   **Runtime**: **Docker** (Render will detect the `Dockerfile` we created).
    *   **Instance Type**: **Free** (Note: Free tier spins down after inactivity, causing a 50s delay on first request. $7/mo tier is instant).

3.  **Environment Variables** (Optional):
    *   If you just use SQLite, no need to add anything yet.
    *   `PORT`: Render auto-sets this to `10000`, the Dockerfile reads it.

4.  **Persistent Disk (CRITICAL)**:
    *   Since we use SQLite (`hydration_app.db`) and store user images in `img/`, we need a **Disk** so data isn't lost on restart.
    *   Go to **Disks** in the service settings (This requires a Paid plan ~$7/mo).
    *   **Mount Path**: `/app/hydration`
    *   **Size**: 1GB is plenty.
    *   **Mount Path 2** (if supported, else move img folder): `/app/img`
    
    *   *Alternative (Free Tier)*: You will lose data on restart. To avoid this on Free Tier, you must:
        1.  Use **Render PostgreSQL** (Add-on) and set `DATABASE_URL` env var.
        2.  Use **Cloudinary / AWS S3** for image uploads (requires code changes).
        *   **For now**: The Docker setup will work on Free Tier, but **database resets on deployment**.

5.  **Click Create Web Service**.

---

## 📱 Step 3: Connect Flutter App

Once Render finishes building, it will give you a URL like:
`https://well360-backend.onrender.com`

1.  Open your Flutter App.
2.  On the **Login Screen**, tap the **Settings Gear ⚙️**.
3.  Enter the new HTTPS URL: `https://well360-backend.onrender.com`.
4.  Tap **Save**.
5.  Login!

---

## ⚡ Troubleshooting

*   **"Service Unavailable" / 502**: Check Render Logs. Did the build fail?
*   **"Internal Server Error"**: Use `pip install gunicorn` was missing? (We added it).
*   **Database Locked**: SQLite on highly concurrent server might lock. Switch to PostgreSQL for real production usage.

---

## 🔄 Switching to PostgreSQL (Advanced)

If you want a real production database:
1.  Create a **PostgreSQL** database on Render.
2.  Copy the `Internal Database URL`.
3.  In your Web Service **Environment Variables**, add:
    *   Key: `DATABASE_URL`
    *   Value: `postgresql://user:pass@hostname:5432/dbname` (The internal URL).
4.  Redeploy. The app will auto-switch to Postgres!
