"""
Unit tests for Launcher and Updater utilities.
"""

from stackcheck.launcher import find_free_port
from stackcheck.updater import UpdateChecker
from stackcheck import __version__


def test_find_free_port():
    port = find_free_port(start_port=9000, max_attempts=5)
    assert 9000 <= port < 9005


def test_updater_check_offline_or_invalid():
    # Calling with an invalid repo should fail gracefully and return None (no crash)
    result = UpdateChecker.check_for_update(repo_slug="nonexistent_owner_123/nonexistent_repo_456")
    assert result is None
