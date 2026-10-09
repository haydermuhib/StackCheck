"""
Standalone Launcher for StackCheck Desktop & CLI.
Boots the local Streamlit engine programmatically, prevents duplicate port spawning,
waits for verified health checks before opening the browser, and manages instance lifecycles.
"""

import sys
import os

# Ensure safe UTF-8 output encoding on Windows consoles
if sys.platform == "win32":
    if sys.stdout and hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    if sys.stderr and hasattr(sys.stderr, "reconfigure"):
        try:
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

import time
import json
import socket
import shutil
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


from rich.console import Console
from rich.panel import Panel

console = Console(legacy_windows=False)


def ensure_persistent_streamlit_static() -> Path:
    """
    Ensure Streamlit frontend assets are mirrored to persistent user storage.
    Prevents Starlette StaticFiles 500 / FileNotFoundError crashes when
    temporary PyInstaller _MEI directories are deleted after parent process exit.
    """
    persistent_static = STACKCHECK_DIR / "streamlit_static"
    persistent_static.mkdir(parents=True, exist_ok=True)
    try:
        import streamlit

        candidate_sources = [
            Path(streamlit.__file__).parent / "static",
        ]
        if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
            mei = Path(sys._MEIPASS)
            candidate_sources.extend([
                mei / "streamlit" / "static",
                mei / "streamlit" / "static" / "static",
                mei / "static",
            ])

        found_source = None
        for cand in candidate_sources:
            if cand.exists() and any(cand.iterdir()):
                found_source = cand
                break

        if found_source:
            for item in found_source.iterdir():
                dest = persistent_static / item.name
                if item.is_dir():
                    shutil.copytree(item, dest, dirs_exist_ok=True)
                else:
                    if not dest.exists() or dest.stat().st_size != item.stat().st_size:
                        shutil.copy2(item, dest)
    except Exception:
        pass

    # Ensure index.html exists so Starlette never raises RuntimeError on empty dir
    index_file = persistent_static / "index.html"
    if not index_file.exists():
        try:
            index_file.write_text(
                "<!DOCTYPE html><html><head><title>StackCheck</title></head><body><div id='root'></div></body></html>",
                encoding="utf-8"
            )
        except Exception:
            pass

    return persistent_static


def locate_target_script() -> Optional[str]:
    """
    Find the target Streamlit entrypoint app.py and ensure persistent availability.
    Syncs the script and charts to STACKCHECK_DIR/web so that it is never lost when
    temporary PyInstaller _MEI directories are cleaned up by parent process exit.
    """
    candidate_paths = [
        BASE_DIR / "src" / "stackcheck" / "web" / "app.py",
        BASE_DIR / "stackcheck" / "web" / "app.py",
        Path(__file__).resolve().parent / "web" / "app.py",
        Path(os.getcwd()) / "app.py"
    ]
    source_app = None
    for p in candidate_paths:
        if p.exists():
            source_app = p
            break

    if source_app:
        try:
            target_dir = STACKCHECK_DIR / "web"
            target_dir.mkdir(parents=True, exist_ok=True)
            persistent_app = target_dir / "app.py"

            content = source_app.read_text(encoding="utf-8")
            if not persistent_app.exists() or persistent_app.read_text(encoding="utf-8") != content:
                persistent_app.write_text(content, encoding="utf-8")

            source_charts = source_app.parent / "charts.py"
            if source_charts.exists():
                persistent_charts = target_dir / "charts.py"
                charts_content = source_charts.read_text(encoding="utf-8")
                if not persistent_charts.exists() or persistent_charts.read_text(encoding="utf-8") != charts_content:
                    persistent_charts.write_text(charts_content, encoding="utf-8")

            source_dialogs = source_app.parent / "dialogs.py"
            if source_dialogs.exists():
                persistent_dialogs = target_dir / "dialogs.py"
                dialogs_content = source_dialogs.read_text(encoding="utf-8")
                if not persistent_dialogs.exists() or persistent_dialogs.read_text(encoding="utf-8") != dialogs_content:
                    persistent_dialogs.write_text(dialogs_content, encoding="utf-8")

            source_tabs = source_app.parent / "tabs"
            if source_tabs.exists() and source_tabs.is_dir():
                target_tabs = target_dir / "tabs"
                target_tabs.mkdir(parents=True, exist_ok=True)
                for tab_file in source_tabs.glob("*.py"):
                    dest_tab = target_tabs / tab_file.name
                    tab_content = tab_file.read_text(encoding="utf-8")
                    if not dest_tab.exists() or dest_tab.read_text(encoding="utf-8") != tab_content:
                        dest_tab.write_text(tab_content, encoding="utf-8")

            # Also ensure assets (logo, icon) are mirrored to STACKCHECK_DIR/assets
            from stackcheck.config import get_assets_dir
            source_assets = get_assets_dir()


            if source_assets and source_assets.exists():
                target_assets_dir = STACKCHECK_DIR / "assets"
                target_assets_dir.mkdir(parents=True, exist_ok=True)
                for asset_file in source_assets.glob("*"):
                    if asset_file.is_file():
                        dest_file = target_assets_dir / asset_file.name
                        if not dest_file.exists() or dest_file.stat().st_size != asset_file.stat().st_size:
                            dest_file.write_bytes(asset_file.read_bytes())

            # Mirror Streamlit dark theme configuration
            dark_cfg = """[theme]
base = "dark"
primaryColor = "#3b82f6"
backgroundColor = "#0f172a"
secondaryBackgroundColor = "#1e293b"
textColor = "#f8fafc"
font = "sans serif"

[server]
headless = true
enableCORS = false
enableXsrfProtection = true

[browser]
gatherUsageStats = false
"""
            for cfg_dir in [STACKCHECK_DIR / ".streamlit", target_dir / ".streamlit"]:
                try:
                    cfg_dir.mkdir(parents=True, exist_ok=True)
                    (cfg_dir / "config.toml").write_text(dark_cfg, encoding="utf-8")
                except Exception:
                    pass

            # Mirror Streamlit static assets for persistent daemon & offline survival
            ensure_persistent_streamlit_static()

            return str(persistent_app)
        except Exception:
            return str(source_app)

    cached_app = STACKCHECK_DIR / "web" / "app.py"
    if cached_app.exists():
        return str(cached_app)

    return None


def stop_running_instance() -> bool:
    """Stop any active StackCheck server instance and release the port."""
    info = get_running_instance()
    if not info:
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
                # Force kill if still hung (use SIGKILL on Unix, SIGTERM fallback on Windows)
                sig_kill = getattr(signal, "SIGKILL", getattr(signal, "SIGTERM", 15))
                try:
                    os.kill(pid, sig_kill)
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


def safe_open_browser(url: str):
    """Open browser without leaking child process stderr/stdout to terminal."""
    # Don't attempt to open browser if no GUI display is detected on Linux
    if sys.platform.startswith("linux") and not (os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")):
        return

    try:
        devnull = os.open(os.devnull, os.O_WRONLY)
        old_stdout = os.dup(1)
        old_stderr = os.dup(2)
        try:
            os.dup2(devnull, 1)
            os.dup2(devnull, 2)
            webbrowser.open(url)
        finally:
            os.dup2(old_stdout, 1)
            os.dup2(old_stderr, 2)
            os.close(old_stdout)
            os.close(old_stderr)
            os.close(devnull)
    except Exception:
        try:
            webbrowser.open(url)
        except Exception:
            pass


def wait_for_server_and_open_browser(url: str, port: int, timeout: float = 15.0):
    """
    Poll until server is verifiably accepting TCP connections, then open browser.
    Prevents 'connection refused' or 'not found' errors on slower machines.
    """
    def _worker():
        start_t = time.time()
        while time.time() - start_t < timeout:
            if is_port_listening(port):
                break
            time.sleep(0.2)

        # Brief pause to let Streamlit HTTP routes settle
        time.sleep(0.4)
        safe_open_browser(url)

    t = threading.Thread(target=_worker, daemon=True)
    t.start()


def launch():
    """Main launcher entrypoint."""
    from stackcheck import __version__

    # 1. Single-instance check: If already running, focus browser instead of spawning duplicate
    running = get_running_instance()
    if running:
        existing_url = running.get("url", f"http://localhost:{running.get('port', 8501)}")
        existing_pid = running.get("pid")
        console.print(Panel(
            f"[bold green]StackCheck is already running![/bold green]\n\n"
            f"  🌐 [bold white]Dashboard URL:[/]  [bold underline cyan]{existing_url}[/]\n"
            f"  🆔 [bold white]Process PID:[/]    [bold yellow]{existing_pid}[/]\n\n"
            f"  🚀 [italic]Opening existing dashboard in your browser...[/]\n"
            f"  [dim]Tip: Run[/] [bold magenta]stackcheck stop[/] [dim]to terminate the server.[/]",
            border_style="green",
            padding=(1, 2)
        ))
        safe_open_browser(existing_url)
        return

    # 2. Locate target app.py
    target_script = locate_target_script()
    if not target_script:
        console.print("[bold red]✘ Error: Could not locate StackCheck app.py[/]")
        sys.exit(1)

    port = find_free_port(8501)
    app_url = f"http://localhost:{port}"

    # 4. Record PID and port info
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

    banner_text = (
        f"[bold cyan]StackCheck Desktop Intelligence Engine[/] [bold green]v{__version__}[/]\n"
        f"[dim italic]Interactive Job Market Analytics & Skill Intelligence[/]\n\n"
        f"  🌐 [bold white]Local Dashboard:[/]  [bold underline cyan]{app_url}[/]\n"
        f"  🆔 [bold white]Process PID:[/]      [bold yellow]{my_pid}[/]\n"
        f"  📂 [bold white]Data Workspace:[/]   [dim]{STACKCHECK_DIR}[/]\n\n"
        f"  [dim]💡 Tip: Press[/] [bold]Ctrl+C[/] [dim]or run[/] [bold magenta]stackcheck stop[/] [dim]to stop this server anytime.[/]"
    )
    console.print(Panel(
        banner_text,
        title="[bold green]Server Active[/bold green]",
        border_style="cyan",
        padding=(1, 2)
    ))

    # Wait for server readiness probe before opening browser
    wait_for_server_and_open_browser(app_url, port=port, timeout=12.0)

    # Silence noisy debug and polling loggers
    import logging
    for logger_name in ["streamlit", "tornado", "urllib3", "watchdog"]:
        logging.getLogger(logger_name).setLevel(logging.WARNING)

    # Ensure Streamlit static assets exist and Starlette static route handler uses persistent storage
    try:
        persistent_static = ensure_persistent_streamlit_static()
        from streamlit import file_util
        file_util.get_static_dir = lambda: str(persistent_static)

        # Also ensure original package static directory exists if referenced anywhere
        import streamlit
        st_static_path = Path(streamlit.__file__).parent / "static"
        st_static_path.mkdir(parents=True, exist_ok=True)
        if not (st_static_path / "index.html").exists():
            (st_static_path / "index.html").touch(exist_ok=True)
    except Exception:
        pass

    from streamlit import config
    from streamlit.web import bootstrap

    config.set_option("global.developmentMode", False)
    config.set_option("logger.level", "warning")
    config.set_option("server.port", port)
    config.set_option("server.address", "127.0.0.1")
    config.set_option("server.headless", True)
    config.set_option("server.fileWatcherType", "none")
    config.set_option("browser.serverPort", port)
    config.set_option("browser.serverAddress", "localhost")
    config.set_option("browser.gatherUsageStats", False)
    config.set_option("client.toolbarMode", "viewer")
    config.set_option("theme.base", "dark")
    config.set_option("theme.primaryColor", "#3b82f6")
    config.set_option("theme.backgroundColor", "#0f172a")
    config.set_option("theme.secondaryBackgroundColor", "#1e293b")
    config.set_option("theme.textColor", "#f8fafc")

    flag_options = {
        "server_port": port,
        "server_headless": True,
        "server_address": "127.0.0.1",
        "server_fileWatcherType": "none",
        "browser_serverPort": port,
        "browser_serverAddress": "localhost",
        "browser_gatherUsageStats": False,
        "client_toolbarMode": "viewer",
        "global_developmentMode": False,
        "logger_level": "warning",
        "theme_base": "dark",
        "theme_primaryColor": "#3b82f6",
        "theme_backgroundColor": "#0f172a",
        "theme_secondaryBackgroundColor": "#1e293b",
        "theme_textColor": "#f8fafc"
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
