"""
SQLite database layer for certificate records.
Pure Python, zero Streamlit imports.
"""

import datetime
import logging
import sqlite3
from typing import Optional

from core.config import DB_PATH

log = logging.getLogger(__name__)


def init_db() -> None:
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS certificates (
                cert_id TEXT PRIMARY KEY,
                student_name TEXT NOT NULL,
                course_name TEXT NOT NULL,
                level TEXT NOT NULL,
                issue_date TEXT NOT NULL,
                branch TEXT NOT NULL,
                instructor TEXT NOT NULL,
                director TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        c.execute("PRAGMA table_info(certificates)")
        columns = {row[1] for row in c.fetchall()}

        migrations = {
            ("branch", "center"): "ALTER TABLE certificates RENAME COLUMN center TO branch",
            ("branch",): "ALTER TABLE certificates ADD COLUMN branch TEXT NOT NULL DEFAULT 'Main Branch'",
            ("instructor",): "ALTER TABLE certificates ADD COLUMN instructor TEXT NOT NULL DEFAULT 'Instructor'",
            ("director",): "ALTER TABLE certificates ADD COLUMN director TEXT NOT NULL DEFAULT 'Academic Director'",
            ("level",): "ALTER TABLE certificates ADD COLUMN level TEXT NOT NULL DEFAULT 'Level 1'",
            ("issue_date",): "ALTER TABLE certificates ADD COLUMN issue_date TEXT NOT NULL DEFAULT ''",
            ("created_at",): "ALTER TABLE certificates ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
        }

        for (needed, *depends), sql in migrations.items():
            if needed not in columns:
                if not depends or depends[0] in columns:
                    c.execute(sql)


def save_certificate(
    cert_id: str,
    student_name: str,
    course_name: str,
    level: str,
    issue_date: datetime.date,
    branch: str,
    instructor: str,
    director: str,
) -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO certificates
            (cert_id, student_name, course_name, level, issue_date, branch, instructor, director)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (cert_id, student_name, course_name, level, str(issue_date), branch, instructor, director),
        )


def get_certificate(cert_id: str) -> Optional[dict]:
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT * FROM certificates WHERE cert_id = ?", (cert_id.strip(),)
        ).fetchone()
        return dict(row) if row else None


def list_certificates() -> list[dict]:
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT cert_id, student_name, course_name, level, issue_date, "
            "branch, instructor, director, created_at "
            "FROM certificates ORDER BY created_at DESC"
        ).fetchall()
        return [dict(r) for r in rows]


init_db()
