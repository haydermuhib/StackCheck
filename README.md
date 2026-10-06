<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/logo.svg">
    <source media="(prefers-color-scheme: light)" srcset="assets/logo-light.svg">
    <img src="assets/logo.svg" alt="StackCheck Logo" width="550" />
  </picture>
</p>

<p align="center">
  <b>Tech Stack Market Intelligence Engine & Data Analytics Dashboard</b><br>
  <sub>Track real-time technology demand, co-occurrence synergies, and compensation benchmarks.</sub>
</p>

<p align="center">
  <a href="https://github.com/haydermuhib/StackCheck"><img src="https://img.shields.io/badge/Python-3.10%2B-blue?style=flat-square&logo=python" alt="Python 3.10+" /></a>
  <a href="https://streamlit.io"><img src="https://img.shields.io/badge/Streamlit-1.42%2B-FF4B4B?style=flat-square&logo=streamlit" alt="Streamlit" /></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-green?style=flat-square" alt="License: MIT" /></a>
  <a href="https://github.com/haydermuhib/StackCheck/releases"><img src="https://img.shields.io/badge/Version-0.1.9-cyan?style=flat-square" alt="v0.1.9" /></a>
  <a href="https://github.com/haydermuhib/StackCheck"><img src="https://img.shields.io/badge/Architecture-Portable%20Zero--Install-purple?style=flat-square" alt="Portable Zero-Install" /></a>
</p>

---

## ⚡ 1-Line Universal Install

Install the standalone portable binary with zero dependencies:

### 🍎 macOS & 🐧 Linux (Terminal)
```bash
curl -fsSL https://raw.githubusercontent.com/haydermuhib/StackCheck/main/install.sh | bash
```

### 🪟 Windows (PowerShell)
```powershell
curl.exe -L "https://github.com/haydermuhib/StackCheck/releases/latest/download/StackCheck-windows-x64.exe" -o StackCheck.exe; .\StackCheck.exe
```
> **Tip for Windows:** You can also directly download and run [**StackCheck-windows-x64.exe**](https://github.com/haydermuhib/StackCheck/releases/latest/download/StackCheck-windows-x64.exe) from GitHub Releases. If Windows SmartScreen prompts on first launch, click **More info** &rarr; **Run anyway**.

---

Once installed, launch the web dashboard instantly:
```bash
stackcheck
```

---

## 📋 Overview

StackCheck collects live job postings from HiringCafe, extracts requested technologies with section-aware priority weighting, and displays market data in an interactive Streamlit dashboard. It helps engineers and analysts evaluate current technology demand, examine skill combinations, and compare compensation benchmarks across regional job markets.

---

## 🌟 Key Features

| Capability | Description |
| :--- | :--- |
| 🔍 **Live HiringCafe Ingestion** | Query by keywords, location (Pakistan, USA, UK, Germany, India, Remote, etc.), workplace mode (*Remote / Hybrid / Onsite*), experience level, and limit. |
| 🧹 **Data Cleaning & Normalization** | Deterministic SHA-256 fingerprinting to eliminate duplicate postings across companies and canonical country resolution (*"USA", "PK", "Lahore", "Indai", "NZ"*). |
| 🧠 **Section-Aware Priority Weighting** | Separates **"What we look for"** (Requirements) from **"Day-to-day"** (Responsibilities) with decaying positional multipliers ($1.8\times \to 1.0\times$). |
| 💱 **Currency Normalization Engine** | Live Open Exchange rates sync with offline baseline rates (`INR`, `PHP`, `CRC`, `EUR`, `GBP`, `CAD`, etc.), outlier safeguards, and interactive custom rate overrides. |
| 📊 **Statistical Visualizations** | Demanded skills frequency %, Seaborn co-occurrence heatmaps (`Python + SQL`, `Snowflake + dbt`), and min/avg/max compensation ranges. |
| 💼 **Interactive Job Explorer** | Filterable table with multi-select filters for **Experience Level**, **Country**, and **Skills** (ANY / ALL match mode) with direct employer apply links. |
| 📦 **Portable Standalone App** | Zero-install binary architecture (Ventoy style) with embedded Python runtime, local SQLite isolation, and in-place GitHub updater. |

---

## 💡 What StackCheck Delivers (That Job Boards Don't)

Raw job boards like HiringCafe provide search lists, but job seekers and tech leaders cannot derive market intelligence from raw cards alone. StackCheck transforms raw job descriptions into structured, actionable market analytics:

| Market Intelligence Dimension | Raw Job Board (e.g. HiringCafe) | StackCheck Intelligence Engine |
| :--- | :---: | :---: |
| **Skill Frequency & Demand Ranking** | ❌ None (raw cards only) | ✅ Top in-demand technologies ranked by market frequency % & weighted score |
| **Section-Aware Priority Weighting** | ❌ None (treats all text identically) | ✅ Differentiates core **Requirements** ($1.8\times$) from general body text ($1.0\times$) |
| **Tech Co-Occurrence & Synergies** | ❌ None | ✅ Seaborn correlation heatmaps revealing tool synergies (`SQL + Python`, `dbt + Snowflake`) |
| **Salary Benchmarks & Error Bars** | ❌ Raw unvalidated numbers | ✅ Statistical Min, Avg, Max benchmarks with sample validation ($N \ge 3$) and confidence labels |
| **Workplace Compensation Premium** | ❌ None | ✅ Automatic Remote vs. Hybrid vs. Onsite compensation spread analysis |
| **Stack Density & Breadth Metrics** | ❌ None | ✅ Quantitative distribution of required skills per job posting |
| **Cross-Market Research Workspaces** | ❌ None | ✅ Isolated multi-project research workspaces with historical search memory |
| **Data Ownership & Portability** | ❌ Cloud-locked | ✅ 100% offline local SQLite storage with instant CSV, JSON, and Markdown export |

---

## 🛡️ Polite, Ethical & Ultralight Scraping Footprint

StackCheck is engineered to be **safe, sustainable, and respectful** of origin job servers. It never overloads or abuses public infrastructure:

- **⚡ 98% Request Reduction (Batch SSR Harvesting):** Unlike naive scrapers that spin up heavy headless browsers (Puppeteer/Selenium) and visit 2,000 individual job page URLs one-by-one, StackCheck ingests **60 to 90 complete, structured job records per single GET request** via Next.js `__NEXT_DATA__`. Collecting 2,000 jobs requires only ~25–30 total lightweight requests.
- **⏱️ Human-Cadence Request Pacing:** Requests are throttled sequentially with built-in courtesy pauses (`time.sleep(0.35)`), mimicking a normal human user browsing search results. There is zero DDoS or server stress.
- **🔒 Zero-Re-scrape Architecture (100% Local Compute):** Postings are saved directly into your local SQLite database (`~/.stackcheck/stackcheck.db`). All subsequent skill extraction, NLP disambiguation, salary recalculations, filtering, and chart re-rendering occur **entirely offline on your local machine**—sending zero recurring network traffic to HiringCafe.
- **🛡️ Strict Role Relevance Filtering:** Tokenized validation prevents irrelevant roles (e.g. infrastructure/SRE roles mentioning "data") from polluting niche queries like Data Analyst.

---

## 🏗️ System Architecture

```
┌──────────────────────┐     ┌──────────────────────┐     ┌──────────────────────┐
│  HiringCafe Public   │────▶│    Deduplicator &    │────▶│    Section-Aware     │
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
<summary><b>📋 Technical Component Breakdown</b></summary>

- `src/stackcheck/client/hiringcafe.py`: Direct payload requests with pagination, workplace filters, and exponential backoff retry.
- `src/stackcheck/client/normalizer.py`: Title classification, geographic country aliases, and duplicate fingerprinting.
- `src/stackcheck/analyzer/rule_extractor.py`: Positional regex extractor separating requirements from general description text.
- `src/stackcheck/analyzer/metrics.py`: Skill co-occurrence correlation matrix, salary percentiles, and weighted scoring.
- `src/stackcheck/storage/repository.py`: Multi-workspace SQLite repository handling schema migration and upserts.
- `src/stackcheck/launcher.py`: Desktop launcher with free port discovery and automated browser opening.
- `src/stackcheck/updater.py`: GitHub Releases API update checker with timeout protection.

</details>

---

## 📐 Analytical Methodology

StackCheck implements the criteria popularized by tech hiring research:

1. **Clean Dataset**: Filters out duplicates, spam, and expired job listings using a composite title-company-location fingerprint.
2. **Category Grouping**: Structures required skills into explicit technical categories (Languages, BI Tools, Databases, Cloud/DevOps, AI/ML).
3. **Requirement Priority Multipliers**:
   - *Requirement Bullet #1:* $1.8\times$ (core skill)
   - *Requirement Bullet #2:* $1.5\times$
   - *Requirement Bullet #3:* $1.3\times$
   - *Day-to-day Responsibilities:* $1.2\times$
   - *General body text:* $1.0\times$
   - *Nice-to-have / Preferred:* $0.7\times$
4. **Geographic Comparison**: Analyzes how demand for tools like **Power BI** vs **Tableau** or cloud providers (**AWS** vs **Azure** vs **GCP**) varies across regional markets.

---

## 🚀 Installation & Local Development

<details>
<summary><b>📋 Option A: 1-Line Standalone CLI Install (Recommended)</b></summary>

```bash
# Install to ~/.local/bin/stackcheck with desktop launcher and SVG icon
curl -fsSL https://raw.githubusercontent.com/haydermuhib/StackCheck/main/install.sh | bash

# Launch browser dashboard
stackcheck
```

</details>

<details>
<summary><b>📋 Option B: Manual Virtualenv Setup (Developers)</b></summary>

```bash
# Clone repository
git clone https://github.com/haydermuhib/StackCheck.git
cd StackCheck

# Setup virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install in editable mode
pip install -e .

# Run dashboard
streamlit run app.py
```

</details>

<details>
<summary><b>📋 Option C: Compile Standalone Desktop Binary</b></summary>

```bash
# Build single-folder desktop distribution
python build_app.py --onedir

# Or build single-file portable executable
python build_app.py --onefile
```

</details>

---

## ⚙️ CLI Usage Reference

StackCheck includes scriptable CLI commands for automated data collection and process lifecycle control:

```bash
# Launch interactive Streamlit Web Dashboard
stackcheck

# Show version
stackcheck -v

# Check running server status, URL, and PID
stackcheck status

# Verify runtime dependencies and C-extensions
stackcheck check

# Stop running server and release ports
stackcheck stop

# Check for updates and download latest GitHub Release
stackcheck update

# Scrape Data Analyst roles in Pakistan (or any country)
stackcheck search "Data Analyst" --location Pakistan --limit 30

# Scrape Backend Engineers with remote filter
stackcheck search "Backend Engineer" --workplace remote --limit 50

# Export active workspace dataset to CSV, JSON, and Markdown
stackcheck export --format all
```

---

## 🧪 Running Tests

StackCheck includes automated unit tests covering the parser, metrics engine, SQLite repository, web charts, and desktop launcher:

```bash
pytest tests/
```

---

## 📌 Quick Reference Card

| Command / Resource | Purpose |
| :--- | :--- |
| `stackcheck` | Launch local web dashboard |
| `stackcheck -v` | Print installed StackCheck version |
| `stackcheck status` | Check server status, PID, and URL |
| `stackcheck check` | Verify runtime environment & compiled C-extensions |
| `stackcheck stop` | Stop running server |
| `stackcheck search <title>` | Scrape live jobs from HiringCafe into SQLite |
| `stackcheck export --format all` | Export dataset to `CSV`, `JSON`, and `Markdown` |
| `stackcheck update` | In-place self-updater from GitHub Releases |
| [index.html](index.html) | Standalone interactive presentation showcase |
| [LICENSE](LICENSE) | MIT Open-Source License |

---

## 📄 License

This project is licensed under the [MIT License](LICENSE) (c) 2026 Haider Ali Tariq.
