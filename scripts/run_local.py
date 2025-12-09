"""
Convenience launcher to run backend (FastAPI) and frontend (Streamlit) together.

Usage:
    python scripts/run_local.py

This script:
1) Loads .env so API keys are available.
2) Starts uvicorn on port 8000 and Streamlit on 8501.
3) Gracefully stops both on Ctrl+C.
"""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).parent.parent


def main() -> None:
    load_dotenv(PROJECT_ROOT / ".env")

    backend_cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "backend.app.main:app",
        "--reload",
        "--port",
        "8000",
    ]

    frontend_cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        "frontend/streamlit_app.py",
        "--server.port",
        "8501",
    ]

    print("Starting backend:", " ".join(backend_cmd))
    backend = subprocess.Popen(backend_cmd, cwd=PROJECT_ROOT)
    time.sleep(1.5)  # small gap to avoid interleaved logs on startup

    print("Starting frontend:", " ".join(frontend_cmd))
    frontend = subprocess.Popen(frontend_cmd, cwd=PROJECT_ROOT)

    try:
        # Wait until one process exits
        while True:
            backend_code = backend.poll()
            frontend_code = frontend.poll()
            if backend_code is not None:
                print(f"Backend exited with code {backend_code}")
                break
            if frontend_code is not None:
                print(f"Frontend exited with code {frontend_code}")
                break
            time.sleep(1.0)
    except KeyboardInterrupt:
        print("\nStopping processes...")
    finally:
        for proc in (backend, frontend):
            if proc.poll() is None:
                proc.terminate()
        for proc in (backend, frontend):
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()


if __name__ == "__main__":
    main()

