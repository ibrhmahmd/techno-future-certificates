# API Contracts: Certificate Service

**Base URL**: `/api/v1/certificates`

## Endpoints

### POST /certificates — Generate Certificate

**Auth**: Requires `certificates.generate` permission

**Request Body** (`GenerateCertificateInput`):
```json
{
  "student_name": "string (required)",
  "course_track": "string (required, one of 13 track keys)",
  "level": "string (required, one of 3 levels)",
  "issue_date": "string (required, YYYY-MM-DD)",
  "branch": "string (required)",
  "instructor": "string (optional)",
  "director": "string (optional)",
  "custom_color": "string (optional, hex color)"
}
```

**Response** (`ApiResponse[CertificateReadDTO]`):
```json
{
  "success": true,
  "data": {
    "id": 1,
    "cert_id": "TKTF-HTM-20260727-A3F1",
    "student_name": "John Doe",
    "course_name": "HTML",
    "course_track": "html",
    "level": "Level 1 Junior",
    "issue_date": "2026-07-27",
    "branch": "Cairo",
    "instructor": "Jane Smith",
    "director": "Dr. Ahmed",
    "custom_color": null,
    "revoked_at": null,
    "revoked_reason": null,
    "created_at": "2026-07-27T10:30:00Z"
  },
  "message": "Certificate generated successfully"
}
```

**Error Responses**:
- `422` — Validation error (missing fields, invalid track, future date)
- `409` — Certificate already exists for this student/track/date (returns existing cert)
- `401` — Unauthorized

---

### GET /certificates/{cert_id} — Verify Certificate (PUBLIC)

**Auth**: None required

**Response** (`ApiResponse[CertificateReadDTO]`):
```json
{
  "success": true,
  "data": {
    "cert_id": "TKTF-HTM-20260727-A3F1",
    "student_name": "John Doe",
    "course_name": "HTML",
    "level": "Level 1 Junior",
    "issue_date": "2026-07-27",
    "branch": "Cairo",
    "instructor": "Jane Smith",
    "director": "Dr. Ahmed",
    "revoked": false,
    "revoked_reason": null
  },
  "message": "Certificate verified"
}
```

**Note**: Revoked certificates return `revoked: true` with `revoked_reason`. Internal fields (`id`, `created_at`, `custom_color`) are excluded from public verification response.

**Error Responses**:
- `404` — Certificate not found

---

### GET /certificates — List Certificates (Registry)

**Auth**: Requires authenticated user

**Query Parameters**:
- `page` (int, default 1)
- `page_size` (int, default 20, max 100)
- `search` (string, optional — matches student_name or cert_id)
- `track` (string, optional — filter by course_track)
- `include_revoked` (bool, default false)

**Response** (`PaginatedResponse[CertificateReadDTO]`):
```json
{
  "success": true,
  "data": [...],
  "total": 150,
  "skip": 0,
  "limit": 20
}
```

---

### GET /certificates/{cert_id}/pdf — Download PDF

**Auth**: Requires authenticated user

**Response**: `application/pdf` binary stream

**Error Responses**:
- `404` — Certificate not found
- `500` — PDF rendering failed (returns HTML fallback)

---

### GET /certificates/{cert_id}/html — Download HTML

**Auth**: Requires authenticated user

**Response**: `text/html` binary stream

---

### POST /certificates/export — Export CSV

**Auth**: Requires authenticated user

**Request Body** (optional, same filters as list endpoint):
```json
{
  "track": "string (optional)",
  "search": "string (optional)",
  "include_revoked": false
}
```

**Response**: `text/csv` file download

---

### POST /certificates/{cert_id}/revoke — Revoke Certificate

**Auth**: Requires `certificates.generate` permission

**Request Body**:
```json
{
  "reason": "string (required)"
}
```

**Response** (`ApiResponse[CertificateReadDTO]`):
Returns updated certificate with `revoked_at` and `revoked_reason` set.

**Error Responses**:
- `404` — Certificate not found
- `409` — Certificate already revoked
