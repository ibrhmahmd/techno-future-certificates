# Research: Certificate Service

**Date**: 2026-07-27

## R1: PDF Rendering Engine

**Decision**: xhtml2pdf (pure Python)

**Rationale**: The existing codebase already uses xhtml2pdf. It's pure Python (no Chromium/Playwright dependency), works on Streamlit Cloud and HF Spaces, and produces acceptable A4 landscape PDFs. The existing CSS (`certificate_style.css`) is already optimized for xhtml2pdf rendering.

**Alternatives considered**:
- Playwright/Puppeteer: Rejected — requires Chromium, fails on Streamlit Cloud, adds ~400MB dependency
- WeasyPrint: Viable but xhtml2pdf is already integrated and tested
- ReportLab: Too low-level for HTML template-based rendering

## R2: Database Strategy

**Decision**: PostgreSQL via SQLModel + existing UnitOfWork pattern

**Rationale**: The existing backend uses PostgreSQL with SQLModel. The certificate module must integrate as a vertical slice, using the shared database connection. No separate SQLite.

**Alternatives considered**:
- SQLite: Rejected — not suitable for production multi-user system, can't share with existing backend
- SQLAlchemy Core: Rejected — existing modules use SQLModel, should be consistent

## R3: Architecture Pattern

**Decision**: Vertical slice module matching existing `techno_data_` patterns

**Rationale**: The certificate service must be a self-contained module usable by CRM, Academics, Finance, and Notifications modules. Following the existing vertical slice patterns (Protocol interfaces, UnitOfWork, DTOs, ApiResponse envelope) ensures consistency and testability.

**Key patterns to follow**:
- `@runtime_checkable` Protocol interfaces for repositories and services
- `{Verb}{Entity}Input` for input DTOs, `{Entity}{Qualifier}DTO` for output DTOs
- UnitOfWork with eager repository init (simpler modules) or lazy init (complex modules)
- `ApiResponse[T]` envelope for all responses
- Typed exception hierarchy (`AppError` → `NotFoundError`, `ValidationError`, etc.)

## R4: Certificate ID Generation

**Decision**: Format `TKTF-{TRACK_PREFIX}-{YYYYMMDD}-{4HEX}` with DB unique constraint

**Rationale**: The format is readable, includes date context, and the 4-hex suffix provides collision resistance. DB unique constraint on `(student_name, course_track, issue_date)` prevents duplicates. If a duplicate is detected, the existing certificate is returned.

**Alternatives considered**:
- UUID-only: Rejected — not human-readable, can't be spoken over phone
- Sequential: Rejected — exposes count, not suitable for public-facing IDs

## R5: QR Code Generation

**Decision**: `qrcode` library with base64 embedding

**Rationale**: The existing codebase uses `qrcode` library. QR codes encode a verification URL (`{VERIFY_BASE_URL}/{cert_id}`). The QR is base64-encoded and embedded in the HTML template, then rendered into PDF by xhtml2pdf.

**Configuration**: `VERIFY_BASE_URL` from application settings (not hardcoded).

## R6: Asset Management

**Decision**: Move assets into module directory, use relative paths with base64 embedding for HTML/PDF

**Rationale**: For self-containment, assets (logos, fonts, CSS, HTML template) should live inside the module directory. For PDF/HTML rendering, assets are base64-encoded to produce self-contained output. The `assests` typo will be corrected to `assets` during migration.

**Directory structure**:
```
modules/certificates/
  assets/
    fonts/          # Space Grotesk, Inter
    logos/          # Track logos, company logo
    templates/      # certificate_template.html
    styles/         # certificate_style.css
```

## R7: Track Consolidation

**Decision**: Single source of truth in `constants.py`

**Rationale**: Track definitions are currently scattered across 4 locations (config.py, renderer.py, database.py, and the CSS). Consolidating into `constants.py` with a `TRACKS` dict mapping track name → prefix, logo, accent color, data attribute.

## R8: Revocation Strategy

**Decision**: Soft revocation with `revoked_at` and `revoked_reason` fields

**Rationale**: Certificates are immutable after creation but can be revoked. Revoked certificates are excluded from default registry listings but remain verifiable by ID (returns `revoked: true` flag). This preserves audit history while allowing corrections.

## R9: Audit Trail

**Decision**: Dedicated `certificate_audit_log` table

**Rationale**: State-changing operations (generate, revoke) are logged with actor, timestamp, operation type, and certificate ID. Read operations are not logged. This provides traceability without noise.

**Schema**: `id`, `cert_id` (FK), `action` (Literal['generated', 'revoked']), `actor_id` (nullable int), `actor_name` (nullable str), `timestamp`, `metadata` (JSONB, optional).
