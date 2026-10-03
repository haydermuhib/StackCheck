"""
StackCheck Standalone Executable Builder.
Uses PyInstaller to bundle StackCheck into a single standalone binary with embedded icon & Streamlit runtime.
"""

import sys
import os
import platform
import argparse
import subprocess
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
SRC_DIR = ROOT_DIR / "src"
ASSETS_DIR = ROOT_DIR / "assets"

# Ensure UTF-8 output encoding on Windows consoles
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


def get_streamlit_static_dir():
    import streamlit
    return Path(streamlit.__file__).parent / "static"


def build(onefile: bool = True):
    print("=" * 60)
    print("  [*] Building StackCheck Standalone Desktop Application")
    print(f"  OS Platform: {platform.system()} {platform.machine()}")
    print(f"  Packaging Mode: {'Single File Executable (--onefile)' if onefile else 'Folder Bundle (--onedir)'}")
    print("=" * 60)

    static_dir = get_streamlit_static_dir()
    sep = ";" if platform.system() == "Windows" else ":"

    # Determine icon file
    if platform.system() == "Windows" and (ASSETS_DIR / "icon.ico").exists():
        icon_arg = str(ASSETS_DIR / "icon.ico")
    elif (ASSETS_DIR / "icon.png").exists():
        icon_arg = str(ASSETS_DIR / "icon.png")
    else:
        icon_arg = None

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name=StackCheck",
        "--clean",
        "--noconfirm",
        "--onefile" if onefile else "--onedir",
        f"--add-data={SRC_DIR / 'stackcheck'}{sep}stackcheck",
        f"--add-data={static_dir}{sep}streamlit/static",
        f"--add-data={ASSETS_DIR}{sep}assets",
        "--copy-metadata=streamlit",
        "--copy-metadata=altair",
        "--copy-metadata=rich",
        "--copy-metadata=click",
        "--hidden-import=streamlit",
        "--hidden-import=streamlit.web.bootstrap",
        "--hidden-import=streamlit.runtime.scriptrunner.magic_expressions",
        "--hidden-import=altair",
        "--hidden-import=pandas",
        "--hidden-import=matplotlib",
        "--hidden-import=requests",
        "--hidden-import=pydantic",
        "--hidden-import=packaging",
        "--hidden-import=sqlite3",
        "--hidden-import=stackcheck",
        str(SRC_DIR / "stackcheck" / "launcher.py")
    ]

    if icon_arg:
        cmd.append(f"--icon={icon_arg}")

    print("Executing PyInstaller...")
    res = subprocess.run(cmd, cwd=str(ROOT_DIR))
    if res.returncode == 0:
        print("\n" + "=" * 60)
        print("  [OK] Build successful!")
        dist_path = ROOT_DIR / "dist" / ("StackCheck.exe" if platform.system() == "Windows" else "StackCheck")
        print(f"  [+] Generated Executable: {dist_path}")
        print("=" * 60)
    else:
        print(f"\n[ERROR] Build failed with exit code {res.returncode}")
        sys.exit(res.returncode)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build StackCheck standalone executable")
    parser.add_argument("--onedir", action="store_true", help="Build as a folder bundle rather than a single file")
    args = parser.parse_args()
    build(onefile=not args.onedir)
