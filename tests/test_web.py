"""
Unit tests for StackCheck Web Dashboard, Charts, and Pandas DataFrames.
"""

import matplotlib
matplotlib.use("Agg")  # Non-interactive backend for tests
import matplotlib.pyplot as plt

from stackcheck.models import JobPost, SearchQuery, Region, WorkplaceType, ExperienceLevel, ExtractedSkill, TechCategory, SalaryInfo
from stackcheck.analyzer.metrics import MetricsEngine
from stackcheck.web.charts import (
    plot_top_skills,
    plot_co_occurrence_heatmap,
    plot_salary_by_tech,
    plot_distributions,
    plot_category_breakdown
)


def create_sample_jobs():
    return [
        JobPost(
            id="job1",
            title="Senior Data Analyst",
            company="Shopify",
            location="San Francisco, CA",
            country="United States",
            region=Region.USA,
            workplace_type=WorkplaceType.REMOTE,
            experience_level=ExperienceLevel.SENIOR,
            salary=SalaryInfo(min_amount=130000, max_amount=170000, currency="USD"),
            extracted_skills=[
                ExtractedSkill(canonical_name="Python", category=TechCategory.PROGRAMMING_LANGUAGES, priority_weight=1.8),
                ExtractedSkill(canonical_name="SQL", category=TechCategory.DATABASES_STORAGE, priority_weight=1.8),
                ExtractedSkill(canonical_name="Tableau", category=TechCategory.BI_DATA_TOOLS, priority_weight=1.5),
            ],
            requirement_bullets=["5+ years Python and SQL", "Experience in Tableau dashboards"]
        ),
        JobPost(
            id="job2",
            title="Data Analyst",
            company="Grab",
            location="Singapore",
            country="Singapore",
            region=Region.APAC,
            workplace_type=WorkplaceType.HYBRID,
            experience_level=ExperienceLevel.MID,
            salary=SalaryInfo(min_amount=90000, max_amount=120000, currency="USD"),
            extracted_skills=[
                ExtractedSkill(canonical_name="Python", category=TechCategory.PROGRAMMING_LANGUAGES, priority_weight=1.5),
                ExtractedSkill(canonical_name="SQL", category=TechCategory.DATABASES_STORAGE, priority_weight=1.5),
                ExtractedSkill(canonical_name="Power BI", category=TechCategory.BI_DATA_TOOLS, priority_weight=1.2),
            ],
            requirement_bullets=["Strong SQL and Power BI skills"]
        )
    ]


def test_dataframe_conversions():
    jobs = create_sample_jobs()
    stats = MetricsEngine.aggregate(jobs, query_keywords="Data Analyst")
    
    df_jobs = MetricsEngine.to_jobs_dataframe(jobs)
    assert not df_jobs.empty
    assert len(df_jobs) == 2
    assert "Job Title" in df_jobs.columns
    assert "Extracted Skills" in df_jobs.columns
    
    df_skills = MetricsEngine.to_skills_dataframe(stats)
    assert not df_skills.empty
    assert "Skill" in df_skills.columns
    assert "Market Demand %" in df_skills.columns


def test_charts_generation():
    jobs = create_sample_jobs()
    stats = MetricsEngine.aggregate(jobs, query_keywords="Data Analyst")

    fig_top = plot_top_skills(stats, top_n=5)
    assert fig_top is not None
    plt.close(fig_top)

    fig_heat = plot_co_occurrence_heatmap(stats, top_n=5)
    assert fig_heat is not None
    plt.close(fig_heat)

    fig_sal = plot_salary_by_tech(stats)
    assert fig_sal is not None
    plt.close(fig_sal)

    fig_wp, fig_exp = plot_distributions(stats)
    assert fig_wp is not None
    assert fig_exp is not None
    plt.close(fig_wp)
    plt.close(fig_exp)

    fig_cat = plot_category_breakdown(stats)
    assert fig_cat is not None
    plt.close(fig_cat)


def test_extended_job_market_charts():
    from stackcheck.web.charts import (
        plot_salary_by_country_scatter,
        plot_top_hiring_companies,
        plot_experience_skill_matrix,
        plot_stack_density_distribution
    )
    jobs = create_sample_jobs()
    stats = MetricsEngine.aggregate(jobs, query_keywords="Data Analyst")

    # 1. Country scatter plot
    fig_scatter = plot_salary_by_country_scatter(stats.country_salary_data)
    assert fig_scatter is not None
    plt.close(fig_scatter)

    # 2. Top hiring companies
    fig_comp = plot_top_hiring_companies(stats.top_hiring_companies)
    assert fig_comp is not None
    plt.close(fig_comp)

    # 3. Experience skill matrix
    fig_exp_matrix = plot_experience_skill_matrix(stats.experience_skills_breakdown)
    assert fig_exp_matrix is not None
    plt.close(fig_exp_matrix)

    # 4. Stack density distribution
    fig_density = plot_stack_density_distribution(stats.stack_density_stats)
    assert fig_density is not None
    plt.close(fig_density)


def test_plot_salary_by_tech_sorting_options():
    jobs = create_sample_jobs()
    stats = MetricsEngine.aggregate(jobs, query_keywords="Data Analyst")
    
    fig_by_salary = plot_salary_by_tech(stats, min_samples=1, sort_by="avg_salary")
    assert fig_by_salary is not None
    plt.close(fig_by_salary)

    fig_by_samples = plot_salary_by_tech(stats, min_samples=1, sort_by="sample_count")
    assert fig_by_samples is not None
    plt.close(fig_by_samples)


