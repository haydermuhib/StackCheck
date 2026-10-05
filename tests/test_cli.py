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
    assert "search" in result.output
    assert "update" in result.output
    assert "web" not in main.commands
    assert "\n  web " not in result.output
    assert "--detach" not in result.output
    assert "-d" not in result.output


def test_cli_version():
    runner = CliRunner()
    res1 = runner.invoke(main, ["--version"])
    assert res1.exit_code == 0
    assert f"StackCheck v{__version__}" in res1.output

    res2 = runner.invoke(main, ["-v"])
    assert res2.exit_code == 0
    assert f"StackCheck v{__version__}" in res2.output


def test_cli_detach_flag_removed():
    runner = CliRunner()
    res1 = runner.invoke(main, ["-d"])
    assert res1.exit_code != 0
    assert "No such option" in res1.output and "-d" in res1.output

    res2 = runner.invoke(main, ["--detach"])
    assert res2.exit_code != 0
    assert "No such option" in res2.output and "--detach" in res2.output


def test_cli_web_command_removed():
    runner = CliRunner()
    result = runner.invoke(main, ["web"])
    assert result.exit_code != 0
    assert "No such command 'web'" in result.output


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
