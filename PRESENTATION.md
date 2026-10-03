# StackCheck: Tech Stack Intelligence & Market Analytics
## Automated Job Scraping, Section-Aware AI Extraction & Terminal Dashboard

**Duration:** 25 minutes  
**Audience:** Engineers, Data Analysts, Product Leaders & Recruiters  
**Date:** 2026-10-03  

---

## Agenda

1. Problem & Market Motivation (3 min)
2. Analytical Methodology (Baraa Khatib Salkini Framework) (4 min)
3. End-to-End System Architecture (5 min)
4. Data Ingestion, Deduplication & Quality Pipeline (4 min)
5. Section-Aware Extraction & Priority Weighting (4 min)
6. Interactive TUI & Live Demo (3 min)
7. Global Benchmarks, Community Sync & Q&A (2 min)

**Total Duration: 25 minutes**

---

## 1. Problem & Market Motivation

Traditional job scraping tools offer superficial keyword matching, resulting in skewed demand metrics and noise.

```
┌────────────────────────────────┐     ┌────────────────────────────────┐
│   Generic Keyword Matching     │     │     StackCheck Intelligence    │
├────────────────────────────────┤     ├────────────────────────────────┤
│ • Treats "R" in "for" as skill │ vs  │ • Context-aware word boundary  │
│ • Ignores requirement priority │     │ • Positional weight multiplier │
│ • Polluted by spam & duplicates│     │ • Deduplication & spam filters │
│ • Flat counts across regions   │     │ • Geo & work-mode segmentation │
└────────────────────────────────┘     └────────────────────────────────┘
```

### Key Questions Solved
- Which technologies are genuinely *mandatory* vs *nice-to-have*?
- How does tech stack demand differ across **USA**, **Europe**, and **India**?
- What are the top **co-occurrence pairings** (e.g. `Python + SQL`, `Tableau + Snowflake`)?
- How do skills correlate with compensation and remote work eligibility?

---

## 2. Analytical Methodology (Baraa Khatib Salkini Framework)

StackCheck incorporates the proven data analysis framework used on **22,000+ real-world tech job advertisements** across **4,000+ companies** in ~100 countries.

<div style="display: flex; gap: 15px; justify-content: center; flex-wrap: wrap;">
    <div style="border: 2px solid #73daca; border-radius: 8px; padding: 12px; min-width: 180px; background: rgba(115,218,202,0.1);">
        <strong style="color: #73daca;">1. Data Cleaning</strong>
        <p>Deduplication by fingerprint, spam detection, expiration filtering.</p>
    </div>
    <div style="border: 2px solid #7aa2f7; border-radius: 8px; padding: 12px; min-width: 180px; background: rgba(122,162,247,0.1);">
        <strong style="color: #7aa2f7;">2. Categorization</strong>
        <p>Languages, BI Tools, Data Platforms, Cloud/DevOps, AI/ML.</p>
    </div>
    <div style="border: 2px solid #bb9af7; border-radius: 8px; padding: 12px; min-width: 180px; background: rgba(187,154,247,0.1);">
        <strong style="color: #bb9af7;">3. Section Priority</strong>
        <p>Weighted analysis on "What We Look For" vs "Day to Day".</p>
    </div>
    <div style="border: 2px solid #e0af68; border-radius: 8px; padding: 12px; min-width: 180px; background: rgba(224,175,104,0.1);">
        <strong style="color: #e0af68;">4. Geo Segmentation</strong>
        <p>Regional variance: USA vs Europe vs India vs Global Remote.</p>
    </div>
</div>

---

## 3. End-to-End System Architecture

```
┌─────────────────┐       ┌────────────────────────┐       ┌──────────────────────┐
│  HiringCafe API │──────▶│ Job Normalizer Pipeline│──────▶│ Section Extractor    │
│  HTTP Client    │       │ • Fingerprint Dedup    │       │ • Regex + Boundaries │
└─────────────────┘       │ • Spam/Junk Filter     │       │ • Positional Weights │
                          │ • Geo/Workplace Class  │       │ • Optional LLM Hook  │
                          └────────────────────────┘       └──────────┬───────────┘
                                                                      │
                                                                      ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           SQLite Local Persistence                              │
│              (Jobs Table, Skills Table, Search Runs, Community Log)             │
└────────────────────────────────────┬────────────────────────────────────────────┘
                                     │
                 ┌───────────────────┴───────────────────┐
                 ▼                                       ▼
      ┌─────────────────────┐                 ┌──────────────────────┐
      │   Web Dashboard     │                 │   Export / Sync Hub  │
      │  (Streamlit/Seaborn)│                 │ • JSON / CSV / MD    │
      │ • Matplotlib OOP    │                 │ • Central Telemetry  │
      │ • Real-time metrics │                 │ • Community Trends   │
      └─────────────────────┘                 └──────────────────────┘
```

<details>
<summary><b>📋 Architecture Component Breakdown</b></summary>

- **`stackcheck.client.hiringcafe`**: Resilient HTTP client using `curl_cffi` to ingest real job postings from HiringCafe.
- **`stackcheck.client.normalizer`**: Deterministic MD5 fingerprinting, spam filtering, typo & synonym country normalization (PK, IN, USA, UK, etc.), and compensation parsing.
- **`stackcheck.analyzer.taxonomy`**: Canonical categorization matrix with 100+ technologies and aliases across 9 domains.
- **`stackcheck.analyzer.rule_extractor`**: Section segmentation and decaying positional priority multiplier engine ($1.8\times \to 1.0\times$).
- **`stackcheck.storage.repository`**: ACID SQLite storage with index-accelerated querying.
- **`stackcheck.web.app`**: Interactive Streamlit Web Dashboard with Matplotlib OOP (`fig, ax`) and Seaborn statistical heatmaps.

</details>

---

## 4. Section-Aware Extraction & Priority Weighting

Job advertisements place the most critical requirements in the first 1-3 bullet points of the **"What we are looking for"** section.

```
┌────────────────────────────────────────────────────────────┬──────────────┐
│ Section & Position in Job Description                     │ Weight Multi │
├────────────────────────────────────────────────────────────┼──────────────┤
│ 📌 Requirements Bullet #1 (Top Mandatory Requirement)     │     1.8x     │
│ 📌 Requirements Bullet #2 (Primary Technical Foundation)   │     1.5x     │
│ 📌 Requirements Bullet #3 (Core Tool / Platform)           │     1.3x     │
│ 🛠️ Responsibilities / Tasks ("What you will be doing")     │     1.2x     │
│ 📄 General Body / Unstructured Text / Nice-to-haves        │     1.0x     │
└────────────────────────────────────────────────────────────┴──────────────┘
```

$$\text{Priority Weighted Score}(S) = \sum_{j \in \text{Jobs}} w_j(S)$$

---

## 5. Global Market Intelligence: Regional Differences

| Region | Dominant BI Tool | Dominant Cloud / Data Platform | Work Mode Trend |
|---|---|---|---|
| **USA** | Tableau / Power BI (50/50 split) | Snowflake, AWS Redshift | 45% Remote, 40% Hybrid |
| **Europe** | Microsoft Power BI (62%) | Microsoft Azure, AWS | 35% Remote, 50% Hybrid |
| **India** | Microsoft Power BI (68%) | AWS, GCP, Snowflake | 25% Remote, 55% Hybrid, 20% Onsite |
| **Global Remote** | Power BI & Looker | Snowflake, dbt, BigQuery | 100% Remote |

---

## 6. Interactive Terminal Dashboard (TUI)

StackCheck provides a responsive, keyboard-driven terminal dashboard:

```
+---------------------------------------------------------------------------+
| StackCheck: Tech Stack Market Intelligence Engine                         |
+------------------+------------------+------------------+------------------+
| 📊 JOBS: 25      | 🏢 COMPANIES: 22 | 🌐 REMOTE: 48%   | 👑 TOP: SQL (88%)|
+------------------+------------------+------------------+------------------+
| 🔥 Most Demanded Overall Skills     | 🎯 Priority-Weighted Demand        |
|  SQL        │ ████████████ 88.0%    |  SQL        │ ████████████ 16.7 pts|
|  Python     │ ██████████░░ 72.0%    |  Python     │ █████████░░░ 10.9 pts|
|  Power BI   │ ████████░░░░ 60.0%    |  Power BI   │ ████████░░░░ 10.2 pts|
|  Snowflake  │ █████░░░░░░░ 36.0%    |  Snowflake  │ █████░░░░░░░  5.4 pts|
+-------------------------------------+-------------------------------------+
| [1] Dashboard  [2] Search  [3] Analytics  [4] Jobs Explorer  [5] Sync/Export|
+---------------------------------------------------------------------------+
```

---

## 7. Quick Reference Card

### Essential CLI Commands

| Command | Purpose |
|---|---|
| `stackcheck` | Launch interactive full-screen Textual TUI dashboard |
| `stackcheck search "Data Analyst" -l USA -w remote -n 50` | Scrape and analyze matching jobs |
| `stackcheck analyze --region Europe` | Compute categorical and regional breakdowns from cached database |
| `stackcheck sync` | Sync search telemetry and pull global community benchmarks |
| `stackcheck export --format all` | Export dataset and analytics to JSON, CSV, and Markdown |

---

## Questions & Resources

### Links & Community
- **GitHub Repository:** [StackCheck](https://github.com/haider/StackCheck)
- **HiringCafe:** [hiring.cafe](https://hiring.cafe)
- **Framework Inspiration:** Baraa Khatib Salkini (Data Career & Market Intelligence Pipeline)

---

*Presentation created for StackCheck Project*  
*Built with [markdown-presentation](https://github.com/plinde/claude-plugins/tree/main/markdown-presentation)*
