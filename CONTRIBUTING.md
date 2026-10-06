# Contributing to StackCheck

Thank you for your interest in contributing to StackCheck. This document covers setting up a local development environment, running tests, and submitting changes.

## Development setup

StackCheck requires Python 3.10 or later.

1. Clone the repository:
   ```bash
   git clone https://github.com/haydermuhib/StackCheck.git
   cd StackCheck
   ```

2. Create and activate a virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
   On Windows PowerShell:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

3. Install the package in editable mode with development dependencies:
   ```bash
   pip install -e .
   pip install pytest pyinstaller
   ```
   If you use `uv`, you can run:
   ```bash
   uv pip install -e . pytest pyinstaller
   ```

## Running the application locally

You can launch the dashboard with the CLI entrypoint:
```bash
stackcheck
```

Or run the Streamlit application directly:
```bash
streamlit run src/stackcheck/web/app.py
```

## Running tests

The test suite uses pytest. Run all tests before submitting changes:
```bash
pytest tests/
```

To run a specific test file:
```bash
pytest tests/test_analyzer.py
pytest tests/test_web.py
```

All 36 tests must pass without warnings or failures.

## Project layout

The source code lives inside `src/stackcheck`:

- `client/`: HiringCafe client using `curl_cffi`, batch page harvesting, and normalizers.
- `analyzer/`: Rule-based skill extraction, positional weighting, and compensation math.
- `storage/`: SQLite storage layer, multi-project workspaces, and CSV or JSON exports.
- `web/`: Streamlit analytics UI, Matplotlib and Seaborn dark charts, and dialog modals.
- `cli.py`: Click command line interface and background process launcher.
- `tests/`: Unit and integration test suite covering ingestion, normalization, charts, and storage.

## Submitting changes

1. Create a descriptive branch from `main`:
   ```bash
   git checkout -b fix-salary-percentile-calculation
   ```

2. Keep changes focused. A pull request should address one bug or feature.

3. Write tests for any new behavior or bug fix. Confirm existing tests continue to pass.

4. Follow existing conventions:
   - Use standard Python type hints.
   - Keep charts accessible against dark backgrounds (`#0F172A`).
   - Avoid adding external dependencies unless necessary.
   - Keep user-facing text concise and free of promotional jargon.

5. Write a clear commit message explaining the problem and the solution.

6. Push your branch and open a pull request against the `main` branch.

## Reporting issues

If you encounter a bug or unexpected behavior, open an issue on GitHub with:

- Your operating system and Python version.
- Exact commands run and query parameters used.
- Complete traceback or console logs.
- What you expected to happen versus what actually occurred.
