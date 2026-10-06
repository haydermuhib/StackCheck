<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/logo.svg">
    <source media="(prefers-color-scheme: light)" srcset="assets/logo-light.svg">
    <img src="assets/logo.svg" alt="StackCheck Logo" width="550" />
  </picture>
</p>

<p align="center">
  <b>Tech Stack Market Intelligence Engine and Data Analytics Dashboard</b><br>
  <sub>Track technology demand, skill pairings, and compensation benchmarks from live job posts.</sub>
</p>

<p align="center">
  <a href="https://github.com/haydermuhib/StackCheck"><img src="https://img.shields.io/badge/Python-3.10%2B-blue?style=flat-square&logo=python" alt="Python 3.10+" /></a>
  <a href="https://streamlit.io"><img src="https://img.shields.io/badge/Streamlit-1.42%2B-FF4B4B?style=flat-square&logo=streamlit" alt="Streamlit" /></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-green?style=flat-square" alt="License: MIT" /></a>
  <a href="https://github.com/haydermuhib/StackCheck/releases"><img src="https://img.shields.io/badge/Version-0.1.9-cyan?style=flat-square" alt="v0.1.9" /></a>
  <a href="https://github.com/haydermuhib/StackCheck"><img src="https://img.shields.io/badge/Architecture-Portable%20Binary-purple?style=flat-square" alt="Portable Binary" /></a>
</p>

---

## Quick installation

Install the standalone binary without external dependencies:

### macOS and Linux
```bash
curl -fsSL https://raw.githubusercontent.com/haydermuhib/StackCheck/main/install.sh | bash
```

### Windows (PowerShell)
```powershell
curl.exe -L "https://github.com/haydermuhib/StackCheck/releases/latest/download/StackCheck-windows-x64.exe" -o StackCheck.exe; .\StackCheck.exe
```

You can also download [StackCheck-windows-x64.exe](https://github.com/haydermuhib/StackCheck/releases/latest/download/StackCheck-windows-x64.exe) directly from GitHub Releases. If Windows SmartScreen prompts on first launch, select **More info**, then **Run anyway**.

---

Run the web dashboard:
```bash
stackcheck
```

---

## Overview

StackCheck collects live job listings from HiringCafe, extracts technical requirements with section-based weighting, and visualizes market statistics in a local Streamlit dashboard. It helps engineers and analysts evaluate technology demand, inspect skill combinations, and benchmark compensation across regional job markets.

---

## Core capabilities

| Capability | Description |
| :--- | :--- |
| Live job ingestion | Query by keyword, location (Pakistan, United States, United Kingdom, Germany, India, Remote), workplace mode (Remote, Hybrid, Onsite), experience level, and result limit. |
| Data cleaning and deduplication | Uses SHA-256 fingerprinting to remove duplicate listings across companies, and resolves location typos to canonical country names. |
| Section-aware priority weighting | Differentiates required skills (1.8x multiplier) from general responsibilities (1.0x to 1.2x) based on where they appear in the post. |
| Currency normalization | Converts foreign currencies (INR, PHP, EUR, GBP, CAD, PKR) to annual USD benchmarks with daily exchange rates and offline fallback tables. |
| Statistical charts | Displays top skill frequencies, co-occurrence heatmaps (such as Python with SQL, or Snowflake with dbt), and compensation spreads. |
| Interactive job explorer | Filterable table with options for experience level, country, and technology tags, with direct application links. |
| Standalone application | Self-contained executable with embedded runtime, local SQLite storage, and in-place GitHub updater. |

---

## Comparison with standard job boards

Standard job boards return search cards, but do not calculate aggregate market metrics. StackCheck processes job descriptions into structured analytics:

| Metric | Standard job board | StackCheck |
| :--- | :--- | :--- |
| Skill demand ranking | Search result cards only | Top technologies ranked by frequency and weighted score |
| Section weighting | Treats all text equally | Weights mandatory qualifications higher than general summaries |
| Skill pairings | Not available | Correlation matrices showing tools frequently requested together |
| Compensation benchmarks | Unstandardized numbers | Calculated minimum, median, and maximum bands with sample counts |
| Workplace spread | Not available | Compensation comparisons across remote, hybrid, and onsite listings |
| Skill breadth | Not available | Average number of technologies required per listing |
| Workspaces | Not available | Project-scoped searches with historical search runs |
| Data export | Web interface only | Local SQLite database with exports to CSV, JSON, and Markdown |

---

## Scraping design and limits

StackCheck is built to query origin servers responsibly without causing service disruption:

- **Batch data retrieval:** StackCheck reads server-rendered payloads containing 60 to 90 complete listings per HTTP request. Gathering 2,000 listings requires roughly 25 to 30 requests.
- **Paced requests:** Requests run sequentially with built-in courtesy pauses (0.35 seconds between calls) over a persistent connection.
- **Local computation:** Ingested listings save directly to a local SQLite database (`~/.stackcheck/stackcheck.db`). Skill parsing, salary calculations, and chart generation run entirely on your local machine.
- **Relevance filtering:** Tokenized validation checks role titles to keep unrelated jobs from polluting specific searches.

---

## System architecture

```
┌──────────────────────┐     ┌──────────────────────┐     ┌──────────────────────┐
│  HiringCafe Public   │────▶│    Deduplicator and   │────▶│    Section-Aware     │
│      API Client      │     │  Country Normalizer  │     │   Priority Weighting │
└──────────────────────┘     └──────────────────────┘     └──────────┬───────────┘
                                                                     │
                                                                     ▼
┌──────────────────────┐     ┌──────────────────────┐     ┌──────────────────────┐
│ Export Reports       │◀────│   Streamlit Web UI   │◀────│ Local SQLite Storage │
│ (CSV, JSON, Markdown)│     │ & Matplotlib OOP Ax  │     │ (~/.stackcheck/*.db) │
└──────────────────────┘     └──────────────────────┘     └──────────────────────┘
```

<details>
<summary><b>Component breakdown</b></summary>

- `src/stackcheck/client/hiringcafe.py`: Requests payloads with pagination, workplace filters, and retry logic.
- `src/stackcheck/client/normalizer.py`: Title categorization, geographic aliases, and duplicate fingerprinting.
- `src/stackcheck/analyzer/rule_extractor.py`: Positional regex extractor separating requirements from general text.
- `src/stackcheck/analyzer/metrics.py`: Skill co-occurrence matrix, salary distributions, and weighted scoring.
- `src/stackcheck/storage/repository.py`: Multi-project SQLite repository managing schema migrations and upserts.
- `src/stackcheck/launcher.py`: Desktop launcher with free port selection and browser launch logic.
- `src/stackcheck/updater.py`: GitHub Releases update checker with timeout protection.

</details>

---

## Methodology

1. **Dataset cleaning:** Drops duplicates and spam by generating a title-company-location composite hash.
2. **Category classification:** Groups technologies into categories (Languages, BI Tools, Databases, Cloud and DevOps, AI and Machine Learning).
3. **Requirement weighting:**
   - First requirement item: 1.8x
   - Second requirement item: 1.5x
   - Third requirement item: 1.3x
   - Day-to-day responsibilities: 1.2x
   - General post text: 1.0x
   - Preferred qualifications: 0.7x
4. **Regional comparisons:** Measures how tool adoption varies across countries and regional markets.

---

## Installation options

<details>
<summary><b>Option A: 1-line script (Recommended)</b></summary>

```bash
# Installs to ~/.local/bin/stackcheck with desktop shortcut and icon
curl -fsSL https://raw.githubusercontent.com/haydermuhib/StackCheck/main/install.sh | bash

# Launch dashboard
stackcheck
```

</details>

<details>
<summary><b>Option B: Python source setup</b></summary>

```bash
git clone https://github.com/haydermuhib/StackCheck.git
cd StackCheck

python3 -m venv .venv
source .venv/bin/activate

pip install -e .

streamlit run app.py
```

</details>

<details>
<summary><b>Option C: Build standalone executable</b></summary>

```bash
# Build standalone folder distribution
python build_app.py --onedir

# Or build single-file binary
python build_app.py --onefile
```

</details>

---

## Command line interface

```bash
# Launch web dashboard
stackcheck

# Print version
stackcheck -v

# Check status of running dashboard process
stackcheck status

# Verify runtime dependencies
stackcheck check

# Stop running dashboard process
stackcheck stop

# Check for updates and upgrade in-place
stackcheck update

# Query jobs for a role and location
stackcheck search "Data Analyst" --location "United States" --limit 30

# Query remote backend engineering jobs
stackcheck search "Backend Engineer" --workplace remote --limit 50

# Export dataset
stackcheck export --format all
```

---

## Running tests

Run the unit test suite:

```bash
pytest tests/
```

---

## Quick reference

| Command or file | Purpose |
| :--- | :--- |
| `stackcheck` | Launch local web dashboard |
| `stackcheck -v` | Print installed version |
| `stackcheck status` | Check server status, process ID, and port |
| `stackcheck check` | Verify runtime dependencies |
| `stackcheck stop` | Stop running dashboard process |
| `stackcheck search <query>` | Query live jobs into local SQLite storage |
| `stackcheck export --format all` | Export dataset to CSV, JSON, and Markdown |
| `stackcheck update` | Update binary from GitHub Releases |
| [index.html](index.html) | Landing page |
| [LICENSE](LICENSE) | MIT License |

---

## License

This project is licensed under the [MIT License](LICENSE).
