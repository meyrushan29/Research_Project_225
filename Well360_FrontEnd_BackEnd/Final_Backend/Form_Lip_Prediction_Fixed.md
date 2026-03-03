# Form & Lip Prediction – Fixes Applied

## What Was Fixed

### 1. **Form prediction (API service)**
- **60s timeout** so the request doesn’t hang.
- **ClientException handling** – clear “Cannot reach backend at …” message instead of generic “Failed to fetch”.
- **Timeout handling** – “Request timed out. Backend may be slow. Try again.”
- **401 handling** – “Session expired or invalid. Please log in again.”
- **Token** – `Authorization: Bearer ${token.trim()}` so whitespace doesn’t break auth.

### 2. **Form screen**
- **Pre-check before submit** – calls `GET /hydration/health` first.
- If backend is not reachable, shows an **orange snackbar**:  
  “Backend not reachable at &lt;baseUrl&gt;. Start backend (uvicorn) and check URL in Settings.”
- No request is sent until the backend is reachable (avoids silent failures).

### 3. **Lip prediction**
- **401 handling** – same “Session expired or invalid. Please log in again.” message.
- **Token** – `Bearer ${token!.trim()}` for consistency.

### 4. **Shared backend check**
- **`ApiService.checkBackendReachable()`** – `GET /hydration/health`, no auth. Used before form submit.
- **`ApiService.checkHydrationBackend()`** – same plus `lip_model_available`. Used before lip submit.

---

## What You Must Do for Predictions to Work

### 1. Backend URL (critical on Flutter web)

- In the app, open the **Login** screen and set **API Base URL** to:
  - **`http://127.0.0.1:8000`**
- Do **not** use `http://localhost:8000` when running the app in Chrome; use **127.0.0.1**.
- If you had a custom URL saved before, update it to `http://127.0.0.1:8000` and save.

### 2. Backend running

```bash
cd Final_Backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Wait until you see: `Application startup complete.`

### 3. Log in

- Use the same backend (e.g. register/login via the app).
- Form and lip endpoints require a valid token; if you see “Session expired…”, log in again.

### 4. Test

- **Form:** Hydration → Form → fill fields → Submit.  
  - If backend is down: orange “Backend not reachable…” snackbar.  
  - If backend is up: result screen with recommendations.
- **Lip:** Hydration → Lip Analysis → pick image → Submit.  
  - Same reachability check first; then prediction.

---

## Quick Checklist

| Step | Action |
|------|--------|
| 1 | Backend URL in app = `http://127.0.0.1:8000` |
| 2 | Backend running (uvicorn on port 8000) |
| 3 | Logged in (token present) |
| 4 | Form submit → pre-check → then POST /predict/form |
| 5 | Lip submit → pre-check → then POST /predict/lip |

---

## Error Messages You Might See

| Message | Meaning | What to do |
|--------|---------|------------|
| “Backend not reachable at …” | App can’t reach the API. | Start backend; set URL to `http://127.0.0.1:8000`. |
| “Session expired or invalid. Please log in again.” | Token missing or invalid. | Log in again. |
| “Request timed out…” | Backend too slow (e.g. first model load). | Retry once; if it persists, check backend logs. |
| “Error 422: …” | Validation (e.g. wrong type or missing field). | Check form values; backend expects types as in schema. |
| “Error 500: …” | Server error. | Check backend terminal/logs for the traceback. |

---

## Files Changed

- **`flutter_application_1/lib/services/api_service.dart`**  
  Form timeout & errors, `checkBackendReachable()`, 401 handling, token trim for form and lip.
- **`flutter_application_1/lib/screens/hydration/form_screen.dart`**  
  Pre-check before form submit and orange snackbar when backend unreachable.

After pulling these changes, do a **full restart** of the Flutter app (or at least Hot Restart) so the new API and form logic are used.
