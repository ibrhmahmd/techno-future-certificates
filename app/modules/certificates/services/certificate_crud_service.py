"""
Certificate CRUD service — business logic for all certificate operations.
"""

import csv
import logging
from datetime import datetime, timezone
from io import BytesIO
from typing import Optional

from app.modules.certificates.constants import TRACK_KEYS, TRACK_DATA_ATTRS
from app.modules.certificates.models.certificate_models import Certificate
from app.modules.certificates.repositories.unit_of_work import CertificatesUnitOfWork
from app.modules.certificates.schemas.certificate_schemas import (
    CertificateReadDTO,
    CertificateVerifyDTO,
    GenerateCertificateInput,
)
from app.modules.certificates.schemas.response_schemas import CertificateListResponseDTO
from app.modules.certificates.services.certificate_render_service import render_html, render_pdf
from app.modules.certificates.validators.certificate_validators import (
    generate_cert_id,
    get_track_display_name,
    get_track_color,
)

log = logging.getLogger(__name__)


class CertificateCrudService:
    def __init__(self, uow: CertificatesUnitOfWork) -> None:
        self._uow = uow

    def generate(
        self,
        dto: GenerateCertificateInput,
        actor_name: Optional[str] = None,
    ) -> CertificateReadDTO:
        """Generate a new certificate or return existing if duplicate."""
        # Check for existing certificate (unique constraint)
        existing = self._uow.certificates.get_by_unique_key(
            student_name=dto.student_name,
            course_track=dto.course_track,
            issue_date=dto.issue_date,
        )
        if existing:
            from fastapi import HTTPException
            raise HTTPException(
                status_code=409,
                detail={
                    "error": "ConflictError",
                    "message": "Certificate already exists for this student/track/date",
                    "cert_id": existing.cert_id,
                },
            )

        # Get track display name
        course_name = get_track_display_name(dto.course_track)

        # Generate unique cert ID
        cert_id = generate_cert_id(dto.course_track, dto.issue_date)

        # Create certificate record
        cert = Certificate(
            cert_id=cert_id,
            student_name=dto.student_name,
            course_name=course_name,
            course_track=dto.course_track,
            level=dto.level,
            issue_date=dto.issue_date,
            branch=dto.branch,
            instructor=dto.instructor,
            director=dto.director,
            custom_color=dto.custom_color,
            created_at=datetime.now(timezone.utc),
        )

        cert = self._uow.certificates.create(cert)
        self._uow.flush()

        # Audit log
        self._uow.audit_log.create(
            cert_id=cert_id,
            action="generated",
            actor_name=actor_name,
        )

        self._uow.commit()
        return CertificateReadDTO.model_validate(cert)

    def verify(self, cert_id: str) -> Optional[CertificateVerifyDTO]:
        """Look up a certificate by ID for public verification."""
        cert = self._uow.certificates.get_by_cert_id(cert_id)
        if not cert:
            return None

        return CertificateVerifyDTO(
            cert_id=cert.cert_id,
            student_name=cert.student_name,
            course_name=cert.course_name,
            level=cert.level,
            issue_date=cert.issue_date,
            branch=cert.branch,
            instructor=cert.instructor,
            director=cert.director,
            revoked=cert.revoked_at is not None,
            revoked_reason=cert.revoked_reason,
        )

    def get_by_id(self, cert_id: str) -> Optional[CertificateReadDTO]:
        """Look up a certificate by ID (full details, auth required)."""
        cert = self._uow.certificates.get_by_cert_id(cert_id)
        if not cert:
            return None
        return CertificateReadDTO.model_validate(cert)

    def list_certificates(
        self,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        track: Optional[str] = None,
        include_revoked: bool = False,
    ) -> CertificateListResponseDTO:
        """List certificates with pagination, search, and filter."""
        items, total = self._uow.certificates.list_paginated(
            page=page,
            page_size=page_size,
            search=search,
            track=track,
            include_revoked=include_revoked,
        )

        return CertificateListResponseDTO(
            items=[CertificateReadDTO.model_validate(cert) for cert in items],
            total=total,
            page=page,
            page_size=page_size,
        )

    def download_pdf(self, cert_id: str) -> bytes:
        """Generate PDF for a certificate."""
        cert = self._uow.certificates.get_by_cert_id(cert_id)
        if not cert:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Certificate not found")

        custom_color = cert.custom_color or get_track_color(cert.course_track)
        return render_pdf(
            student_name=cert.student_name,
            course_name=cert.course_name,
            course_track=cert.course_track,
            level=cert.level,
            issue_date=cert.issue_date,
            branch=cert.branch,
            cert_id=cert.cert_id,
            instructor=cert.instructor,
            director=cert.director,
            custom_color=custom_color,
        )

    def download_html(self, cert_id: str) -> str:
        """Generate HTML for a certificate."""
        cert = self._uow.certificates.get_by_cert_id(cert_id)
        if not cert:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Certificate not found")

        custom_color = cert.custom_color or get_track_color(cert.course_track)
        return render_html(
            student_name=cert.student_name,
            course_name=cert.course_name,
            course_track=cert.course_track,
            level=cert.level,
            issue_date=cert.issue_date,
            branch=cert.branch,
            cert_id=cert.cert_id,
            instructor=cert.instructor,
            director=cert.director,
            custom_color=custom_color,
        )

    def export_csv(
        self,
        track: Optional[str] = None,
        search: Optional[str] = None,
        include_revoked: bool = False,
    ) -> bytes:
        """Export certificates as CSV."""
        items, _ = self._uow.certificates.list_paginated(
            page=1,
            page_size=10000,
            search=search,
            track=track,
            include_revoked=include_revoked,
        )

        output = BytesIO()
        writer = csv.writer(output)
        writer.writerow([
            "cert_id", "student_name", "course_name", "level",
            "issue_date", "branch", "instructor", "director", "created_at",
        ])

        for cert in items:
            writer.writerow([
                cert.cert_id,
                cert.student_name,
                cert.course_name,
                cert.level,
                cert.issue_date.isoformat(),
                cert.branch,
                cert.instructor or "",
                cert.director or "",
                cert.created_at.isoformat(),
            ])

        return output.getvalue()

    def revoke(
        self,
        cert_id: str,
        reason: str,
        actor_name: Optional[str] = None,
    ) -> CertificateReadDTO:
        """Revoke a certificate."""
        cert = self._uow.certificates.get_by_cert_id(cert_id)
        if not cert:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Certificate not found")

        if cert.revoked_at is not None:
            from fastapi import HTTPException
            raise HTTPException(
                status_code=409,
                detail="Certificate is already revoked",
            )

        updated = self._uow.certificates.update(
            cert_id,
            revoked_at=datetime.now(timezone.utc),
            revoked_reason=reason,
        )

        self._uow.audit_log.create(
            cert_id=cert_id,
            action="revoked",
            actor_name=actor_name,
            action_metadata={"reason": reason},
        )

        self._uow.commit()
        return CertificateReadDTO.model_validate(updated)
