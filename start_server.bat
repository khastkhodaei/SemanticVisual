@echo off
title SemanticDFL Visualization and Top-P Lab Server
cd /d "%~dp0"

echo =====================================================================
echo    SemanticDFL - Visualizer and Top-P Deep-Dive Lab [ACM 2026]
echo =====================================================================
echo.

if exist ".venv\Scripts\activate.bat" (
    echo [*] Activating virtual environment: .venv
    call .venv\Scripts\activate.bat
)
if exist "venv\Scripts\activate.bat" (
    echo [*] Activating virtual environment: venv
    call venv\Scripts\activate.bat
)

python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python was not found in your PATH.
    echo Please install Python 3.10+ and add it to PATH.
    pause
    exit /b 1
)

echo [*] Starting FastAPI Uvicorn Server on http://127.0.0.1:8000
echo [*] Top-P Lab URL: http://127.0.0.1:8000/static/top_p_lab.html
echo [*] Storyboard URL: http://127.0.0.1:8000/static/index.html
echo.
echo Press Ctrl+C in this window to stop the server.
echo.

start "" powershell -NoProfile -Command "Start-Sleep -Seconds 2; Start-Process 'http://127.0.0.1:8000/static/top_p_lab.html'"

python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload

pause
