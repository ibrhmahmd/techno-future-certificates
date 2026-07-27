# Data Model: Certificate Service

**Date**: 2026-07-27

## Entities

### Certificate

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| id | `int` | PK, auto-increment | Internal surrogate key |
| cert_id | `str` | UNIQUE, NOT NULL, indexed | Format: `TKTF-{PREFIX}-{YYYYMMDD}-{4HEX}` |
| student_name | `str` | NOT NULL | Student full name |
| course_name | `str` | NOT NULL | Track display name (e.g., "HTML", "Python") |
| course_track | `str` | NOT NULL | Track key (e.g., "html", "python") |
| level | `str` | NOT NULL | One of: "Level 1 Junior", "Level 2 Intermediate", "Level 3 Advanced" |
| issue_date | `date` | NOT NULL | Certificate issue date |
| branch | `str` | NOT NULL | Branch/location name |
| instructor | `str` | NULLABLE | Instructor name (omit from cert if blank) |
| director | `str` | NULLABLE | Director name (omit from cert if blank) |
| custom_color | `str` | NULLABLE | Custom accent color override (hex) |
| revoked_at | `datetime` | NULLABLE | Timestamp of revocation (null = active) |
| revoked_reason | `str` | NULLABLE | Reason for revocation |
| created_at | `datetime` | NOT NULL | Record creation timestamp (UTC) |

**Unique constraint**: `(student_name, course_track, issue_date)`

**Indexes**:
- `cert_id` (unique)
- `student_name` (for search)
- `course_track` (for filter)
- `created_at` (for sort)

### CertificateAuditLog

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| id | `int` | PK, auto-increment | Internal surrogate key |
| cert_id | `str` | NOT NULL, FK → Certificate.cert_id | Certificate affected |
| action | `str` | NOT NULL | One of: "generated", "revoked" |
| actor_id | `int` | NULLABLE | User ID who performed the action |
| actor_name | `str` | NULLABLE | Display name of actor |
| timestamp | `datetime` | NOT NULL | When the action occurred (UTC) |
| metadata | `dict` | NULLABLE | Additional context (JSONB) |

**Indexes**:
- `cert_id` (for lookups)
- `timestamp` (for audit queries)

## Relationships

- `CertificateAuditLog.cert_id` → `Certificate.cert_id` (many-to-one)
- A Certificate can have many AuditLog entries

## State Transitions

```
Certificate States:
  ACTIVE (revoked_at is NULL)
    → REVOKED (revoked_at is set, revoked_reason provided)

Revocation is one-way — certificates cannot be un-revoked.
```

## Validation Rules

| Rule | Field(s) | Description |
|------|----------|-------------|
| Required | student_name | Cannot be empty or whitespace-only |
| Required | course_name | Must match a known track display name |
| Required | course_track | Must match a known track key |
| Required | level | Must be one of the 3 valid levels |
| Required | issue_date | Cannot be in the future |
| Required | branch | Cannot be empty |
| Unique | (student_name, course_track, issue_date) | One cert per student per track per date |
| Format | cert_id | Must match `TKTF-[A-Z]{3}-\d{8}-[0-9A-F]{4}` |
| Format | custom_color | Must be valid hex color if provided |
