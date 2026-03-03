# Fix: "Cannot reach backend" / "Failed to fetch" (Flutter Web)

## What’s going on

The backend is running (e.g. uvicorn on port 8000) and works when you call it from the same machine (e.g. Python or browser at `http://localhost:8000/docs`), but the **Flutter web app in Chrome** shows:

- **"Cannot reach backend at http://localhost:8000"**  
- **"Error: Failed to fetch"**

This is usually because the browser treats `localhost` in a special way when the app is served from another port (e.g. Flutter dev server), and blocks or fails the request.

## Fix: use 127.0.0.1 instead of localhost

Use **`http://127.0.0.1:8000`** as the backend URL in the app instead of **`http://localhost:8000`**.

### Option A – Use the new default (no custom URL)

1. **Clear the saved backend URL** (so the app uses the new default):
   - On **web**: e.g. clear site data for the app’s origin, or use the in‑app URL field and set it to `http://127.0.0.1:8000` (see Option B).
   - Or run the app again after the code change so it uses the updated default.
2. **Restart the Flutter app** (hot restart or full restart).
3. The app now defaults to **`http://127.0.0.1:8000`** on web.

### Option B – Set the URL in the app

1. Open the **login** (or settings) screen where you can set the **API Base URL**.
2. Set it to: **`http://127.0.0.1:8000`** (no trailing slash).
3. Save and try the request again (e.g. lip analysis).

## Check that the backend is reachable

In the **same browser** where you run the Flutter app, open:

- **http://127.0.0.1:8000/hydration/health**

You should see something like:

```json
{"status":"ok","module":"hydration","lip_model_available":true,"predict_lip_endpoint":"/predict/lip"}
```

If that works in the browser but the app still says "Cannot reach backend", use **`http://127.0.0.1:8000`** as the backend URL in the app (Option B above).

## Summary

| Before (often fails in Chrome) | After (recommended) |
|-------------------------------|----------------------|
| `http://localhost:8000`       | `http://127.0.0.1:8000` |

## Start the backend so the frontend can reach it

**Important:** The backend must listen on **all interfaces** (`0.0.0.0`), not only `127.0.0.1`, so that:
- **Flutter Web** (same PC) can use `http://127.0.0.1:8000`
- **Android Emulator** can use `http://10.0.2.2:8000`
- **Physical device** can use `http://YOUR_PC_IP:8000`

**Recommended (binds 0.0.0.0 automatically):**

```bash
cd Final_Backend
python run.py
```

**Alternative:**

```bash
cd Final_Backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Do not** use `uvicorn main:app --reload` without `--host 0.0.0.0` if you need the app (emulator/device) to connect.

## URL by platform

| Where you run the app | Backend URL to set in app (Login → Settings) |
|------------------------|-----------------------------------------------|
| **Chrome / Web**       | `http://127.0.0.1:8000`                       |
| **Android Emulator**   | `http://10.0.2.2:8000`                         |
| **Physical device**    | `http://YOUR_PC_IP:8000` (e.g. from `ipconfig`) |

Then in the app, use the URL for your platform (or use the **Web** / **Emulator** presets in Settings).
