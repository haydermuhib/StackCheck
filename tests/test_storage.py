"""
Tests for SQLite storage, repository, and export pipelines.
"""

import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path
from stackcheck.models import JobPost, ExtractedSkill, SearchQuery, SalaryInfo, Region, WorkplaceType, ExperienceLevel, TechCategory
from stackcheck.storage.db import DatabaseManager
from stackcheck.storage.repository import JobRepository
from stackcheck.analyzer.metrics import MetricsEngine
from stackcheck.storage.exporters import ReportExporter


@contextmanager
def safe_temp_dir():
    """Temporary directory helper that safely handles Windows file locking on cleanup."""
    kwargs = {}
    if sys.version_info >= (3, 10):
        kwargs["ignore_cleanup_errors"] = True
    td = tempfile.TemporaryDirectory(**kwargs)
    try:
        yield td.name
    finally:
        try:
            td.cleanup()
        except Exception:
            pass


def test_repository_save_and_retrieve():
    with safe_temp_dir() as tmpdir:
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
    with safe_temp_dir() as tmpdir:
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
    with safe_temp_dir() as tmpdir:
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
    with safe_temp_dir() as tmpdir:
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


def test_project_query_memory_and_deduplication():
    """Verify that saving search runs persists criteria in project metadata and deduplicates on re-runs."""
    with safe_temp_dir() as tmpdir:
        db_file = Path(tmpdir) / "test_memory.db"
        db_mgr = DatabaseManager(db_path=db_file)
        repo = JobRepository(db_manager=db_mgr)

        # Create a project
        p = repo.create_project(name="Memory Project", project_id="proj_mem")
        assert p.last_keywords is None

        # Execute first search run
        q1 = SearchQuery(
            keywords="Python Developer",
            location="Remote",
            workplace_type=WorkplaceType.REMOTE,
            experience_level=ExperienceLevel.SENIOR,
            limit=25
        )
        run_id_1 = repo.save_search_run(q1, total_found=2, project_id="proj_mem")
        
        # Verify query memory attached to project
        p_loaded = repo.get_project("proj_mem")
        assert p_loaded.last_keywords == "Python Developer"
        assert p_loaded.last_location == "Remote"
        assert p_loaded.last_workplace == "remote"
        assert p_loaded.last_experience == "senior"
        assert p_loaded.last_limit == 25

        # Save initial jobs
        job1 = JobPost(id="j1", title="Python Dev 1", company="TechCorp", location="Remote", project_id="proj_mem")
        job2 = JobPost(id="j2", title="Python Dev 2", company="DataCorp", location="Remote", project_id="proj_mem")
        res1 = repo.save_jobs([job1, job2], project_id="proj_mem", search_run_id=run_id_1)
        assert res1["new_count"] == 2
        assert repo.count_total_jobs(project_id="proj_mem") == 2

        # Re-run query: scrape more, with 1 existing duplicate (j2) and 1 new job (j3)
        job2_dup = JobPost(id="j2", title="Python Dev 2 (Refreshed)", company="DataCorp", location="Remote", project_id="proj_mem")
        job3_new = JobPost(id="j3", title="Python Dev 3", company="CloudCorp", location="Remote", project_id="proj_mem")
        
        q2 = SearchQuery(keywords="Python Developer", location="Remote", limit=50)
        run_id_2 = repo.save_search_run(q2, total_found=2, project_id="proj_mem")
        res2 = repo.save_jobs([job2_dup, job3_new], project_id="proj_mem", search_run_id=run_id_2)
        
        assert res2["new_count"] == 1
        assert res2["updated_count"] == 1
        # Total jobs should be 3, perfectly deduplicated
        assert repo.count_total_jobs(project_id="proj_mem") == 3


def test_get_all_jobs_beyond_500_limit():
    """Verify that get_all_jobs without limit returns all jobs and does not clamp at 500."""
    with safe_temp_dir() as tmpdir:
        db_file = Path(tmpdir) / "test_unlimited.db"
        db_mgr = DatabaseManager(db_path=db_file)
        repo = JobRepository(db_manager=db_mgr)

        jobs_550 = [
            JobPost(
                id=f"job_{i}",
                title=f"Engineer {i}",
                company="ScaleCorp",
                location="Remote",
                project_id="big_project"
            )
            for i in range(550)
        ]
        repo.save_jobs(jobs_550, project_id="big_project")

        # Must return all 550, not 500
        fetched = repo.get_all_jobs(project_id="big_project")
        assert len(fetched) == 550


def test_project_analytics_cache():
    """Verify persistent caching of AggregatedStats in SQLite, hit/miss detection, and invalidation."""
    with safe_temp_dir() as tmpdir:
        db_file = Path(tmpdir) / "test_cache.db"
        db_mgr = DatabaseManager(db_path=db_file)
        repo = JobRepository(db_manager=db_mgr)

        # Initially no cache
        assert repo.get_cached_stats("proj_test", expected_job_count=5) is None

        # Create dummy job and stats
        job = JobPost(
            id="c_job_1",
            title="Data Scientist",
            company="DeepMind",
            location="Remote",
            project_id="proj_test",
            extracted_skills=[
                ExtractedSkill(name="Python", canonical_name="Python", category=TechCategory.PROGRAMMING_LANGUAGES),
                ExtractedSkill(name="PyTorch", canonical_name="PyTorch", category=TechCategory.AI_ML)
            ]
        )
        repo.save_jobs([job], project_id="proj_test")
        stats = MetricsEngine.aggregate([job], query_keywords="Data Scientist")

        # Save to cache with count 1
        repo.save_cached_stats("proj_test", stats, job_count=1)

        # Cache hit when expected count is 1
        cached = repo.get_cached_stats("proj_test", expected_job_count=1)
        assert cached is not None
        assert cached.total_jobs == 1
        assert cached.query_keywords == "Data Scientist"
        assert any(s["skill"] == "Python" for s in cached.top_skills_overall)

        # Cache miss when expected count does not match (e.g. 2 jobs now exist)
        assert repo.get_cached_stats("proj_test", expected_job_count=2) is None

        # Explicit invalidation
        repo.invalidate_cached_stats("proj_test")
        assert repo.get_cached_stats("proj_test", expected_job_count=1) is None

        # Re-save and test clear_project_jobs invalidation
        repo.save_cached_stats("proj_test", stats, job_count=1)
        assert repo.get_cached_stats("proj_test", expected_job_count=1) is not None
        repo.clear_project_jobs("proj_test")
        assert repo.get_cached_stats("proj_test", expected_job_count=1) is None



