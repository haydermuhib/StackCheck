"""
Repository for CRUD operations on Jobs, Search Runs, and Extracted Skills.
"""

import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime
from stackcheck.models import JobPost, ExtractedSkill, SearchQuery, SalaryInfo, Region, WorkplaceType, ExperienceLevel, TechCategory, Project
from stackcheck.storage.db import DatabaseManager


class JobRepository:
    """Data access object for projects, jobs, and analytics."""

    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        self.db = db_manager or DatabaseManager()

    # ------------------ PROJECT OPERATIONS ------------------
    def create_project(self, name: str, description: str = "", project_id: Optional[str] = None) -> Project:
        pid = project_id.strip() if project_id else str(uuid.uuid4())[:8]
        with self.db.get_connection() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO projects (id, name, description) VALUES (?, ?, ?)",
                (pid, name.strip(), description.strip())
            )
            conn.commit()
        return Project(id=pid, name=name.strip(), description=description.strip())

    def get_projects(self) -> List[Project]:
        """Fetch all projects with job and search counts."""
        with self.db.get_connection() as conn:
            query = """
            SELECT p.id, p.name, p.description, p.created_at, p.updated_at,
                   COUNT(DISTINCT j.id) as total_jobs,
                   COUNT(DISTINCT s.id) as total_searches
            FROM projects p
            LEFT JOIN jobs j ON j.project_id = p.id
            LEFT JOIN search_runs s ON s.project_id = p.id
            GROUP BY p.id
            ORDER BY p.created_at ASC
            """
            rows = conn.execute(query).fetchall()
            projects = []
            for r in rows:
                projects.append(Project(
                    id=r["id"],
                    name=r["name"],
                    description=r["description"] or "",
                    created_at=datetime.fromisoformat(r["created_at"]) if r["created_at"] else datetime.utcnow(),
                    updated_at=datetime.fromisoformat(r["updated_at"]) if r["updated_at"] else datetime.utcnow(),
                    total_jobs=r["total_jobs"] or 0,
                    total_searches=r["total_searches"] or 0
                ))
            return projects

    def get_project(self, project_id: str) -> Optional[Project]:
        with self.db.get_connection() as conn:
            query = """
            SELECT p.id, p.name, p.description, p.created_at, p.updated_at,
                   COUNT(DISTINCT j.id) as total_jobs,
                   COUNT(DISTINCT s.id) as total_searches
            FROM projects p
            LEFT JOIN jobs j ON j.project_id = p.id
            LEFT JOIN search_runs s ON s.project_id = p.id
            WHERE p.id = ?
            GROUP BY p.id
            """
            r = conn.execute(query, (project_id,)).fetchone()
            if not r:
                return None
            return Project(
                id=r["id"],
                name=r["name"],
                description=r["description"] or "",
                created_at=datetime.fromisoformat(r["created_at"]) if r["created_at"] else datetime.utcnow(),
                updated_at=datetime.fromisoformat(r["updated_at"]) if r["updated_at"] else datetime.utcnow(),
                total_jobs=r["total_jobs"] or 0,
                total_searches=r["total_searches"] or 0
            )

    def delete_project(self, project_id: str) -> bool:
        if project_id == "default":
            # Don't delete default project, just clear its jobs
            self.clear_project_jobs("default")
            return False
        with self.db.get_connection() as conn:
            conn.execute("DELETE FROM job_skills WHERE job_id IN (SELECT id FROM jobs WHERE project_id = ?)", (project_id,))
            conn.execute("DELETE FROM jobs WHERE project_id = ?", (project_id,))
            conn.execute("DELETE FROM search_runs WHERE project_id = ?", (project_id,))
            conn.execute("DELETE FROM projects WHERE id = ?", (project_id,))
            conn.commit()
            return True

    def clear_project_jobs(self, project_id: str):
        """Clear all jobs and search runs from a specific project."""
        with self.db.get_connection() as conn:
            conn.execute("DELETE FROM job_skills WHERE job_id IN (SELECT id FROM jobs WHERE project_id = ?)", (project_id,))
            conn.execute("DELETE FROM jobs WHERE project_id = ?", (project_id,))
            conn.execute("DELETE FROM search_runs WHERE project_id = ?", (project_id,))
            conn.commit()

    # ------------------ JOB & SEARCH OPERATIONS ------------------
    def save_search_run(self, query: SearchQuery, total_found: int, project_id: Optional[str] = None) -> str:
        run_id = str(uuid.uuid4())
        active_proj = project_id or getattr(query, "project_id", "default") or "default"
        with self.db.get_connection() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO projects (id, name, description) VALUES (?, ?, ?)",
                (active_proj, active_proj, "Workspace")
            )
            conn.execute(
                """
                INSERT INTO search_runs (id, project_id, keywords, location, region, workplace_type, experience_level, total_found)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    active_proj,
                    query.keywords,
                    query.location,
                    query.region.value if query.region else None,
                    query.workplace_type.value if query.workplace_type else None,
                    query.experience_level.value if query.experience_level else None,
                    total_found
                )
            )
            conn.commit()
        return run_id

    def save_jobs(self, jobs: List[JobPost], search_run_id: Optional[str] = None, project_id: Optional[str] = None) -> Dict[str, int]:
        """Batch upsert jobs and their extracted skills within a project. Returns {'new_count': X, 'updated_count': Y}."""
        if not jobs:
            return {"new_count": 0, "updated_count": 0}

        new_count = 0
        updated_count = 0

        with self.db.get_connection() as conn:
            for job in jobs:
                active_proj = project_id or getattr(job, "project_id", "default") or "default"
                conn.execute(
                    "INSERT OR IGNORE INTO projects (id, name, description) VALUES (?, ?, ?)",
                    (active_proj, active_proj, "Workspace")
                )
                scoped_job_id = f"{active_proj}_{job.id}" if not job.id.startswith(f"{active_proj}_") else job.id

                existing = conn.execute("SELECT id FROM jobs WHERE id = ? AND project_id = ?", (scoped_job_id, active_proj)).fetchone()
                if existing:
                    updated_count += 1
                else:
                    new_count += 1

                sal_min = job.salary.min_amount if job.salary else None
                sal_max = job.salary.max_amount if job.salary else None
                sal_curr = job.salary.currency if job.salary else "USD"
                sal_per = job.salary.period if job.salary else "yearly"

                conn.execute(
                    """
                    INSERT OR REPLACE INTO jobs 
                    (id, project_id, search_run_id, title, company, location, country, region, workplace_type, experience_level,
                     salary_min, salary_max, salary_currency, salary_period, url, description, source, scraped_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        scoped_job_id,
                        active_proj,
                        search_run_id,
                        job.title,
                        job.company,
                        job.location,
                        job.country,
                        job.region.value,
                        job.workplace_type.value,
                        job.experience_level.value,
                        sal_min,
                        sal_max,
                        sal_curr,
                        sal_per,
                        job.link,
                        job.description,
                        job.source,
                        job.scraped_at.isoformat()
                    )
                )

                # Delete previous skills for this job if updating
                conn.execute("DELETE FROM job_skills WHERE job_id = ?", (scoped_job_id,))

                # Insert extracted skills
                for skill in job.extracted_skills:
                    conn.execute(
                        """
                        INSERT INTO job_skills 
                        (job_id, name, canonical_name, category, source_section, priority_weight, context_snippet)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            scoped_job_id,
                            skill.name,
                            skill.canonical_name,
                            skill.category.value,
                            skill.source_section,
                            skill.priority_weight,
                            skill.context_snippet
                        )
                    )
            conn.commit()
        return {"new_count": new_count, "updated_count": updated_count}

    def get_all_jobs(self, limit: int = 500, region: Optional[str] = None, workplace: Optional[str] = None, project_id: Optional[str] = None) -> List[JobPost]:
        """Fetch jobs with optional project and filter parameters."""
        query_sql = "SELECT * FROM jobs WHERE 1=1"
        params = []

        if project_id:
            query_sql += " AND project_id = ?"
            params.append(project_id)
        if region and region != "All":
            query_sql += " AND region = ?"
            params.append(region)
        if workplace and workplace != "All":
            query_sql += " AND workplace_type = ?"
            params.append(workplace)

        query_sql += " ORDER BY scraped_at DESC LIMIT ?"
        params.append(limit)

        with self.db.get_connection() as conn:
            rows = conn.execute(query_sql, params).fetchall()
            jobs = []
            for r in rows:
                job_id = r["id"]
                # Fetch skills for this job
                skill_rows = conn.execute("SELECT * FROM job_skills WHERE job_id = ?", (job_id,)).fetchall()
                skills = [
                    ExtractedSkill(
                        name=sr["name"],
                        canonical_name=sr["canonical_name"],
                        category=TechCategory(sr["category"]) if sr["category"] in [c.value for c in TechCategory] else TechCategory.OTHER,
                        source_section=sr["source_section"],
                        priority_weight=sr["priority_weight"],
                        context_snippet=sr["context_snippet"]
                    )
                    for sr in skill_rows
                ]

                salary = None
                if r["salary_min"] or r["salary_max"]:
                    salary = SalaryInfo(
                        min_amount=r["salary_min"],
                        max_amount=r["salary_max"],
                        currency=r["salary_currency"],
                        period=r["salary_period"]
                    )

                clean_id = job_id
                prefix = f"{r['project_id']}_"
                if clean_id.startswith(prefix):
                    clean_id = clean_id[len(prefix):]

                jobs.append(JobPost(
                    id=clean_id,
                    project_id=r["project_id"] if "project_id" in r.keys() else "default",
                    search_run_id=r["search_run_id"] if "search_run_id" in r.keys() else None,
                    title=r["title"],
                    company=r["company"],
                    location=r["location"],
                    country=r["country"],
                    region=Region(r["region"]) if r["region"] in [reg.value for reg in Region] else Region.OTHER,
                    workplace_type=WorkplaceType(r["workplace_type"]) if r["workplace_type"] in [w.value for w in WorkplaceType] else WorkplaceType.UNKNOWN,
                    experience_level=ExperienceLevel(r["experience_level"]) if r["experience_level"] in [e.value for e in ExperienceLevel] else ExperienceLevel.MID,
                    salary=salary,
                    description=r["description"],
                    url=r["url"],
                    apply_url=r["url"],
                    source=r["source"],
                    scraped_at=datetime.fromisoformat(r["scraped_at"]) if r["scraped_at"] else datetime.utcnow(),
                    extracted_skills=skills
                ))
            return jobs

    def count_total_jobs(self, project_id: Optional[str] = None) -> int:
        with self.db.get_connection() as conn:
            if project_id:
                row = conn.execute("SELECT COUNT(*) as cnt FROM jobs WHERE project_id = ?", (project_id,)).fetchone()
            else:
                row = conn.execute("SELECT COUNT(*) as cnt FROM jobs").fetchone()
            return row["cnt"] if row else 0

    def get_search_runs(self, limit: int = 25, project_id: Optional[str] = None) -> List[Dict[str, Any]]:
        with self.db.get_connection() as conn:
            if project_id:
                rows = conn.execute("SELECT * FROM search_runs WHERE project_id = ? ORDER BY created_at DESC LIMIT ?", (project_id, limit)).fetchall()
            else:
                rows = conn.execute("SELECT * FROM search_runs ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
            return [dict(r) for r in rows]

    def clear_all(self):
        """Clear all cached jobs, skills, and search runs across all projects."""
        with self.db.get_connection() as conn:
            conn.execute("DELETE FROM job_skills")
            conn.execute("DELETE FROM jobs")
            conn.execute("DELETE FROM search_runs")
            conn.commit()


