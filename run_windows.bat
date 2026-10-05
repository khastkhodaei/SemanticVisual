@echo off
chcp 65001 >nul
echo ===================================================
echo   SemanticDFL / Top-P Lab - Local Server Runner
echo ===================================================
echo.
echo Starting FastAPI Uvicorn Server at http://127.0.0.1:8000 ...
echo Top-P Lab URL: http://127.0.0.1:8000/static/top_p_lab.html
echo Storyboard URL: http://127.0.0.1:8000
echo.
echo Press Ctrl+C to stop the server.
echo.

python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
if %errorlevel% neq 0 (
    echo.
    echo Server stopped or encountered an error.
    pause
)
