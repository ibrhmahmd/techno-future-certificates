"""
Database engine and session configuration.
"""

import logging
import os
from collections.abc import Generator

from sqlalchemy import text
from sqlmodel import Session, SQLModel, create_engine

log = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///certificates.db")

engine = create_engine(DATABASE_URL, echo=False)


def create_db_and_tables() -> None:
    """Create all tables defined by SQLModel metadata."""
    SQLModel.metadata.create_all(engine)
    _drop_unique_constraint()


_DROPPED_CONSTRAINT = False


def _drop_unique_constraint() -> None:
    """Drop the old unique constraint on (student_name, course_track, issue_date)."""
    global _DROPPED_CONSTRAINT
    if _DROPPED_CONSTRAINT:
        return
    for sql in (
        "ALTER TABLE certificates DROP CONSTRAINT IF EXISTS uq_cert_student_track_date",
        "ALTER TABLE certificates DROP CONSTRAINT uq_cert_student_track_date",
    ):
        try:
            with engine.connect() as conn:
                conn.execute(text(sql))
                conn.commit()
            log.info("Dropped unique constraint uq_cert_student_track_date")
            break
        except Exception:
            pass
    _DROPPED_CONSTRAINT = True


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency — yields a DB session, auto-closes."""
    with Session(engine) as session:
        yield session
