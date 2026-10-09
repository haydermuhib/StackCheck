# StackCheck: Tech Stack Market Intelligence

## Automated Job Scraping, Section-Aware Skill Extraction, and Web Analytics

**Duration:** 25 minutes  
**Audience:** Engineers, Data Analysts, Product Leaders, and Technical Recruiters  
**Date:** 2026-10-05  
**Version:** v0.2.1  

---

## Agenda

1. Problem and market motivation (2 min)
2. Raw job board compared to StackCheck (3 min)
3. Scraping design and courtesy limits (3 min)
4. End-to-end system architecture (4 min)
5. Section-aware extraction and priority weighting (3 min)
6. Currency normalization and salary benchmarking (3 min)
7. Regional trends and workplace compensation (3 min)
8. Interactive analytics dashboard (2 min)
9. Quick reference and CLI commands (2 min)

**Total Duration: 25 minutes**

---

## 1. Problem and market motivation

Standard job scrapers rely on naive keyword counts. Treating every mention of a technology as equal demand creates skewed insights:

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

### Questions this resolves
- Which technologies are strict core requirements versus nice-to-have mentions?
- How does tech stack demand differ across North America, Europe, and South Asia?
- What tools actually pair together (such as Python with SQL, Snowflake with dbt, or Power BI with DAX)?
- What are reliable, statistically validated salary benchmarks without outlier distortion?

---

## 2. Raw job boards compared to StackCheck

Public job search engines (like HiringCafe) provide search listings. They do not aggregate, correlate, or statistically analyze market data. StackCheck processes these listings into structured intelligence:

| Dimension | Raw job board (HiringCafe) | StackCheck |
| :--- | :--- | :--- |
| Skill demand ranking | Search result cards only | Top skills ranked by frequency percentage and weighted score |
| Section weighting | Treats all text equally | Differentiates core requirements (1.8x) from general text (1.0x) |
| Skill pairings | Not available | Heatmaps showing tool pairings (SQL with Python, dbt with Snowflake) |
| Salary benchmarks | Raw figures only | Minimum, average, and maximum benchmarks with sample count validation |
| Workplace spread | Not available | Compensation comparisons across remote, hybrid, and onsite listings |
| Stack breadth | Not available | Quantitative distribution of required skills per job post |
| Research workspaces | Not available | Multi-project workspaces with saved queries |
| Data export | Web interface only | Local SQLite storage with export to CSV, JSON, and Markdown |

---

## 3. Scraping design and courtesy limits

StackCheck queries origin job platforms with structured limits:

- **Batch request retrieval:** Intercepts Next.js `__NEXT_DATA__` server-rendered payloads. Ingests 60 to 90 complete structured jobs per request instead of hitting individual job page URLs.
- **Paced requests:** Built-in courtesy pauses (`time.sleep(0.35)`) and a single persistent HTTP connection keep the network footprint equivalent to normal browsing.
- **Local computation:** Data stores locally in SQLite. Taxonomy extraction, salary recalculations, and chart renderings run entirely offline on local hardware.
- **Circuit breaker:** Stops pagination when a query returns zero new hits or satisfies user limits.
- **Capped depth:** Caps crawl depth at 40 pages (roughly 2,500 jobs) to prevent runaway loops.
- **Role relevance:** Validates title semantics before saving to prevent unrelated roles from polluting datasets.

---

## 4. End-to-end system architecture

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
<summary><b>Component details</b></summary>

- `stackcheck.client.hiringcafe`: Scraper with browser TLS emulation, batch retrieval, and courtesy delays.
- `stackcheck.client.normalizer`: Role relevance validator, SHA-256 deduplicator, country standardizer, and salary parser.
- `stackcheck.analyzer.taxonomy`: 100+ normalized tech definitions across 9 functional categories.
- `stackcheck.analyzer.rule_extractor`: Segments descriptions and applies positional multipliers to requirements.
- `stackcheck.analyzer.currency`: Live exchange rates sync with offline fallback rates and USD conversion.
- `stackcheck.storage.repository`: Multi-project SQLite database with indexed queries.
- `stackcheck.web.charts`: Matplotlib visualization engine with Seaborn correlation heatmaps and error bars.
- `stackcheck.launcher`: Desktop lifecycle manager with instance verification.

</details>

---

## 5. Section-aware extraction and priority weighting

Job postings prioritize core skills in the opening bullet points of the qualifications section. Mentioning a tool in an introductory sentence carries less weight:

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

### Priority score formula
The total priority score for skill S across a dataset of jobs is calculated as:

$$\text{Priority Weighted Score}(S) = \sum_{j \in \text{Jobs}} w_j(S)$$

This separates foundational requirements (such as SQL and Python) from tools mentioned in passing.

---

## 6. Currency normalization and salary benchmarking

### Normalization pipeline
1. **Raw posting:** Detect currency symbol, ISO code, or country context.
2. **Exchange rates:** Read floating rates against USD with a 24-hour cache.
3. **Offline fallbacks:** Bundled offline rates for INR, PKR, PHP, EUR, GBP, CAD, and CRC.
4. **Outlier filtering:** Filter out annual values outside the range of $5,000 to $750,000 USD.
5. **Sample threshold:** Require at least 3 postings with disclosed compensation before displaying benchmark bars.

### Statistical charts
- **Error bars:** Displays minimum, average, and maximum compensation ranges.
- **Sample counts:** Appends `(n=X)` directly to skill labels for sample visibility.
- **Positioning:** Dynamic horizontal padding positions labels past the maximum error cap without text overlaps.

---

## 7. Regional trends and workplace compensation

Demand patterns vary across geographic markets and work arrangements:

### Regional skill preferences
| Region | Primary BI Tool | Primary Cloud / Data Platform | Common Work Mode |
|---|---|---|---|
| United States | Tableau / Power BI | Snowflake, AWS Redshift | 45% Remote, 40% Hybrid |
| Europe | Microsoft Power BI (62%) | Microsoft Azure, AWS | 35% Remote, 50% Hybrid |
| India | Microsoft Power BI (68%) | AWS, GCP, Snowflake | 25% Remote, 55% Hybrid |
| Global Remote | Power BI and Looker | Snowflake, dbt, BigQuery | 100% Remote |

### Workplace mode pay comparisons
StackCheck calculates compensation differentials across Remote, Hybrid, and Onsite postings within the same dataset.

---

## 8. Interactive analytics dashboard

StackCheck provides a multi-tab web dashboard built with Streamlit, Matplotlib, and Seaborn:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ Active Project: Data Analyst Global 2026                 [Sync Rates]       │
├───────────────────┬───────────────────┬───────────────────┬─────────────────┤
│ Total Jobs: 2,140 │ Companies: 840    │ Remote Ratio: 48% │ Top Skill: SQL  │
├───────────────────┴───────────────────┴───────────────────┴─────────────────┤
│                                                                             │
│ [Bar Chart: Top 15 Demanded Skills]      [Seaborn Heatmap: Co-occurrences]  │
│  • Raw frequency % vs weighted score      • Pairwise correlation matrix     │
│  • Positional requirement multipliers     • Tool pairings (e.g. dbt + SQL)  │
│                                                                             │
│ [Salary Benchmarks with Error Bars]      [Workplace & Experience Breakdown] │
│  • Min / Avg / Max range error bars       • Donut and Bar distributions     │
│  • Sample Filter (N >= 3)                • Remote pay premium metrics       │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│ Interactive Job Explorer                                                    │
│ Filter by skills, experience level, and country.                            │
│ Direct employer links for job applications.                                 │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 9. Quick reference and CLI commands

### CLI commands

| Command | Action |
|---|---|
| `stackcheck` | Launch interactive web dashboard |
| `stackcheck status` | Check server status, active port, and process ID |
| `stackcheck check` | Verify runtime dependencies |
| `stackcheck stop` | Stop running dashboard process |
| `stackcheck search "Data Analyst" --limit 50` | Scrape and analyze matching jobs from CLI |
| `stackcheck export --format all` | Export dataset to JSON, CSV, and Markdown |
| `stackcheck update` | In-place updater from GitHub Releases |

### Standalone executable
- **macOS and Linux:** `curl -fsSL https://raw.githubusercontent.com/haydermuhib/StackCheck/main/install.sh | bash`
- **Windows (PowerShell):** `curl.exe -L "https://github.com/haydermuhib/StackCheck/releases/latest/download/StackCheck-windows-x64.exe" -o StackCheck.exe; .\StackCheck.exe`

---

## Resources

- **GitHub repository:** [haydermuhib/StackCheck](https://github.com/haydermuhib/StackCheck)
- **Data source:** [HiringCafe](https://hiring.cafe)
- **Current version:** v0.2.1
