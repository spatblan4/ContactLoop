# ContactLoop Backend

FastAPI is ContactLoop's authentication, authorization, and integration boundary.
The browser uses this REST API for application data and never receives Supabase
service credentials, AWS credentials, or the Contact Brief Lambda endpoint.

Supabase Postgres is the shared Demo database. SQLite remains available as a local
fallback when neither `SUPABASE_DB_URL` nor `DATABASE_URL` is configured.

## Layout

- `app/core/` - configuration (pydantic-settings), engine/session selection, portable
  UUID/JSON column types, shared exceptions.
- `app/models/` - SQLAlchemy 2.0 declarative models: `AuditMixin`
  (`id`, `created_at`, `updated_at`, `created_by`, `updated_by`, soft delete via
  `deleted_at`) on every entity: students, guardians, contact_events, follow_ups,
  teacher_notes, ai_contact_briefs.
- `app/dao/` - repository layer. `BaseDAO` provides get/list/create/update/soft_delete
  with audit stamping; all queries exclude soft-deleted rows. `ContactEventDAO`
  enforces the follow-up sync rules (Connected completes the open follow-up;
  No Answer/Busy/Failed upsert an open follow-up due `ended_at + 1 day` unless
  `follow_up_due_at` is supplied), server-computed `attempt_number`, and student
  soft delete cascades to all dependent rows.
- `app/api/` - authenticated REST endpoints for application data, integrations, and
  Agent generation.
- `app/services/ownership.py` - owner checks for teacher-scoped resources.
- `app/services/outreach_plan.py` - builds minimized, owner-scoped Agent candidates.
- `app/services/outreach_plan_agent.py` - runs the real local Strands Agent with
  Amazon Bedrock.
- `app/services/contact_brief_client.py` - calls the existing Contact Brief Lambda
  only after FastAPI verifies student ownership.

## Setup

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Keep real settings only in the ignored `backend/.env`. Never copy a server-only
setting into a `VITE_*` browser variable.

## Configuration

| Variable | Default | Purpose |
| --- | --- | --- |
| `SUPABASE_DB_URL` | - | Full Postgres DSN (`postgresql+psycopg://...`). Highest priority. |
| `DATABASE_URL` | - | Generic SQLAlchemy URL override. |
| `SQLITE_PATH` | `./data/contactloop.db` | SQLite fallback database file (parent dirs created automatically). |
| `SUPABASE_JWT_SECRET` | - | Optional Supabase JWT secret. |
| `SUPABASE_URL` | - | Server-side Supabase project URL used for protected Function calls. |
| `SUPABASE_SECRET_KEY` | - | Server-only key used for protected Supabase Function calls. |
| `CONTACT_BRIEF_ENDPOINT` | - | Existing Lambda endpoint; never exposed to the browser. |
| `AWS_REGION` | `us-east-2` | Bedrock region for the local Outreach Agent. |
| `BEDROCK_MODEL_ID` | - | Bedrock model for the local Outreach Agent; the Demo uses `amazon.nova-lite-v1:0`. |
| `CORS_ORIGINS` | `*` | Comma-separated browser origins allowed to call FastAPI. |
| `APP_ENV` | `development` | Environment name surfaced by the meta endpoint. |

AWS credentials are loaded through the normal server-side AWS credential provider
chain. Do not store access keys in this repository.

## Agent safety boundaries

- Every Outreach candidate is derived from the authenticated teacher's owner ID.
- Candidate context excludes phone numbers, provider IDs, tokens, and credentials.
- Agent output containing a student outside the authorized candidate set is rejected.
- Agent generation never writes a follow-up. A teacher must confirm that action.
- Contact Brief generation produces a draft that remains teacher-reviewable.

## Verification

From the `backend` directory, using the virtual environment created above:

```bash
.venv/bin/python -m pytest tests -q
```

The optional DAO smoke script exercises the portable local data layer:

`scripts/dao_smoke.py` exercises every DAO against a temporary SQLite file: CRUD,
audit stamping, soft-delete visibility, follow-up sync for all four call results,
attempt numbering, duplicate open follow-up conflicts, AI brief approve/supersede,
teacher note CRUD, and the student soft-delete cascade:

```bash
python scripts/dao_smoke.py
```
