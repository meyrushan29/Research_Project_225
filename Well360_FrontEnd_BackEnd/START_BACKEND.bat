@echo off
title Well360 Backend - KEEP THIS WINDOW OPEN
echo.
echo ============================================
echo   Well360 Backend - Starting...
echo ============================================
echo   Keep this window OPEN while using the app.
echo   Backend URL: http://127.0.0.1:8000
echo ============================================
echo.

cd /d "%~dp0Final_Backend"
if errorlevel 1 (
    echo ERROR: Final_Backend folder not found.
    pause
    exit /b 1
)

python run.py
if errorlevel 1 (
    echo.
    echo Backend exited with an error. Check above.
    pause
)
