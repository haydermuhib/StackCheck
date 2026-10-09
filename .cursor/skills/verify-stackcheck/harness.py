#!/usr/bin/env python3
"""
StackCheck Verification Harness.
Drives the Streamlit GUI headlessly via Streamlit AppTest and tests CLI commands,
capturing structured verification evidence and doctor status reports.
"""

import sys
import os
import time
import json
import subprocess
from pathlib import Path
from typing import Dict, Any

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
EVIDENCE_DIR = REPO_ROOT / ".stackcheck" / "evidence"


def run_doctor() -> Dict[str, Any]:
    """Read-only health check to ensure StackCheck environment is valid and ready."""
    results = {
        "timestamp": time.time(),
        "python_version": sys.version,
        "repo_root": str(REPO_ROOT),
        "checks": {}
    }

    # Check 1: Python packages
    try:
        import streamlit
        import pandas
        import matplotlib
        import rich
        _ = (matplotlib, rich)
        results["checks"]["imports"] = {
            "status": "PASS",
            "streamlit_version": streamlit.__version__,
            "pandas_version": pandas.__version__
        }

    except Exception as e:
        results["checks"]["imports"] = {"status": "FAIL", "error": str(e)}

    # Check 2: App entrypoint exists
    app_py = REPO_ROOT / "src" / "stackcheck" / "web" / "app.py"
    results["checks"]["app_entrypoint"] = {
        "status": "PASS" if app_py.exists() else "FAIL",
        "path": str(app_py)
    }

    # Check 3: CLI entrypoint executable
    cli_py = REPO_ROOT / "src" / "stackcheck" / "cli.py"
    results["checks"]["cli_entrypoint"] = {
        "status": "PASS" if cli_py.exists() else "FAIL",
        "path": str(cli_py)
    }

    # Check 4: SQLite DB accessibility
    try:
        from stackcheck.storage.repository import JobRepository
        repo = JobRepository()
        projects = repo.get_projects()
        results["checks"]["database"] = {
            "status": "PASS",
            "projects_count": len(projects)
        }
    except Exception as e:
        results["checks"]["database"] = {"status": "FAIL", "error": str(e)}

    is_healthy = all(c.get("status") == "PASS" for c in results["checks"].values())
    results["healthy"] = is_healthy
    return results


def verify_ui() -> Dict[str, Any]:
    """Drives the Streamlit application headlessly and captures DOM state and widget evidence."""
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    os.environ["MPLCONFIGDIR"] = "/tmp/matplotlib-verify"

    evidence = {
        "timestamp": time.time(),
        "type": "ui",
        "target": "src/stackcheck/web/app.py",
        "status": "UNKNOWN"
    }

    from streamlit.testing.v1 import AppTest
    at = AppTest.from_file(str(REPO_ROOT / "src" / "stackcheck" / "web" / "app.py"))
    at.run(timeout=15)

    if at.exception:
        evidence["status"] = "FAIL"
        evidence["error"] = [str(e) for e in at.exception]
        return evidence

    tabs_count = len(at.tabs)
    button_labels = [b.label for b in at.button]
    selectbox_labels = [s.label for s in at.selectbox]
    metric_labels = [m.label for m in at.metric]

    evidence["status"] = "PASS"
    evidence["state"] = {
        "tabs_count": tabs_count,
        "buttons": button_labels,
        "selectboxes": selectbox_labels,
        "metrics_found": metric_labels
    }

    evidence_file = EVIDENCE_DIR / "ui_verification_proof.json"
    with open(evidence_file, "w", encoding="utf-8") as f:
        json.dump(evidence, f, indent=2)

    evidence["evidence_file"] = str(evidence_file)
    return evidence


def verify_cli() -> Dict[str, Any]:
    """Runs StackCheck CLI commands and records exit codes and outputs."""
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    
    python_bin = sys.executable
    cmd = [python_bin, "-m", "stackcheck.cli", "--help"]
    
    proc = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True)
    
    evidence = {
        "timestamp": time.time(),
        "type": "cli",
        "command": "python -m stackcheck.cli --help",
        "exit_code": proc.returncode,
        "stdout_snippet": proc.stdout[:300],
        "status": "PASS" if proc.returncode == 0 and "StackCheck" in proc.stdout else "FAIL"
    }

    evidence_file = EVIDENCE_DIR / "cli_verification_proof.json"
    with open(evidence_file, "w", encoding="utf-8") as f:
        json.dump(evidence, f, indent=2)

    evidence["evidence_file"] = str(evidence_file)
    return evidence


def main():
    arg = sys.argv[1] if len(sys.argv) > 1 else "doctor"
    if arg == "doctor":
        res = run_doctor()
        print(json.dumps(res, indent=2))
        sys.exit(0 if res.get("healthy") else 1)
    elif arg == "ui":
        res = verify_ui()
        print(json.dumps(res, indent=2))
        sys.exit(0 if res.get("status") == "PASS" else 1)
    elif arg == "cli":
        res = verify_cli()
        print(json.dumps(res, indent=2))
        sys.exit(0 if res.get("status") == "PASS" else 1)
    elif arg == "all":
        doc = run_doctor()
        ui = verify_ui()
        cli = verify_cli()
        summary = {"doctor": doc, "ui": ui, "cli": cli}
        print(json.dumps(summary, indent=2))
        sys.exit(0 if (doc.get("healthy") and ui.get("status") == "PASS" and cli.get("status") == "PASS") else 1)
    else:
        print(f"Unknown action: {arg}. Available: doctor, ui, cli, all")
        sys.exit(2)


if __name__ == "__main__":
    main()
