#!/usr/bin/env bash
# =====================================================================
#   SemanticDFL - Visualizer & Top-P Deep-Dive Lab (ACM 2026)
#   Linux / macOS Server Launcher
# =====================================================================

set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
cd "$DIR"

echo "====================================================================="
echo "   SemanticDFL - Visualizer & Top-P Deep-Dive Lab (ACM 2026)"
echo "====================================================================="
echo ""

# Activate virtual environment if present
if [ -f ".venv/bin/activate" ]; then
    echo "[*] Activating virtual environment (.venv)..."
    source .venv/bin/activate
elif [ -f "venv/bin/activate" ]; then
    echo "[*] Activating virtual environment (venv)..."
    source venv/bin/activate
fi

# Detect Python interpreter
PYTHON_CMD="python3"
if ! command -v python3 &> /dev/null; then
    if command -v python &> /dev/null; then
        PYTHON_CMD="python"
    else
        echo "[ERROR] Python 3 was not found in your PATH."
        exit 1
    fi
fi

echo "[*] Using Python: $($PYTHON_CMD --version)"
echo "[*] Starting FastAPI Uvicorn Server on http://127.0.0.1:8000 ..."
echo "[*] Top-P Lab:   http://127.0.0.1:8000/static/top_p_lab.html"
echo "[*] Storyboard:  http://127.0.0.1:8000/static/index.html"
echo ""
echo "Press Ctrl+C to stop the server."
echo ""

# Open default browser after a brief delay
(
    sleep 2
    if command -v xdg-open &> /dev/null; then
        xdg-open "http://127.0.0.1:8000/static/top_p_lab.html" >/dev/null 2>&1 || true
    elif command -v open &> /dev/null; then
        open "http://127.0.0.1:8000/static/top_p_lab.html" >/dev/null 2>&1 || true
    fi
) &

# Run server
$PYTHON_CMD -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
