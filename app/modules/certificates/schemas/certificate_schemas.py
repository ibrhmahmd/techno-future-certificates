"""
Certificate DTOs — input and output data transfer objects.
"""

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator

from app.modules.certificates.constants import TRACK_KEYS


class GenerateCertificateInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    student_name: str
    course_track: str
    level: str
    issue_date: date
    branch: str
    custom_color: Optional[str] = None

    @field_validator("student_name")
    @classmethod
    def validate_student_name(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Student name is required")
        return v.strip()

    @field_validator("course_track")
    @classmethod
    def validate_course_track(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Course track is required")
        return v.strip()

    @field_validator("level")
    @classmethod
    def validate_level(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Level is required")
        return v.strip()

    @field_validator("issue_date")
    @classmethod
    def validate_issue_date(cls, v: date) -> date:
        from datetime import date as date_cls
        if v > date_cls.today():
            raise ValueError("Issue date cannot be in the future")
        return v

    @field_validator("custom_color")
    @classmethod
    def validate_custom_color(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip()
        if not v:
            return None
        if not v.startswith("#") or len(v) != 7:
            raise ValueError("Custom color must be a valid hex color (e.g., #FF0000)")
        try:
            int(v[1:], 16)
        except ValueError:
            raise ValueError("Custom color must be a valid hex color")
        return v


class RevokeCertificateInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    reason: str

    @field_validator("reason")
    @classmethod
    def validate_reason(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Revocation reason is required")
        return v.strip()


class CertificateReadDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True, frozen=True)

    id: int
    cert_id: str
    student_name: str
    course_name: str
    course_track: str
    level: str
    issue_date: date
    branch: str
    custom_color: Optional[str]
    revoked_at: Optional[datetime]
    revoked_reason: Optional[str]
    created_at: datetime


class CertificateVerifyDTO(BaseModel):
    """Public verification response — excludes internal fields."""

    model_config = ConfigDict(from_attributes=True, frozen=True)

    cert_id: str
    student_name: str
    course_name: str
    level: str
    issue_date: date
    branch: str
    revoked: bool
    revoked_reason: Optional[str]
