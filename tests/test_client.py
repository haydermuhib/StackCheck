"""
Tests for HiringCafe client and job ingestion pipeline.
"""

from stackcheck.models import SearchQuery, JobPost, WorkplaceType, ExperienceLevel
from stackcheck.client.hiringcafe import HiringCafeClient
from stackcheck.client.normalizer import JobNormalizer
from stackcheck.analyzer.rule_extractor import RuleExtractor


def test_hiringcafe_client_structure():
    client = HiringCafeClient(use_llm_if_available=False)
    assert client.session is not None
    assert client.rule_extractor is not None


def test_hiringcafe_job_parsing():
    # Test real v5 payload parsing logic
    sample_raw = {
        "apply_url": "https://example.com/apply",
        "job_information": {
            "title": "Staff Data Engineer",
            "company_name": "Databricks",
            "description": "What we are looking for:\n• Advanced Python, SQL, and Apache Spark\n• Databricks and Snowflake",
            "location": "San Francisco, CA"
        },
        "v5_processed_job_data": {
            "core_job_title": "Staff Data Engineer",
            "company_name": "Databricks",
            "technical_tools": ["Python", "SQL", "Spark", "Snowflake", "Databricks"],
            "requirements_summary": "Expert in Python, SQL, and Apache Spark with Snowflake experience.",
            "formatted_workplace_location": "San Francisco, CA",
            "workplace_type": "Remote",
            "yearly_min_compensation": 180000,
            "yearly_max_compensation": 240000,
            "listed_compensation_currency": "USD"
        }
    }

    client = HiringCafeClient()
    extractor = RuleExtractor()
    desc = sample_raw["job_information"]["description"]
    skills, req_b, task_b = extractor.process_job_description(desc)

    assert len(skills) >= 3
    skill_names = [s.canonical_name for s in skills]
    assert "Python" in skill_names
    assert "SQL" in skill_names


def test_location_normalization():
    assert JobNormalizer.normalize_location_query("pk") == "Pakistan"
    assert JobNormalizer.normalize_location_query("lahore") == "Pakistan"
    assert JobNormalizer.normalize_location_query("indai") == "India"
    assert JobNormalizer.normalize_location_query("bangalore") == "India"
    assert JobNormalizer.normalize_location_query("nz") == "New Zealand"
    assert JobNormalizer.normalize_location_query("brasil") == "Brazil"
    assert JobNormalizer.normalize_location_query("tokyo") == "Japan"
    assert JobNormalizer.normalize_location_query("korea") == "South Korea"
    assert JobNormalizer.normalize_location_query("amercia") == "United States"

