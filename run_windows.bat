@echo off
rem =====================================================================
rem    SemanticDFL - Visualizer and Top-P Deep-Dive Lab
rem =====================================================================

cd /d "%~dp0"
title SemanticDFL Server

echo =====================================================================
echo    SemanticDFL - Visualizer and Top-P Deep-Dive Lab
echo =====================================================================
echo.

rem 1. Check local virtual environment (.venv)
if exist ".venv\Scripts\python.exe" (
    echo [*] Found virtual environment: .venv
    ".venv\Scripts\python.exe" run.py
    goto end
)

rem 2. Check local virtual environment (venv)
if exist "venv\Scripts\python.exe" (
    echo [*] Found virtual environment: venv
    "venv\Scripts\python.exe" run.py
    goto end
)

rem 3. Check system Python
where python >nul 2>&1
if %errorlevel% equ 0 (
    echo [*] Found system Python
    python run.py
    goto end
)

rem 4. Check Windows Python Launcher (py)
where py >nul 2>&1
if %errorlevel% equ 0 (
    echo [*] Found Windows Python Launcher
    py -3 run.py
    goto end
)

rem 5. Check Local AppData Python
if exist "%LocalAppData%\Programs\Python\Python313\python.exe" (
    "%LocalAppData%\Programs\Python\Python313\python.exe" run.py
    goto end
)
if exist "%LocalAppData%\Programs\Python\Python312\python.exe" (
    "%LocalAppData%\Programs\Python\Python312\python.exe" run.py
    goto end
)
if exist "%LocalAppData%\Programs\Python\Python311\python.exe" (
    "%LocalAppData%\Programs\Python\Python311\python.exe" run.py
    goto end
)
if exist "%LocalAppData%\Programs\Python\Python310\python.exe" (
    "%LocalAppData%\Programs\Python\Python310\python.exe" run.py
    goto end
)

echo [ERROR] Python 3.10+ was not found on your system.
echo Please install Python from https://www.python.org/
echo Make sure to check "Add Python to PATH" during installation.
echo.

:end
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Execution failed or server stopped with error code %errorlevel%.
)
echo.
pause
