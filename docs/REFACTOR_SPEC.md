# ContactLoop Refactor Specification (v1)

This document is the single source of truth for the parallel refactor. Every agent/worktree MUST follow it exactly. Do not deviate from file ownership, naming, or API contracts defined here.

## 1. Goals

1. Rebuild the backend from scratch as a Python **FastAPI** application under `backend/`.
2. Keep **Supabase (Postgres)** as the primary database, with an automatic **local SQLite fallback** when no Supabase/DB connection is configured.
3. Normalize all entities with audit columns: `created_at`, `updated_at`, `created_by`, `updated_by`, plus **soft delete** via `deleted_at`.
4. Normalize the DAO layer (repository pattern, uniform interface).
5. Provide complete, consistent CRUD REST APIs for all entities (no missing verbs).
6. Refactor the frontend data layer to call the FastAPI backend (fetch-based client behind a compatibility facade); keep the existing exported function names so UI code keeps working.
7. Full test suites (backend pytest + frontend node --test).

## 2. Target architecture

```
backend/
  app/
    __init__.py
    main.py                  # FastAPI app factory, CORS, exception handlers, health
    core/
      config.py              # pydantic-settings Settings
      database.py            # engine/session selection: Supabase Postgres or SQLite fallback
      types.py               # portable UUID/JSON type decorators for SQLite compatibility
      softdelete.py          # SoftDeleteQuery / helpers (if needed)
    models/
      base.py                # DeclarativeBase + AuditMixin
      student.py
      guardian.py
      contact_event.py
      follow_up.py
      teacher_note.py
      ai_contact_brief.py
    dao/
      base.py                # BaseDAO: get/list/create/update/soft_delete with audit stamping
      student_dao.py
      guardian_dao.py
      contact_event_dao.py
      follow_up_dao.py
      teacher_note_dao.py
      ai_contact_brief_dao.py
    schemas/
      common.py              # Page/Error envelope helpers
      student.py guardian.py contact_event.py follow_up.py teacher_note.py ai_brief.py dashboard.py import_students.py
    api/
      deps.py                # DB session dependency, current-user dependency
      v1/
        router.py            # aggregates all v1 routers
        students.py guardians.py contact_events.py follow_ups.py teacher_notes.py ai_briefs.py dashboard.py imports.py voice.py
  requirements.txt           # fastapi, uvicorn[standard], sqlalchemy>=2, pydantic, pydantic-settings, httpx, pytest, python-multipart
  .env.example
  README.md
  data/                      # SQLite file + uploaded voice notes (gitignored except .gitkeep)
  tests/                     # pytest suite (owned by the tests worktree)
```

### Database selection (core/database.py)

- Priority: `SUPABASE_DB_URL` (full Postgres DSN, e.g. `postgresql+psycopg://...`) → `DATABASE_URL` (generic override) → **SQLite fallback** `sqlite:///<SQLITE_PATH>` (default `./data/contactloop.db`, created automatically with parent dirs).
- Use SQLAlchemy 2.0 style (`DeclarativeBase`, `Mapped`, `mapped_column`), sync engine, `sessionmaker`.
- All tables are created via `Base.metadata.create_all(engine)` on startup (idempotent). UUID primary keys use a portable `TypeDecorator` over `CHAR(36)`/`uuid` so the same models work on Postgres and SQLite. JSON columns use `sqlalchemy.JSON` (works on both).
- `Settings` (pydantic-settings) reads env with prefix-free names: `SUPABASE_DB_URL`, `DATABASE_URL`, `SQLITE_PATH`, `SUPABASE_JWT_SECRET` (optional), `CORS_ORIGINS` (default `*`), `APP_ENV`.
- Expose which mode is active via `GET /api/v1/meta` → `{"database": "postgres"|"sqlite", "app_env": ...}`.

### Audit + soft delete (models/base.py)

`AuditMixin` provides, on EVERY entity:

```
id           UUID PK (client-side uuid4 default)
created_at   timestamptz  not null, server_default now()
updated_at   timestamptz  not null, server_default now(), onupdate now()
created_by   UUID | null   (who created this record)
updated_by   UUID | null   (who last modified it)
deleted_at   timestamptz | null   (soft delete marker; null = alive)
```

Rules:
- `BaseDAO` stamps `created_at/created_by` on create and `updated_at/updated_by` on every update (ORM `onupdate` for `updated_at`; explicit stamp for `updated_by`).
- ALL queries exclude rows where `deleted_at IS NOT NULL` (default query filters).
- `DELETE` endpoints perform soft delete: set `deleted_at` (and `updated_by`). No hard deletes from the API.
- `updated_at` must change on every mutation.

### Entities (normalized)

- `students`: `name`, `first_name?`, `last_name?`, `initials`, `accent` (default `'sage'`), `owner_id` UUID|null (Supabase auth user). Audit columns.
- `guardians`: `student_id` FK→students, `name`, `relation`, `phone` (nullable), `email?`, `preferred_contact_method?`. Audit columns.
- `contact_events`: `student_id` FK, `guardian_id` FK, `call_time` (default now), `duration_seconds?`, `result` in (Connected, No Answer, Busy, Failed), `attempt_number` int >0, `topic?`, `planned_topic?`, `discussed_topics` JSON list, `teacher_note?`, `follow_up_id` FK?→follow_ups, `provider?`, `provider_call_id?`, `provider_status?`, `started_at?`, `ended_at?`. Audit columns.
- `follow_ups`: `student_id` FK, `guardian_id?` FK, `due_at`, `status` in (open, completed, dismissed), `contact_event_id?` FK→contact_events, `completed_at?` (NEW: set when status becomes completed). Audit columns. Partial unique index "one open follow-up per (student_id, guardian_id)".
- `teacher_notes`: `student_id` FK, `contact_event_id?` FK, `content` (non-empty), `source` in (typed, voice), `teacher_confirmed` bool default false. Audit columns.
- `ai_contact_briefs`: `student_id` FK, `date_from`, `date_to`, `version` int >0, `status` in (draft, approved, superseded), `key_topics`/`parent_concerns`/`recorded_resolutions`/`open_items` JSON lists, `suggested_next_step?`, `generated_at`, `approved_at?`. Audit columns. Unique (student_id, date_from, date_to, version).

### Business rules (must be enforced in backend, replicated from the old Postgres trigger)

On contact-event create/update where `ended_at` is not null:
- `result == 'Connected'` → complete the open follow-up for (student_id, guardian_id): set `status='completed'`, `completed_at`, `contact_event_id=event.id`.
- `result in (No Answer, Busy, Failed)` → upsert the open follow-up for (student_id, guardian_id): `due_at = ended_at + 1 day` unless a `follow_up_due_at` was supplied by the caller; link `contact_event_id=event.id`.
- `attempt_number` is always computed server-side: previous attempts for the same (student_id, guardian_id) + 1.
- If a `follow_up_id` was supplied by the caller, prefer closing/updating that one.

## 3. REST API contract (prefix `/api/v1`, JSON, snake_case fields)

Standard response codes: 200 (ok), 201 (created), 204 (no content for DELETE), 400 (validation), 404 (missing), 409 (conflict, e.g. duplicate open follow-up). Errors: FastAPI style `{"detail": "message"}`.

Auth: optional. `GET /api/v1/health` → `{"status":"ok"}`; `GET /api/v1/meta`.

- `students`
  - `GET /students?search=` (search matches name/initials/guardian name/phone; includes guardians in response)
  - `POST /students` `{name, first_name?, last_name?, initials?, accent?, guardians:[{name, relation, phone, email?, preferred_contact_method?}]}` → 201 student (with guardians)
  - `GET /students/{id}` / `PATCH /students/{id}` / `DELETE /students/{id}` (soft delete cascades to the student's guardians, contact_events, follow_ups, teacher_notes, ai_contact_briefs — all soft)
- `guardians`
  - `GET /guardians?student_id=` / `POST /guardians` `{student_id, name, relation, phone?, email?, preferred_contact_method?}` / `GET/PATCH/DELETE /guardians/{id}` (soft)
- `contact-events`
  - `GET /contact-events?student_id=&from=&to=&result=`
  - `POST /contact-events` `{student_id, guardian_id, result, duration_seconds?, planned_topic?, discussed_topics?, topic?, teacher_note?, follow_up_due_at?, call_time?}` → 201 (server computes `attempt_number`, runs follow-up sync)
  - `GET /contact-events/{id}` / `PATCH /contact-events/{id}` (re-runs follow-up sync if result/ended_at changed) / `DELETE /contact-events/{id}` (soft)
- `follow-ups`
  - `GET /follow-ups?status=&student_id=` / `POST /follow-ups` `{student_id, guardian_id?, due_at, status?}` / `GET /follow-ups/{id}` / `PATCH /follow-ups/{id}` (status transitions) / `DELETE /follow-ups/{id}` (soft)
- `teacher-notes`
  - `GET /teacher-notes?student_id=` / `POST /teacher-notes` `{student_id, contact_event_id?, content, source?}` / `GET /teacher-notes/{id}` / `PATCH /teacher-notes/{id}` / `DELETE /teacher-notes/{id}` (soft)
- `ai-briefs`
  - `GET /ai-briefs?student_id=&latest=true`
  - `POST /ai-briefs` `{student_id, date_from, date_to, version?, status?, key_topics?, parent_concerns?, recorded_resolutions?, open_items?, suggested_next_step?}`
  - `GET /ai-briefs/{id}` / `PATCH /ai-briefs/{id}` / `DELETE /ai-briefs/{id}` (soft)
  - `POST /ai-briefs/{id}/approve` → sets status approved + approved_at
  - `POST /ai-briefs/{id}/supersede` → sets status superseded
- Aggregates
  - `GET /data/load` → `{students:[...with guardians...], events:[...], follow_ups:[...open...], teacher_notes:[...], ai_briefs:[...not superseded...]}` (mirrors the old `loadContactLoopData`)
  - `POST /import/students` `{students:[{student_key, first_name?, last_name?, name}], guardians:[{student_key, name, relationship, phone?, email?}]}` → `{imported_students: n, imported_guardians: m}` (idempotent upsert by student_key+owner)
  - `GET /dashboard/summary?from=&to=` → `{call_attempts, connected, unsuccessful, follow_ups_due}`
- Voice (local-mode stub)
  - `POST /voice/uploads` `{student_id, content_type}` → `{upload_url, object_key}` where `upload_url` points at `PUT /voice/files/{object_key}` (stores under `backend/data/voice_notes/`)
  - `POST /voice/transcriptions` `{student_id, object_key}` → `{job_id}`
  - `GET /voice/transcriptions/{job_id}` → `{status: "completed", transcript: "(Voice note saved locally. Transcription is not configured.)"}` — stub keeps the UI flow working in local mode.
- `POST /ai/contact-brief/generate` → 501 with a clear message unless an AI provider env is configured (reserved; disabled by default, same as today).

## 4. Frontend data layer

- New `src/lib/api/` package: `client.js` (fetch wrapper: base URL from `VITE_API_BASE_URL`, JSON encode/decode, error normalization to `Error` with `.detail`), plus per-entity modules implementing the API contract above.
- `src/lib/supabase.js` becomes a **compatibility facade**: keeps every existing exported name (`loadContactLoopData`, `importStudents`, `createContactEvent`, `updateFollowUp`, `createStudent`, `updateStudent`, `deleteStudent`, `saveAiContactBrief`, `updateAiContactBrief`, `supersedeAiContactBrief`, `approveAiContactBrief`, `removeAiContactBrief`, `createTeacherNote`, `createVoiceUpload`, `startVoiceTranscription`, `getVoiceTranscriptStatus`, `invokeContactBrief`) with the same call/return shapes, now backed by the FastAPI client. It also exports the new full-CRUD functions: `listGuardians`, `createGuardian`, `updateGuardian`, `deleteGuardian`, `updateContactEvent`, `deleteContactEvent`, `listFollowUps`, `createFollowUp`, `deleteFollowUp`, `updateTeacherNote`, `deleteTeacherNote`, `hasBackendConfig`.
- UI code (`src/app.js`) continues to import from `./lib/supabase.js` — no import churn required.
- `.env.example` gains `VITE_API_BASE_URL=http://localhost:8000`.

## 5. File ownership (strict, to keep parallel worktrees conflict-free)

- `backend-core` owns: `backend/app/core/**`, `backend/app/models/**`, `backend/app/dao/**`, `backend/requirements.txt`, `backend/README.md`, `backend/.env.example`, `backend/data/.gitkeep`, `backend/.gitignore`.
- `backend-api` owns: `backend/app/main.py`, `backend/app/__init__.py`, `backend/app/schemas/**`, `backend/app/api/**`. Must NOT create requirements.txt or touch core/models/dao (they arrive via merge).
- `frontend-api` owns: `src/lib/api/**`, `src/lib/supabase.js`, `.env.example`.
- `frontend-ui` owns: `src/app.js`, `src/styles.css`, `src/lib/*.js` EXCEPT `src/lib/supabase.js` and `src/lib/api/**`.
- `tests` owns: `backend/tests/**`, `tests/**` (frontend). Must not modify application code; report needed fixes in its final summary instead.

## 6. Test requirements

- Backend (pytest, `backend/tests/`): in-memory SQLite via `SQLITE_PATH` or a test fixture; cover health/meta, full CRUD for every entity, audit stamping (created_at/updated_at/created_by/updated_by present and mutating), soft delete (row hidden after DELETE, cascade for student delete), follow-up sync rules (Connected completes open FU with completed_at; No Answer/Busy/Failed upserts open FU due next day; unique open per student+guardian), attempt_number sequencing, import upsert, voice stub flow, error codes (404/400/409).
- Frontend (node --test): update/extend tests for the new api modules with mocked fetch; keep all existing passing tests green (fix only tests owned in `tests/**`).

## 7. Conventions

- Python 3.11+, SQLAlchemy 2.0 typed style, no comments/docstrings bloat, module docstrings only where non-obvious.
- Keep IDs as UUID strings in JSON.
- Do not remove Supabase-related env/docs; the Supabase Postgres target stays first-class.
- Each worktree MUST commit all of its work before finishing (single clean commit preferred).
