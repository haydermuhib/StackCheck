"""Tests for enhanced salary benchmark charting with sample size thresholds and collision-free annotations."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from stackcheck.models import AggregatedStats
from stackcheck.web.charts import plot_salary_by_tech


def make_mock_stats(salary_data):
    return AggregatedStats(
        query_keywords="Data Analyst",
        total_jobs=100,
        unique_companies=40,
        workplace_distribution={},
        experience_distribution={},
        category_breakdown={},
        top_skills_overall=[],
        weighted_top_skills=[],
        co_occurrences=[],
        geo_breakdown={},
        salary_by_top_tech=salary_data
    )


def test_plot_salary_by_tech_sample_filtering():
    # Build stats with a mix of high-sample skills and single outlier skills
    mock_stats = make_mock_stats({
        "ClickHouse": {"min": 168500, "avg": 168500, "max": 168500, "samples": 1},
        "C++": {"min": 90000, "avg": 155000, "max": 360000, "samples": 2},
        "SQL": {"min": 70000, "avg": 105000, "max": 140000, "samples": 45},
        "Python": {"min": 75000, "avg": 110000, "max": 150000, "samples": 38},
        "Tableau": {"min": 65000, "avg": 95000, "max": 130000, "samples": 22},
        "Excel": {"min": 50000, "avg": 75000, "max": 100000, "samples": 50},
    })

    # 1. With min_samples=5: ClickHouse (n=1) and C++ (n=2) MUST be filtered out
    fig_filtered = plot_salary_by_tech(mock_stats, min_samples=5)
    assert fig_filtered is not None
    ax = fig_filtered.axes[0]
    yticklabels = [t.get_text() for t in ax.get_yticklabels()]
    assert any("SQL" in label for label in yticklabels)
    assert any("Python" in label for label in yticklabels)
    assert not any("ClickHouse" in label for label in yticklabels)
    assert not any("C++" in label for label in yticklabels)

    # 2. Verify sample count is present in tick labels (e.g., 'SQL (n=45)')
    sql_label = next(l for l in yticklabels if "SQL" in l)
    assert "(n=45)" in sql_label
    plt.close(fig_filtered)

    # 3. Graceful degradation: If min_samples is higher than any available, it gracefully returns available
    sparse_stats = make_mock_stats({
        "RareTool": {"min": 100000, "avg": 100000, "max": 100000, "samples": 1}
    })
    fig_sparse = plot_salary_by_tech(sparse_stats, min_samples=10)
    assert fig_sparse is not None
    plt.close(fig_sparse)
