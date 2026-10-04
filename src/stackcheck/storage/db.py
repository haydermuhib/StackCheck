"""
SQLite Database Schema and Connection Manager for StackCheck.
"""

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from stackcheck.config import LOCAL_DB_PATH


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS projects (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS search_runs (
    id TEXT PRIMARY KEY,
    project_id TEXT DEFAULT 'default',
    keywords TEXT NOT NULL,
    location TEXT,
    region TEXT,
    workplace_type TEXT,
    experience_level TEXT,
    total_found INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS jobs (
    id TEXT PRIMARY KEY,
    project_id TEXT DEFAULT 'default',
    search_run_id TEXT,
    title TEXT NOT NULL,
    company TEXT NOT NULL,
    location TEXT,
    country TEXT,
    region TEXT,
    workplace_type TEXT,
    experience_level TEXT,
    salary_min REAL,
    salary_max REAL,
    salary_currency TEXT DEFAULT 'USD',
    salary_period TEXT DEFAULT 'yearly',
    url TEXT,
    description TEXT,
    source TEXT DEFAULT 'hiringcafe',
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY (search_run_id) REFERENCES search_runs(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS job_skills (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id TEXT NOT NULL,
    name TEXT NOT NULL,
    canonical_name TEXT NOT NULL,
    category TEXT NOT NULL,
    source_section TEXT DEFAULT 'general',
    priority_weight REAL DEFAULT 1.0,
    context_snippet TEXT,
    FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS community_sync_log (
    id TEXT PRIMARY KEY,
    sync_type TEXT NOT NULL,
    status TEXT NOT NULL,
    records_synced INTEGER DEFAULT 0,
    synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

INDEXES_SQL = """
CREATE INDEX IF NOT EXISTS idx_jobs_project ON jobs(project_id);
CREATE INDEX IF NOT EXISTS idx_search_runs_project ON search_runs(project_id);
CREATE INDEX IF NOT EXISTS idx_jobs_region ON jobs(region);
CREATE INDEX IF NOT EXISTS idx_jobs_workplace ON jobs(workplace_type);
CREATE INDEX IF NOT EXISTS idx_job_skills_canonical ON job_skills(canonical_name);
CREATE INDEX IF NOT EXISTS idx_job_skills_category ON job_skills(category);
"""


class DatabaseManager:
    """Manages SQLite connection lifecycle and schema migrations."""

    def __init__(self, db_path: Path = LOCAL_DB_PATH):
        self.db_path = db_path
        self.init_db()

    @contextmanager
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
        finally:
            conn.close()

    def init_db(self):
        """Execute migration schema if tables do not exist and ensure project_id columns."""
        with self.get_connection() as conn:
            conn.executescript(SCHEMA_SQL)
            
            # Migration check: Ensure project_id column exists for existing databases
            for table in ["search_runs", "jobs"]:
                cursor = conn.execute(f"PRAGMA table_info({table})")
                cols = [row["name"] for row in cursor.fetchall()]
                if cols and "project_id" not in cols:
                    conn.execute(f"ALTER TABLE {table} ADD COLUMN project_id TEXT DEFAULT 'default'")
            
            # Create indexes now that all columns are guaranteed to exist
            conn.executescript(INDEXES_SQL)

            # Ensure default project exists
            conn.execute(
                "INSERT OR IGNORE INTO projects (id, name, description) VALUES ('default', 'Default Workspace', 'General tech stack research and job market intelligence.')"
            )
            conn.commit()
