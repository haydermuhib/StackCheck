"""
Auto-update checker for StackCheck.
Checks GitHub Releases for new versions and provides release notes and direct download links.
"""

import json
import logging
from typing import Optional, Dict, Any
import requests
from packaging import version

from stackcheck import __version__

logger = logging.getLogger(__name__)

# Default repository slug (can be overridden via env var STACKCHECK_GITHUB_REPO)
DEFAULT_REPO = "haider/StackCheck"


class UpdateChecker:
    """Checks for newer releases of StackCheck from GitHub Releases."""

    @staticmethod
    def check_for_update(repo_slug: str = DEFAULT_REPO, current_ver: str = __version__) -> Optional[Dict[str, Any]]:
        """
        Check GitHub Releases for a newer version.
        Returns release metadata dict if a newer version is available, else None.
        Runs with a 2-second timeout to ensure the app never hangs if offline.
        """
        url = f"https://api.github.com/repos/{repo_slug}/releases/latest"
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": f"StackCheck/{current_ver}"
        }
        try:
            resp = requests.get(url, headers=headers, timeout=2.5)
            if resp.status_code == 200:
                data = resp.json()
                latest_tag = data.get("tag_name", "").lstrip("v")
                if not latest_tag:
                    return None

                # Compare versions using packaging.version
                if version.parse(latest_tag) > version.parse(current_ver):
                    # Extract binary assets if attached
                    assets = []
                    for asset in data.get("assets", []):
                        assets.append({
                            "name": asset.get("name"),
                            "download_url": asset.get("browser_download_url"),
                            "size_bytes": asset.get("size", 0)
                        })

                    return {
                        "has_update": True,
                        "current_version": current_ver,
                        "latest_version": latest_tag,
                        "release_title": data.get("name") or f"Release v{latest_tag}",
                        "html_url": data.get("html_url", f"https://github.com/{repo_slug}/releases"),
                        "body": data.get("body", "").strip(),
                        "published_at": data.get("published_at", ""),
                        "assets": assets
                    }
        except Exception as e:
            logger.debug(f"Update check skipped or failed: {e}")

        return None
