"""
Certificate audit log repository — tracks state-changing operations.
"""

from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Session, select

from app.modules.certificates.models.certificate_models import CertificateAuditLog


class CertificateAuditLogRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create(
        self,
        cert_id: str,
        action: str,
        actor_id: Optional[int] = None,
        actor_name: Optional[str] = None,
        action_metadata: Optional[dict] = None,
    ) -> CertificateAuditLog:
        log = CertificateAuditLog(
            cert_id=cert_id,
            action=action,
            actor_id=actor_id,
            actor_name=actor_name,
            timestamp=datetime.now(timezone.utc),
            action_metadata=action_metadata,
        )
        self._session.add(log)
        self._session.flush()
        return log

    def list_by_cert_id(self, cert_id: str) -> list[CertificateAuditLog]:
        stmt = select(CertificateAuditLog).where(
            CertificateAuditLog.cert_id == cert_id
        ).order_by(CertificateAuditLog.timestamp.desc())
        results = self._session.exec(stmt)
        return list(results.all())
