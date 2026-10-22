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

$pythonCmd = $null

if (Test-Path ".\.venv\Scripts\python.exe") {
    $pythonCmd = ".\.venv\Scripts\python.exe"
    Write-Host "[*] Virtualenv detected: .venv" -ForegroundColor Yellow
} elseif (Test-Path ".\venv\Scripts\python.exe") {
    $pythonCmd = ".\venv\Scripts\python.exe"
    Write-Host "[*] Virtualenv detected: venv" -ForegroundColor Yellow
} else {
    $cmd = Get-Command python -ErrorAction SilentlyContinue
    if ($cmd) {
        $pythonCmd = "python"
    } else {
        $cmdPy = Get-Command py -ErrorAction SilentlyContinue
        if ($cmdPy) {
            $pythonCmd = "py -3"
        }
    }
}

if (-not $pythonCmd) {
    Write-Error "[ERROR] Python 3.10+ was not found on your system."
    Read-Host "Press Enter to exit..."
    exit 1
}

Write-Host "[*] Using Python: $pythonCmd" -ForegroundColor Green
Write-Host "[*] Starting application... Your browser will open automatically once ready.`n" -ForegroundColor Green

& $pythonCmd run.py
