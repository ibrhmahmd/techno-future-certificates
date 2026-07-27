# Implementation Plan: Certificate Service

**Branch**: `001-certificate-service` | **Date**: 2026-07-27 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/001-certificate-service/spec.md`

## Summary

Restructure the existing `certificate-generator` codebase into a vertical slice module (`app/modules/certificates/`) that integrates with the existing `techno_data_` backend architecture. The module provides certificate generation, verification (public), registry browsing, PDF/HTML rendering, CSV export, revocation, and cross-system integration via Protocol interfaces. Uses xhtml2pdf for PDF rendering (no browser dependency), PostgreSQL via SQLModel, and follows existing patterns (UnitOfWork, DTOs, ApiResponse envelope, typed exceptions).

## Technical Context

**Language/Version**: Python 3.13

**Primary Dependencies**: FastAPI, SQLModel, xhtml2pdf, qrcode, pydantic

**Storage**: PostgreSQL (shared with existing backend)

**Testing**: pytest (existing backend standard)

**Target Platform**: Linux server (Docker), HF Spaces (static)

**Project Type**: Web service (FastAPI module)

**Performance Goals**: PDF rendering < 5s, verification < 1s, list with pagination < 500ms

**Constraints**: No browser dependency for PDF, must integrate with existing UnitOfWork/Protocol patterns, must be callable from other modules without importing internals

**Scale/Scope**: ~13 tracks, low-to-medium volume (hundreds to low thousands of certificates)

## Constitution Check

*No constitution defined (template only). Skipping gate check.*

## Project Structure

### Documentation (this feature)

```text
specs/001-certificate-service/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── api.md
│   ├── interfaces.md
│   └── dtos.md
├── checklists/
│   └── requirements.md
└── tasks.md             # Phase 2 output (via /speckit.tasks)
```

### Source Code (repository root)

```text
app/
├── modules/
│   └── certificates/
│       ├── __init__.py                    # Public API re-exports
│       ├── constants.py                   # TRACKS dict, LevelType, permission keys
│       ├── models/
│       │   ├── __init__.py
│       │   ├── certificate_models.py      # Certificate, CertificateAuditLog (SQLModel)
│       ├── schemas/
│       │   ├── __init__.py
│       │   ├── certificate_schemas.py     # GenerateCertificateInput, CertificateReadDTO, etc.
│       │   └── response_schemas.py        # CertificateListResponseDTO, CertificateVerifyDTO
│       ├── repositories/
│       │   ├── __init__.py
│       │   ├── interface.py               # CertificateRepositoryInterface (Protocol)
│       │   ├── certificate_repository.py  # Concrete repository
│       │   ├── audit_log_repository.py    # Audit log repository
│       │   └── unit_of_work.py            # CertificatesUnitOfWork
│       ├── services/
│       │   ├── __init__.py
│       │   ├── interface.py               # CertificateServiceInterface (Protocol)
│       │   ├── certificate_crud_service.py # Business logic (generate, verify, list, revoke)
│       │   └── certificate_render_service.py # PDF/HTML/CSV rendering
│       ├── validators/
│       │   └── certificate_validators.py  # Input validation helpers
│       └── assets/
│           ├── fonts/                     # Space Grotesk, Inter
│           ├── logos/                     # Track logos, company logo
│           ├── templates/                 # certificate_template.html
│           └── styles/                    # certificate_style.css
│
├── api/
│   ├── routers/
│   │   └── certificates.py               # FastAPI router
│   └── dependencies.py                    # get_certificate_service factory
│
├── db/
│   └── migrations/                        # Alembic migration for new tables
│
└── shared/
    ├── base_repository.py                 # (existing, optional reuse)
    └── datetime_utils.py                  # utc_now() (existing)

tests/
├── contract/
│   └── test_certificate_contracts.py      # Protocol compliance tests
├── integration/
│   └── test_certificate_integration.py    # Full flow tests with DB
└── unit/
    ├── test_certificate_validators.py     # Validation logic
    └── test_certificate_service.py        # Service logic (mocked UoW)
```

**Structure Decision**: Follows the existing vertical slice pattern from `techno_data_` backend. Module is self-contained with its own models, schemas, repositories, services, and assets. Wired into the FastAPI app via router registration and dependency injection.

## Complexity Tracking

*No constitution violations to justify.*
