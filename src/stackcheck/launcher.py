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

            # Also ensure assets (logo, icon) are mirrored to STACKCHECK_DIR/assets
            source_assets = None
            if hasattr(sys, "_MEIPASS"):
                p_mei = Path(sys._MEIPASS) / "assets"
                if p_mei.exists():
                    source_assets = p_mei
            if not source_assets:
                for candidate_asset in [
                    BASE_DIR / "assets",
                    source_app.parent.parent.parent.parent / "assets",
                    source_app.parent.parent / "assets",
                    Path.cwd() / "assets"
                ]:
                    if candidate_asset.exists():
                        source_assets = candidate_asset
                        break

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


def _launch_detached():
    """Launch StackCheck in a detached background daemon process."""
    import subprocess
    STACKCHECK_DIR.mkdir(parents=True, exist_ok=True)
    log_file_path = STACKCHECK_DIR / "stackcheck.log"

    if getattr(sys, "frozen", False):
        cmd = [sys.executable, "web"]
    else:
        cmd = [sys.executable, "-m", "stackcheck.cli", "web"]

    log_file = open(log_file_path, "a", encoding="utf-8")

    env = os.environ.copy()
    # In PyInstaller one-file bundles, child processes inherit _MEIPASS2, which points to
    # the parent's temporary folder. When the parent exits, PyInstaller cleans up that folder,
    # causing FileNotFoundError on child accesses. Removing _MEIPASS2 ensures the child
    # extracts and manages its own independent temporary directory.
    env.pop("_MEIPASS2", None)
    if "LD_LIBRARY_PATH_ORIG" in env:
        env["LD_LIBRARY_PATH"] = env["LD_LIBRARY_PATH_ORIG"]

    kwargs: Dict[str, Any] = {
        "stdout": log_file,
        "stderr": subprocess.STDOUT,
        "stdin": subprocess.DEVNULL,
        "close_fds": True,
        "env": env,
    }

    if sys.platform == "win32":
        creationflags = getattr(subprocess, "DETACHED_PROCESS", 0) | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
        kwargs["creationflags"] = creationflags
    else:
        kwargs["start_new_session"] = True

    try:
        proc = subprocess.Popen(cmd, **kwargs)
    except Exception as e:
        console.print(f"[bold red]✘ Failed to spawn background process:[/] {e}")
        return

    with console.status("[bold cyan]Starting StackCheck background service...", spinner="dots"):
        start_time = time.time()
        running_info = None
        while time.time() - start_time < 15.0:
            if proc.poll() is not None:
                break
            running_info = get_running_instance()
            if running_info:
                break
            time.sleep(0.3)

    if running_info:
        url = running_info.get("url")
        pid = running_info.get("pid")
        console.print("[bold green]✔[/bold green] StackCheck background service started successfully.")
        console.print(Panel(
            f"[bold green]StackCheck Background Service Active[/bold green]\n\n"
            f"  🌐 [bold white]Dashboard URL:[/]  [bold underline cyan]{url}[/]\n"
            f"  🆔 [bold white]Process PID:[/]    [bold yellow]{pid}[/]\n"
            f"  📝 [bold white]Logs:[/]           [dim]{log_file_path}[/]\n\n"
            f"  [dim]Commands:[/] [bold cyan]stackcheck status[/] [dim]•[/] [bold magenta]stackcheck stop[/]",
            border_style="green",
            padding=(1, 2)
        ))
        safe_open_browser(url)
    else:
        console.print("[bold red]✘ Failed to verify StackCheck background service startup.[/]")
        if log_file_path.exists():
            try:
                with open(log_file_path, "r", encoding="utf-8", errors="ignore") as f:
                    lines = f.readlines()[-15:]
                    if lines:
                        console.print(Panel("".join(lines), title="[bold red]Startup Log Snippet[/]", border_style="red"))
            except Exception:
                pass
        sys.exit(1)


def launch(detach: bool = False):
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

    # 2. Detached mode requested
    if detach:
        _launch_detached()
        return

    # 3. Locate target app.py
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
