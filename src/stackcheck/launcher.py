"""
Standalone Launcher for StackCheck Desktop & CLI.
Boots the local Streamlit engine programmatically, prevents duplicate port spawning,
waits for verified health checks before opening the browser, and manages instance lifecycles.
"""

import sys
import os
import time
import json
import socket
import atexit
import signal
import threading
import webbrowser
from pathlib import Path
from typing import Optional, Dict, Any

# Fix sys._MEIPASS for PyInstaller one-file bundles
if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
    BASE_DIR = Path(sys._MEIPASS)
else:
    BASE_DIR = Path(__file__).resolve().parent.parent.parent

import tempfile


def _resolve_stackcheck_dir() -> Path:
    target = Path.home() / ".stackcheck"
    try:
        target.mkdir(parents=True, exist_ok=True)
        test_file = target / ".write_test"
        test_file.touch(exist_ok=True)
        test_file.unlink(missing_ok=True)
        return target
    except (OSError, PermissionError):
        fallback = Path(tempfile.gettempdir()) / ".stackcheck"
        try:
            fallback.mkdir(parents=True, exist_ok=True)
            return fallback
        except OSError:
            return Path.cwd() / ".stackcheck"


STACKCHECK_DIR = _resolve_stackcheck_dir()
PID_FILE = STACKCHECK_DIR / "stackcheck.pid"
INFO_FILE = STACKCHECK_DIR / "stackcheck.json"


def is_port_listening(port: int, host: str = "127.0.0.1") -> bool:
    """Check if a TCP port is currently accepting connections."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.4)
        try:
            return s.connect_ex((host, port)) == 0
        except OSError:
            return False


def get_running_instance() -> Optional[Dict[str, Any]]:
    """
    Check if a StackCheck server instance is currently alive and responding.
    Returns metadata dict if running, else cleans up stale pid files and returns None.
    """
    if not INFO_FILE.exists():
        return None

    try:
        with open(INFO_FILE, "r") as f:
            data = json.load(f)
        pid = data.get("pid")
        port = data.get("port", 8501)

        # Check if process is still alive
        is_alive = False
        if pid:
            try:
                os.kill(pid, 0)
                is_alive = True
            except OSError:
                is_alive = False

        # If process is alive and port is accepting connections, instance is active
        if is_alive and is_port_listening(port):
            return data
        elif not is_alive and not is_port_listening(port):
            cleanup_instance_files()
    except Exception:
        cleanup_instance_files()

    return None


def cleanup_instance_files():
    """Remove PID and info metadata files."""
    try:
        if PID_FILE.exists():
            PID_FILE.unlink()
        if INFO_FILE.exists():
            INFO_FILE.unlink()
    except OSError:
        pass


def stop_running_instance() -> bool:
    """Stop any active StackCheck server instance and release the port."""
    info = get_running_instance()
    if not info:
        # Also check fallback if pid file was missing but port 8501 is occupied
        cleanup_instance_files()
        return False

    pid = info.get("pid")
    port = info.get("port")
    if pid:
        try:
            os.kill(pid, signal.SIGTERM)
            # Give it up to 2 seconds to release port
            for _ in range(20):
                time.sleep(0.1)
                if not is_port_listening(port):
                    break
            else:
                # Force kill if still hung
                try:
                    os.kill(pid, signal.SIGKILL)
                except OSError:
                    pass
        except OSError:
            pass

    cleanup_instance_files()
    return True


def find_free_port(start_port: int = 8501, max_attempts: int = 15) -> int:
    """Find an available port starting from start_port."""
    for port in range(start_port, start_port + max_attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    return start_port


def wait_for_server_and_open_browser(url: str, port: int, timeout: float = 15.0):
    """
    Poll until server is verifiably accepting TCP connections, then open browser.
    Prevents 'connection refused' or 'not found' errors on slower machines.
    """
    def _worker():
        start_t = time.time()
        ready = False
        while time.time() - start_t < timeout:
            if is_port_listening(port):
                ready = True
                break
            time.sleep(0.2)

        # Brief pause to let Streamlit HTTP routes settle
        time.sleep(0.4)
        webbrowser.open(url)

    t = threading.Thread(target=_worker, daemon=True)
    t.start()


def launch():
    """Main launcher entrypoint."""
    from streamlit.web import bootstrap

    # 1. Single-instance check: If already running, focus browser instead of spawning duplicate
    running = get_running_instance()
    if running:
        existing_url = running.get("url", f"http://localhost:{running.get('port', 8501)}")
        print("=" * 60)
        print("  ℹ️ StackCheck is already running!")
        print(f"  🌐 URL: {existing_url} (PID: {running.get('pid')})")
        print("  🚀 Opening existing dashboard in your browser...")
        print("=" * 60)
        webbrowser.open(existing_url)
        return

    # 2. Locate target app.py
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

    # 3. Record PID and port info
    STACKCHECK_DIR.mkdir(parents=True, exist_ok=True)
    my_pid = os.getpid()
    with open(PID_FILE, "w") as f:
        f.write(str(my_pid))

    with open(INFO_FILE, "w") as f:
        json.dump({
            "pid": my_pid,
            "port": port,
            "url": app_url,
            "start_time": time.time()
        }, f)

    atexit.register(cleanup_instance_files)

    print("=" * 60)
    print("  🚀 Starting StackCheck Desktop Intelligence Engine...")
    print(f"  🌐 Local Dashboard: {app_url}")
    print(f"  🆔 Process PID:     {my_pid}")
    print("  💡 Tip: Run 'stackcheck stop' to stop this server anytime.")
    print("=" * 60)

    # 4. Wait for server readiness probe before opening browser
    wait_for_server_and_open_browser(app_url, port=port, timeout=12.0)

    from streamlit import config

    # Crucial for PyInstaller/frozen standalone app and CLI distribution:
    # 1. In PyInstaller/frozen runtime, Streamlit detects that "site-packages" is missing
    #    from __file__ and defaults global.developmentMode to True.
    #    When global.developmentMode is True, Streamlit DOES NOT MOUNT the static asset
    #    routes (index.html, JS, CSS) and points browser to Vite dev port 3000, causing
    #    the browser to open to a "404 Not Found" page.
    # 2. bootstrap.run() does NOT automatically call bootstrap.load_config_options(flag_options),
    #    so we must explicitly set config options and call load_config_options to ensure
    #    server.port, global.developmentMode=False, and browser settings take effect immediately.
    config.set_option("global.developmentMode", False)
    config.set_option("server.port", port)
    config.set_option("server.address", "127.0.0.1")
    config.set_option("server.headless", True)
    config.set_option("browser.serverPort", port)
    config.set_option("browser.serverAddress", "localhost")
    config.set_option("browser.gatherUsageStats", False)
    config.set_option("client.toolbarMode", "viewer")

    flag_options = {
        "server_port": port,
        "server_headless": True,
        "server_address": "127.0.0.1",
        "browser_serverPort": port,
        "browser_serverAddress": "localhost",
        "browser_gatherUsageStats": False,
        "client_toolbarMode": "viewer",
        "global_developmentMode": False
    }

    bootstrap.load_config_options(flag_options)

    try:
        bootstrap.run(
            target_script,
            is_hello=False,
            args=[],
            flag_options=flag_options
        )
    finally:
        cleanup_instance_files()


if __name__ == "__main__":
    from stackcheck.cli import main
    main()
