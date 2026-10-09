# Executive Dashboard & KPIs

Displays high-level market metrics, top demanded skills, salary averages, and domain category distributions for the active research workspace.

## Sub-features

- `kpi-total-jobs`: Summary card of total postings analyzed in the workspace.
- `kpi-unique-companies`: Count of distinct hiring organizations.
- `kpi-top-skill`: Top technology required across jobs with market frequency percentage.
- `kpi-benchmark-salary`: Average annual benchmark compensation in USD.
- `chart-top-skills`: Horizontal bar chart of top in-demand skills with section-weighted toggles.
- `chart-domain-breakdown`: Donut/pie breakdown of skill classifications.

## How to get to it (user POV)

1. Open the StackCheck web application at `http://127.0.0.1:8501`.
2. The default view opens directly to the first tab: `:material/dashboard: Executive dashboard`.
3. If in another tab, click on the **Executive dashboard** tab button.

## Driving it with AppTest

Preconditions:
- StackCheck database contains at least 1 job post or active workspace.

Steps:
- Mount app: `at = AppTest.from_file("src/stackcheck/web/app.py").run()`
- Select tab: Ensure `at.tabs[0]` is active.
- Assert KPI metric cards:
  ```python
  labels = [m.label for m in at.metric]
  assert "Total jobs analyzed" in labels
  assert "Top demanded skill" in labels
  ```

## Gotchas

- When workspace has 0 jobs, an informational banner ("Welcome to StackCheck...") is shown instead of charts.
- Matplotlib chart generation requires non-interactive backend (`matplotlib.use('Agg')`).
