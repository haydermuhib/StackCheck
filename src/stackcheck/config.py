"""
Configuration and constants for StackCheck
"""

import os
from pathlib import Path

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

def _resolve_db_path() -> Path:
    env_path = os.getenv("STACKCHECK_DB_PATH")
    if env_path:
        return Path(env_path)
    cwd_db = WORKSPACE_DIR / "stackcheck.db"
    if cwd_db.exists():
        return cwd_db
    return DEFAULT_DATA_DIR / "stackcheck.db"


LOCAL_DB_PATH = _resolve_db_path()
EXPORTS_DIR = Path(os.getenv("STACKCHECK_EXPORTS_DIR", WORKSPACE_DIR / "exports"))
try:
    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
except Exception:
    pass

# Central Community DB Sync endpoint (Mockable / Configurable for Supabase / REST hub)
CENTRAL_HUB_URL = os.getenv("STACKCHECK_CENTRAL_HUB_URL", "https://api.stackcheck.community/v1")
CENTRAL_HUB_ENABLED = os.getenv("STACKCHECK_CENTRAL_HUB_ENABLED", "true").lower() in ("true", "1", "yes")

# LLM Configuration for deep description parsing
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

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
