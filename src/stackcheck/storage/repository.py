"""
Repository for CRUD operations on Jobs, Search Runs, and Extracted Skills.
"""

import uuid
from collections import defaultdict
from typing import List, Optional, Dict, Any
from datetime import datetime
from stackcheck.models import JobPost, ExtractedSkill, SearchQuery, SalaryInfo, Region, WorkplaceType, ExperienceLevel, TechCategory, Project, AggregatedStats
from stackcheck.storage.db import DatabaseManager

VALID_CATEGORIES = {c.value for c in TechCategory}
VALID_REGIONS = {reg.value for reg in Region}
VALID_WORKPLACES = {w.value for w in WorkplaceType}
VALID_EXPERIENCES = {e.value for e in ExperienceLevel}



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
        """Fetch all projects with job and search counts and last query metadata."""
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
                pid = r["id"]
                last_run = conn.execute(
                    "SELECT keywords, location, workplace_type, experience_level, query_limit, total_found FROM search_runs WHERE project_id = ? ORDER BY created_at DESC LIMIT 1",
                    (pid,)
                ).fetchone()

                last_limit_val = None
                if last_run:
                    last_limit_val = last_run["query_limit"] if ("query_limit" in last_run.keys() and last_run["query_limit"]) else last_run["total_found"]

                projects.append(Project(
                    id=pid,
                    name=r["name"],
                    description=r["description"] or "",
                    created_at=datetime.fromisoformat(r["created_at"]) if r["created_at"] else datetime.utcnow(),
                    updated_at=datetime.fromisoformat(r["updated_at"]) if r["updated_at"] else datetime.utcnow(),
                    total_jobs=r["total_jobs"] or 0,
                    total_searches=r["total_searches"] or 0,
                    last_keywords=last_run["keywords"] if last_run else None,
                    last_location=last_run["location"] if last_run else None,
                    last_workplace=last_run["workplace_type"] if last_run else None,
                    last_experience=last_run["experience_level"] if last_run else None,
                    last_limit=last_limit_val,
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

            last_run = conn.execute(
                "SELECT keywords, location, workplace_type, experience_level, query_limit, total_found FROM search_runs WHERE project_id = ? ORDER BY created_at DESC LIMIT 1",
                (project_id,)
            ).fetchone()

            last_limit_val = None
            if last_run:
                last_limit_val = last_run["query_limit"] if ("query_limit" in last_run.keys() and last_run["query_limit"]) else last_run["total_found"]

            return Project(
                id=r["id"],
                name=r["name"],
                description=r["description"] or "",
                created_at=datetime.fromisoformat(r["created_at"]) if r["created_at"] else datetime.utcnow(),
                updated_at=datetime.fromisoformat(r["updated_at"]) if r["updated_at"] else datetime.utcnow(),
                total_jobs=r["total_jobs"] or 0,
                total_searches=r["total_searches"] or 0,
                last_keywords=last_run["keywords"] if last_run else None,
                last_location=last_run["location"] if last_run else None,
                last_workplace=last_run["workplace_type"] if last_run else None,
                last_experience=last_run["experience_level"] if last_run else None,
                last_limit=last_limit_val,
            )

    def get_project_latest_query(self, project_id: str) -> Optional[SearchQuery]:
        """Fetch the most recent SearchQuery used in this project."""
        with self.db.get_connection() as conn:
            r = conn.execute(
                "SELECT keywords, location, workplace_type, experience_level, query_limit, total_found FROM search_runs WHERE project_id = ? ORDER BY created_at DESC LIMIT 1",
                (project_id,)
            ).fetchone()
            if not r:
                return None
            wp = WorkplaceType(r["workplace_type"]) if r["workplace_type"] and r["workplace_type"] != "any" else None
            exp = ExperienceLevel(r["experience_level"]) if r["experience_level"] and r["experience_level"] != "any" else None
            q_limit = r["query_limit"] if ("query_limit" in r.keys() and r["query_limit"]) else (r["total_found"] or 25)
            return SearchQuery(
                keywords=r["keywords"] or "Data Analyst",
                location=r["location"] or "",
                workplace_type=wp,
                experience_level=exp,
                limit=q_limit,
                project_id=project_id
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
        """Clear all jobs and search runs from a specific project and invalidate cached analytics."""
        with self.db.get_connection() as conn:
            conn.execute("DELETE FROM job_skills WHERE job_id IN (SELECT id FROM jobs WHERE project_id = ?)", (project_id,))
            conn.execute("DELETE FROM jobs WHERE project_id = ?", (project_id,))
            conn.execute("DELETE FROM search_runs WHERE project_id = ?", (project_id,))
            conn.execute("DELETE FROM project_analytics_cache WHERE project_id = ?", (project_id,))
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
                INSERT INTO search_runs (id, project_id, keywords, location, region, workplace_type, experience_level, query_limit, total_found)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    active_proj,
                    query.keywords,
                    query.location,
                    query.region.value if query.region else None,
                    query.workplace_type.value if query.workplace_type else None,
                    query.experience_level.value if query.experience_level else None,
                    query.limit,
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

    def get_all_jobs(self, limit: Optional[int] = None, region: Optional[str] = None, workplace: Optional[str] = None, project_id: Optional[str] = None) -> List[JobPost]:
        """Fetch jobs with optional project and filter parameters. If limit is None, returns all matching jobs."""
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

        query_sql += " ORDER BY scraped_at DESC"
        if limit is not None and limit > 0:
            query_sql += " LIMIT ?"
            params.append(limit)

        with self.db.get_connection() as conn:
            rows = conn.execute(query_sql, params).fetchall()
            if not rows:
                return []

            job_ids = [r["id"] for r in rows]
            skills_by_job = defaultdict(list)

            # Batch fetch all skills in chunks of 500 to eliminate N+1 queries
            for i in range(0, len(job_ids), 500):
                chunk = job_ids[i:i + 500]
                placeholders = ",".join("?" for _ in chunk)
                chunk_skills = conn.execute(
                    f"SELECT job_id, name, canonical_name, category, source_section, priority_weight, context_snippet FROM job_skills WHERE job_id IN ({placeholders})",
                    chunk
                ).fetchall()
                for sr in chunk_skills:
                    cat_val = sr["category"]
                    cat_enum = TechCategory(cat_val) if cat_val in VALID_CATEGORIES else TechCategory.OTHER
                    skills_by_job[sr["job_id"]].append(
                        ExtractedSkill(
                            name=sr["name"],
                            canonical_name=sr["canonical_name"],
                            category=cat_enum,
                            source_section=sr["source_section"],
                            priority_weight=sr["priority_weight"],
                            context_snippet=sr["context_snippet"]
                        )
                    )

            jobs = []
            for r in rows:
                job_id = r["id"]
                skills = skills_by_job.get(job_id, [])

                sal_min = r["salary_min"]
                sal_max = r["salary_max"]
                salary = None
                if sal_min is not None or sal_max is not None:
                    salary = SalaryInfo(
                        min_amount=sal_min,
                        max_amount=sal_max,
                        currency=r["salary_currency"] or "USD",
                        period=r["salary_period"] or "yearly"
                    )

                clean_id = job_id
                prefix = f"{r['project_id']}_"
                if clean_id.startswith(prefix):
                    clean_id = clean_id[len(prefix):]

                reg_val = r["region"]
                reg_enum = Region(reg_val) if reg_val in VALID_REGIONS else Region.OTHER

                wp_val = r["workplace_type"]
                wp_enum = WorkplaceType(wp_val) if wp_val in VALID_WORKPLACES else WorkplaceType.UNKNOWN

                exp_val = r["experience_level"]
                exp_enum = ExperienceLevel(exp_val) if exp_val in VALID_EXPERIENCES else ExperienceLevel.MID

                jobs.append(JobPost(
                    id=clean_id,
                    project_id=r["project_id"] if "project_id" in r.keys() else "default",
                    search_run_id=r["search_run_id"] if "search_run_id" in r.keys() else None,
                    title=r["title"],
                    company=r["company"],
                    location=r["location"],
                    country=r["country"],
                    region=reg_enum,
                    workplace_type=wp_enum,
                    experience_level=exp_enum,
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
            conn.execute("DELETE FROM project_analytics_cache")
            conn.commit()

    # ------------------ ANALYTICS CACHE OPERATIONS ------------------
    def get_cached_stats(self, project_id: str, expected_job_count: int) -> Optional[AggregatedStats]:
        """
        Fetch pre-calculated analytics for a project if the job count matches.
        Returns AggregatedStats on cache hit, or None on cache miss/stale data.
        """
        with self.db.get_connection() as conn:
            row = conn.execute(
                "SELECT stats_json, job_count FROM project_analytics_cache WHERE project_id = ?",
                (project_id,)
            ).fetchone()
            if not row:
                return None
            if row["job_count"] != expected_job_count:
                return None
            try:
                return AggregatedStats.model_validate_json(row["stats_json"])
            except Exception:
                return None

    def save_cached_stats(self, project_id: str, stats: AggregatedStats, job_count: int):
        """Persist calculated analytics JSON for a project."""
        stats_json = stats.model_dump_json()
        with self.db.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO project_analytics_cache (project_id, stats_json, job_count, calculated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(project_id) DO UPDATE SET
                    stats_json = excluded.stats_json,
                    job_count = excluded.job_count,
                    calculated_at = CURRENT_TIMESTAMP
                """,
                (project_id, stats_json, job_count)
            )
            conn.commit()

    def invalidate_cached_stats(self, project_id: str):
        """Explicitly clear the cached analytics for a project."""
        with self.db.get_connection() as conn:
            conn.execute("DELETE FROM project_analytics_cache WHERE project_id = ?", (project_id,))
            conn.commit()



