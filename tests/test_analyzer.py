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
