# ContactLoop Backend

FastAPI backend for ContactLoop. Supabase (Postgres) stays the primary database with
an automatic local SQLite fallback, so the app runs with zero configuration.

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

`app/main.py`, `app/schemas/`, and `app/api/` are owned by a separate worktree and
arrive via merge.

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate     # Windows
# source .venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
cp .env.example .env
```

## Configuration

| Variable | Default | Purpose |
| --- | --- | --- |
| `SUPABASE_DB_URL` | - | Full Postgres DSN (`postgresql+psycopg://...`). Highest priority. |
| `DATABASE_URL` | - | Generic SQLAlchemy URL override. |
| `SQLITE_PATH` | `./data/contactloop.db` | SQLite fallback database file (parent dirs created automatically). |
| `SUPABASE_JWT_SECRET` | - | Optional Supabase JWT secret. |
| `CORS_ORIGINS` | `*` | Comma-separated allowed CORS origins. |
| `APP_ENV` | `development` | Environment name surfaced by the meta endpoint. |

## Smoke test

`scripts/dao_smoke.py` exercises every DAO against a temporary SQLite file: CRUD,
audit stamping, soft-delete visibility, follow-up sync for all four call results,
attempt numbering, duplicate open follow-up conflicts, AI brief approve/supersede,
teacher note CRUD, and the student soft-delete cascade:

```bash
python scripts/dao_smoke.py
```
