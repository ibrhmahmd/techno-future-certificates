"""
Certificate API endpoints.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import HTMLResponse, Response, StreamingResponse
from sqlmodel import Session

from app.modules.certificates.constants import Permissions
from app.modules.certificates.repositories.unit_of_work import CertificatesUnitOfWork
from app.modules.certificates.schemas.certificate_schemas import (
    CertificateReadDTO,
    CertificateVerifyDTO,
    GenerateCertificateInput,
    RevokeCertificateInput,
)
from app.modules.certificates.schemas.response_schemas import CertificateListResponseDTO
from app.modules.certificates.services.certificate_crud_service import CertificateCrudService

log = logging.getLogger(__name__)

router = APIRouter(tags=["Certificates"])


def get_certificate_service(
    session: Session = Depends(),
) -> CertificateCrudService:
    """Factory for CertificateCrudService — follows existing dependency pattern."""
    uow = CertificatesUnitOfWork(session)
    return CertificateCrudService(uow)


# ─── US1: Generate Certificate ───

@router.post(
    "/certificates",
    response_model=dict,
    summary="Generate a new certificate",
)
def generate_certificate(
    dto: GenerateCertificateInput,
    service: CertificateCrudService = Depends(get_certificate_service),
    # current_user: User = Depends(require_permission(Permissions.GENERATE)),
):
    """Generate a course completion certificate. Returns 409 if duplicate exists."""
    result = service.generate(dto, actor_name="system")
    return {"success": True, "data": result.model_dump(), "message": "Certificate generated successfully"}


@router.get(
    "/certificates/{cert_id}/pdf",
    summary="Download certificate as PDF",
)
def download_pdf(
    cert_id: str,
    service: CertificateCrudService = Depends(get_certificate_service),
):
    """Download the certificate PDF. Returns HTML fallback on render failure."""
    try:
        pdf_bytes = service.download_pdf(cert_id)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{cert_id}.pdf"'},
        )
    except Exception as exc:
        log.warning("PDF render failed for %s: %s", cert_id, exc)
        html = service.download_html(cert_id)
        return HTMLResponse(content=html)


@router.get(
    "/certificates/{cert_id}/html",
    summary="Download certificate as HTML",
)
def download_html(
    cert_id: str,
    service: CertificateCrudService = Depends(get_certificate_service),
):
    """Download the certificate as a self-contained HTML file."""
    html = service.download_html(cert_id)
    return HTMLResponse(
        content=html,
        headers={"Content-Disposition": f'attachment; filename="{cert_id}.html"'},
    )


# ─── US2: Validate Certificate (Public) ───

@router.get(
    "/certificates/{cert_id}",
    response_model=dict,
    summary="Verify a certificate (public, no auth required)",
)
def verify_certificate(
    cert_id: str,
    service: CertificateCrudService = Depends(get_certificate_service),
):
    """Public verification endpoint — no authentication required."""
    result = service.verify(cert_id)
    if not result:
        return Response(
            content='{"success": false, "message": "Certificate not found"}',
            status_code=404,
            media_type="application/json",
        )
    return {"success": True, "data": result.model_dump(), "message": "Certificate verified"}


# ─── US3: Browse Certificate Registry ───

@router.get(
    "/certificates",
    response_model=dict,
    summary="List certificates with pagination and filters",
)
def list_certificates(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    track: Optional[str] = Query(None),
    include_revoked: bool = Query(False),
    service: CertificateCrudService = Depends(get_certificate_service),
    # current_user: User = Depends(get_current_user),
):
    """List all certificates with pagination, search, and track filter."""
    result = service.list_certificates(
        page=page,
        page_size=page_size,
        search=search,
        track=track,
        include_revoked=include_revoked,
    )
    return {
        "success": True,
        "data": [item.model_dump() for item in result.items],
        "total": result.total,
        "skip": (result.page - 1) * result.page_size,
        "limit": result.page_size,
    }


@router.post(
    "/certificates/export",
    summary="Export certificates as CSV",
)
def export_csv(
    track: Optional[str] = None,
    search: Optional[str] = None,
    include_revoked: bool = False,
    service: CertificateCrudService = Depends(get_certificate_service),
    # current_user: User = Depends(get_current_user),
):
    """Export filtered certificates as a CSV file download."""
    csv_bytes = service.export_csv(track=track, search=search, include_revoked=include_revoked)
    return StreamingResponse(
        iter([csv_bytes]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=certificates.csv"},
    )


# ─── US4: Revoke Certificate ───

@router.post(
    "/certificates/{cert_id}/revoke",
    response_model=dict,
    summary="Revoke a certificate",
)
def revoke_certificate(
    cert_id: str,
    dto: RevokeCertificateInput,
    service: CertificateCrudService = Depends(get_certificate_service),
    # current_user: User = Depends(require_permission(Permissions.GENERATE)),
):
    """Revoke a certificate. Returns 409 if already revoked."""
    result = service.revoke(cert_id, reason=dto.reason, actor_name="system")
    return {"success": True, "data": result.model_dump(), "message": "Certificate revoked successfully"}
