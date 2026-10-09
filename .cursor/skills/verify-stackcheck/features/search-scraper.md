# Search & Scraper Pipeline

Collects live postings into the active workspace with configurable keywords, normalized locations, workplace modes, experience levels, and pagination caps.

## Sub-features

- `filter-roles`: Quick-pick roles or custom keywords input.
- `filter-locations`: Auto-normalized geographic region or global filter.
- `filter-workplace`: Remote only, Hybrid, or Onsite toggles.
- `filter-experience`: Entry, Mid, Senior, or Lead seniority levels.
- `action-crawl`: Paginating scraper with real-time progress bar.

## How to get to it (user POV)

1. Look at the left sidebar under the header **Search and scraper filters**.
2. Select a role from **Role quick-picks** (or enter custom keywords).
3. Select or enter a target location in **Location or country**.
4. Choose workplace mode and experience level.
5. Click **Collect postings into project**.

## Driving it with AppTest

Preconditions:
- Application mounted in AppTest.

Steps:
- Inspect sidebar widgets:
  ```python
  selectbox_labels = [s.label for s in at.selectbox]
  assert "Role quick-picks:" in selectbox_labels
  assert "Workplace mode:" in selectbox_labels
  ```
- Trigger run button:
  ```python
  btn = [b for b in at.button if b.label == "Collect postings into project"][0]
  # In testing, avoid hammering external live APIs without mocking
  ```

## Gotchas

- HiringCafe rate limits: In automated tests, mock `client.search_jobs` to return fixture jobs rather than making live external HTTP requests.
- Deep crawl ("Fetch all available") caps at 40 pages / ~2,500 jobs safety circuit breaker.
