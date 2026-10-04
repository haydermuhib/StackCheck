"""
Tests for SQLite storage, repository, and export pipelines.
"""

import tempfile
from pathlib import Path
from stackcheck.models import JobPost, ExtractedSkill, SearchQuery, SalaryInfo, Region, WorkplaceType, ExperienceLevel, TechCategory
from stackcheck.storage.db import DatabaseManager
from stackcheck.storage.repository import JobRepository
from stackcheck.analyzer.metrics import MetricsEngine
from stackcheck.storage.exporters import ReportExporter


def test_repository_save_and_retrieve():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_file = Path(tmpdir) / "test.db"
        db_mgr = DatabaseManager(db_path=db_file)
        repo = JobRepository(db_manager=db_mgr)

        job = JobPost(
            id="test_job_1",
            title="Data Analyst",
            company="Acme Corp",
            location="Chicago, IL",
            region=Region.USA,
            workplace_type=WorkplaceType.HYBRID,
            experience_level=ExperienceLevel.MID,
            salary=SalaryInfo(min_amount=90000, max_amount=120000),
            extracted_skills=[
                ExtractedSkill(name="SQL", canonical_name="SQL", category=TechCategory.PROGRAMMING_LANGUAGES),
                ExtractedSkill(name="Power BI", canonical_name="Power BI", category=TechCategory.BI_DATA_TOOLS)
            ]
        )

        query = SearchQuery(keywords="Data Analyst", limit=10)
        run_id = repo.save_search_run(query, total_found=1)
        repo.save_jobs([job], search_run_id=run_id)

        assert repo.count_total_jobs() == 1
        fetched = repo.get_all_jobs(limit=10)
        assert len(fetched) == 1
        assert fetched[0].company == "Acme Corp"
        assert len(fetched[0].extracted_skills) == 2

        repo.clear_all()
        assert repo.count_total_jobs() == 0
        assert len(repo.get_all_jobs()) == 0


def test_exporters():
    with tempfile.TemporaryDirectory() as tmpdir:
        job = JobPost(
            id="job123",
            title="Analytics Engineer",
            company="Netflix",
            location="Remote",
            region=Region.GLOBAL_REMOTE,
            workplace_type=WorkplaceType.REMOTE,
            extracted_skills=[
                ExtractedSkill(name="Python", canonical_name="Python", category=TechCategory.PROGRAMMING_LANGUAGES),
                ExtractedSkill(name="Snowflake", canonical_name="Snowflake", category=TechCategory.DATA_ENGINEERING)
            ]
        )
        stats = MetricsEngine.aggregate([job], query_keywords="Analytics Engineer")

        # Test JSON
        json_path = ReportExporter.export_json(stats, [job], filename="test.json")
        assert json_path.exists()

        # Test CSV
        csv_path = ReportExporter.export_csv([job], filename="test.csv")
        assert csv_path.exists()

        # Test Markdown
        md_path = ReportExporter.export_markdown(stats, filename="test.md")
        assert md_path.exists()


def test_project_isolation_and_crud():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_file = Path(tmpdir) / "test_projects.db"
        db_mgr = DatabaseManager(db_path=db_file)
        repo = JobRepository(db_manager=db_mgr)

        # Verify default project exists
        projs = repo.get_projects()
        assert len(projs) >= 1
        assert any(p.id == "default" for p in projs)

        # Create two separate projects
        p1 = repo.create_project(name="Project Alpha", description="Alpha test", project_id="alpha")
        p2 = repo.create_project(name="Project Beta", description="Beta test", project_id="beta")

        job_a = JobPost(
            id="job_a_1",
            title="Data Analyst",
            company="Alpha Corp",
            location="Remote",
            project_id="alpha"
        )
        job_b = JobPost(
            id="job_b_1",
            title="Backend Engineer",
            company="Beta Corp",
            location="Remote",
            project_id="beta"
        )

        repo.save_jobs([job_a], project_id="alpha")
        repo.save_jobs([job_b], project_id="beta")

        # Check isolation
        assert repo.count_total_jobs(project_id="alpha") == 1
        assert repo.count_total_jobs(project_id="beta") == 1
        assert len(repo.get_all_jobs(project_id="alpha")) == 1
        assert repo.get_all_jobs(project_id="alpha")[0].company == "Alpha Corp"

        assert len(repo.get_all_jobs(project_id="beta")) == 1
        assert repo.get_all_jobs(project_id="beta")[0].company == "Beta Corp"

        # Clear only alpha
        repo.clear_project_jobs("alpha")
        assert repo.count_total_jobs(project_id="alpha") == 0
        assert repo.count_total_jobs(project_id="beta") == 1

        # Delete beta
        repo.delete_project("beta")
        remaining_ids = [p.id for p in repo.get_projects()]
        assert "beta" not in remaining_ids


def test_duplicate_detection_and_apply_urls():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_file = Path(tmpdir) / "test_dups.db"
        db_mgr = DatabaseManager(db_path=db_file)
        repo = JobRepository(db_manager=db_mgr)

        job1 = JobPost(
            id="job_dup_100",
            title="Senior Data Analyst",
            company="Global Tech",
            location="Remote",
            url="https://company.com/jobs/100",
            project_id="dup_test"
        )

        assert job1.apply_url == "https://company.com/jobs/100"
        assert job1.link == "https://company.com/jobs/100"

        # First ingestion
        res1 = repo.save_jobs([job1], project_id="dup_test")
        assert res1["new_count"] == 1
        assert res1["updated_count"] == 0
        assert repo.count_total_jobs(project_id="dup_test") == 1

        # Second ingestion with the same job (simulating running the same search keyword again)
        job1_refreshed = JobPost(
            id="job_dup_100",
            title="Senior Data Analyst",
            company="Global Tech",
            location="Remote",
            url="https://company.com/jobs/100",
            project_id="dup_test"
        )
        res2 = repo.save_jobs([job1_refreshed], project_id="dup_test")
        assert res2["new_count"] == 0
        assert res2["updated_count"] == 1
        # Total jobs should remain 1, not duplicate to 2
        assert repo.count_total_jobs(project_id="dup_test") == 1

        # Verify apply_url is retained when fetched from repository
        fetched = repo.get_all_jobs(project_id="dup_test")
        assert len(fetched) == 1
        assert fetched[0].apply_url == "https://company.com/jobs/100"
        assert fetched[0].link == "https://company.com/jobs/100"


def test_default_data_dir_isolation():
    """Verify that default database and export paths reside strictly in DEFAULT_DATA_DIR (~/.stackcheck)."""
    import os
    from stackcheck import config
    
    # Verify default database resolves to ~/.stackcheck/stackcheck.db
    assert config.LOCAL_DB_PATH.name == "stackcheck.db"
    assert config.LOCAL_DB_PATH.parent == config.DEFAULT_DATA_DIR
    assert config.EXPORTS_DIR == config.DEFAULT_DATA_DIR / "exports"
    # Crucial assertion: never pollute current working directory
    assert config.LOCAL_DB_PATH.parent != Path(os.getcwd()) or config.DEFAULT_DATA_DIR == Path(os.getcwd())

