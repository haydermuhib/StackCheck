"""
Auto-update checker and installer for StackCheck.
Checks GitHub Releases for new versions, streams downloads with visual progress,
and performs in-place binary upgrades.
"""

import sys
import os
import stat
import platform
import logging
from pathlib import Path
from typing import Optional, Dict, Any, Callable
import requests
from packaging import version

from stackcheck import __version__

logger = logging.getLogger(__name__)

# Official GitHub repository slug
DEFAULT_REPO = os.environ.get("STACKCHECK_GITHUB_REPO", "haydermuhib/StackCheck")


class UpdateChecker:
    """Checks for newer releases of StackCheck from GitHub Releases."""

    @staticmethod
    def get_target_asset_name() -> str:
        """Determine release asset binary name for current platform."""
        sys_name = platform.system().lower()
        arch = platform.machine().lower()
        if arch in ["x86_64", "amd64"]:
            arch_tag = "x64"
        elif arch in ["arm64", "aarch64"]:
            arch_tag = "arm64"
        else:
            arch_tag = "x64"

        if sys_name == "windows":
            return f"StackCheck-windows-{arch_tag}.exe"
        elif sys_name == "darwin":
            return f"StackCheck-macos-{arch_tag}"
        else:
            return f"StackCheck-linux-{arch_tag}"

    @classmethod
    def check_for_update(cls, repo_slug: str = DEFAULT_REPO, current_ver: str = __version__) -> Optional[Dict[str, Any]]:
        """
        Check GitHub Releases for a newer version.
        Returns release metadata dict if a newer version is available, else None.
        Runs with a 3-second timeout to ensure the app never hangs if offline.
        """
        url = f"https://api.github.com/repos/{repo_slug}/releases/latest"
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": f"StackCheck/{current_ver}"
        }
        try:
            resp = requests.get(url, headers=headers, timeout=3.0)
            if resp.status_code == 200:
                data = resp.json()
                latest_tag = data.get("tag_name", "").lstrip("v")
                if not latest_tag:
                    return None

                target_asset_name = cls.get_target_asset_name()
                matching_asset = None
                assets = []
                for asset in data.get("assets", []):
                    item = {
                        "name": asset.get("name"),
                        "download_url": asset.get("browser_download_url"),
                        "size_bytes": asset.get("size", 0)
                    }
                    assets.append(item)
                    if asset.get("name") == target_asset_name:
                        matching_asset = item

                # If exact name wasn't matched, check fallback
                if not matching_asset and assets:
                    matching_asset = assets[0]

                has_update = version.parse(latest_tag) > version.parse(current_ver)

                return {
                    "has_update": has_update,
                    "current_version": current_ver,
                    "latest_version": latest_tag,
                    "release_title": data.get("name") or f"Release v{latest_tag}",
                    "html_url": data.get("html_url", f"https://github.com/{repo_slug}/releases"),
                    "body": data.get("body", "").strip(),
                    "published_at": data.get("published_at", ""),
                    "target_asset": matching_asset,
                    "assets": assets
                }
        except Exception as e:
            logger.debug(f"Update check skipped or failed: {e}")

        return None

    @classmethod
    def download_asset(
        cls,
        download_url: str,
        dest_path: Path,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> bool:
        """
        Stream download asset with chunked progress callback.
        progress_callback signature: (chunk_bytes, total_bytes)
        """
        headers = {"User-Agent": f"StackCheck/{__version__}"}
        resp = requests.get(download_url, headers=headers, stream=True, timeout=30.0)
        resp.raise_for_status()

        total_bytes = int(resp.headers.get("content-length", 0))
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        temp_dest = dest_path.with_suffix(".tmp")

        try:
            with open(temp_dest, "wb") as f:
                for chunk in resp.iter_content(chunk_size=64 * 1024):
                    if chunk:
                        f.write(chunk)
                        if progress_callback:
                            progress_callback(len(chunk), total_bytes)
            
            # Atomically rename
            if temp_dest.exists():
                temp_dest.replace(dest_path)
                # Ensure executable permissions on Linux/macOS
                if platform.system() != "Windows":
                    current_stat = os.stat(dest_path)
                    os.chmod(dest_path, current_stat.st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
            return True
        finally:
            if temp_dest.exists():
                try:
                    temp_dest.unlink()
                except OSError:
                    pass

    @classmethod
    def get_install_target_path(cls) -> Path:
        """Determine path of the executable to replace."""
        # 1. If running as standalone PyInstaller binary:
        if getattr(sys, "frozen", False):
            return Path(sys.executable).resolve()
        
        # 2. Check standard ~/.local/bin/stackcheck location:
        local_bin = Path.home() / ".local" / "bin" / ("stackcheck.exe" if platform.system() == "Windows" else "stackcheck")
        if local_bin.exists():
            return local_bin

        # 3. Default to ~/.local/bin target:
        return local_bin
