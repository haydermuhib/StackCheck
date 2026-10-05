# Remove Detach Flag (-d) & Redundant `web` Command Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove the broken `-d`/`--detach` daemon mode flag and redundant `stackcheck web` command, standardizing on the stable foreground `stackcheck` desktop launcher and preventing PyInstaller `/tmp/_MEI...` cleanup crashes.

**Architecture:** In PyInstaller onefile executables, detaching a child process while terminating the parent causes the bootloader to clean up `/tmp/_MEI...`, deleting compiled NumPy/Pandas C-extensions. Removing the detached daemon mode simplifies the process lifecycle to reliable foreground execution (`stackcheck`) where the parent process remains alive and healthy. Eliminating the redundant `stackcheck web` command streamlines the CLI so `stackcheck` is the single unified entrypoint for the dashboard.

**Tech Stack:** Python 3.10+, Click, Rich, Streamlit, Pytest.

**Spec:** User issue report:
- `FileNotFoundError: [Errno 2] No such file or directory: '/tmp/_MEI000016576lOjVJ/numpy/_core'`
- `ModuleNotFoundError: No module named 'numpy._core._multiarray_umath'`
- User requirement: Remove `-d`/`--detach` support and remove redundant `stackcheck web` command.

## Global Constraints
- Preserve all existing commands: `stackcheck`, `stackcheck status`, `stackcheck stop`, `stackcheck check`, `stackcheck update`, `stackcheck search`, `stackcheck analyze`, `stackcheck export`, `stackcheck projects`, `stackcheck sync`.
- `stackcheck status` and `stackcheck stop` must continue to work for running dashboard processes (reading `~/.stackcheck/instance_info.json`).
- All tests in `tests/` must pass cleanly via `./.venv/bin/pytest -v`.
- Follow strict TDD: Red (failing test) -> Green (minimal implementation) -> Refactor.

---

### Task 1: Remove `-d` / `--detach` flag and `web` command from CLI (TDD)

**Files:**
- Modify: `tests/test_cli.py`
- Modify: `src/stackcheck/cli.py`

**Interfaces:**
- Consumes: `stackcheck.cli.main`
- Produces: Clean CLI entrypoint without `-d`/`--detach` options and without `web` subcommand.

- [ ] **Step 1: Write the failing tests in `tests/test_cli.py`**

Update `test_cli_help` to assert `--detach`, `-d`, and `web` are NOT in `main --help` output.
Replace `test_cli_web_detach_flag` with tests asserting:
1. `runner.invoke(main, ["-d"])` exits with code != 0 and contains "No such option: -d"
2. `runner.invoke(main, ["--detach"])` exits with code != 0 and contains "No such option: --detach"
3. `runner.invoke(main, ["web"])` exits with code != 0 and contains "No such command 'web'"

```python
def test_cli_help():
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "Tech Stack Intelligence Engine" in result.output
    assert "status" in result.output
    assert "stop" in result.output
    assert "search" in result.output
    assert "update" in result.output
    assert "web" not in result.output
    assert "--detach" not in result.output
    assert "-d" not in result.output


def test_cli_detach_flag_removed():
    runner = CliRunner()
    res1 = runner.invoke(main, ["-d"])
    assert res1.exit_code != 0
    assert "No such option: -d" in res1.output

    res2 = runner.invoke(main, ["--detach"])
    assert res2.exit_code != 0
    assert "No such option: --detach" in res2.output


def test_cli_web_command_removed():
    runner = CliRunner()
    result = runner.invoke(main, ["web"])
    assert result.exit_code != 0
    assert "No such command 'web'" in result.output
```

- [ ] **Step 2: Run test to verify it fails**

Run: `./.venv/bin/pytest tests/test_cli.py -k "test_cli_help or test_cli_detach_flag_removed or test_cli_web_command_removed" -v`
Expected: FAIL because `-d` and `web` currently exist.

- [ ] **Step 3: Modify `src/stackcheck/cli.py` to remove `-d` and `web` command**

1. Remove `@click.option("-d", "--detach", ...)` from `main`.
2. Update signature to `def main(ctx):` and call `launch()` with no arguments.
3. Remove `@main.command() def web(detach):` function completely.
4. Update `status()` command output:
   Replace:
   `"Run [bold cyan]stackcheck[/] (foreground) or [bold cyan]stackcheck -d[/] (background daemon)\n"`
   With:
   `"Run [bold cyan]stackcheck[/] to launch the interactive dashboard.\n"`

- [ ] **Step 4: Run tests to verify they pass**

Run: `./.venv/bin/pytest tests/test_cli.py -v`
Expected: PASS

- [ ] **Step 5: Commit changes**

```bash
git add tests/test_cli.py src/stackcheck/cli.py
git commit -m "refactor(cli): remove -d flag and redundant web command"
```

---

### Task 2: Simplify launcher engine by removing detached daemon logic (TDD)

**Files:**
- Modify: `tests/test_launcher.py`
- Modify: `src/stackcheck/launcher.py`

**Interfaces:**
- Consumes: `src/stackcheck/launcher.py`
- Produces: `launch()` with signature `() -> None` without detached background spawning.

- [ ] **Step 1: Write failing test in `tests/test_launcher.py`**

Replace `test_detached_env_sanitization` with a signature check:
```python
def test_launcher_signature_no_detach():
    import inspect
    from stackcheck.launcher import launch
    sig = inspect.signature(launch)
    assert "detach" not in sig.parameters
```

- [ ] **Step 2: Run test to verify it fails**

Run: `./.venv/bin/pytest tests/test_launcher.py::test_launcher_signature_no_detach -v`
Expected: FAIL because `detach` is currently a parameter of `launch`.

- [ ] **Step 3: Modify `src/stackcheck/launcher.py`**

1. Remove `_launch_detached()` function.
2. Change `def launch(detach: bool = False):` to `def launch():`.
3. Remove `if detach: _launch_detached(); return` block.

- [ ] **Step 4: Run tests to verify they pass**

Run: `./.venv/bin/pytest tests/test_launcher.py -v`
Expected: PASS

- [ ] **Step 5: Commit changes**

```bash
git add tests/test_launcher.py src/stackcheck/launcher.py
git commit -m "refactor(launcher): remove _launch_detached and detach parameter"
```

---

### Task 3: Update documentation and references across the repository

**Files:**
- Modify: `README.md`
- Modify: `ARCHITECTURE.md`
- Modify: `PRESENTATION.md`
- Modify: `llms.txt`
- Modify: `llm.txt`

- [ ] **Step 1: Update `README.md`**
  - In `## ⚙️ CLI Usage Reference`: remove `# Launch Web Dashboard as detached background service \n stackcheck -d`.
  - In `## 📌 Quick Reference Card`: remove `stackcheck -d` row.

- [ ] **Step 2: Update `ARCHITECTURE.md`**
  - Line 48: Change `# Rich CLI interface with detached daemon support` -> `# Rich CLI interface`.
  - Line 194: Remove `Detached Daemon Mode (-d)` bullet point.
  - Line 196: Update mention of detached instances to focus on foreground execution and offline survival.
  - Lines 300, 313: Update test names.
  - Lines 340, 354: Remove `stackcheck -d` examples.

- [ ] **Step 3: Update `PRESENTATION.md`**
  - In Section 9 Quick Reference CLI table: remove `stackcheck -d` row.

- [ ] **Step 4: Update `llms.txt` and `llm.txt`**
  - Remove references to detached daemon `-d`.

- [ ] **Step 5: Commit documentation updates**

```bash
git add README.md ARCHITECTURE.md PRESENTATION.md llms.txt llm.txt
git commit -m "docs: remove -d flag and detached daemon references"
```

---

### Task 4: Version Bump to v0.1.9 and Final Verification

**Files:**
- Modify: `pyproject.toml`
- Modify: `src/stackcheck/__init__.py`

- [ ] **Step 1: Bump version to `0.1.9`**
  - `pyproject.toml`: `version = "0.1.9"`
  - `src/stackcheck/__init__.py`: `__version__ = "0.1.9"`

- [ ] **Step 2: Run complete test suite**

Run: `./.venv/bin/pytest -v`
Expected: All tests pass (35+ passed).

- [ ] **Step 3: Commit and push with tag v0.1.9**

```bash
git add pyproject.toml src/stackcheck/__init__.py
git commit -m "chore: bump version to v0.1.9"
git tag -a v0.1.9 -m "Release v0.1.9: Remove broken -d daemon flag and redundant web command"
git push origin main --tags
```
