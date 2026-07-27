# Feature Specification: Certificate Service

**Feature Branch**: `001-certificate-service`

**Created**: 2026-07-27

**Status**: Draft

**Input**: User description: "Organize the certificate-generator codebase into a vertical slice architecture that supports integrating this service into other existing systems (CRM, Academics, Finance, Notifications)"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Generate Certificate (Priority: P1)

As an admin, I want to generate a course completion certificate for a student so that they receive official proof of completing a Techno Future program.

**Why this priority**: This is the core value proposition. Without certificate generation, no other feature matters.

**Independent Test**: Can be fully tested by submitting a certificate generation form with valid student data and verifying a certificate record is created and a PDF is produced.

**Acceptance Scenarios**:

1. **Given** an admin is authenticated, **When** they submit a certificate generation request with student name, course, level, date, branch, instructor, and director, **Then** a unique certificate ID is generated and the certificate is persisted in the database.
2. **Given** a certificate has been generated, **When** the admin requests the PDF, **Then** a print-ready A4 landscape PDF is returned with the correct student name, course, level, date, branch, signatures, QR code, and track-specific accent color.
3. **Given** a certificate has been generated, **When** the admin requests the HTML version, **Then** a self-contained HTML file with embedded fonts, logos, and QR code is returned.
4. **Given** a certificate generation request with a missing required field (student name), **When** submitted, **Then** a validation error is returned without creating a record.
5. **Given** a duplicate certificate ID already exists, **When** a new certificate is generated with the same track and date, **Then** the existing record is updated (not duplicated).

---

### User Story 2 - Validate Certificate (Priority: P2)

As a verifier (employer, parent, or admin), I want to look up a certificate by its ID without logging in so that I can confirm its authenticity.

**Why this priority**: Verification is essential for trust. Without it, certificates have no credibility.

**Independent Test**: Can be tested by generating a certificate, then looking it up by ID and verifying all fields match.

**Acceptance Scenarios**:

1. **Given** a certificate exists with ID `TKTF-HTM-20260722-A3F1`, **When** a user searches for that ID, **Then** the system returns all certificate details (student name, course, level, date, branch, instructor, director) and confirms authenticity.
2. **Given** a certificate does not exist with ID `TKTF-XXX-00000000-Z999`, **When** a user searches for that ID, **Then** the system returns a "not found" message without exposing internal details.
3. **Given** a QR code on a certificate links to the verification URL, **When** scanned, **Then** the user is directed to the verification page with the certificate ID pre-filled.

---

### User Story 3 - Browse Certificate Registry (Priority: P3)

As an admin, I want to browse, search, filter, and export all issued certificates so that I can manage the certificate inventory and generate reports.

**Why this priority**: Operational efficiency. admins need to find and re-download certificates without re-generating them.

**Independent Test**: Can be tested by generating multiple certificates, then searching, filtering by track, and exporting to CSV.

**Acceptance Scenarios**:

1. **Given** certificates exist in the system, **When** an admin opens the registry, **Then** they see a list of all certificates sorted by creation date (newest first) with total count, this month's count, and most popular track.
2. **Given** certificates exist across multiple tracks, **When** an admin filters by a specific track, **Then** only certificates for that track are displayed.
3. **Given** certificates exist with various student names, **When** an admin searches by student name or certificate ID, **Then** matching certificates are displayed.
4. **Given** the registry is filtered, **When** the admin exports to CSV, **Then** a CSV file with all filtered records is downloaded.
5. **Given** a certificate in the registry, **When** the admin clicks "Download PDF", **Then** the PDF for that specific certificate is generated and downloaded.

---

### User Story 4 - Cross-System Integration (Priority: P4)

As a developer building other modules (CRM, Academics, Finance), I want to call the certificate service programmatically so that certificates can be generated automatically when enrollments complete, payments clear, or other triggers fire.

**Why this priority**: Enables automation and eliminates manual certificate generation. Required for the vertical slice integration.

**Independent Test**: Can be tested by calling the service interface from another module and verifying the certificate is created.

**Acceptance Scenarios**:

1. **Given** the Academics module completes an enrollment, **When** it calls the certificate service with student and course data, **Then** a certificate is generated and the certificate ID is returned.
2. **Given** the Finance module confirms a payment, **When** it requests a certificate for the paid student, **Then** the certificate service generates the certificate and returns the result.
3. **Given** a certificate is generated via the service interface, **When** the Notifications module is triggered, **Then** the certificate PDF can be attached to an email or WhatsApp message.

---

### Edge Cases

- What happens when a track name does not match any known track? System MUST reject with a clear validation error.
- What happens when the issue date is in the future? System MUST reject with a validation error.
- What happens when the PDF rendering engine fails? System MUST return the HTML version as a fallback and log the error.
- What happens when two certificates are generated for the same student on the same date for the same track? System MUST enforce a unique constraint on `(student_name, course_track, issue_date)` and return the existing certificate with a clear message.
- What happens when the database is unavailable? System MUST return a 500 error with a user-friendly message.
- What happens when a certificate ID contains invalid characters? System MUST reject with a validation error.
- What happens when a revoked certificate is looked up? System MUST return all details but include a `revoked: true` flag and the revocation reason.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST generate unique certificate IDs in the format `TKTF-{TRACK_PREFIX}-{YYYYMMDD}-{4HEX}` where TRACK_PREFIX is the first 3 uppercase letters of the track name.
- **FR-002**: System MUST persist certificate records with: cert_id, student_name, course_name, level, issue_date, branch, instructor, director, created_at.
- **FR-003**: System MUST support 13 course tracks: HTML, CSS, JavaScript, Python, Advanced, Problem Solving, Robotics WeDo 2.0, Robotics SPIKE Essential, Robotics SPIKE Prime, Robotics EV3, Robotics Arduino, Scratch, Scratch Jr.
- **FR-004**: System MUST support 3 levels: Level 1 Junior, Level 2 Intermediate, Level 3 Advanced.
- **FR-005**: System MUST render certificates as A4 landscape PDF with embedded fonts (Space Grotesk, Inter), track logos, company logo, QR code, and track-specific accent colors.
- **FR-006**: System MUST render certificates as self-contained HTML with base64-encoded assets (fonts, logos, QR codes).
- **FR-007**: System MUST generate QR codes linking to a verification URL with the certificate ID.
- **FR-008**: System MUST allow certificate lookup by exact certificate ID.
- **FR-009**: System MUST support listing all certificates with pagination, search by student name or ID, and filter by track.
- **FR-010**: System MUST support CSV export of certificate records.
- **FR-011**: System MUST provide a programmatic service interface (Protocol/Interface) for other modules to call.
- **FR-012**: System MUST use the shared database connection (PostgreSQL) managed by the existing UnitOfWork pattern.
- **FR-013**: System MUST validate all input fields before persisting (required fields, date format, track exists, level exists).
- **FR-014**: System MUST allow optional instructor and director fields (omit from certificate if blank).
- **FR-015**: System MUST support custom accent colors per certificate, with a fallback to the track's default color.
- **FR-016**: System MUST declare permission constants (`certificates.generate`, `certificates.verify`) for the Auth module to enforce.
- **FR-017**: System MUST support certificate revocation with `revoked_at` timestamp and optional `revoked_reason` field. Revoked certificates MUST be excluded from default registry listings but remain verifiable by ID.
- **FR-018**: System MUST maintain an audit trail for state-changing operations (generate, revoke) recording: actor (user/service identity), timestamp, operation type, and certificate ID. Read operations (verify, list) MUST NOT be logged.
- **FR-019**: System MUST enforce a unique database constraint on `(student_name, course_track, issue_date)`. If a duplicate is detected, the existing certificate MUST be returned with a clear "already exists" message.
- **FR-020**: System MUST serve certificate verification (lookup by ID) without requiring authentication. The verification endpoint MUST be publicly accessible.

### Key Entities

- **Certificate**: Represents an issued course completion certificate. Key attributes: unique ID, student name, course track, level, issue date, branch location, instructor name, director name, creation timestamp, `revoked_at` (nullable), `revoked_reason` (nullable).
- **Track**: A predefined course offering (e.g., HTML, Python, Robotics). Each track has a name, logo, accent color, and data attribute for CSS styling.
- **Level**: A proficiency tier (Junior, Intermediate, Advanced) indicating the student's completion level.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Admins can generate a certificate (fill form + download PDF) in under 2 minutes.
- **SC-002**: Certificate verification by ID returns results in under 1 second.
- **SC-003**: The service can be called from any other module via its Protocol interface without importing internal implementation details.
- **SC-004**: PDF rendering works without any browser dependencies (no Chromium/Playwright required).
- **SC-005**: All 13 tracks produce visually distinct certificates with correct accent colors and logos.
- **SC-006**: Certificate IDs are globally unique (no collisions across tracks, dates, or students).
- **SC-007**: The service integrates into the existing vertical slice architecture with consistent patterns (UnitOfWork, Protocol interfaces, DTOs, ApiResponse envelope).

## Clarifications

### Session 2026-07-27

- Q: Who should be authorized to generate certificates vs verify them? → A: Permission-based — module declares permission keys (e.g., `certificates.generate`, `certificates.verify`), Auth module enforces them.
- Q: Should certificates be immutable after creation, or can they be revoked/deleted? → A: Immutable + revocable — soft delete with `revoked_at` timestamp and `revoked_reason` field.
- Q: What level of logging/audit trail should the certificate service maintain? → A: Audit trail for writes only — log generate + revoke operations with actor + timestamp. Read operations are not logged.
- Q: How should the system handle concurrent certificate generation for the same student/track/date? → A: DB unique constraint on `(student_name, course_track, issue_date)` — return existing cert on conflict.
- Q: Should the certificate verification endpoint be public or authenticated? → A: Public — verification is open to anyone with the cert ID. Generation requires `certificates.generate` permission.

## Assumptions

- The existing PostgreSQL database and connection infrastructure will be used (no separate SQLite).
- The existing authentication and authorization system (Auth module) will be reused for access control.
- The existing FastAPI application factory and router registration pattern will be followed.
- Assets (logos, fonts, CSS, HTML template) will be moved into the module directory for self-containment.
- The xhtml2pdf library will be used for PDF rendering (pure Python, no browser dependency).
- QR codes will default to a configurable base URL from the application settings, not hardcoded localhost.
- The "assests" typo will be corrected to "assets" during migration.
- Track definitions will be consolidated into a single source of truth (constants.py) instead of scattered across 4 locations.
- The Certificate module will be read-only for other slices (they generate and query, but don't modify certificates directly).
- Email/WhatsApp delivery of certificates is handled by the Notifications module, not the Certificate module.
