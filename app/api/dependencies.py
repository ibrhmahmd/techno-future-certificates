"""
Dependency injection factories for services.
Follows the existing get_*_service pattern.
"""

from typing import TYPE_CHECKING

from fastapi import Depends
from sqlmodel import Session

from app.database import get_db

if TYPE_CHECKING:
    from app.modules.certificates.services.certificate_crud_service import CertificateCrudService


def get_certificate_service(
    session: Session = Depends(get_db),
) -> "CertificateCrudService":
    """Create CertificateCrudService with UnitOfWork."""
    from app.modules.certificates.repositories.unit_of_work import CertificatesUnitOfWork
    from app.modules.certificates.services.certificate_crud_service import CertificateCrudService

    uow = CertificatesUnitOfWork(session)
    return CertificateCrudService(uow)
