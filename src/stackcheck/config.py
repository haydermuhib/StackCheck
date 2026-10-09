"""
Configuration and constants for StackCheck
"""

import os
from pathlib import Path

import sys

# Paths
WORKSPACE_DIR = Path(os.getcwd())
try:
    DEFAULT_DATA_DIR = Path.home() / ".stackcheck"
    DEFAULT_DATA_DIR.mkdir(parents=True, exist_ok=True)
except (OSError, PermissionError):
    DEFAULT_DATA_DIR = WORKSPACE_DIR / ".stackcheck"
    try:
        DEFAULT_DATA_DIR.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass


def get_assets_dir() -> Path:
    """Resolve the assets directory reliably across local dev, installed packages, user workspace, and PyInstaller bundles."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        meipass_assets = Path(sys._MEIPASS) / "assets"
        if meipass_assets.exists():
            return meipass_assets

    user_assets = DEFAULT_DATA_DIR / "assets"
    if user_assets.exists() and (user_assets / "logo.png").exists():
        return user_assets

    repo_assets = Path(__file__).resolve().parent.parent.parent / "assets"
    if repo_assets.exists():
        return repo_assets

    pkg_assets = Path(__file__).resolve().parent / "assets"
    if pkg_assets.exists():
        return pkg_assets

    cwd_assets = Path.cwd() / "assets"
    if cwd_assets.exists():
        return cwd_assets

    return repo_assets


# Database & Exports in central user data directory (~/.stackcheck/)
LOCAL_DB_PATH = Path(os.getenv("STACKCHECK_DB_PATH", DEFAULT_DATA_DIR / "stackcheck.db"))
EXPORTS_DIR = Path(os.getenv("STACKCHECK_EXPORTS_DIR", DEFAULT_DATA_DIR / "exports"))
try:
    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
except Exception:
    pass


# HiringCafe API Endpoints
HIRINGCAFE_BASE_URL = "https://hiring.cafe"
HIRINGCAFE_SEARCH_ENDPOINT = "https://hiring.cafe/api/search"
DEFAULT_USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"

# UI Theme (Tokyo Night aesthetic)
THEME = {
    "bg_primary": "#1a1b26",
    "bg_secondary": "#24283b",
    "bg_tertiary": "#1f2335",
    "text_primary": "#c0caf5",
    "text_secondary": "#a9b1d6",
    "text_muted": "#565f89",
    "accent_blue": "#7aa2f7",
    "accent_teal": "#73daca",
    "accent_purple": "#bb9af7",
    "accent_amber": "#e0af68",
    "accent_green": "#9ece6a",
    "accent_coral": "#f7768e",
    "border_color": "#3b4261",
}
