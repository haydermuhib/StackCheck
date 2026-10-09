"""
Unit tests for Launcher and Updater utilities.
"""

from stackcheck.launcher import find_free_port
from stackcheck.updater import UpdateChecker


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


def test_locate_target_script_and_persistent_sync():
    from pathlib import Path
    from stackcheck.launcher import locate_target_script, STACKCHECK_DIR
    script = locate_target_script()
    assert script is not None
    p = Path(script)
    assert p.exists()
    assert p.is_file()
    content = p.read_text(encoding="utf-8")
    assert "Streamlit Web Dashboard for StackCheck" in content
    # Verify persistent copy in STACKCHECK_DIR/web/app.py
    persistent_copy = STACKCHECK_DIR / "web" / "app.py"
    assert persistent_copy.exists()


def test_launcher_signature_no_detach():
    import inspect
    from stackcheck.launcher import launch
    sig = inspect.signature(launch)
    assert "detach" not in sig.parameters
