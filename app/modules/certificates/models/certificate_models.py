"""
Certificate domain models — SQLModel entities.
"""

from datetime import date, datetime, timezone
from typing import Optional

from sqlalchemy import Column, Index, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel


class Certificate(SQLModel, table=True):
    __tablename__ = "certificates"
    __table_args__ = (
        UniqueConstraint("student_name", "course_track", "issue_date", name="uq_cert_student_track_date"),
        Index("ix_cert_cert_id", "cert_id"),
        Index("ix_cert_student_name", "student_name"),
        Index("ix_cert_course_track", "course_track"),
        Index("ix_cert_created_at", "created_at"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    cert_id: str = Field(nullable=False, unique=True, index=True)
    student_name: str = Field(nullable=False)
    course_name: str = Field(nullable=False)
    course_track: str = Field(nullable=False)
    level: str = Field(nullable=False)
    issue_date: date = Field(nullable=False)
    branch: str = Field(nullable=False)
    instructor: Optional[str] = Field(default=None, nullable=True)
    director: Optional[str] = Field(default=None, nullable=True)
    custom_color: Optional[str] = Field(default=None, nullable=True)
    revoked_at: Optional[datetime] = Field(default=None, nullable=True)
    revoked_reason: Optional[str] = Field(default=None, nullable=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class CertificateAuditLog(SQLModel, table=True):
    __tablename__ = "certificate_audit_log"
    __table_args__ = (
        Index("ix_audit_cert_id", "cert_id"),
        Index("ix_audit_timestamp", "timestamp"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    cert_id: str = Field(nullable=False, index=True)
    action: str = Field(nullable=False)  # "generated" | "revoked"
    actor_id: Optional[int] = Field(default=None, nullable=True)
    actor_name: Optional[str] = Field(default=None, nullable=True)
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    action_metadata: Optional[dict] = Field(default=None, sa_column=Column("metadata", JSONB))
