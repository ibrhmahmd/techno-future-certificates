"""
Certificate repository — CRUD operations for Certificate entity.
"""

from datetime import date
from typing import Any, Optional

from sqlalchemy import func
from sqlmodel import Session, col, select

from app.modules.certificates.models.certificate_models import Certificate


class CertificateRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, certificate: Certificate) -> Certificate:
        self._session.add(certificate)
        self._session.flush()
        return certificate

    def get_by_cert_id(self, cert_id: str) -> Optional[Certificate]:
        return self._exec_one(
            select(Certificate).where(Certificate.cert_id == cert_id)
        )

    def _exec_one(self, stmt: Any) -> Optional[Certificate]:
        results = self._session.exec(stmt)
        return results.first()

    def get_by_unique_key(
        self, student_name: str, course_track: str, issue_date: date
    ) -> Optional[Certificate]:
        stmt = select(Certificate).where(
            Certificate.student_name == student_name,
            Certificate.course_track == course_track,
            Certificate.issue_date == issue_date,
        )
        return self._exec_one(stmt)

    def list_paginated(
        self,
        page: int,
        page_size: int,
        search: Optional[str] = None,
        track: Optional[str] = None,
        include_revoked: bool = False,
    ) -> tuple[list[Certificate], int]:
        stmt = select(Certificate)

        if not include_revoked:
            stmt = stmt.where(Certificate.revoked_at.is_(None))

        if search:
            pattern = f"%{search}%"
            stmt = stmt.where(
                Certificate.student_name.ilike(pattern)
                | Certificate.cert_id.ilike(pattern)
            )

        if track:
            stmt = stmt.where(Certificate.course_track == track)

        # Get total count
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = self._session.exec(count_stmt).one()

        # Apply pagination
        stmt = stmt.order_by(Certificate.created_at.desc())
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)

        results = self._session.exec(stmt)
        items = list(results.all())

        return items, total

    def update(self, cert_id: str, **kwargs: Any) -> Optional[Certificate]:
        cert = self.get_by_cert_id(cert_id)
        if not cert:
            return None
        for key, value in kwargs.items():
            setattr(cert, key, value)
        self._session.add(cert)
        self._session.flush()
        return cert
