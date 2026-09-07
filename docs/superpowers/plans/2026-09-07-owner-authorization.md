# Owner Authorization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Require FastAPI login for every business endpoint and prevent one account from reading or mutating another account's students or related records.

**Architecture:** Keep the existing FastAPI `users` and `auth_tokens` authentication. Add focused ownership lookup helpers that resolve resources through `students.owner_id`; API routes use the authenticated `User` and return 404 for both missing and foreign-owned resources. Existing list DAOs continue to apply owner filters.

**Tech Stack:** Python 3.14, FastAPI, SQLAlchemy 2, pytest, SQLite test database.

## Global Constraints

- Do not modify or merge `main` and do not push.
- Do not access or modify Supabase or AWS in this plan.
- `/auth/register`, `/auth/login`, health, and meta remain public.
- Every business endpoint requires a valid FastAPI bearer token.
- Cross-owner access and missing resources both return 404.
- Client-provided `X-User-Id` never establishes identity or audit ownership.
- Keep changes surgical; do not refactor unrelated CRUD behavior.

---

### Task 1: Authenticated test baseline and student ownership

**Files:**
- Modify: `backend/tests/conftest.py`
- Modify: `backend/tests/test_students.py`
- Create: `backend/app/services/ownership.py`
- Modify: `backend/app/api/v1/students.py`
- Modify: `backend/app/api/deps.py`

**Interfaces:**
- Produces: `require_owned_student(db: Session, student_id: UUID, owner_id: UUID) -> Student`.
- Produces: pytest fixtures `anonymous_client`, `auth_user`, `auth_headers`, and `second_auth`.
- Consumes: existing `get_current_user() -> User`, `StudentDAO.list(owner_id=...)`, and `NotFoundError`.

- [ ] **Step 1: Add authenticated fixtures and failing student authorization tests**

  Make the existing `client` fixture register one default account and attach its bearer token to `client.headers`. Add an independent `anonymous_client`, expose the default user/headers, and add `second_auth` returning a second user's headers. Add tests proving: anonymous student list/create/get/update/delete return 401; the default user sees their own student; the second user receives 404 for get/update/delete and cannot see it in list results; `X-User-Id` cannot spoof ownership.

- [ ] **Step 2: Run the focused tests and verify RED**

  Run: `.venv/bin/python -m pytest backend/tests/test_students.py -q`

  Expected: authorization tests fail because student routes still accept anonymous requests and ID routes do not enforce owner.

- [ ] **Step 3: Implement minimal student authorization**

  Add `require_owned_student` using a SQLAlchemy `select(Student)` constrained by `Student.id`, `Student.owner_id`, and `Student.deleted_at.is_(None)`. If no row exists, raise `NotFoundError("student not found")`.

  Change every student route to depend on `get_current_user`. Use `user.id` for list filtering, `owner_id`, `created_by`, and `updated_by`. Call `require_owned_student` before get, patch, and delete. Remove trust in `X-User-Id` from the student path.

- [ ] **Step 4: Run focused tests and verify GREEN**

  Run: `.venv/bin/python -m pytest backend/tests/test_students.py backend/tests/test_auth.py -q`

  Expected: all selected tests pass.

- [ ] **Step 5: Commit Task 1 locally**

  Commit only the files in Task 1 with message: `fix: enforce student ownership`.

---

### Task 2: Related-resource ownership

**Files:**
- Modify: `backend/app/services/ownership.py`
- Modify: `backend/app/api/v1/guardians.py`
- Modify: `backend/app/api/v1/contact_events.py`
- Modify: `backend/app/api/v1/follow_ups.py`
- Modify: `backend/app/api/v1/teacher_notes.py`
- Modify: `backend/app/api/v1/ai_briefs.py`
- Modify: `backend/tests/test_guardians.py`
- Modify: `backend/tests/test_contact_events.py`
- Modify: `backend/tests/test_follow_ups.py`
- Modify: `backend/tests/test_teacher_notes.py`
- Modify: `backend/tests/test_ai_briefs.py`
- Modify: `backend/tests/conftest.py`

**Interfaces:**
- Consumes: `require_owned_student(...)` from Task 1.
- Produces: `require_owned_resource(db: Session, model: type, resource_id: UUID, owner_id: UUID, label: str) -> object`.

- [ ] **Step 1: Add failing cross-owner tests for every resource family**

  For guardian, contact event, follow-up, teacher note, and AI brief, add tests proving: anonymous list/create/get/update/delete return 401; user B cannot list records belonging to user A; user B receives 404 for ID get/update/delete; user B cannot create a record under user A's student. For approve/supersede AI brief actions, require the same 404 behavior.

- [ ] **Step 2: Run the five focused modules and verify RED**

  Run: `.venv/bin/python -m pytest backend/tests/test_guardians.py backend/tests/test_contact_events.py backend/tests/test_follow_ups.py backend/tests/test_teacher_notes.py backend/tests/test_ai_briefs.py -q`

  Expected: new anonymous and cross-owner cases fail against the current permissive ID routes.

- [ ] **Step 3: Implement minimal resource ownership helper and route checks**

  Implement `require_owned_resource` as a query joining the resource model's `student_id` to an alive `Student` whose `owner_id` equals the authenticated user. Return the resource or raise `NotFoundError(f"{label} not found")`.

  On create, first call `require_owned_student` for the payload's `student_id`. On list, pass `owner_id=user.id`. On get/update/delete and AI approve/supersede, resolve ownership before invoking the existing DAO mutation. Use `user.id` for audit stamping.

- [ ] **Step 4: Run the focused modules and verify GREEN**

  Run: `.venv/bin/python -m pytest backend/tests/test_guardians.py backend/tests/test_contact_events.py backend/tests/test_follow_ups.py backend/tests/test_teacher_notes.py backend/tests/test_ai_briefs.py -q`

  Expected: all selected tests pass.

- [ ] **Step 5: Commit Task 2 locally**

  Commit only Task 2 files with message: `fix: isolate student-related resources by owner`.

---

### Task 3: Aggregate, import, voice, and Agent route protection

**Files:**
- Modify: `backend/app/api/v1/dashboard.py`
- Modify: `backend/app/api/v1/imports.py`
- Modify: `backend/app/api/v1/voice.py`
- Modify: `backend/app/api/v1/ai_briefs.py`
- Modify: `backend/tests/test_dashboard.py`
- Modify: `backend/tests/test_import.py`
- Modify: `backend/tests/test_voice.py`
- Modify: `backend/tests/test_outreach_plan.py`

**Interfaces:**
- Consumes: authenticated `User` from `get_current_user` and ownership helpers from Tasks 1–2.
- Preserves: public `/api/health`, `/api/v1/health`, `/api/v1/meta`, `/api/v1/auth/register`, and `/api/v1/auth/login`.

- [ ] **Step 1: Add failing anonymous-access and owner-scope tests**

  Add tests proving dashboard load/summary, student import, voice upload/transcription/status, Contact Brief stub, and Outreach Plan return 401 without a bearer token. Confirm authenticated dashboard/import/voice behavior remains functional and Outreach Plan candidates contain only the current user's students.

- [ ] **Step 2: Run the focused tests and verify RED**

  Run: `.venv/bin/python -m pytest backend/tests/test_dashboard.py backend/tests/test_import.py backend/tests/test_voice.py backend/tests/test_outreach_plan.py backend/tests/test_ai_briefs.py -q`

  Expected: currently anonymous dashboard/import/voice/Contact Brief paths fail the new expectations.

- [ ] **Step 3: Require authentication and apply owner checks**

  Replace optional `get_current_user_id` dependencies with `get_current_user`. Require `User` on all voice and Contact Brief routes. For any voice or AI request containing a student ID, call `require_owned_student` before processing. Keep health/meta/auth public.

- [ ] **Step 4: Run the full backend suite**

  Run: `.venv/bin/python -m pytest backend/tests -q`

  Expected: all backend tests pass with zero failures.

- [ ] **Step 5: Run frontend contracts and build**

  Run: `npm test`

  Expected: all frontend tests pass.

  Run: `npm run build`

  Expected: production build exits 0; the existing bundle-size warning is acceptable.

- [ ] **Step 6: Verify diff and public/private boundary**

  Run: `git diff --check`

  Run authenticated and anonymous requests against a temporary TestClient or local backend. Expected: public endpoints return 200/expected auth result; every business endpoint returns 401 anonymously; cross-owner IDs return 404.

- [ ] **Step 7: Commit Task 3 locally**

  Commit only Task 3 files with message: `fix: require authentication across business APIs`.

---

### Completion gate

- [ ] Re-read `docs/superpowers/specs/2026-09-07-fastapi-supabase-owner-security-design.md` and confirm every API authorization rule is covered.
- [ ] Record exact test counts and any warnings in `progress.md`.
- [ ] Do not begin Supabase migration until this authorization plan is green.
