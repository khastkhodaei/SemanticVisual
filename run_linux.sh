#!/usr/bin/env bash
# =====================================================================
#   SemanticDFL - Visualizer & Top-P Deep-Dive Lab (ACM 2026)
#   Linux / macOS Server Runner
# =====================================================================

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
cd "$DIR"

if [ -f "./start_server.sh" ]; then
    exec ./start_server.sh "$@"
else
    if [ -f ".venv/bin/activate" ]; then
        source .venv/bin/activate
    elif [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
    fi

    if command -v python3 &>/dev/null; then
        PYTHON_CMD="python3"
    else
        PYTHON_CMD="python"
    fi

    exec $PYTHON_CMD run.py
fi
