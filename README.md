# ContactLoop

Parent-contact tracker for special-education teams. Vanilla JS + Vite frontend, FastAPI backend, Supabase Postgres or local SQLite storage.

## Quick start (local, SQLite)

1. Backend (Python 3.11+):

   ```
   cd backend
   python -m venv .venv
   .venv\Scripts\pip install -r requirements.txt        # Windows
   # source .venv/bin/activate && pip install -r requirements.txt  # macOS/Linux
   .venv\Scripts\python -m uvicorn app.main:app --port 8000
   ```

   With no `SUPABASE_DB_URL` / `DATABASE_URL` set, the backend automatically uses SQLite at `backend/data/contactloop.db`.

2. Frontend: create `.env.local` in the repo root:

   ```
   VITE_API_BASE_URL=http://localhost:8000
   VITE_APP_MODE=demo
   ```

   then `npm install && npm run dev`.

## Docker deployment

```
docker compose up --build
```

- Frontend: http://localhost:8080 (nginx serves the built SPA and proxies `/api/` to the backend)
- Backend data persists in the `contactloop-data` volume (SQLite)
- To use Supabase instead: set `SUPABASE_DB_URL` in `docker-compose.yml` (see comments)

## Tests

- Frontend: `npm test`
- Backend: `npm run test:backend` (or `python -m pytest backend/tests`)

See `docs/REFACTOR_SPEC.md` for the architecture and API contract.
