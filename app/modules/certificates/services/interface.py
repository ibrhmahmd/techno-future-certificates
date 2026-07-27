"""
Service interfaces — Protocol definitions for dependency inversion.
"""

from typing import Optional, Protocol, runtime_checkable

from app.modules.certificates.schemas.certificate_schemas import (
    CertificateReadDTO,
    CertificateVerifyDTO,
    GenerateCertificateInput,
    RevokeCertificateInput,
)
from app.modules.certificates.schemas.response_schemas import CertificateListResponseDTO


@runtime_checkable
class CertificateServiceInterface(Protocol):
    def generate(self, dto: GenerateCertificateInput, actor_name: Optional[str] = None) -> CertificateReadDTO: ...
    def verify(self, cert_id: str) -> Optional[CertificateVerifyDTO]: ...
    def get_by_id(self, cert_id: str) -> Optional[CertificateReadDTO]: ...
    def list_certificates(
        self,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        track: Optional[str] = None,
        include_revoked: bool = False,
    ) -> CertificateListResponseDTO: ...
    def download_pdf(self, cert_id: str) -> bytes: ...
    def download_html(self, cert_id: str) -> str: ...
    def export_csv(
        self,
        track: Optional[str] = None,
        search: Optional[str] = None,
        include_revoked: bool = False,
    ) -> bytes: ...
    def revoke(self, cert_id: str, reason: str, actor_name: Optional[str] = None) -> CertificateReadDTO: ...
