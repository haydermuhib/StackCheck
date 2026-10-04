"""
Unit tests for StackCheck Analyzer, RuleExtractor, and MetricsEngine.
"""

import pytest
from stackcheck.models import JobPost, ExtractedSkill, Region, WorkplaceType, ExperienceLevel, TechCategory
from stackcheck.analyzer.rule_extractor import RuleExtractor, segment_job_description
from stackcheck.client.normalizer import JobNormalizer
from stackcheck.analyzer.metrics import MetricsEngine


def test_segment_job_description():
    sample_text = """
    About Company:
    We build fintech products.

    What we are looking for:
    • Advanced SQL and dimensional data warehouse modeling (Snowflake).
    • Python programming with Pandas and Scikit-learn.
    • Tableau dashboarding.

    What you will be doing:
    • Design ETL pipelines.
    • Run A/B testing experiments.
    """
    segmented = segment_job_description(sample_text)
    assert len(segmented["requirements_bullets"]) >= 3
    assert len(segmented["task_bullets"]) >= 2


def test_rule_extractor_positional_weighting():
    extractor = RuleExtractor()
    sample_text = """
    What we are looking for:
    • Expert in Python and PostgreSQL
    • Experience with Tableau
    • Nice to have: Docker
    """
    skills, req_b, task_b = extractor.process_job_description(sample_text)
    skill_dict = {s.canonical_name: s for s in skills}

    assert "Python" in skill_dict
    assert "PostgreSQL" in skill_dict
    assert "Tableau" in skill_dict
    # First bullet point gets highest priority weight multiplier (>= 1.5)
    assert skill_dict["Python"].priority_weight >= 1.5


def test_job_normalizer():
    # Deduplication fingerprint
    fp1 = JobNormalizer.compute_fingerprint("Data Analyst", "Google", "SQL and Python required.")
    fp2 = JobNormalizer.compute_fingerprint("data analyst", "google", "SQL and Python required.")
    assert fp1 == fp2

    # Workplace parsing
    assert JobNormalizer.parse_workplace_type("Remote, USA") == WorkplaceType.REMOTE
    assert JobNormalizer.parse_workplace_type("New York, NY (Hybrid)") == WorkplaceType.HYBRID
    assert JobNormalizer.parse_workplace_type("San Francisco, CA") == WorkplaceType.ONSITE

    # Region parsing
    assert JobNormalizer.parse_region_and_country("San Francisco, CA")[0] == Region.USA
    assert JobNormalizer.parse_region_and_country("London, UK")[0] == Region.EUROPE
    assert JobNormalizer.parse_region_and_country("Bengaluru, India")[0] == Region.INDIA


def test_metrics_engine_aggregation():
    jobs = [
        JobPost(
            id="job1",
            title="Senior Data Analyst",
            company="Stripe",
            location="San Francisco, CA",
            region=Region.USA,
            workplace_type=WorkplaceType.HYBRID,
            extracted_skills=[
                ExtractedSkill(name="SQL", canonical_name="SQL", category=TechCategory.PROGRAMMING_LANGUAGES, priority_weight=1.8),
                ExtractedSkill(name="Python", canonical_name="Python", category=TechCategory.PROGRAMMING_LANGUAGES, priority_weight=1.5),
                ExtractedSkill(name="Snowflake", canonical_name="Snowflake", category=TechCategory.DATA_ENGINEERING, priority_weight=1.3),
            ]
        ),
        JobPost(
            id="job2",
            title="Data Analyst",
            company="Spotify",
            location="Remote",
            region=Region.GLOBAL_REMOTE,
            workplace_type=WorkplaceType.REMOTE,
            extracted_skills=[
                ExtractedSkill(name="SQL", canonical_name="SQL", category=TechCategory.PROGRAMMING_LANGUAGES, priority_weight=1.8),
                ExtractedSkill(name="Power BI", canonical_name="Power BI", category=TechCategory.BI_DATA_TOOLS, priority_weight=1.5),
                ExtractedSkill(name="Python", canonical_name="Python", category=TechCategory.PROGRAMMING_LANGUAGES, priority_weight=1.0),
            ]
        )
    ]

    stats = MetricsEngine.aggregate(jobs, query_keywords="Test Query")
    assert stats.total_jobs == 2
    assert stats.unique_companies == 2
    
    # Check top skills
    skill_names = [s["skill"] for s in stats.top_skills_overall]
    assert "SQL" in skill_names
    assert "Python" in skill_names

    # Check co-occurrence
    co_pairs = [(p.skill_a, p.skill_b) for p in stats.co_occurrences]
    assert ("Python", "SQL") in co_pairs or ("SQL", "Python") in co_pairs


def test_job_market_extended_metrics():
    from stackcheck.models import SalaryInfo
    jobs = [
        JobPost(
            id="j1",
            title="Senior Data Engineer",
            company="Airbnb",
            location="San Francisco, CA",
            country="United States",
            region=Region.USA,
            workplace_type=WorkplaceType.REMOTE,
            experience_level=ExperienceLevel.SENIOR,
            salary=SalaryInfo(min_amount=160000, max_amount=190000),
            extracted_skills=[
                ExtractedSkill(name="Python", canonical_name="Python", category=TechCategory.PROGRAMMING_LANGUAGES, priority_weight=1.8),
                ExtractedSkill(name="SQL", canonical_name="SQL", category=TechCategory.PROGRAMMING_LANGUAGES, priority_weight=1.5),
                ExtractedSkill(name="Spark", canonical_name="Spark", category=TechCategory.DATA_ENGINEERING, priority_weight=1.2),
            ]
        ),
        JobPost(
            id="j2",
            title="Junior Data Analyst",
            company="Airbnb",
            location="London, UK",
            country="United Kingdom",
            region=Region.EUROPE,
            workplace_type=WorkplaceType.ONSITE,
            experience_level=ExperienceLevel.ENTRY,
            salary=SalaryInfo(min_amount=45000, max_amount=55000),
            extracted_skills=[
                ExtractedSkill(name="SQL", canonical_name="SQL", category=TechCategory.PROGRAMMING_LANGUAGES, priority_weight=1.8),
                ExtractedSkill(name="Excel", canonical_name="Excel", category=TechCategory.OTHER, priority_weight=1.0),
            ]
        ),
        JobPost(
            id="j3",
            title="Lead ML Engineer",
            company="Meta",
            location="Remote",
            country="United States",
            region=Region.USA,
            workplace_type=WorkplaceType.REMOTE,
            experience_level=ExperienceLevel.LEAD,
            salary=None,  # No salary disclosed
            extracted_skills=[
                ExtractedSkill(name="Python", canonical_name="Python", category=TechCategory.PROGRAMMING_LANGUAGES, priority_weight=1.8),
                ExtractedSkill(name="PyTorch", canonical_name="PyTorch", category=TechCategory.AI_ML, priority_weight=1.5),
            ]
        )
    ]

    stats = MetricsEngine.aggregate(jobs, query_keywords="Data")
    # 2 out of 3 jobs have disclosed salary: 66.7%
    assert 66.0 <= stats.salary_transparency_pct <= 67.0
    assert len(stats.country_salary_data) == 2
    assert stats.country_salary_data[0]["country"] == "United States"
    assert stats.country_salary_data[0]["salary"] == 175000

    # Top hiring companies
    assert len(stats.top_hiring_companies) == 2
    assert stats.top_hiring_companies[0]["company"] == "Airbnb"
    assert stats.top_hiring_companies[0]["job_count"] == 2

    # Stack density
    assert stats.stack_density_stats["avg_skills_per_job"] > 2.0
    assert stats.stack_density_stats["median_skills"] in (2, 2.0, 3)

    # Experience salary stats
    assert "senior" in stats.experience_salary_stats
    assert stats.experience_salary_stats["senior"]["median"] == 175000
    assert "entry" in stats.experience_salary_stats
    assert stats.experience_salary_stats["entry"]["median"] == 50000

    # Workplace salary stats
    assert "remote" in stats.workplace_salary_stats
    assert stats.workplace_salary_stats["remote"]["median"] == 175000


def test_currency_manager_conversions():
    from pathlib import Path
    from stackcheck.analyzer.currency import CurrencyManager
    from stackcheck.models import SalaryInfo
    import tempfile

    with tempfile.NamedTemporaryFile(suffix=".json") as tf:
        cm = CurrencyManager(cache_file=Path(tf.name))
        
        # 1. Standard USD yearly
        assert cm.convert_to_usd(150000, "USD", period="yearly") == 150000.0

        # 2. Hourly USD conversion
        assert cm.convert_to_usd(50, "USD", period="hourly") == 50 * 2080

        # 3. Monthly USD conversion
        assert cm.convert_to_usd(10000, "USD", period="monthly") == 120000.0

        # 4. Foreign currencies
        inr_usd = cm.convert_to_usd(3000000, "INR", period="yearly")
        assert 30000 <= inr_usd <= 40000  # ~35.7k USD

        php_usd = cm.convert_to_usd(1440000, "PHP", period="yearly")
        assert 20000 <= php_usd <= 30000  # ~25.2k USD

        # 5. Smart inference when currency was defaulted to USD but amount in millions in foreign country
        crc_usd = cm.convert_to_usd(36000000, "USD", country="Costa Rica", period="yearly")
        assert 60000 <= crc_usd <= 80000  # ~70.2k USD instead of 36 million!

        # 6. SalaryInfo formatting
        sal_php = SalaryInfo(min_amount=120000, max_amount=120000, currency="PHP", period="monthly")
        assert "₱" in sal_php.formatted
        assert "/ monthly" in sal_php.formatted

        sal_usd = SalaryInfo(min_amount=150000, max_amount=180000, currency="USD", period="yearly")
        assert "$" in sal_usd.formatted


