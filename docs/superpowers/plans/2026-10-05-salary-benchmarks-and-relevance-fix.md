# Salary Benchmarks & Search Relevance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Eliminate $N=1$ outlier skew in salary benchmark charts, fix Matplotlib cap label collisions, and prevent irrelevant non-analyst postings from polluting specific role queries.

**Architecture:** 
1. Introduce role relevance validation in `JobNormalizer` and `HiringCafeClient` requiring all significant search terms (and title matching) instead of loose `any()` matching.
2. Upgrade `plot_salary_by_tech` in `charts.py` to support dynamic sample thresholds (`min_samples >= 3`), dual ranking modes (top in-demand skills vs. highest salary), sample size labels `(n=X)`, and collision-free label positioning.
3. Expose interactive filtering and sorting controls for the salary benchmark chart in `src/stackcheck/web/app.py`.

**Tech Stack:** Python 3.10+, Matplotlib OOP, Seaborn, Pandas, Streamlit, Pytest.

**Spec:** Fix salary benchmark distortions where 1-sample infrastructure/low-latency jobs (e.g., ClickHouse, C++, Terraform) top Data Analyst salary charts with overlapping label artifacts.

## Global Constraints

- Preserve all existing public signatures or provide backward-compatible default parameters.
- All tests must be executed via `./.venv/bin/pytest`.
- Visual styling must adhere to the existing theme (`#0f172a`, `#3b82f6`, `#e2e8f0`, `despine`).
- Strict TDD: Write failing test, verify RED, implement minimal code, verify GREEN, commit.

---

### Task 1: Strict Role Relevance Filter in JobNormalizer & HiringCafeClient

**Files:**
- Modify: `src/stackcheck/client/normalizer.py`
- Modify: `src/stackcheck/client/hiringcafe.py:133-138`
- Test: `tests/test_normalizer_relevance.py`

**Interfaces:**
- Consumes: `title: str`, `description: str`, `keywords: str`
- Produces: `JobNormalizer.is_role_relevant(title: str, description: str, keywords: str) -> bool`

- [ ] **Step 1: Write the failing test**

Create `tests/test_normalizer_relevance.py`:
```python
"""Tests for role relevance filtering in JobNormalizer."""
from stackcheck.client.normalizer import JobNormalizer


def test_is_role_relevant_exact_and_multiterm():
    # True positives: Genuine Data Analyst jobs
    assert JobNormalizer.is_role_relevant(
        title="Senior Data Analyst",
        description="Looking for an experienced Data Analyst to build SQL and Tableau reports.",
        keywords="Data Analyst"
    ) is True

    assert JobNormalizer.is_role_relevant(
        title="Product Analyst (Growth)",
        description="Analyze user behavioral data and run A/B experiments.",
        keywords="Data Analyst"
    ) is True

    # True negative: Backend / Infrastructure engineer that mentions "data" but is not an analyst
    assert JobNormalizer.is_role_relevant(
        title="Staff Site Reliability Engineer",
        description="Manage high availability data pipelines using Terraform, ClickHouse, and Cassandra.",
        keywords="Data Analyst"
    ) is False

    # True negative: C++ platform engine developer
    assert JobNormalizer.is_role_relevant(
        title="Low Latency C++ Systems Engineer",
        description="Process trading data streams with ultra-low latency.",
        keywords="Data Analyst"
    ) is False

    # Wildcard / All queries should accept all
    assert JobNormalizer.is_role_relevant(
        title="Any Role",
        description="Any description",
        keywords="all"
    ) is True
    assert JobNormalizer.is_role_relevant(
        title="Any Role",
        description="Any description",
        keywords=""
    ) is True
```

- [ ] **Step 2: Run test to verify it fails**

Run: `./.venv/bin/pytest tests/test_normalizer_relevance.py -v`
Expected: FAIL with `AttributeError: type object 'JobNormalizer' has no attribute 'is_role_relevant'`

- [ ] **Step 3: Write minimal implementation**

In `src/stackcheck/client/normalizer.py`, add `is_role_relevant`:
```python
    @staticmethod
    def is_role_relevant(title: str, description: str, keywords: str) -> bool:
        """
        Validate whether a job posting is genuinely relevant to the search query.
        Prevents broad matches where an unrelated role (e.g. SRE) mentions the word 'data'.
        """
        if not keywords or keywords.strip().lower() in ("all", "*"):
            return True

        kw_clean = keywords.strip().lower()
        title_lower = title.lower()
        desc_lower = description.lower()
        full_text = f"{title_lower} {desc_lower}"

        # 1. Exact phrase match in title or description
        if kw_clean in full_text:
            return True

        # 2. Tokenize query keywords (ignoring small stop words)
        stop_words = {"and", "or", "in", "the", "a", "an", "of", "for", "with", "to", "at"}
        tokens = [t for t in re.split(r"\s+", kw_clean) if t and t not in stop_words and len(t) > 1]
        if not tokens:
            return True

        # 3. Check if all required tokens appear in the text
        all_tokens_present = all(tok in full_text for tok in tokens)
        if not all_tokens_present:
            return False

        # 4. If query explicitly specifies a role class ('analyst', 'engineer', 'developer', 'scientist', 'manager'),
        # require that this role class is represented in the title or as a primary role descriptor
        role_classes = ["analyst", "engineer", "developer", "scientist", "architect", "manager", "designer"]
        specified_roles = [r for r in role_classes if r in tokens]
        if specified_roles:
            # At least one specified role class must be present in the job title
            if not any(r in title_lower for r in specified_roles):
                return False

        return True
```

And in `src/stackcheck/client/hiringcafe.py:L133-L138`, replace the loose `any()` check:
```python
            # Step 1: Filter by keyword relevance if doing broad fetch
            raw_tools = ' '.join(tech_tools if isinstance(tech_tools, list) else [])
            combined_desc = f"{raw_desc} {raw_tools}"
            if not JobNormalizer.is_role_relevant(title, combined_desc, query.keywords):
                continue
```

- [ ] **Step 4: Run test to verify it passes**

Run: `./.venv/bin/pytest tests/test_normalizer_relevance.py tests/test_client.py -v`
Expected: PASS (all tests pass)

- [ ] **Step 5: Commit**

```bash
git add src/stackcheck/client/normalizer.py src/stackcheck/client/hiringcafe.py tests/test_normalizer_relevance.py
git commit -m "fix(client): enforce strict role relevance filtering to prevent query pollution"
```

---

### Task 2: Robust Salary Benchmark Filtering, Sample Counts, and Collision-Free Labels

**Files:**
- Modify: `src/stackcheck/web/charts.py:115-185`
- Test: `tests/test_salary_chart_robustness.py`

**Interfaces:**
- Consumes: `stats: AggregatedStats`, `min_samples: int = 3`, `top_n: int = 12`, `sort_by: str = "avg_salary"`
- Produces: `plot_salary_by_tech(...) -> Optional[plt.Figure]` with `(n=X)` annotations and collision-free label coordinates.

- [ ] **Step 1: Write the failing test**

Create `tests/test_salary_chart_robustness.py`:
```python
"""Tests for enhanced salary benchmark charting with sample size thresholds and collision-free annotations."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from stackcheck.models import AggregatedStats
from stackcheck.web.charts import plot_salary_by_tech


def test_plot_salary_by_tech_sample_filtering():
    # Build stats with a mix of high-sample skills and single outlier skills
    mock_stats = AggregatedStats(
        total_jobs=100,
        unique_companies=40,
        salary_by_top_tech={
            "ClickHouse": {"min": 168500, "avg": 168500, "max": 168500, "samples": 1},
            "C++": {"min": 90000, "avg": 155000, "max": 360000, "samples": 2},
            "SQL": {"min": 70000, "avg": 105000, "max": 140000, "samples": 45},
            "Python": {"min": 75000, "avg": 110000, "max": 150000, "samples": 38},
            "Tableau": {"min": 65000, "avg": 95000, "max": 130000, "samples": 22},
            "Excel": {"min": 50000, "avg": 75000, "max": 100000, "samples": 50},
        }
    )

    # 1. With min_samples=5: ClickHouse (n=1) and C++ (n=2) MUST be filtered out
    fig_filtered = plot_salary_by_tech(mock_stats, min_samples=5)
    assert fig_filtered is not None
    ax = fig_filtered.axes[0]
    yticklabels = [t.get_text() for t in ax.get_yticklabels()]
    assert any("SQL" in label for label in yticklabels)
    assert any("Python" in label for label in yticklabels)
    assert not any("ClickHouse" in label for label in yticklabels)
    assert not any("C++" in label for label in yticklabels)
    plt.close(fig_filtered)

    # 2. Verify sample count is present in tick labels (e.g., 'SQL (n=45)')
    sql_label = next(l for l in yticklabels if "SQL" in l)
    assert "(n=45)" in sql_label

    # 3. Graceful degradation: If min_samples is higher than any available, it gracefully returns available
    sparse_stats = AggregatedStats(
        total_jobs=2,
        unique_companies=2,
        salary_by_top_tech={
            "RareTool": {"min": 100000, "avg": 100000, "max": 100000, "samples": 1}
        }
    )
    fig_sparse = plot_salary_by_tech(sparse_stats, min_samples=10)
    assert fig_sparse is not None
    plt.close(fig_sparse)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `./.venv/bin/pytest tests/test_salary_chart_robustness.py -v`
Expected: FAIL because `(n=45)` is not in yticklabels and default parameters/filtering differ.

- [ ] **Step 3: Write minimal implementation**

In `src/stackcheck/web/charts.py`, replace `plot_salary_by_tech`:
```python
def plot_salary_by_tech(
    stats: AggregatedStats, 
    min_samples: int = 3, 
    top_n: int = 12,
    sort_by: str = "avg_salary"
) -> Optional[plt.Figure]:
    """
    Generate grouped salary comparison (Min, Avg, Max) with sample size protection
    and collision-free label layout.
    """
    if not stats.salary_by_top_tech:
        return None

    # Collect candidate records
    all_records = []
    for skill, s_info in stats.salary_by_top_tech.items():
        samples = s_info.get("samples", 0)
        avg_sal = s_info.get("avg", 0)
        if samples > 0 and avg_sal > 0:
            all_records.append({
                "Skill": skill,
                "Min Salary": s_info.get("min", 0),
                "Avg Salary": avg_sal,
                "Max Salary": s_info.get("max", 0),
                "Samples": samples
            })

    if not all_records:
        return None

    # Filter by minimum sample size; gracefully fall back if threshold excludes all data
    data = [r for r in all_records if r["Samples"] >= min_samples]
    if len(data) < 3 and min_samples > 1:
        # Fallback to lower threshold if dataset has sparse salaries
        data = [r for r in all_records if r["Samples"] >= 1]

    if not data:
        return None

    df = pd.DataFrame(data)

    # Sort logic
    if sort_by == "sample_count":
        df = df.sort_values(by=["Samples", "Avg Salary"], ascending=[True, True]).tail(top_n)
    else:
        df = df.sort_values(by=["Avg Salary", "Samples"], ascending=[True, True]).tail(top_n)

    fig, ax = plt.subplots(figsize=(9.5, max(4.5, len(df) * 0.42)), dpi=150)

    y_pos = np.arange(len(df))
    height = 0.55

    # Plot average bar
    bars = ax.barh(y_pos, df["Avg Salary"], height=height, color="#3b82f6", alpha=0.85, label="Average Salary")

    # Add error bar range from Min to Max
    err_min = df["Avg Salary"] - df["Min Salary"]
    err_max = df["Max Salary"] - df["Avg Salary"]
    ax.errorbar(
        df["Avg Salary"],
        y_pos,
        xerr=[err_min, err_max],
        fmt="none",
        ecolor="#0f172a",
        elinewidth=1.6,
        capsize=4,
        capthick=1.4,
        label="Salary Range (Min - Max)"
    )

    # Collision-free text annotation positioned safely to the right of the max whisker
    max_x_val = max(df["Max Salary"].max(), df["Avg Salary"].max())
    offset = max_x_val * 0.02

    for bar, avg_val, max_val in zip(bars, df["Avg Salary"], df["Max Salary"]):
        # Place label past the max error cap to prevent collision
        label_x = max(avg_val, max_val) + offset
        ax.text(
            label_x,
            bar.get_y() + bar.get_height() / 2,
            f"${avg_val:,.0f}",
            va="center",
            ha="left",
            fontsize=8.5,
            fontweight="bold",
            color="#1e293b"
        )

    # Include sample size (n=X) in tick labels
    formatted_labels = [f"{row['Skill']}  (n={int(row['Samples'])})" for _, row in df.iterrows()]
    ax.set_yticks(y_pos)
    ax.set_yticklabels(formatted_labels, fontsize=9.5, fontweight="semibold")
    ax.xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, p: f"${x*1e-3:,.0f}k"))
    
    # Expand x-limit to prevent annotation cutoff
    ax.set_xlim(0, (max_x_val + offset) * 1.15)
    
    ax.set_title("Salary Benchmarks by Extracted Technology (USD / Yr)", fontsize=13, fontweight="bold", pad=14, color="#0f172a")
    ax.set_xlabel("Compensation ($ USD)", fontsize=10, fontweight="semibold", color="#475569")
    ax.legend(loc="lower right", frameon=True)
    
    sns.despine(ax=ax, top=True, right=True)
    fig.tight_layout()
    return fig
```

- [ ] **Step 4: Run test to verify it passes**

Run: `./.venv/bin/pytest tests/test_salary_chart_robustness.py tests/test_web.py -v`
Expected: PASS (all tests pass)

- [ ] **Step 5: Commit**

```bash
git add src/stackcheck/web/charts.py tests/test_salary_chart_robustness.py
git commit -m "fix(charts): add sample thresholding, (n=X) labels, and collision-free salary text positioning"
```

---

### Task 3: Interactive UI Controls in Streamlit App

**Files:**
- Modify: `src/stackcheck/web/app.py:622-633`
- Test: `tests/test_web.py`

**Interfaces:**
- Consumes: `st.selectbox`, `st.slider`, `plot_salary_by_tech`
- Produces: Dynamic interactive salary benchmarking in Tab 2.

- [ ] **Step 1: Write the test verifying parameter propagation**

Add to `tests/test_web.py`:
```python
def test_plot_salary_by_tech_sorting_options():
    jobs = create_sample_jobs()
    stats = MetricsEngine.aggregate(jobs, query_keywords="Data Analyst")
    
    fig_by_salary = plot_salary_by_tech(stats, min_samples=1, sort_by="avg_salary")
    assert fig_by_salary is not None
    plt.close(fig_by_salary)

    fig_by_samples = plot_salary_by_tech(stats, min_samples=1, sort_by="sample_count")
    assert fig_by_samples is not None
    plt.close(fig_by_samples)
```

- [ ] **Step 2: Run test to verify it passes**

Run: `./.venv/bin/pytest tests/test_web.py -k test_plot_salary_by_tech_sorting_options -v`
Expected: PASS

- [ ] **Step 3: Update `src/stackcheck/web/app.py`**

In `src/stackcheck/web/app.py:623-635`, update Section 3 (Salary Benchmarks):
```python
            # 3. Salary Benchmarks & Workplace/Experience Distributions
            col_sal, col_dist = st.columns([1.3, 1])

            with col_sal:
                st.subheader("💵 Salary Benchmarks by Technology")
                st.caption("Displays Min, Avg, and Max compensation with sample size validation.")
                
                c_ctrl1, c_ctrl2 = st.columns([1, 1.2])
                with c_ctrl1:
                    sal_min_samples = st.selectbox(
                        "Min Postings Required (N):",
                        options=[1, 2, 3, 5, 10],
                        index=2,  # Default to min 3 samples
                        help="Filters out one-off outlier roles that skew salary averages.",
                        key="sal_min_samples_select"
                    )
                with c_ctrl2:
                    sal_sort_mode = st.selectbox(
                        "Rank Order By:",
                        options=["Highest Average Salary", "Most Disclosed Postings (Sample Count)"],
                        index=0,
                        key="sal_sort_mode_select"
                    )
                
                sort_key = "sample_count" if "Sample" in sal_sort_mode else "avg_salary"
                sal_fig = plot_salary_by_tech(stats, min_samples=sal_min_samples, sort_by=sort_key)
                if sal_fig:
                    st.pyplot(sal_fig, width="stretch")
                else:
                    st.info(f"No technologies have at least {sal_min_samples} salary samples in the current dataset. Try lowering the minimum postings threshold.")
```

- [ ] **Step 4: Run full test suite to verify no regressions**

Run: `./.venv/bin/pytest -v`
Expected: 34+ passed in ~5s

- [ ] **Step 5: Commit**

```bash
git add src/stackcheck/web/app.py tests/test_web.py
git commit -m "feat(web): add interactive sample threshold and rank ordering controls to salary chart"
```

---

### Task 4: End-to-End Verification

**Files:**
- Test: Full test suite and synthetic pipeline simulation

- [ ] **Step 1: Run complete test suite**

Run: `./.venv/bin/pytest -v`
Expected: All tests PASS with pristine output.

- [ ] **Step 2: Verify git status is clean**

Run: `git status`
Expected: Clean working tree.
