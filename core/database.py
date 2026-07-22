"""
SQLite database layer for certificate records.
Pure Python, zero Streamlit imports.
"""

import datetime
import sqlite3

from core.config import DB_PATH


def init_db():
    conn = sqlite3.connect(DB_PATH)
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
    columns = [row[1] for row in c.fetchall()]

    if "branch" not in columns:
        if "center" in columns:
            c.execute("ALTER TABLE certificates RENAME COLUMN center TO branch")
        else:
            c.execute(
                "ALTER TABLE certificates ADD COLUMN branch TEXT NOT NULL DEFAULT 'Main Branch'"
            )

    if "instructor" not in columns:
        c.execute(
            "ALTER TABLE certificates ADD COLUMN instructor TEXT NOT NULL DEFAULT 'Instructor'"
        )

    if "director" not in columns:
        c.execute(
            "ALTER TABLE certificates ADD COLUMN director TEXT NOT NULL DEFAULT 'Academic Director'"
        )

    if "level" not in columns:
        c.execute(
            "ALTER TABLE certificates ADD COLUMN level TEXT NOT NULL DEFAULT 'Level 1'"
        )

    if "issue_date" not in columns:
        c.execute(
            "ALTER TABLE certificates ADD COLUMN issue_date TEXT NOT NULL DEFAULT ''"
        )

    if "created_at" not in columns:
        c.execute(
            "ALTER TABLE certificates ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
        )

    conn.commit()
    conn.close()


def save_certificate(
    cert_id: str,
    student_name: str,
    course_name: str,
    level: str,
    issue_date: datetime.date,
    branch: str,
    instructor: str,
    director: str,
):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        """
        INSERT OR REPLACE INTO certificates
        (cert_id, student_name, course_name, level, issue_date, branch, instructor, director)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """,
        (
            cert_id,
            student_name,
            course_name,
            level,
            str(issue_date),
            branch,
            instructor,
            director,
        ),
    )
    conn.commit()
    conn.close()


def get_certificate(cert_id: str):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM certificates WHERE cert_id = ?", (cert_id.strip(),))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None


def list_certificates():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute(
        "SELECT cert_id, student_name, course_name, level, issue_date, "
        "branch, instructor, director, created_at "
        "FROM certificates ORDER BY created_at DESC"
    )
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]


init_db()
