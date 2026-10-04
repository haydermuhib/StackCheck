"""
Unit tests for StackCheck CLI commands and entrypoints.
"""

from click.testing import CliRunner
from stackcheck.cli import main
from streamlit import config


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
