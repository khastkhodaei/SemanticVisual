#!/usr/bin/env bash
# ===================================================
#   SemanticDFL / Top-P Lab - Local Server Runner (Linux / macOS)
# ===================================================

echo "==================================================="
echo "  SemanticDFL / Top-P Lab - Local Server Runner"
echo "==================================================="
echo ""
echo "Starting FastAPI Uvicorn Server at http://127.0.0.1:8000 ..."
echo "Top-P Lab URL: http://127.0.0.1:8000/static/top_p_lab.html"
echo "Storyboard URL: http://127.0.0.1:8000"
echo ""
echo "Press Ctrl+C to stop the server."
echo ""

# Prefer python3 if available, otherwise python
if command -v python3 &>/dev/null; then
    PYTHON_CMD="python3"
else
    PYTHON_CMD="python"
fi

$PYTHON_CMD -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
