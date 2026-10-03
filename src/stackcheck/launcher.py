"""
Standalone Launcher for StackCheck Desktop & CLI.
Boots the local Streamlit engine programmatically and automatically opens the user's browser.
"""

import sys
import os
import time
import socket
import threading
import webbrowser
from pathlib import Path

# Fix sys._MEIPASS for PyInstaller one-file bundles
if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
    BASE_DIR = Path(sys._MEIPASS)
else:
    BASE_DIR = Path(__file__).resolve().parent.parent.parent


def find_free_port(start_port: int = 8501, max_attempts: int = 20) -> int:
    """Find an available port starting from start_port."""
    for port in range(start_port, start_port + max_attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    return start_port


def open_browser_delayed(url: str, delay: float = 1.2):
    """Open default web browser after server initializes."""
    def _worker():
        time.sleep(delay)
        webbrowser.open(url)
    t = threading.Thread(target=_worker, daemon=True)
    t.start()


def launch():
    """Main launcher entrypoint."""
    from streamlit.web import bootstrap

    # Locate the target app.py
    candidate_paths = [
        BASE_DIR / "src" / "stackcheck" / "web" / "app.py",
        BASE_DIR / "stackcheck" / "web" / "app.py",
        Path(__file__).resolve().parent / "web" / "app.py",
        Path(os.getcwd()) / "app.py"
    ]

    target_script = None
    for p in candidate_paths:
        if p.exists():
            target_script = str(p)
            break

    if not target_script:
        print("❌ Error: Could not locate StackCheck app.py")
        sys.exit(1)

    port = find_free_port(8501)
    app_url = f"http://localhost:{port}"

    print("=" * 60)
    print("  🚀 Starting StackCheck Desktop Intelligence Engine...")
    print(f"  🌐 Local Dashboard: {app_url}")
    print("=" * 60)

    # Automatically open browser in background
    open_browser_delayed(app_url, delay=1.5)

    flag_options = {
        "server_port": port,
        "server_headless": True,
        "server_address": "127.0.0.1",
        "browser_gatherUsageStats": False,
        "client_toolbarMode": "viewer",
        "global_developmentMode": False
    }

    bootstrap.run(
        target_script,
        is_hello=False,
        args=[],
        flag_options=flag_options
    )


if __name__ == "__main__":
    launch()
