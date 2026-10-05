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
