"""
Certificate Service Module

Vertical slice for certificate generation, verification, registry, and cross-system integration.

Usage from other modules:
    from app.modules.certificates import CertificateService, CertificatesUnitOfWork
    from app.modules.certificates.schemas import GenerateCertificateInput

    uow = CertificatesUnitOfWork(session)
    service = CertificateService(uow)
    dto = service.generate(GenerateCertificateInput(...), actor=current_user)
    # dto.cert_id can be passed to Notifications module
"""

from app.modules.certificates.services.certificate_crud_service import CertificateCrudService
from app.modules.certificates.repositories.unit_of_work import CertificatesUnitOfWork
from app.modules.certificates.schemas.certificate_schemas import (
    GenerateCertificateInput,
    RevokeCertificateInput,
    CertificateReadDTO,
    CertificateVerifyDTO,
)
from app.modules.certificates.schemas.response_schemas import CertificateListResponseDTO
from app.modules.certificates.constants import TRACKS, LEVELS, Permissions

# Alias for convenience
CertificateService = CertificateCrudService

__all__ = [
    "CertificateService",
    "CertificateCrudService",
    "CertificatesUnitOfWork",
    "GenerateCertificateInput",
    "RevokeCertificateInput",
    "CertificateReadDTO",
    "CertificateVerifyDTO",
    "CertificateListResponseDTO",
    "TRACKS",
    "LEVELS",
    "Permissions",
]
