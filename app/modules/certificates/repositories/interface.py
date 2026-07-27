"""
Repository interfaces — Protocol definitions for dependency inversion.
"""

from datetime import date
from typing import Optional, Protocol, runtime_checkable

from sqlmodel import Session

from app.modules.certificates.models.certificate_models import Certificate


@runtime_checkable
class CertificateRepositoryInterface(Protocol):
    def create(self, certificate: Certificate) -> Certificate: ...
    def get_by_cert_id(self, cert_id: str) -> Optional[Certificate]: ...
    def get_by_unique_key(self, student_name: str, course_track: str, issue_date: date) -> Optional[Certificate]: ...
    def list_paginated(
        self,
        page: int,
        page_size: int,
        search: Optional[str],
        track: Optional[str],
        include_revoked: bool,
    ) -> tuple[list[Certificate], int]: ...
    def update(self, cert_id: str, **kwargs: object) -> Optional[Certificate]: ...
