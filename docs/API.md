# API Reference — Techno Future Certificates

**Base URL:** `https://techno-future-certs.fastapicloud.dev/api/v1`

All endpoints return JSON unless noted otherwise.

---

## Health Check

```
GET /health
```

No auth required. Returns `{"status": "ok"}`.

---

## Generate Certificate

```
POST /api/v1/certificates
```

Create a new course completion certificate.

### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `student_name` | string | yes | Full name of the student |
| `course_track` | string | yes | Track key (see list below) |
| `level` | string | yes | Level `"1"`, `"2"`, or `"3"` |
| `issue_date` | string (date) | yes | Issue date in `YYYY-MM-DD` format |
| `branch` | string | yes | Branch name (e.g. "Heliopolis") |
| `custom_color` | string (hex) | no | Override accent color (e.g. `#FF0000`) |

### Valid Track Keys

| Key | Display Name |
|-----|-------------|
| `html` | HTML — Web Structure |
| `css` | CSS — Styling & Layout |
| `javascript` | JavaScript — Interactivity |
| `python` | Python — Programming |
| `advanced` | Advanced — Web Pro |
| `problem_solving` | Problem Solving — Logic |
| `robotics-wedo` | Robotics WeDo 2.0 |
| `robotics-spike-essential` | Robotics SPIKE Essential |
| `robotics-spike-prime` | Robotics SPIKE Prime |
| `robotics-ev3` | Robotics EV3 |
| `robotics-arduino` | Robotics Arduino |
| `scratch` | Scratch |
| `scratch-jr` | Scratch Jr |

### Valid Levels

- `"1"` — mapped to `Level 1 — Junior`
- `"2"` — mapped to `Level 2 — Intermediate`
- `"3"` — mapped to `Level 3 — Advanced`

### Example

```json
{
  "student_name": "Ahmed Mohamed",
  "course_track": "html",
  "level": "1",
  "issue_date": "2026-07-28",
  "branch": "Heliopolis",
  "custom_color": null
}
```

### Response `201`

```json
{
  "success": true,
  "data": {
    "id": 1,
    "cert_id": "TKTF-HTM-20260728-ABCD",
    "student_name": "Ahmed Mohamed",
    "course_name": "HTML — Web Structure",
    "course_track": "html",
    "level": "Level 1 — Junior",
    "issue_date": "2026-07-28",
    "branch": "Heliopolis",
    "custom_color": null,
    "revoked_at": null,
    "revoked_reason": null,
    "created_at": "2026-07-28T12:00:00Z"
  },
  "message": "Certificate generated successfully"
}
```

### Error `409`

Returns `409 Conflict` if a duplicate certificate exists for the same student + track + level + date.

---

## List Certificates

```
GET /api/v1/certificates
```

Paginated list of certificates with optional filters.

### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | int | `1` | Page number (≥ 1) |
| `page_size` | int | `20` | Items per page (1–100) |
| `search` | string | — | Search by student name or cert ID |
| `track` | string | — | Filter by track key |
| `include_revoked` | bool | `false` | Include revoked certificates |

### Response `200`

```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "cert_id": "TKTF-HTM-20260728-ABCD",
      "student_name": "Ahmed Mohamed",
      "course_name": "HTML — Web Structure",
      "course_track": "html",
      "level": "Level 1 — Junior",
      "issue_date": "2026-07-28",
      "branch": "Heliopolis",
      "custom_color": null,
      "revoked_at": null,
      "revoked_reason": null,
      "created_at": "2026-07-28T12:00:00Z"
    }
  ],
  "total": 1,
  "skip": 0,
  "limit": 20
}
```

---

## Get / Verify Certificate (Public)

```
GET /api/v1/certificates/{cert_id}
```

No auth required. Returns certificate details or `404`.

### Response `200`

```json
{
  "success": true,
  "data": {
    "cert_id": "TKTF-HTM-20260728-ABCD",
    "student_name": "Ahmed Mohamed",
    "course_name": "HTML — Web Structure",
    "level": "Level 1 — Junior",
    "issue_date": "2026-07-28",
    "branch": "Heliopolis",
    "revoked": false,
    "revoked_reason": null
  },
  "message": "Certificate verified"
}
```

### Response `404`

```json
{
  "success": false,
  "message": "Certificate not found"
}
```

---

## Download Certificate PDF

```
GET /api/v1/certificates/{cert_id}/pdf
```

Downloads the certificate as a PDF file. Falls back to HTML if PDF rendering fails.

### Response

`200` with `Content-Type: application/pdf` and `Content-Disposition: attachment`.

**Filename format:** `{StudentName}_{CourseName}_{YYYYMMDD}.pdf`

---

## Download Certificate HTML

```
GET /api/v1/certificates/{cert_id}/html
```

Downloads the certificate as a self-contained HTML file.

### Response

`200` with `Content-Type: text/html` and `Content-Disposition: attachment`.

**Filename format:** `{StudentName}_{CourseName}_{YYYYMMDD}.html`

---

## Revoke Certificate

```
POST /api/v1/certificates/{cert_id}/revoke
```

Revoke an existing certificate.

### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `reason` | string | yes | Reason for revocation |

### Example

```json
{
  "reason": "Issued in error — duplicate entry"
}
```

### Response `200`

```json
{
  "success": true,
  "data": {
    "id": 1,
    "cert_id": "TKTF-HTM-20260728-ABCD",
    "revoked_at": "2026-07-28T13:00:00Z",
    "revoked_reason": "Issued in error — duplicate entry"
  },
  "message": "Certificate revoked successfully"
}
```

### Error `409`

Returns `409 Conflict` if the certificate is already revoked.

---

## Export Certificates as CSV

```
GET /api/v1/certificates/export
```

Downloads filtered certificates as a CSV file.

### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `track` | string | — | Filter by track key |
| `search` | string | — | Search by student name or cert ID |
| `include_revoked` | bool | `false` | Include revoked certificates |

### Response

`200` with `Content-Type: text/csv` and `Content-Disposition: attachment; filename=certificates.csv`.

---

## Certificate ID Format

Certificates are issued with IDs following this pattern:

```
TKTF-{TRACK_PREFIX}-{YYYYMMDD}-{XXXX}
```

| Part | Description |
|------|-------------|
| `TKTF` | Static prefix |
| `HTM` / `CSS` / `PYT` etc. | Track abbreviation |
| `20260728` | Issue date (YYYYMMDD) |
| `ABCD` | Random 4-char hex suffix |

---

## Data Types

### Certificate (Read)

| Field | Type | Notes |
|-------|------|-------|
| `id` | int | Internal ID |
| `cert_id` | string | Public certificate ID |
| `student_name` | string | Full name |
| `course_name` | string | Resolved course display name |
| `course_track` | string | Track key |
| `level` | string | Level enum string |
| `issue_date` | date | YYYY-MM-DD |
| `branch` | string | Branch location |
| `custom_color` | string or null | Hex color override |
| `revoked_at` | datetime or null | |
| `revoked_reason` | string or null | |
| `created_at` | datetime | |

### Certificate (Public Verify)

| Field | Type | Notes |
|-------|------|-------|
| `cert_id` | string | Public certificate ID |
| `student_name` | string | |
| `course_name` | string | |
| `level` | string | |
| `issue_date` | date | |
| `branch` | string | |
| `revoked` | bool | |
| `revoked_reason` | string or null | |
