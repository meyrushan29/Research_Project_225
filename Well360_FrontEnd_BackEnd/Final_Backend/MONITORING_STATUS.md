# Monitoring Status – Backend & Frontend

## Started Services

### Backend (Terminal 167760)
- **Command:** `python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000`
- **Status:** Running
- **Log:** `INFO: Application startup complete.`
- **URL:** http://127.0.0.1:8000

### Frontend (Terminal 671703)
- **Command:** `flutter run -d chrome`
- **Status:** Running (Chrome debug mode)
- **Log:** `Flutter run key commands.` (r=reload, R=restart, q=quit)

---

## Checks Performed

| Check | Result |
|-------|--------|
| Backend health GET /hydration/health | 200 OK, `lip_model_available: true` |
| Auth POST /auth/login-json | 401 (expected for wrong credentials) |
| Form POST /predict/form (no auth) | 401 Not authenticated |
| Flutter analyze (api_service, combined_result_screen) | No issues found |

---

## Fixes Applied During Monitoring

1. **api_service.dart** – Removed unnecessary `!` on token (`token!.trim()` → `token.trim()` inside `if (token != null)`).
2. **combined_result_screen.dart** – Removed unused import `auth_service.dart`.
3. **combined_result_screen.dart** – Removed unnecessary cast and `.toList()` in suggestions spread (`Map<String, dynamic>.from(suggestion)` and spread without `.toList()`).

---

## Remaining Flutter Analyze Items (Non-blocking)

- **camera_screen.dart:** Unused import, unused field, `avoid_print`, `withOpacity` deprecation (use `withValues()`).
- **form_screen.dart:** Curly braces for single-line ifs, `use_build_context_synchronously`.
- **login_screen.dart:** `use_build_context_synchronously`.
- **lip_trends_screen.dart:** Unused variables, unnecessary import.
- **profile_screen.dart:** `prefer_const_constructors`.

These are style/info and do not stop the app from running.

---

## How to Use

1. **Backend:** Leave the backend terminal running. Reloads on file change.
2. **Frontend:** Use the Chrome window that opened. In the Flutter terminal press `r` for hot reload, `R` for hot restart.
3. **App URL:** In the app, set API Base URL to **http://127.0.0.1:8000** (Login screen) so form and lip prediction work.

---

## If You See Errors

- **Backend terminal:** Watch for Python tracebacks or 500 responses.
- **Frontend terminal:** Watch for Dart/Flutter errors after hot reload.
- **Browser:** F12 → Console and Network to see JS errors or failed API calls.

No runtime errors were seen during this monitoring session.
