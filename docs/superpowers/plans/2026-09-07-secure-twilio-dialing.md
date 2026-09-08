# Secure Twilio Dialing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restore ContactLoop's existing Twilio call flow without giving the browser a Supabase secret or direct database access.

**Architecture:** The frontend submits a selected, owned student ID and optional planned topic to a FastAPI endpoint using its existing bearer token. FastAPI verifies the user owns the student, then invokes the already-deployed Supabase `start-call` Edge Function with the server-only legacy `service_role` key. A second protected FastAPI endpoint proxies the existing `sync-call-status` Function only after confirming the current user owns the requested contact event. The Edge Functions retain their existing Twilio credentials and remain the only components that call Twilio.

**Tech Stack:** Vanilla JavaScript/Vite, FastAPI, SQLAlchemy, httpx, existing Supabase Edge Function, Twilio.

## Global Constraints

- Do not create, replace, or deploy a Lambda, Edge Function, Twilio resource, or Supabase project resource.
- Do not put `SUPABASE_SECRET_KEY` or any Twilio secret in `VITE_*`, browser storage, source control, test output, or chat.
- Do not make a live Twilio call in automated or manual verification.
- Require existing FastAPI bearer authentication and `students.owner_id` validation before invoking `start-call`.
- Keep Demo data fictitious; do not add or query non-Demo student content.

---

### Task 1: Add a server-only existing-Function client

**Files:**
- Modify: `backend/app/core/config.py`
- Create: `backend/app/services/supabase_functions.py`
- Test: `backend/tests/test_supabase_functions.py`

**Interfaces:**
- Consumes: `SUPABASE_URL`, `SUPABASE_SECRET_KEY` from `backend/.env`.
- Produces: `invoke_start_call(student_id: UUID, planned_topic: str | None) -> dict` and `invoke_call_status_sync(event_id: UUID) -> dict`.

- [x] **Step 1: Write the failing tests**

```python
def test_start_call_posts_only_student_and_topic(monkeypatch):
    captured = {}
    monkeypatch.setattr(httpx, "post", lambda url, **kwargs: captured.update(url=url, **kwargs) or Response(200, json={"eventId": "event-1"}))
    assert invoke_start_call(UUID("11111111-1111-4111-8111-111111111111"), "Behavior") == {"eventId": "event-1"}
    assert captured["json"] == {"studentId": "11111111-1111-4111-8111-111111111111", "plannedTopic": "Behavior"}

def test_start_call_never_attempts_network_without_server_configuration(monkeypatch):
    monkeypatch.setattr(settings, "supabase_secret_key", None)
    with pytest.raises(ServiceUnavailableError):
        invoke_start_call(UUID("11111111-1111-4111-8111-111111111111"), None)
```

- [x] **Step 2: Run the new test**

Run: `pytest backend/tests/test_supabase_functions.py -q`

Expected: FAIL because the Function client does not exist yet.

- [x] **Step 3: Implement the minimal client**

```python
def invoke_start_call(student_id: UUID, planned_topic: str | None) -> dict:
    if not settings.supabase_url or not settings.supabase_secret_key:
        raise ServiceUnavailableError("Twilio calling is not configured on this server.")
    response = httpx.post(
        f"{settings.supabase_url.rstrip('/')}/functions/v1/start-call",
        headers={"apikey": settings.supabase_secret_key, "Authorization": f"Bearer {settings.supabase_secret_key}"},
        json={"studentId": str(student_id), "plannedTopic": planned_topic},
        timeout=15,
    )
    response.raise_for_status()
    return response.json()
```

- [x] **Step 4: Run the new test**

Run: `pytest backend/tests/test_supabase_functions.py -q`

Expected: PASS without making a network request.

### Task 2: Add protected FastAPI call and status endpoints

**Files:**
- Create: `backend/app/api/v1/telephony.py`
- Modify: `backend/app/api/v1/router.py`
- Test: `backend/tests/test_telephony.py`

**Interfaces:**
- Consumes: `POST /api/v1/telephony/calls` JSON `{ "student_id": UUID, "planned_topic": string | null }` and `POST /api/v1/telephony/call-status-sync` JSON `{ "event_id": UUID }`, both with FastAPI bearer token.
- Produces: existing Function response JSON; call start requires `require_owned_student`, while an event-specific status sync requires `require_owned_resource(ContactEvent, event_id, owner_id, "Contact event")`.

- [x] **Step 1: Write the failing tests**

```python
def test_start_call_requires_login(anonymous_client, make_student):
    student = make_student(guardians=[])
    assert anonymous_client.post("/api/v1/telephony/calls", json={"student_id": student["id"]}).status_code == 401

def test_start_call_rejects_other_users_student(client, second_auth, make_student):
    student = make_student(guardians=[])
    response = client.post("/api/v1/telephony/calls", json={"student_id": student["id"]}, headers=second_auth["headers"])
    assert response.status_code == 404

def test_call_status_sync_rejects_other_users_event(client, second_auth, make_student, make_event):
    student = make_student(guardians=[])
    event = make_event(student["id"])
    response = client.post("/api/v1/telephony/call-status-sync", json={"event_id": event["id"]}, headers=second_auth["headers"])
    assert response.status_code == 404
```

- [x] **Step 2: Run the new test**

Run: `pytest backend/tests/test_telephony.py -q`

Expected: FAIL because the route does not exist.

- [x] **Step 3: Implement the minimal endpoint**

```python
@router.post("/calls")
def start_call(payload: StartCallRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    require_owned_student(db, payload.student_id, user.id)
    return invoke_start_call(payload.student_id, payload.planned_topic)

@router.post("/call-status-sync")
def sync_call_status(payload: CallStatusSyncRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    require_owned_resource(db, ContactEvent, payload.event_id, user.id, "Contact event")
    return invoke_call_status_sync(payload.event_id)
```

- [x] **Step 4: Run the new test**

Run: `pytest backend/tests/test_telephony.py -q`

Expected: PASS with the outbound Function client monkeypatched; no Twilio request occurs.

### Task 3: Route the frontend through FastAPI and preserve the contact picker

**Files:**
- Modify: `src/lib/telephony.js`
- Modify: `tests/telephony.test.js`
- Modify: `.env` (local, ignored) only after tests pass

**Interfaces:**
- Consumes: `POST /api/v1/telephony/calls` through `apiFetch`.
- Produces: `getTelephonyProvider().startCall(studentId, { plannedTopic })` without any browser Supabase client.

- [x] **Step 1: Write the failing test**

```javascript
test('Twilio provider sends the selected student and topic through FastAPI', async () => {
  const requests = [];
  globalThis.fetch = async (url, init) => { requests.push({ url, init }); return new Response('{"eventId":"event-1"}', { status: 200 }); };
  await new TwilioTelephonyProvider().startCall('student-1', { plannedTopic: 'Behavior' });
  assert.deepEqual(requests[0], { url: 'http://127.0.0.1:8000/api/v1/telephony/calls', init: { method: 'POST', body: JSON.stringify({ student_id: 'student-1', planned_topic: 'Behavior' }) } });
});
```

- [x] **Step 2: Run the new test**

Run: `node --test tests/telephony.test.js`

Expected: FAIL because the provider still invokes `supabase.functions` directly.

- [x] **Step 3: Implement the minimal frontend proxy call**

```javascript
export class TwilioTelephonyProvider {
  async startCall(studentId, { plannedTopic = null } = {}) {
    return apiFetch(`${API_PREFIX}/telephony/calls`, {
      method: 'POST',
      body: { student_id: studentId, planned_topic: plannedTopic },
    });
  }

  async syncCallStatus(eventId = null) {
    if (!eventId) return { synced: [] };
    return apiFetch(`${API_PREFIX}/telephony/call-status-sync`, {
      method: 'POST',
      body: { event_id: eventId },
    });
  }
}
```

- [x] **Step 4: Set local live-call mode**

Set only the local ignored `.env` value:

```env
VITE_TELEPHONY_PROVIDER=twilio
```

Keep all `VITE_SUPABASE_*` values absent.

- [x] **Step 5: Run focused and full verification**

Run:

```bash
pytest backend/tests/test_supabase_functions.py backend/tests/test_telephony.py -q
npm test
npm run build
```

Expected: all tests and production build pass; no Twilio call occurs.

### Task 4: Verify the live path without dialing

**Files:**
- Modify: `progress.md`

- [x] **Step 1: Verify process configuration without exposing secrets**

Run a local diagnostic that prints only boolean configuration state and key role, never values.

- [x] **Step 2: Verify endpoint protections**

Run unauthenticated and cross-owner endpoint tests; both must reject before `invoke_start_call` runs.

- [x] **Step 3: Do not press Call now**

Leave real phone initiation for an explicit, user-controlled click after the implementation has been handed off.
