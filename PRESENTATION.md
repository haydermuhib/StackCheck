# StackCheck: Tech Stack Intelligence & Market Analytics
## Automated Job Scraping, Section-Aware Skill Extraction & Interactive Web Analytics

**Duration:** 25 minutes  
**Audience:** Engineers, Data Analysts, Product Leaders & Technical Recruiters  
**Date:** 2026-10-04  

---

## Agenda

1. Problem and Market Motivation (3 min)
2. Analytical Methodology: Baraa Khatib Salkini Framework (4 min)
3. End-to-End System Architecture (4 min)
4. Section-Aware Extraction and Priority Weighting (3 min)
5. Currency Normalization and Compensation Benchmarks (3 min)
6. Regional Tech Stack Trends (3 min)
7. Interactive Streamlit Analytics Dashboard (3 min)
8. Quick Reference and Setup (2 min)

**Total Duration: 25 minutes**

---

## 1. Problem and Market Motivation

Generic job scraping relies on naive keyword searches. That approach treats any mention of a technology as equal demand, skewing market insights.

```
┌────────────────────────────────┐     ┌────────────────────────────────┐
│    Generic Keyword Matching    │     │    StackCheck Intelligence     │
├────────────────────────────────┤     ├────────────────────────────────┤
│ • Treats "R" in "for" as skill │ vs  │ • Context-aware word boundary  │
│ • Ignores requirement priority │     │ • Positional weight multiplier │
│ • Polluted by spam & duplicates│     │ • SHA-256 fingerprint dedupe   │
│ • Skewed by mixed currencies   │     │ • Normalized USD conversions   │
└────────────────────────────────┘     └────────────────────────────────┘
```

### Questions This Solves
- Which skills are strict requirements versus nice-to-have extras?
- How does tech stack demand differ across North America, Europe, and South Asia?
- What tools pair together most often (for example, Python with SQL, or Snowflake with dbt)?
- What is the realistic compensation distribution for specific tool stacks?

---

## 2. Analytical Methodology (Baraa Khatib Salkini Framework)

StackCheck builds on the data analysis framework applied to 22,000 real job postings across 4,000 companies in roughly 100 countries.

<div style="display: flex; gap: 15px; justify-content: center; flex-wrap: wrap;">
    <div style="border: 2px solid #73daca; border-radius: 8px; padding: 12px; min-width: 180px; background: rgba(115,218,202,0.1);">
        <strong style="color: #73daca;">1. Data Cleaning</strong>
        <p>SHA-256 fingerprint deduplication, spam detection, and country normalization.</p>
    </div>
    <div style="border: 2px solid #7aa2f7; border-radius: 8px; padding: 12px; min-width: 180px; background: rgba(122,162,247,0.1);">
        <strong style="color: #7aa2f7;">2. Taxonomy Mapping</strong>
        <p>100+ normalized technologies grouped across 9 functional categories.</p>
    </div>
    <div style="border: 2px solid #bb9af7; border-radius: 8px; padding: 12px; min-width: 180px; background: rgba(187,154,247,0.1);">
        <strong style="color: #bb9af7;">3. Section Priority</strong>
        <p>Position-based multipliers prioritizing requirements over day-to-day descriptions.</p>
    </div>
    <div style="border: 2px solid #e0af68; border-radius: 8px; padding: 12px; min-width: 180px; background: rgba(224,175,104,0.1);">
        <strong style="color: #e0af68;">4. Geo & Currency Normalization</strong>
        <p>Regional segmentation and daily exchange rate conversion into canonical USD.</p>
    </div>
</div>

---

## 3. End-to-End System Architecture

```
┌───────────────────┐      ┌───────────────────────────┐      ┌───────────────────────────┐
│  HiringCafe API   │─────▶│  Job Normalizer Pipeline  │─────▶│ Section-Aware Extractor   │
│  (curl_cffi TLS)  │      │  • SHA-256 Fingerprint    │      │  • Section Segmentation   │
└───────────────────┘      │  • Geo Synonym Mapping    │      │  • Positional Multipliers │
                           │  • Spam & Junk Filter     │      │  • 100+ Skill Taxonomy    │
                           └───────────────────────────┘      └─────────────┬─────────────┘
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
        │  • Interactive Explorer │                   │ • JSON, CSV, Markdown   │
        └─────────────────────────┘                   └─────────────────────────┘
```

<details>
<summary><b>Component Details</b></summary>

- `stackcheck.client.hiringcafe`: Scrapes live job postings from HiringCafe with browser TLS fingerprint impersonation.
- `stackcheck.client.normalizer`: Deduplicates posts by title, company, and description. Standardizes country names and parses salaries.
- `stackcheck.analyzer.taxonomy`: Maintains 100+ tech definitions across languages, databases, BI tools, and cloud platforms.
- `stackcheck.analyzer.rule_extractor`: Segments job descriptions into sections and applies decaying positional weights.
- `stackcheck.analyzer.currency`: Caches daily exchange rates with 24-hour TTL, supports offline fallback rates, and normalizes foreign currencies to USD.
- `stackcheck.storage.repository`: SQLite persistence with project-scoped isolation and multi-keyword search logging.
- `stackcheck.web.app`: Streamlit web dashboard with Matplotlib charts, Seaborn heatmaps, and direct apply links.

</details>

---

## 4. Section-Aware Extraction and Priority Weighting

Job advertisements place the most critical requirements in the first bullet points of the qualifications section. Mentioning a tool in an introductory paragraph or in a nice-to-have list carries much less weight.

```
┌────────────────────────────────────────────────────────────┬──────────────┐
│ Section and Position in Job Posting                        │ Multiplier   │
├────────────────────────────────────────────────────────────┼──────────────┤
│ Requirements Bullet #1 (Top Mandatory Requirement)         │     1.8x     │
│ Requirements Bullet #2 (Primary Technical Foundation)       │     1.5x     │
│ Requirements Bullet #3 (Core Tool or Platform)             │     1.3x     │
│ Responsibilities / Day-to-Day Tasks                        │     1.2x     │
│ General Body, Overview, or Unstructured Text               │     1.0x     │
└────────────────────────────────────────────────────────────┴──────────────┘
```

### Priority Score Formula
The total priority score for skill $S$ across a set of jobs is calculated as:

$$\text{Priority Weighted Score}(S) = \sum_{j \in \text{Jobs}} w_j(S)$$

This separates foundational stack requirements from superficial keyword mentions.

---

## 5. Currency Normalization and Compensation Benchmarks

Job listings report salaries in various currencies and intervals (hourly, monthly, annual). Without normalization, non-USD amounts distort salary analytics.

```
┌───────────────────────────────────────────────────────────────────────────────┐
│ 1. Raw Posting: Detect currency symbol, ISO code, or country context          │
├───────────────────────────────────────────────────────────────────────────────┤
│ 2. Floating API Sync: Query daily rates against USD with 24-hour TTL cache    │
├───────────────────────────────────────────────────────────────────────────────┤
│ 3. Offline Fallbacks: Built-in rates for INR, PKR, PHP, EUR, GBP, CAD, CRC    │
├───────────────────────────────────────────────────────────────────────────────┤
│ 4. Outlier Filter: Filter annual values outside $5,000 to $750,000 USD        │
└───────────────────────────────────────────────────────────────────────────────┘
```

- Converts hourly rates assuming 2,080 working hours per year.
- Converts monthly salaries assuming 12 months per year.
- Detects listings in foreign markets that mistakenly use the dollar sign for local currency.
- Users can review and adjust exchange rates directly from the web dashboard sidebar.

---

## 6. Regional Tech Stack Trends

Demand patterns shift significantly by geography:

| Region | Primary BI Tool | Primary Cloud / Data Platform | Common Work Mode |
|---|---|---|---|
| USA | Tableau / Power BI (balanced) | Snowflake, AWS Redshift | 45% Remote, 40% Hybrid |
| Europe | Microsoft Power BI (62%) | Microsoft Azure, AWS | 35% Remote, 50% Hybrid |
| India | Microsoft Power BI (68%) | AWS, GCP, Snowflake | 25% Remote, 55% Hybrid |
| Global Remote | Power BI & Looker | Snowflake, dbt, BigQuery | 100% Remote |

---

## 7. Interactive Streamlit Analytics Dashboard

StackCheck runs a local web application built with Streamlit, Matplotlib, and Seaborn:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 📊 Active Project: Data Engineering 2026                 [🔄 Sync Rates]    │
├───────────────────┬───────────────────┬───────────────────┬─────────────────┤
│ Total Jobs: 142   │ Companies: 98     │ Remote Ratio: 52% │ Top Skill: SQL  │
├───────────────────┴───────────────────┴───────────────────┴─────────────────┤
│                                                                             │
│ [Bar Chart: Top 15 Demanded Skills]      [Seaborn Heatmap: Co-occurrences]  │
│  • Raw frequency % vs weighted demand     • Symmetrical correlation matrix  │
│  • Categorical color coding               • Tool clustering (e.g. dbt + SQL)│
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│ 💼 Interactive Job Explorer                                                 │
│ Filter by skills (ANY / ALL match), experience level, and country.           │
│ Direct employer links for one-click job applications.                       │
└─────────────────────────────────────────────────────────────────────────────┘
```

- Headless and detached execution with `stackcheck -d`
- Health check and process monitoring with `stackcheck status`
- Safe termination with `stackcheck stop`

---

## 8. Quick Reference Card

### Command Line Interface

| Command | Action |
|---|---|
| `stackcheck` | Launch interactive Streamlit web dashboard |
| `stackcheck -d` | Launch web dashboard as a background daemon |
| `stackcheck status` | Check server health, active port, and uptime |
| `stackcheck stop` | Terminate running dashboard processes |
| `stackcheck search -k "Data Engineer" -l Remote` | Scrape and analyze matching jobs from CLI |
| `stackcheck export --format all` | Export dataset to JSON, CSV, and Markdown |

### Standalone Executable
Standalone binaries require no Python installation:
- **macOS / Linux:** `curl -fsSL https://raw.githubusercontent.com/haydermuhib/StackCheck/main/install.sh | bash`
- **Windows (PowerShell):** `curl.exe -L "https://github.com/haydermuhib/StackCheck/releases/latest/download/StackCheck-windows-x64.exe" -o StackCheck.exe; .\StackCheck.exe`

---

## Questions & Resources

- GitHub Repository: [haydermuhib/StackCheck](https://github.com/haydermuhib/StackCheck)
- Data Source: [HiringCafe](https://hiring.cafe)
- Methodology Basis: Baraa Khatib Salkini data analysis framework

---

*Presentation prepared for StackCheck*  
*Built with [markdown-presentation](https://github.com/plinde/claude-plugins/tree/main/markdown-presentation)*
