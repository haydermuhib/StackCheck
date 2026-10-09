# Job Explorer & Data Exports

Browses and filters collected job postings by seniority, country, or specific tech skills, and exports datasets in CSV, JSON, or Markdown formats.

## Sub-features

- `filter-multiselect-exp`: Multi-select filter for seniority levels.
- `filter-multiselect-country`: Country-level filtering.
- `filter-multiselect-skills`: Skill requirement matching (any vs all match mode).
- `table-jobs`: Interactive Streamlit dataframe with direct application links.
- `export-downloads`: Instant download buttons for JSON, CSV, and Markdown briefs.

## How to get to it (user POV)

1. Open the StackCheck dashboard.
2. Click the third tab: `:material/work: Job explorer`.
3. Apply filters via the dropdowns or text search box.
4. Scroll to bottom section **Export dataset** for download buttons.

## Driving it with AppTest

Preconditions:
- Workspace contains populated jobs list.

Steps:
- Switch to third tab: `at.tabs[2]`.
- Verify multiselect controls and download buttons:
  ```python
  multiselects = [m.label for m in at.multiselect]
  assert any("experience" in m.lower() for m in multiselects)
  ```

## Gotchas

- Download buttons are dynamically populated only when `jobs` list is non-empty.
- Filtering by multiple skills uses either "Match any" or "Match all" depending on the segmented control toggle.
