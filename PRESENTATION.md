# StackCheck: Tech Stack Intelligence & Market Analytics
## Automated Job Scraping, Section-Aware Skill Extraction & Interactive Web Analytics

**Duration:** 25 minutes  
**Audience:** Engineers, Data Analysts, Product Leaders & Technical Recruiters  
**Date:** 2026-10-05  
**Version:** v0.1.8  

---

## Agenda

1. Problem & Market Motivation (2 min)
2. Raw Job Board vs. StackCheck Market Intelligence (3 min)
3. Polite, Ethical & Ultralight Scraping Footprint (3 min)
4. End-to-End System Architecture (4 min)
5. Section-Aware Extraction & Priority Weighting (3 min)
6. Currency Normalization & Robust Salary Benchmarking (3 min)
7. Regional Trends & Workplace Compensation Premiums (3 min)
8. Interactive Streamlit Analytics Dashboard (2 min)
9. Quick Reference & CLI Ecosystem (2 min)

**Total Duration: 25 minutes**

---

## 1. Problem and Market Motivation

Generic job scrapers rely on naive keyword counts. Treating every mention of a technology as equal demand creates heavily skewed, misleading market insights:

```
┌────────────────────────────────┐     ┌────────────────────────────────┐
│    Generic Keyword Matching    │     │    StackCheck Intelligence     │
├────────────────────────────────┤     ├────────────────────────────────┤
│ • Treats "R" in "for" as skill │ vs  │ • Context-aware word boundary  │
│ • Ignores requirement priority │     │ • Positional weight multiplier │
│ • 1-sample outliers skew salary│     │ • Statistical sample filters   │
│ • Skewed by mixed currencies   │     │ • Normalized USD conversions   │
│ • Heavy scraping hammers sites │     │ • Polite batch SSR harvesting  │
└────────────────────────────────┘     └────────────────────────────────┘
```

### Questions This Solves
- Which technologies are strict core requirements versus nice-to-have mentions?
- How does tech stack demand differ across North America, Europe, and South Asia?
- What tools actually pair together (e.g. `Python + SQL`, `Snowflake + dbt`, `Power BI + DAX`)?
- What are reliable, statistically validated salary benchmarks without outlier distortion?

---

## 2. Raw Job Board vs. StackCheck Market Intelligence

Public job search engines (like HiringCafe) are designed for individual job discovery—they provide flat search listings. They cannot aggregate, correlate, or statistically analyze market data. StackCheck bridges this gap:

| Capability Dimension | Raw Job Board (e.g. HiringCafe) | StackCheck Intelligence Engine |
| :--- | :---: | :---: |
| **Skill Frequency & Demand Ranking** | ❌ None (raw job cards only) | ✅ Top in-demand skills ranked by frequency % & weighted score |
| **Section-Aware Priority Weighting** | ❌ None (treats all text identically) | ✅ Differentiates core **Requirements** ($1.8\times$) from general body text ($1.0\times$) |
| **Tech Stack Synergies & Co-Occurrence** | ❌ None | ✅ Seaborn correlation heatmaps revealing tool pairings (`SQL + Python`, `dbt + Snowflake`) |
| **Salary Benchmarks & Error Bars** | ❌ Raw numbers only | ✅ Min, Avg, Max benchmarks with sample validation ($N \ge 3$) and confidence labels |
| **Workplace Mode Salary Premiums** | ❌ None | ✅ Automatic Remote vs. Hybrid vs. Onsite compensation spread analysis |
| **Stack Density & Breadth Metrics** | ❌ None | ✅ Quantitative distribution of required skills per job post |
| **Comparative Research Workspaces** | ❌ None | ✅ Multi-project workspace isolation with saved queries |
| **Data Ownership & Portability** | ❌ Cloud-locked | ✅ 100% offline local SQLite storage with instant CSV, JSON, and Markdown export |

---

## 3. Polite, Ethical & Ultralight Scraping Footprint

StackCheck is built to be **sustainable, respectful, and completely non-abusive** to origin job platforms:

<div style="display: flex; gap: 15px; justify-content: center; flex-wrap: wrap;">
    <div style="border: 2px solid #73daca; border-radius: 8px; padding: 14px; min-width: 220px; background: rgba(115,218,202,0.1);">
        <strong style="color: #73daca;">⚡ 98% Request Reduction</strong>
        <p>Intercepts Next.js <code>__NEXT_DATA__</code> SSR payloads. Ingests <b>60 to 90 complete structured jobs per request</b> instead of hitting 2,000 individual job page URLs.</p>
    </div>
    <div style="border: 2px solid #7aa2f7; border-radius: 8px; padding: 14px; min-width: 220px; background: rgba(122,162,247,0.1);">
        <strong style="color: #7aa2f7;">⏱️ Human-Cadence Pacing</strong>
        <p>Built-in courtesy pauses (<code>time.sleep(0.35)</code>) and single persistent HTTP/2 connection. Generates the network footprint of a single human scrolling a feed.</p>
    </div>
    <div style="border: 2px solid #bb9af7; border-radius: 8px; padding: 14px; min-width: 220px; background: rgba(187,154,247,0.1);">
        <strong style="color: #bb9af7;">🔒 Zero-Re-scrape Local Compute</strong>
        <p>Data is stored locally in SQLite. All NLP taxonomy extraction, salary re-calculations, and chart renderings run <b>100% offline on local CPU</b>—zero recurring web traffic.</p>
    </div>
</div>

<details>
<summary><b>📋 Technical Safeguards Breakdown</b></summary>

- **Automated Circuit Breaker:** Stops pagination immediately when a page returns 0 new hits or target limits are satisfied.
- **Safety Ceiling:** Automatically caps deep crawls at 40 pages (~2,500 jobs max) to prevent runaway scraping loops.
- **Browser-Identical TLS Fingerprinting:** Uses `curl_cffi` Chrome 124 TLS handshakes so requests appear as standard modern browser sessions rather than headless bot probes.
- **Strict Role Relevance:** Validates title and query semantics before saving to prevent unrelated roles from polluting datasets.

</details>

---

## 4. End-to-End System Architecture

```
┌───────────────────┐      ┌───────────────────────────┐      ┌───────────────────────────┐
│  HiringCafe API   │─────▶│  Job Normalizer Pipeline  │─────▶│ Section-Aware Extractor   │
│  (curl_cffi TLS)  │      │  • SHA-256 Fingerprint    │      │  • Section Segmentation   │
│  • Batch SSR Hits │      │  • Geo Synonym Mapping    │      │  • Positional Multipliers │
│  • Courtesy Delay │      │  • Strict Role Relevance  │      │  • 100+ Skill Taxonomy    │
└───────────────────┘      └───────────────────────────┘      └─────────────┬─────────────┘
                                                                            │
                                                                            ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                               SQLite Local Persistence                                  │
│                       (~/.stackcheck/stackcheck.db, Multi-Project)                      │
└───────────────────────────────────────────┬─────────────────────────────────────────────┘
                                            │
                     ┌──────────────────────┴──────────────────────┐
                     ▼                                             ▼
        ┌─────────────────────────┐                   ┌─────────────────────────┐
        │  Streamlit Dashboard    │                   │ Currency & Export Hub   │
        │  • Matplotlib OOP (ax)  │                   │ • Live exchange rates   │
        │  • Seaborn Heatmaps     │                   │ • Baseline fallback     │
        │  • Statistical Errorbars│                   │ • JSON, CSV, Markdown   │
        └─────────────────────────┘                   └─────────────────────────┘
```

<details>
<summary><b>📋 Component Details</b></summary>

- `stackcheck.client.hiringcafe`: Respectful live scraper with browser TLS fingerprinting, batch SSR harvesting, and courtesy sleep.
- `stackcheck.client.normalizer`: Role relevance validator, SHA-256 deduplicator, country standardizer, and salary parser.
- `stackcheck.analyzer.taxonomy`: 100+ normalized tech definitions across 9 functional domain categories.
- `stackcheck.analyzer.rule_extractor`: Segments descriptions and applies positional multipliers to requirements.
- `stackcheck.analyzer.currency`: Live Open Exchange rates sync with offline fallback rates and USD conversion.
- `stackcheck.storage.repository`: Multi-project SQLite database with indexed queries and foreign key cascades.
- `stackcheck.web.charts`: Matplotlib OOP visualization engine with Seaborn correlation heatmaps and error bars.
- `stackcheck.launcher`: Desktop lifecycle manager with single-instance verification and persistent frontend asset mirroring.

</details>

---

## 5. Section-Aware Extraction and Priority Weighting

Job descriptions naturally prioritize critical skills in the opening bullet points of the qualifications section. Mentioning a tool in an introductory paragraph or in an unstructured bullet carries significantly less weight:

```
┌────────────────────────────────────────────────────────────┬──────────────┐
│ Section and Position in Job Posting                        │ Multiplier   │
├────────────────────────────────────────────────────────────┼──────────────┤
│ Requirements Bullet #1 (Top Mandatory Requirement)         │     1.8x     │
│ Requirements Bullet #2 (Primary Technical Foundation)       │     1.5x     │
│ Requirements Bullet #3 (Core Tool or Platform)             │     1.3x     │
│ Responsibilities / Day-to-Day Tasks                        │     1.2x     │
│ General Body, Overview, or Unstructured Text               │     1.0x     │
│ Nice-to-have / Preferred Qualifications                    │     0.7x     │
└────────────────────────────────────────────────────────────┴──────────────┘
```

### Priority Score Formula
The total priority score for skill $S$ across a dataset of jobs is calculated as:

$$\text{Priority Weighted Score}(S) = \sum_{j \in \text{Jobs}} w_j(S)$$

This accurately separates foundational requirements (e.g. SQL, Python) from peripheral tools mentioned in passing.

---

## 6. Currency Normalization & Robust Salary Benchmarking

### The Challenge
Job listings report compensation across dozens of foreign currencies (`EUR`, `GBP`, `INR`, `PHP`, `CAD`, `PKR`, `CRC`) and mixed intervals (hourly, monthly, annual). Without normalization and sample thresholds, analytics are severely distorted.

### StackCheck Solution Pipeline
```
┌───────────────────────────────────────────────────────────────────────────────┐
│ 1. Raw Posting: Detect currency symbol, ISO code, or country context          │
├───────────────────────────────────────────────────────────────────────────────┤
│ 2. Floating API Sync: Query daily rates against USD with 24-hour TTL cache    │
├───────────────────────────────────────────────────────────────────────────────┤
│ 3. Offline Fallbacks: Built-in rates for INR, PKR, PHP, EUR, GBP, CAD, CRC    │
├───────────────────────────────────────────────────────────────────────────────┤
│ 4. Outlier Filter: Filter annual values outside $5,000 to $750,000 USD        │
├───────────────────────────────────────────────────────────────────────────────┤
│ 5. Sample Thresholding: Require N ≥ 3 postings with disclosed salaries        │
│    (Eliminates 1-sample extreme outliers from topping the benchmarks)         │
└───────────────────────────────────────────────────────────────────────────────┘
```

### Statistical Error-Bar Charts
- **Error Bars (Min to Max):** Displays the full compensation spectrum alongside the average salary.
- **Sample Count Visibility:** Appends `(n=X)` directly to skill labels for immediate statistical confidence.
- **Collision-Free Annotations:** Dynamic horizontal padding positions labels cleanly past the maximum error cap, eliminating text collision artifacts.

---

## 7. Regional Trends & Workplace Compensation Premiums

Market demand and compensation models vary dramatically across geographic regions and workplace arrangements:

### Regional Skill Preferences
| Region | Primary BI Tool | Primary Cloud / Data Platform | Common Work Mode |
|---|---|---|---|
| **USA** | Tableau / Power BI (balanced) | Snowflake, AWS Redshift | 45% Remote, 40% Hybrid |
| **Europe** | Microsoft Power BI (62%) | Microsoft Azure, AWS | 35% Remote, 50% Hybrid |
| **India** | Microsoft Power BI (68%) | AWS, GCP, Snowflake | 25% Remote, 55% Hybrid |
| **Global Remote** | Power BI & Looker | Snowflake, dbt, BigQuery | 100% Remote |

### Workplace Mode Pay Premiums
StackCheck automatically calculates the **Remote Pay Premium**:
- Evaluates median compensation across Remote vs. Hybrid vs. Onsite postings within the same dataset.
- Identifies whether remote distributed talent commands a premium or parity in specific engineering niches.

---

## 8. Interactive Streamlit Analytics Dashboard

StackCheck provides a multi-tab web dashboard built with Streamlit, Matplotlib OOP, and Seaborn:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 📊 Active Project: Data Analyst Global 2026              [🔄 Sync Rates]    │
├───────────────────┬───────────────────┬───────────────────┬─────────────────┤
│ Total Jobs: 2,140 │ Companies: 840    │ Remote Ratio: 48% │ Top Skill: SQL  │
├───────────────────┴───────────────────┴───────────────────┴─────────────────┤
│                                                                             │
│ [Bar Chart: Top 15 Demanded Skills]      [Seaborn Heatmap: Co-occurrences]  │
│  • Raw frequency % vs weighted score      • Pairwise correlation matrix     │
│  • Positional requirement multipliers     • Tool synergies (e.g. dbt + SQL) │
│                                                                             │
│ [Salary Benchmarks with Error Bars]      [Workplace & Experience Breakdown] │
│  • Min / Avg / Max range error bars       • Donut & Bar distributions       │
│  • Interactive Sample Filter (N ≥ 3)     • Remote Pay Premium KPI Card     │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│ 💼 Interactive Job Explorer                                                 │
│ Filter by skills (ANY / ALL match), experience level, and country.           │
│ Direct employer links for one-click job applications.                       │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 9. Quick Reference & CLI Ecosystem

### Command Line Interface

| Command | Action |
|---|---|
| `stackcheck` | Launch interactive Streamlit web dashboard |
| `stackcheck -d` | Launch web dashboard as a background daemon |
| `stackcheck status` | Check server health, active port, and uptime |
| `stackcheck check` | Verify runtime environment & compiled C-extensions |
| `stackcheck stop` | Terminate running dashboard processes |
| `stackcheck search "Data Analyst" --limit 50` | Scrape and analyze matching jobs from CLI |
| `stackcheck export --format all` | Export dataset to JSON, CSV, and Markdown |
| `stackcheck update` | In-place self-updater from GitHub Releases |

### Standalone Executable (Zero-Install)
- **macOS / Linux:** `curl -fsSL https://raw.githubusercontent.com/haydermuhib/StackCheck/main/install.sh | bash`
- **Windows (PowerShell):** `curl.exe -L "https://github.com/haydermuhib/StackCheck/releases/latest/download/StackCheck-windows-x64.exe" -o StackCheck.exe; .\StackCheck.exe`

---

## Questions & Resources

- **GitHub Repository:** [haydermuhib/StackCheck](https://github.com/haydermuhib/StackCheck)
- **Data Source:** [HiringCafe](https://hiring.cafe)
- **Methodology Basis:** Baraa Khatib Salkini tech hiring data framework
- **Current Version:** v0.1.8 (35 passing automated unit tests)

---

*Presentation prepared for StackCheck*  
*Built with [markdown-presentation](https://github.com/plinde/claude-plugins/tree/main/markdown-presentation)*
