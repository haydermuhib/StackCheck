# StackCheck verification map

This directory is the maintained source for verifying user-facing features of StackCheck. Read the index before driving the app, then use the matching feature file as the recipe.

## Baseline preconditions

- Active virtual environment with dependencies installed at `.venv/bin/python`.
- Working directory set to repository root `/home/haider/Desktop/MyGithub/StackCheck`.
- Ensure `MPLCONFIGDIR=/tmp/matplotlib-verify` is exported to prevent font-cache permission warnings.
- Run doctor check: `.venv/bin/python .cursor/skills/verify-stackcheck/harness.py doctor`.

## Driving conventions

- Prefer `streamlit.testing.v1.AppTest` for headless and hermetic UI driving.
- Prefer ARIA labels and widget keys over raw HTML selectors.
- Save proofs to `.stackcheck/evidence/`. Do not purge proofs during cleanup.

## Features

- [Executive Dashboard & Analytics](./dashboard-kpis.md) covers top tech skills, co-occurrence heatmaps, and compensation KPIs.
- [Search & Scraper Pipeline](./search-scraper.md) covers role quick-picks, location queries, and limits.
- [Job Explorer & Data Exports](./job-explorer.md) covers multi-filter facet searching, tabular views, and CSV/JSON downloads.
