---
name: verify-stackcheck
description: "Verify StackCheck web UI and CLI behavior headlessly. Drives Streamlit tabs, search filters, and terminal commands to capture empirical proof."
---

# Verify StackCheck

This skill drives and asserts StackCheck behavior headlessly across both its Web GUI (Streamlit) and CLI command surfaces.

## 1. Doctor

Run the read-only environment and dependency sanity check:

```bash
.venv/bin/python .cursor/skills/verify-stackcheck/harness.py doctor
```

Must return `"healthy": true` with valid database connectivity and entrypoint paths.

## 2. Launch

To run the live desktop server for end-to-end browser inspection:

```bash
# Starts StackCheck on isolated port 8502 without opening a desktop browser window
.venv/bin/python -m stackcheck.launcher --port 8502 --headless
```

Ready when `is_port_listening(8502)` returns true and `http://127.0.0.1:8502` answers HTTP 200.

## 3. Drive

### Headless UI Drive
To verify the Streamlit dashboard structure, tabs, widgets, and state without running a network server:

```bash
.venv/bin/python .cursor/skills/verify-stackcheck/harness.py ui
```

This drives `src/stackcheck/web/app.py` via `streamlit.testing.v1.AppTest`, asserting:
- 3 primary tabs are mounted (`Executive dashboard`, `Statistical analytics`, `Job explorer`).
- Research workspace selector and modal dialog buttons (`New`, `Default`, `Delete`).
- Scraper filters (`Role quick-picks`, `Country quick-picks`, `Workplace mode`).

### CLI Drive
To verify command-line argument parsing and command execution:

```bash
.venv/bin/python .cursor/skills/verify-stackcheck/harness.py cli
```

## 4. Evidence

All verification runs record timestamped evidence artifacts in:
- `.stackcheck/evidence/ui_verification_proof.json`
- `.stackcheck/evidence/cli_verification_proof.json`

Evidence records include widget inventories, active tab counts, exit codes, and stdout snippets.

## 5. Cleanup

To shut down any running server instance:

```bash
# Clean shutdown via launcher instance tracker
.venv/bin/python -c "from stackcheck.launcher import stop_running_instance; stop_running_instance()"
```

Proof JSON artifacts in `.stackcheck/evidence/` survive teardown.

## 6. Helpers

- Harness script: `.cursor/skills/verify-stackcheck/harness.py`
  - `doctor`: validates environment readiness.
  - `ui`: executes headless Streamlit AppTest run.
  - `cli`: validates CLI entrypoint and commands.
  - `all`: runs doctor, UI, and CLI checks in sequence.
