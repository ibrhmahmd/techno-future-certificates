# Tasks: Certificate Service

**Input**: Design documents from `/specs/001-certificate-service/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Not explicitly requested in spec. Test tasks omitted.

**Organization**: Tasks grouped by user story for independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3, US4)
- Exact file paths included in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Module scaffolding, constants, assets migration

- [ ] T001 Create module directory structure at `app/modules/certificates/` with `__init__.py` files for all subpackages (models, schemas, repositories, services, validators, assets)
- [ ] T002 [P] Create `app/modules/certificates/constants.py` with TRACKS dict (13 tracks mapping name to prefix, logo path, accent color, data attribute), LevelType literal, PERMISSIONS dict, and cert_id format
- [ ] T003 [P] Migrate assets from current location into `app/modules/certificates/assets/` -- move fonts to `assets/fonts/`, logos to `assets/logos/`, template to `assets/templates/certificate_template.html`, CSS to `assets/styles/certificate_style.css`. Correct "assests" typo to "assets" throughout
- [ ] T004 [P] Create `app/modules/certificates/__init__.py` with public API re-exports: CertificateService, CertificatesUnitOfWork, GenerateCertificateInput, CertificateReadDTO, CertificateVerifyDTO, CertificateListResponseDTO

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Data model, UnitOfWork, base infrastructure that ALL user stories depend on

**CRITICAL**: No user story work can begin until this phase is complete

- [ ] T005 [P] Create Certificate SQLModel entity in `app/modules/certificates/models/certificate_models.py` -- fields: id (int PK), cert_id (unique str), student_name, course_name, course_track, level, issue_date, branch, instructor (nullable), director (nullable), custom_color (nullable), revoked_at (nullable datetime), revoked_reason (nullable str), created_at (UTC). Table args: unique constraint on (student_name, course_track, issue_date), indexes on cert_id, student_name, course_track, created_at
- [ ] T006 [P] Create CertificateAuditLog SQLModel entity in `app/modules/certificates/models/certificate_models.py` -- fields: id (int PK), cert_id (str FK), action (Literal['generated', 'revoked']), actor_id (nullable int), actor_name (nullable str), timestamp (UTC), metadata (nullable JSONB)
- [ ] T007 [P] Create CertificateRepositoryInterface Protocol in `app/modules/certificates/repositories/interface.py` -- methods: create, get_by_cert_id, get_by_unique_key, list_paginated, update. Decorated with @runtime_checkable
- [ ] T008 [P] Create CertificateAuditLogRepository in `app/modules/certificates/repositories/audit_log_repository.py` -- methods: create (log action), list_by_cert_id
- [ ] T009 Create CertificateRepository in `app/modules/certificates/repositories/certificate_repository.py` -- implements CRUD: create (flush only), get_by_cert_id, get_by_unique_key (student_name + course_track + issue_date), list_paginated (with search/track/revoke filters + total count), update (setattr loop + flush). All use self._session, never commit
- [ ] T010 Create CertificatesUnitOfWork in `app/modules/certificates/repositories/unit_of_work.py` -- takes Session, eagerly initializes certificates and audit_log repositories, exposes commit/flush/rollback
- [ ] T011 [P] Create input DTOs in `app/modules/certificates/schemas/certificate_schemas.py` -- GenerateCertificateInput (with validators: required fields, track exists, level valid, date not future, custom_color hex format), RevokeCertificateInput (reason required). Use ConfigDict(str_strip_whitespace=True)
- [ ] T012 [P] Create output DTOs in `app/modules/certificates/schemas/certificate_schemas.py` -- CertificateReadDTO (from_attributes=True, frozen=True), CertificateVerifyDTO (excludes id, created_at, custom_color; adds revoked bool). Use ConfigDict
- [ ] T013 [P] Create CertificateListResponseDTO in `app/modules/certificates/schemas/response_schemas.py` -- items list, total, page, page_size. ConfigDict(frozen=True)
- [ ] T014 [P] Create CertificateServiceInterface Protocol in `app/modules/certificates/services/interface.py` -- methods: generate, verify, get_by_id, list_certificates, download_pdf, download_html, export_csv, revoke. Decorated with @runtime_checkable
- [ ] T015 [P] Create certificate validators in `app/modules/certificates/validators/certificate_validators.py` -- validate_track_exists, validate_level_exists, validate_date_not_future, validate_hex_color, validate_cert_id_format

**Checkpoint**: Foundation ready -- models, UnitOfWork, DTOs, interfaces all in place. User story implementation can begin.

---

## Phase 3: User Story 1 -- Generate Certificate (Priority: P1) MVP

**Goal**: Admin generates a course completion certificate, unique cert_id created, PDF/HTML downloadable

**Independent Test**: Submit generation form with valid data, cert_id returned, PDF renders correctly with track color, logo, QR code

### Implementation for User Story 1

- [ ] T016 [US1] Implement cert_id generator in `app/modules/certificates/validators/certificate_validators.py` -- format `TKTF-{TRACK_PREFIX}-{YYYYMMDD}-{4HEX}`, uses constants.TRACKS for prefix lookup, random hex suffix
- [ ] T017 [US1] Implement certificate render service in `app/modules/certificates/services/certificate_render_service.py` -- load template from assets/templates/, load CSS from assets/styles/, load fonts/logos from assets/, generate QR code (qrcode library + base64), render HTML (Jinja2 or string.Template), convert to PDF via xhtml2pdf. Methods: render_html(cert_data) returns str, render_pdf(cert_data) returns bytes. Fallback: return HTML if PDF fails
- [ ] T018 [US1] Implement CertificateCrudService.generate() in `app/modules/certificates/services/certificate_crud_service.py` -- validate input (track exists, level valid, date not future), check unique constraint (student_name + course_track + issue_date), generate cert_id, create Certificate record via UoW, flush, log audit entry (action='generated'), commit, return CertificateReadDTO
- [ ] T019 [US1] Implement POST /certificates endpoint in `app/api/routers/certificates.py` -- accepts GenerateCertificateInput, requires certificates.generate permission, calls service.generate(), returns ApiResponse[CertificateReadDTO]. Handle 409 conflict (duplicate) with existing cert data
- [ ] T020 [US1] Implement GET /certificates/{cert_id}/pdf endpoint in `app/api/routers/certificates.py` -- requires auth, calls service.download_pdf(), returns StreamingResponse with application/pdf content type. Fallback to HTML on render failure
- [ ] T021 [US1] Implement GET /certificates/{cert_id}/html endpoint in `app/api/routers/certificates.py` -- requires auth, calls service.download_html(), returns StreamingResponse with text/html content type
- [ ] T022 [US1] Register certificate router in FastAPI app -- add `app/api/routers/certificates.py` router to the app router list in `app/api/` (follow existing registration pattern)
- [ ] T023 [US1] Create get_certificate_service factory in `app/api/dependencies.py` -- takes Session (Depends(get_db)), creates CertificatesUnitOfWork, returns CertificateService. Follow existing get_*_service pattern
- [ ] T024 [US1] Run Alembic migration to create `certificates` and `certificate_audit_log` tables with unique constraint and indexes

**Checkpoint**: Admin can generate a certificate, get cert_id, download PDF with correct track styling and QR code. Duplicate detection works.

---

## Phase 4: User Story 2 -- Validate Certificate (Priority: P2)

**Goal**: Anyone (public, no auth) looks up a cert_id and sees authenticity details or "not found"

**Independent Test**: Generate a cert, then GET /certificates/{cert_id} without auth, returns details with revoked:false. Non-existent ID returns 404.

### Implementation for User Story 2

- [ ] T025 [US2] Implement CertificateCrudService.verify() in `app/modules/certificates/services/certificate_crud_service.py` -- look up by cert_id, return CertificateVerifyDTO (public-safe fields only), or None if not found
- [ ] T026 [US2] Implement GET /certificates/{cert_id} endpoint (public) in `app/api/routers/certificates.py` -- NO auth required (Depends(get_current_user_optional) or no auth dependency), calls service.verify(), returns ApiResponse[CertificateVerifyDTO] or 404. Include revoked status
- [ ] T027 [US2] Handle revoked certificate verification -- when cert is revoked, return full details with revoked:true and revoked_reason in the response

**Checkpoint**: Public can verify any certificate by ID. Revoked certs show revocation status. No auth required.

---

## Phase 5: User Story 3 -- Browse Certificate Registry (Priority: P3)

**Goal**: Admin browses, searches, filters, exports all issued certificates

**Independent Test**: Generate multiple certs, list with pagination, filter by track, search by name, export CSV

### Implementation for User Story 3

- [ ] T028 [US3] Implement CertificateCrudService.list_certificates() in `app/modules/certificates/services/certificate_crud_service.py` -- accepts page, page_size, search (student_name or cert_id LIKE), track filter, include_revoked flag. Excludes revoked by default. Returns CertificateListResponseDTO
- [ ] T029 [US3] Implement CertificateCrudService.export_csv() in `app/modules/certificates/services/certificate_crud_service.py` -- accepts same filters as list, returns CSV bytes with columns: cert_id, student_name, course_name, level, issue_date, branch, instructor, director, created_at
- [ ] T030 [US3] Implement GET /certificates endpoint in `app/api/routers/certificates.py` -- requires auth, accepts query params (page, page_size, search, track, include_revoked), returns PaginatedResponse[CertificateReadDTO]
- [ ] T031 [US3] Implement POST /certificates/export endpoint in `app/api/routers/certificates.py` -- requires auth, accepts filter body, returns StreamingResponse with text/csv content type and Content-Disposition header for download
- [ ] T032 [US3] Verify GET /certificates/{cert_id}/pdf works from registry flow -- reuse existing PDF endpoint (T020), ensure it works from the registry UI flow

**Checkpoint**: Admin can list all certs with pagination, search by name/ID, filter by track, export filtered results as CSV, and download PDFs from the list.

---

## Phase 6: User Story 4 -- Cross-System Integration (Priority: P4)

**Goal**: Other modules (CRM, Academics, Finance, Notifications) call certificate service programmatically

**Independent Test**: Import CertificateService from another module, call generate() via Protocol interface, verify cert_id returned

### Implementation for User Story 4

- [ ] T033 [US4] Verify Protocol interface compliance -- ensure CertificateService satisfies CertificateServiceInterface Protocol (runtime_checkable). Add assertion test or type check
- [ ] T034 [US4] Implement CertificateCrudService.revoke() in `app/modules/certificates/services/certificate_crud_service.py` -- look up by cert_id, check not already revoked, set revoked_at and revoked_reason, flush, log audit entry (action='revoked'), commit, return CertificateReadDTO
- [ ] T035 [US4] Implement POST /certificates/{cert_id}/revoke endpoint in `app/api/routers/certificates.py` -- requires certificates.generate permission, accepts RevokeCertificateInput, returns ApiResponse[CertificateReadDTO]. Handle 409 if already revoked
- [ ] T036 [US4] Document cross-module usage pattern -- add docstring/example in `app/modules/certificates/__init__.py` showing how to import and call from another module (Academics, Finance, etc.)
- [ ] T037 [US4] Ensure notifications integration point -- verify that generate() returns cert_id that can be passed to NotificationService for email/WhatsApp delivery (no implementation, just interface compatibility)

**Checkpoint**: Other modules can import and use CertificateService via Protocol interface. Revocation works. Cross-module contract is documented.

---

## Phase 7: Polish and Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T038 [P] Add permission constants to Auth module registration -- register `certificates.generate` and `certificates.verify` permissions in the Auth/roles system
- [ ] T039 [P] Add certificate module to app module registry -- ensure `app/modules/certificates` is discoverable and its router is registered in the FastAPI app factory
- [ ] T040 Run quickstart.md validation -- execute all 10 validation scenarios from `specs/001-certificate-service/quickstart.md` and verify expected outcomes
- [ ] T041 Code cleanup -- remove old files that are now in the module, ensure no duplicate code, verify "assests" typo is corrected everywhere

---

## Dependencies and Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies, start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 completion, BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Phase 2, generates cert_id, PDF, core flow
- **US2 (Phase 4)**: Depends on Phase 2, can run parallel with US1 (uses same models/service)
- **US3 (Phase 5)**: Depends on Phase 2, can run parallel with US1/US2 (pagination/filter on same models)
- **US4 (Phase 6)**: Depends on Phase 2, can run parallel with US1/US2/US3 (Protocol compliance + revoke)
- **Polish (Phase 7)**: Depends on all user stories complete

### User Story Dependencies

- **US1 (P1)**: Can start after Phase 2. No dependencies on other stories.
- **US2 (P2)**: Can start after Phase 2. Uses CertificateReadDTO from US1 but is independently testable.
- **US3 (P3)**: Can start after Phase 2. Uses same repository/service layer but is independently testable.
- **US4 (P4)**: Can start after Phase 2. Protocol interface exists from Phase 2. Revoke is independent.

### Within Each User Story

- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- T002, T003, T004 can run in parallel (Setup)
- T005, T006, T007, T008 can run in parallel (Foundational models/interfaces)
- T011, T012, T013, T014, T015 can run in parallel (Foundational DTOs/validators)
- T038, T039 can run in parallel (Polish)

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. STOP and VALIDATE: Test User Story 1 independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational: Foundation ready
2. Add User Story 1: Test independently, Deploy/Demo (MVP!)
3. Add User Story 2: Test independently, Deploy/Demo
4. Add User Story 3: Test independently, Deploy/Demo
5. Add User Story 4: Test independently, Deploy/Demo
6. Each story adds value without breaking previous stories

---

## Task Summary

- **Total tasks**: 41
- **Phase 1 (Setup)**: 4 tasks
- **Phase 2 (Foundational)**: 11 tasks
- **Phase 3 (US1 - Generate)**: 9 tasks
- **Phase 4 (US2 - Validate)**: 3 tasks
- **Phase 5 (US3 - Registry)**: 5 tasks
- **Phase 6 (US4 - Integration)**: 5 tasks
- **Phase 7 (Polish)**: 4 tasks
