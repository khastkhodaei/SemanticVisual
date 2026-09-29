# =====================================================================
#   SemanticDFL - Visualizer & Top-P Deep-Dive Lab (ACM 2026)
#   PowerShell Server Launcher
# =====================================================================

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

Write-Host "=====================================================================" -ForegroundColor Cyan
Write-Host "   SemanticDFL - Visualizer & Top-P Deep-Dive Lab (ACM 2026)" -ForegroundColor Cyan
Write-Host "=====================================================================" -ForegroundColor Cyan
Write-Host ""

# Check virtual environment
if (Test-Path ".\.venv\Scripts\Activate.ps1") {
    Write-Host "[*] Activating virtual environment (.venv)..." -ForegroundColor Yellow
    & ".\.venv\Scripts\Activate.ps1"
} elseif (Test-Path ".\venv\Scripts\Activate.ps1") {
    Write-Host "[*] Activating virtual environment (venv)..." -ForegroundColor Yellow
    & ".\venv\Scripts\Activate.ps1"
}

# Check Python command
try {
    $pythonVer = python --version 2>&1
    Write-Host "[*] Using: $pythonVer" -ForegroundColor Gray
} catch {
    Write-Error "[ERROR] Python was not found in your PATH."
    exit 1
}

Write-Host "[*] Launching server on http://127.0.0.1:8000 ..." -ForegroundColor Green
Write-Host "[*] Top-P Lab:   http://127.0.0.1:8000/static/top_p_lab.html" -ForegroundColor Green
Write-Host "[*] Storyboard:  http://127.0.0.1:8000/static/index.html" -ForegroundColor Green
Write-Host "`nPress Ctrl+C to stop the server.`n" -ForegroundColor DarkGray

# Open browser in a separate thread/job
Start-Job -ScriptBlock {
    Start-Sleep -Seconds 2
    Start-Process "http://127.0.0.1:8000/static/top_p_lab.html"
} | Out-Null

python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
