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


def test_is_port_listening_unused_port():
    from stackcheck.launcher import is_port_listening
    # An unused high port should not be listening
    assert not is_port_listening(59999)


def test_instance_tracking_and_cleanup():
    from stackcheck.launcher import cleanup_instance_files, get_running_instance, stop_running_instance
    cleanup_instance_files()
    assert get_running_instance() is None
    # Stopping when not running should safely return False
    assert not stop_running_instance()
