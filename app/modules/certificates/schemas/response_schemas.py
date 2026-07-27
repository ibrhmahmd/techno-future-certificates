"""
Certificate response schemas — paginated and wrapped responses.
"""

from pydantic import BaseModel, ConfigDict

from app.modules.certificates.schemas.certificate_schemas import CertificateReadDTO


class CertificateListResponseDTO(BaseModel):
    model_config = ConfigDict(frozen=True)

    items: list[CertificateReadDTO]
    total: int
    page: int
    page_size: int
