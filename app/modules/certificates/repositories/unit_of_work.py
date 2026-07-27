"""
Certificates Unit of Work — coordinates repository transactions.
"""

from typing import Optional

from sqlmodel import Session

from app.modules.certificates.repositories.certificate_repository import CertificateRepository
from app.modules.certificates.repositories.audit_log_repository import CertificateAuditLogRepository


class CertificatesUnitOfWork:
    def __init__(self, session: Session) -> None:
        self._session = session
        self.certificates = CertificateRepository(session)
        self.audit_log = CertificateAuditLogRepository(session)

    def commit(self) -> None:
        self._session.commit()

    def flush(self) -> None:
        self._session.flush()

    def rollback(self) -> None:
        self._session.rollback()
