<p align="center">
  <img src="assets/logo.svg" alt="StackCheck Logo" width="600" />
</p>

<p align="center">
  <b>Tech Stack Market Intelligence Engine & Data Analytics Dashboard</b><br>
  <sub>Track real-time technology demand, co-occurrence synergies, and compensation benchmarks.</sub>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue?style=flat-square&logo=python" alt="Python 3.10+" />
  <img src="https://img.shields.io/badge/Streamlit-1.42%2B-FF4B4B?style=flat-square&logo=streamlit" alt="Streamlit" />
  <img src="https://img.shields.io/badge/License-MIT-green?style=flat-square" alt="License: MIT" />
  <img src="https://img.shields.io/badge/Version-0.1.0-cyan?style=flat-square" alt="v0.1.0" />
</p>

---

StackCheck is an automated job scraper, section-aware skill extractor, and interactive analytics dashboard built for data analysts, software engineers, and hiring managers. Inspired by real-world job market research methodologies (analyzing 22,000+ job ads across 100+ countries), StackCheck parses real job postings from **HiringCafe**, extracts demanded technologies with section-positional priority weighting, groups them into canonical categories, compares geographic markets, and renders interactive statistical visualizations with **Pandas**, **Matplotlib (OOP API: `fig, ax`)**, and **Seaborn**.

---

## 🌟 Key Features

- 🔍 **Live HiringCafe Ingestion**: Query by keywords, location (Pakistan, India, USA, UK, Germany, New Zealand, Singapore, Malaysia, Japan, South Korea, Brazil, Remote, etc.), workplace mode (*Remote / Hybrid / Onsite*), experience level (*Entry / Mid / Senior / Lead*), and custom limit.
- 🧹 **Data Cleaning & Normalization**: Deterministic fingerprinting to eliminate duplicates across companies, filter out spam, and normalize fuzzy typo/synonym country names (*"USA", "PK", "Lahore", "Indai", "Bangalore", "NZ", "Brasil"*).
- 🧠 **Section-Aware Skill Extraction**:
  - Differentiates **"What we are looking for"** (Requirements) from **"What you will be doing"** (Responsibilities).
  - Assigns decaying positional priority multipliers ($1.8\times \to 1.0\times$) so top bullet requirements receive higher weight.
  - Optional LLM enrichment via Gemini / OpenAI for unstructured job postings.
- 📈 **Statistical Data Visualizations (Matplotlib OOP & Seaborn)**:
  - **Top Demanded Skills Bar Chart**: Frequency % vs requirement-weighted scores with direct data labels.
  - **Co-Occurrence Correlation Matrix Heatmap (`sns.heatmap`)**: Discover common tech synergies (e.g., `Python + SQL`, `Tableau + Snowflake`, `FastAPI + Postgres`).
  - **Salary Benchmarks & Error Bars**: Min, Avg, Max compensation ranges across top technologies.
  - **Workplace & Experience Breakdown**: Pie charts and categorical bar plots.
- 💼 **Interactive Job Explorer**: Filterable Pandas DataFrame with search, skill tags, requirement bullet points, and direct application links.
- 🚀 **Future Roadmap & Local Exporters**: One-click export of live datasets to `CSV`, `JSON`, and executive `Markdown` briefs.

---

## 🚀 Quick Start

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/haider/StackCheck.git
cd StackCheck

# Install in virtualenv
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

---

## 🌐 Running the Web Dashboard

Launch the browser interface with a single command:
```bash
streamlit run app.py
# or
stackcheck web
```
The dashboard will open automatically in your browser at `http://localhost:8501`.

---

## ⚙️ Scriptable CLI Usage

StackCheck also provides fast, scriptable CLI commands:

### Scrape & Analyze
```bash
# Search for Data Analyst roles in Pakistan (or any country)
stackcheck search "Data Analyst" --location "Pakistan" --workplace remote --limit 30 --export all

# Search for Backend Engineers
stackcheck search "Backend Engineer" --limit 20
```

### Export Cached Data
```bash
stackcheck export --format all
```
```

---

## 📐 Analytical Methodology

StackCheck implements the criteria popularized by creator **Baraa Khatib Salkini**:

1. **Clean Dataset**: Filters out duplicates, spam, and expired job listings.
2. **Category Grouping**: Structures required skills into explicit technical categories.
3. **Requirement Priority Multipliers**:
   $$\text{Priority Weighted Score}(S) = \sum_{j \in \text{Jobs}} w_j(S)$$
   - *Requirement Bullet #1:* $1.8\times$
   - *Requirement Bullet #2:* $1.5\times$
   - *Requirement Bullet #3:* $1.3\times$
   - *Day-to-day Responsibilities:* $1.2\times$
   - *General body text:* $1.0\times$
4. **Geographic Comparison**: Analyzes how demand for tools like **Power BI** vs **Tableau** or cloud providers (**AWS** vs **Azure** vs **GCP**) varies between the USA, Europe, and India.

---

## 📂 Project Structure

```
StackCheck/
├── pyproject.toml              # Modern package metadata & scripts
├── README.md                   # Project documentation
├── PRESENTATION.md             # Markdown slide deck & timing guide
├── src/
│   └── stackcheck/
│       ├── cli.py              # CLI entrypoints (search, analyze, export, sync)
│       ├── config.py           # Settings, DB paths, Tokyo Night palette
│       ├── models.py           # Pydantic data models
│       ├── client/
│       │   ├── hiringcafe.py   # HiringCafe HTTP scraper & fallback benchmark
│       │   └── normalizer.py   # Deduplication hash, spam filter, region resolver
│       ├── analyzer/
│       │   ├── taxonomy.py     # Canonical taxonomy (100+ technologies)
│       │   ├── rule_extractor.py # Section-aware positional regex extractor
│       │   ├── llm_extractor.py  # Optional LLM parser (Gemini/OpenAI)
│       │   └── metrics.py      # Co-occurrence, weighted scores, geo distribution
│       ├── storage/
│       │   ├── db.py           # SQLite database schema
│       │   ├── repository.py   # Job & skill CRUD operations
│       │   ├── sync.py         # Central database & community sync client
│       │   └── exporters.py    # JSON, CSV, Markdown exporters
│       └── tui/
│           ├── app.py          # Main Textual App & tab navigation
│           ├── screens/        # Dashboard, Search, Analytics, Jobs, Community
│           └── widgets/        # Unicode BarChart, MetricCard
└── tests/                      # Pytest unit tests (100% pass)
```

---

## 🧪 Testing

Run test suite:
```bash
pytest tests/
```

---

## 📄 License
MIT License. Created for job market tech stack intelligence.
