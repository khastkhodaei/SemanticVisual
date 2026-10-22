"""SemanticDFL / Top-P Lab Application Launcher.

Starts FastAPI/Uvicorn server and automatically opens the user's default web browser
once the server is fully initialized and responding to health checks.
"""

import os
import sys
import time
import threading
import urllib.request
import webbrowser
from pathlib import Path

# Ensure project root is in sys.path and current working directory
PROJECT_ROOT = Path(__file__).resolve().parent
os.chdir(PROJECT_ROOT)
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

PORT = 8000
HOST = "127.0.0.1"
TARGET_URL = f"http://{HOST}:{PORT}/static/top_p_lab.html"
HEALTH_URL = f"http://{HOST}:{PORT}/health"


def wait_and_open_browser():
    """Poll the server until healthy, then launch the browser."""
    print(f"[*] Waiting for server to initialize at {HEALTH_URL} ...")
    start_time = time.time()
    # Wait up to 35 seconds for numpy/scipy/sklearn/models to load
    while time.time() - start_time < 35:
        try:
            with urllib.request.urlopen(HEALTH_URL, timeout=1.0) as resp:
                if resp.status == 200:
                    print(f"[*] Server is ready! Opening browser at {TARGET_URL} ...")
                    time.sleep(0.5)
                    webbrowser.open(TARGET_URL)
                    return
        except Exception:
            pass
        time.sleep(0.5)

    print("[!] Timeout waiting for server health check. Opening browser anyway...")
    webbrowser.open(TARGET_URL)


def main():
    print("=" * 70)
    print("   SemanticDFL - Visualizer & Top-P Deep-Dive Lab [ACM 2026]")
    print("=" * 70)
    print(f"[*] Primary Dashboard: {TARGET_URL}")
    print(f"[*] Storyboard Visualizer: http://{HOST}:{PORT}/static/index.html")
    print(f"[*] Press Ctrl+C in this terminal window to stop the server.")
    print("=" * 70)
    print()

    # Start browser-watcher thread
    watcher_thread = threading.Thread(target=wait_and_open_browser, daemon=True)
    watcher_thread.start()

    # Verify uvicorn
    try:
        import uvicorn
    except ImportError:
        print("\n[ERROR] 'uvicorn' is not installed in the active Python environment.")
        print("Please run: pip install -r requirements.txt\n")
        sys.exit(1)

    # Run uvicorn server
    uvicorn.run("backend.main:app", host=HOST, port=PORT, reload=False, log_level="info")


if __name__ == "__main__":
    main()
