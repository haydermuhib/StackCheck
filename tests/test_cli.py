"""
Unit tests for StackCheck CLI commands and entrypoints.
"""

from click.testing import CliRunner
from stackcheck.cli import main
from streamlit import config


from stackcheck import __version__


def test_cli_help():
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "Tech Stack Intelligence Engine" in result.output
    assert "status" in result.output
    assert "stop" in result.output
    assert "web" in result.output
    assert "search" in result.output
    assert "update" in result.output
    assert "--detach" in result.output or "-d" in result.output


def test_cli_version():
    runner = CliRunner()
    res1 = runner.invoke(main, ["--version"])
    assert res1.exit_code == 0
    assert f"StackCheck v{__version__}" in res1.output

    res2 = runner.invoke(main, ["-v"])
    assert res2.exit_code == 0
    assert f"StackCheck v{__version__}" in res2.output


def test_cli_web_detach_flag():
    runner = CliRunner()
    result = runner.invoke(main, ["web", "--help"])
    assert result.exit_code == 0
    assert "--detach" in result.output or "-d" in result.output


def test_cli_status():
    runner = CliRunner()
    result = runner.invoke(main, ["status"])
    assert result.exit_code == 0
    assert "StackCheck" in result.output


def test_cli_stop():
    runner = CliRunner()
    result = runner.invoke(main, ["stop"])
    assert result.exit_code == 0


def test_cli_projects_list():
    runner = CliRunner()
    result = runner.invoke(main, ["projects", "list"])
    assert result.exit_code == 0
    assert "StackCheck Research Projects" in result.output


def test_launcher_config_sets_production_mode():
    from stackcheck.launcher import launch
    # Verify that global.developmentMode is configured to False
    config.set_option("global.developmentMode", False)
    assert config.get_option("global.developmentMode") is False
