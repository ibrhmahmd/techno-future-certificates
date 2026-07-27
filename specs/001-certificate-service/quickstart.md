# Quickstart Validation Guide: Certificate Service

**Date**: 2026-07-27

## Prerequisites

- Python 3.13+
- PostgreSQL database running
- Existing backend infrastructure (FastAPI, SQLModel, Auth module)
- All module dependencies installed (`pip install -r requirements.txt`)

## Setup

1. Run database migration to create `certificates` and `certificate_audit_log` tables
2. Verify the module registers its router with the FastAPI app
3. Verify auth permissions are registered (`certificates.generate`, `certificates.verify`)

## Validation Scenarios

### Scenario 1: Generate a Certificate

```bash
curl -X POST http://localhost:8000/api/v1/certificates \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "student_name": "Ahmed Hassan",
    "course_track": "html",
    "level": "Level 1 Junior",
    "issue_date": "2026-07-27",
    "branch": "Cairo",
    "instructor": "Jane Smith",
    "director": "Dr. Mohamed"
  }'
```

**Expected**: `200 OK` with `cert_id` like `TKTF-HTM-20260727-XXXX`

### Scenario 2: Verify Certificate (Public)

```bash
curl http://localhost:8000/api/v1/certificates/TKTF-HTM-20260727-XXXX
```

**Expected**: `200 OK` with certificate details, `revoked: false`

### Scenario 3: Duplicate Generation Returns Existing

```bash
# Same student, track, date
curl -X POST http://localhost:8000/api/v1/certificates \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "student_name": "Ahmed Hassan",
    "course_track": "html",
    "level": "Level 1 Junior",
    "issue_date": "2026-07-27",
    "branch": "Cairo"
  }'
```

**Expected**: `409 Conflict` with existing certificate data

### Scenario 4: Download PDF

```bash
curl -o cert.pdf http://localhost:8000/api/v1/certificates/TKTF-HTM-20260727-XXXX/pdf \
  -H "Authorization: Bearer <token>"
```

**Expected**: Valid PDF file, opens correctly, shows correct student name and track color

### Scenario 5: Revoke Certificate

```bash
curl -X POST http://localhost:8000/api/v1/certificates/TKTF-HTM-20260727-XXXX/revoke \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"reason": "Duplicate enrollment"}'
```

**Expected**: `200 OK` with `revoked_at` set and `revoked_reason` = "Duplicate enrollment"

### Scenario 6: Verify Revoked Certificate

```bash
curl http://localhost:8000/api/v1/certificates/TKTF-HTM-20260727-XXXX
```

**Expected**: `200 OK` with `revoked: true` and `revoked_reason`

### Scenario 7: List Certificates

```bash
curl "http://localhost:8000/api/v1/certificates?page=1&page_size=10&track=html" \
  -H "Authorization: Bearer <token>"
```

**Expected**: Paginated list, total count, filtered by track

### Scenario 8: Export CSV

```bash
curl -X POST http://localhost:8000/api/v1/certificates/export \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"track": "html"}'
```

**Expected**: CSV file download with filtered records

### Scenario 9: Invalid Track Rejection

```bash
curl -X POST http://localhost:8000/api/v1/certificates \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "student_name": "Test",
    "course_track": "invalid_track",
    "level": "Level 1 Junior",
    "issue_date": "2026-07-27",
    "branch": "Cairo"
  }'
```

**Expected**: `422 Validation Error` with message about invalid track

### Scenario 10: Cross-Module Integration

```python
# From another module (e.g., Academics)
from app.modules.certificates import CertificateService, CertificatesUnitOfWork

uow = CertificatesUnitOfWork(session)
service = CertificateService(uow)
dto = GenerateCertificateInput(
    student_name="Sara Ali",
    course_track="python",
    level="Level 2 Intermediate",
    issue_date=date.today(),
    branch="Alexandria"
)
result = service.generate(dto, actor=current_user)
# result.cert_id can be passed to Notifications module
```

**Expected**: Certificate generated, `cert_id` returned, audit log created
