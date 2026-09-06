"""API smoke test: exercises every REST endpoint against a temporary SQLite database.

Requires the backend requirements installed:

    backend/.venv/Scripts/python backend/scripts/api_smoke.py
"""
import base64
import hashlib
import hmac
import json
import os
import shutil
import sys
import tempfile
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

TMP_DIR = Path(tempfile.mkdtemp(prefix="contactloop_api_smoke_"))
os.environ.pop("SUPABASE_DB_URL", None)
os.environ.pop("DATABASE_URL", None)
os.environ["SQLITE_PATH"] = (TMP_DIR / "contactloop.db").as_posix()
JWT_SECRET = "smoke-test-secret"
os.environ["SUPABASE_JWT_SECRET"] = JWT_SECRET

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

PASSED = []
VOICE_FILES = []


def check(label, condition):
    if not condition:
        raise AssertionError(f"SMOKE FAILED: {label}")
    PASSED.append(label)
    print(f"ok - {label}")


def check_eq(label, actual, expected):
    if actual != expected:
        raise AssertionError(f"SMOKE FAILED: {label} (expected {expected!r}, got {actual!r})")
    PASSED.append(label)
    print(f"ok - {label}")


def parse_dt(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)


def make_jwt(claims, secret):
    header = base64.urlsafe_b64encode(
        json.dumps({"alg": "HS256", "typ": "JWT"}, separators=(",", ":")).encode()
    ).rstrip(b"=")
    payload = base64.urlsafe_b64encode(
        json.dumps(claims, separators=(",", ":")).encode()
    ).rstrip(b"=")
    signing_input = f"{header.decode()}.{payload.decode()}".encode()
    signature = base64.urlsafe_b64encode(
        hmac.new(secret.encode(), signing_input, hashlib.sha256).digest()
    ).rstrip(b"=")
    return f"{header.decode()}.{payload.decode()}.{signature.decode()}"


def assert_audit_fields(label, item, expect_created_by=None):
    for field in ("id", "created_at", "updated_at", "created_by", "updated_by"):
        check(f"{label} has audit field {field}", field in item)
    if expect_created_by is not None:
        check_eq(f"{label} created_by stamped", item["created_by"], expect_created_by)


def main():
    with TestClient(app) as client:
        run(client)
    print(f"\nAPI SMOKE OK: {len(PASSED)} checks passed (sqlite at {TMP_DIR})")
    for path in VOICE_FILES:
        Path(path).unlink(missing_ok=True)
    shutil.rmtree(TMP_DIR, ignore_errors=True)


def run(client):
    unknown = str(uuid.uuid4())

    # --- health / meta / cors -------------------------------------------------
    response = client.get("/api/health")
    check_eq("GET /api/health", (response.status_code, response.json()), (200, {"status": "ok"}))
    response = client.get("/api/v1/health")
    check_eq("GET /api/v1/health", (response.status_code, response.json()), (200, {"status": "ok"}))
    response = client.get("/api/v1/meta")
    check_eq(
        "GET /api/v1/meta reports sqlite mode",
        (response.status_code, response.json().get("database"), "app_env" in response.json()),
        (200, "sqlite", True),
    )
    response = client.get("/api/health", headers={"Origin": "http://localhost:5173"})
    check_eq(
        "CORS allows configured origins",
        response.headers.get("access-control-allow-origin"),
        "*",
    )

    # --- students: create with guardians, audit, search -----------------------
    actor = uuid.uuid4()
    editor = uuid.uuid4()
    response = client.post(
        "/api/v1/students",
        json={
            "name": "Amara Okafor",
            "first_name": "Amara",
            "last_name": "Okafor",
            "initials": "AO",
            "accent": "lavender",
            "guardians": [
                {"name": "Grace Okafor", "relation": "Mother", "phone": "+15550100"},
                {"name": "Dan Okafor", "relation": "Father", "phone": "+15550101"},
            ],
        },
        headers={"X-User-Id": str(actor)},
    )
    check_eq("POST /students status", response.status_code, 201)
    amara = response.json()
    assert_audit_fields("created student", amara, expect_created_by=str(actor))
    check_eq("student name persisted", amara["name"], "Amara Okafor")
    check_eq("student guardians embedded", len(amara["guardians"]), 2)
    assert_audit_fields("embedded guardian", amara["guardians"][0])
    grace = next(g for g in amara["guardians"] if g["name"] == "Grace Okafor")
    dan = next(g for g in amara["guardians"] if g["name"] == "Dan Okafor")

    time.sleep(0.02)
    response = client.patch(
        f"/api/v1/students/{amara['id']}",
        json={"name": "Amara Okafor-Smith"},
        headers={"X-User-Id": str(editor)},
    )
    check_eq("PATCH /students status", response.status_code, 200)
    patched = response.json()
    check_eq("student name updated", patched["name"], "Amara Okafor-Smith")
    check_eq("student created_by unchanged by update", patched["created_by"], str(actor))
    check_eq("student updated_by restamped", patched["updated_by"], str(editor))
    check(
        "student updated_at bumped on mutation",
        parse_dt(patched["updated_at"]) > parse_dt(patched["created_at"]),
    )

    response = client.get("/api/v1/students", params={"search": "Okafor-Smith"})
    check_eq("student search by name", [s["id"] for s in response.json()], [amara["id"]])
    response = client.get("/api/v1/students", params={"search": "AO"})
    check_eq("student search by initials", [s["id"] for s in response.json()], [amara["id"]])
    response = client.get("/api/v1/students", params={"search": "Grace"})
    check_eq("student search by guardian name", [s["id"] for s in response.json()], [amara["id"]])
    response = client.get("/api/v1/students", params={"search": "+15550101"})
    check_eq("student search by guardian phone", [s["id"] for s in response.json()], [amara["id"]])

    response = client.get(f"/api/v1/students/{amara['id']}")
    check_eq("GET /students/{id} status", response.status_code, 200)
    check_eq("GET /students/{id} includes guardians", len(response.json()["guardians"]), 2)
    response = client.get(f"/api/v1/students/{unknown}")
    check_eq("GET unknown student 404", response.status_code, 404)
    check("404 body uses detail envelope", "detail" in response.json())
    response = client.post("/api/v1/students", json={"first_name": "NoName"})
    check_eq("POST /students missing name 400", response.status_code, 400)

    # --- guardians ------------------------------------------------------------
    response = client.get("/api/v1/guardians", params={"student_id": amara["id"]})
    check_eq(
        "guardians listed for student",
        sorted(g["name"] for g in response.json()),
        ["Dan Okafor", "Grace Okafor"],
    )
    response = client.post(
        "/api/v1/guardians",
        json={
            "student_id": amara["id"],
            "name": "Ife Okafor",
            "relation": "Aunt",
            "phone": "+15550102",
        },
        headers={"X-User-Id": str(actor)},
    )
    check_eq("POST /guardians status", response.status_code, 201)
    ife = response.json()
    assert_audit_fields("created guardian", ife, expect_created_by=str(actor))
    response = client.patch(
        f"/api/v1/guardians/{ife['id']}", json={"preferred_contact_method": "phone"}
    )
    check_eq("PATCH /guardians status", response.status_code, 200)
    check_eq("guardian patch persisted", response.json()["preferred_contact_method"], "phone")
    response = client.delete(f"/api/v1/guardians/{dan['id']}", headers={"X-User-Id": str(editor)})
    check_eq("DELETE /guardians status", response.status_code, 204)
    check_eq("DELETE /guardians empty body", response.content, b"")
    response = client.get(f"/api/v1/guardians/{dan['id']}")
    check_eq("soft-deleted guardian 404", response.status_code, 404)
    response = client.get("/api/v1/guardians", params={"student_id": amara["id"]})
    check_eq(
        "soft-deleted guardian hidden from list",
        sorted(g["name"] for g in response.json()),
        ["Grace Okafor", "Ife Okafor"],
    )
    response = client.get("/api/v1/students", params={"search": "+15550101"})
    check_eq("search ignores soft-deleted guardians", response.json(), [])
    response = client.get(f"/api/v1/guardians/{unknown}")
    check_eq("GET unknown guardian 404", response.status_code, 404)

    # --- benny: contact events + follow-up sync -------------------------------
    response = client.post(
        "/api/v1/students",
        json={
            "name": "Benny Lin",
            "initials": "BL",
            "guardians": [
                {"name": "Mei Lin", "relation": "Mother", "phone": "+15550200"},
                {"name": "Jae Lin", "relation": "Father", "phone": "+15550201"},
            ],
        },
    )
    benny = response.json()
    mei = next(g for g in benny["guardians"] if g["name"] == "Mei Lin")
    jae = next(g for g in benny["guardians"] if g["name"] == "Jae Lin")

    def create_event(payload, expect=201):
        response = client.post("/api/v1/contact-events", json=payload)
        check_eq(f"POST /contact-events {payload['result']} status", response.status_code, expect)
        return response.json()

    e1 = create_event(
        {
            "student_id": benny["id"],
            "guardian_id": mei["id"],
            "result": "No Answer",
            "call_time": "2026-01-05T10:00:00Z",
            "ended_at": "2026-01-05T10:00:00Z",
        }
    )
    check_eq("attempt_number computed server-side", e1["attempt_number"], 1)
    assert_audit_fields("created event", e1)
    response = client.get("/api/v1/follow-ups", params={"student_id": benny["id"]})
    check_eq("one follow-up opened", len(response.json()), 1)
    fu = response.json()[0]
    check("No Answer follow-up due ended_at + 1 day", parse_dt(fu["due_at"]) == datetime(2026, 1, 6, 10, 0, 0))
    check_eq("follow-up linked to event", fu["contact_event_id"], e1["id"])
    check_eq("follow-up status open", fu["status"], "open")

    e2 = create_event(
        {
            "student_id": benny["id"],
            "guardian_id": mei["id"],
            "result": "No Answer",
            "call_time": "2026-01-06T11:00:00Z",
            "ended_at": "2026-01-06T11:00:00Z",
        }
    )
    check_eq("second attempt numbered", e2["attempt_number"], 2)
    response = client.get(
        "/api/v1/follow-ups", params={"student_id": benny["id"], "status": "open"}
    )
    check_eq("open follow-up upserted not duplicated", len(response.json()), 1)
    fu = response.json()[0]
    check("upserted follow-up due next day", parse_dt(fu["due_at"]) == datetime(2026, 1, 7, 11, 0, 0))
    open_fu_id = fu["id"]

    response = client.post(
        "/api/v1/follow-ups",
        json={
            "student_id": benny["id"],
            "guardian_id": mei["id"],
            "due_at": "2026-01-08T09:00:00Z",
        },
    )
    check_eq("duplicate open follow-up 409", response.status_code, 409)
    check("409 body uses detail envelope", "detail" in response.json())

    response = client.post(
        "/api/v1/follow-ups",
        json={
            "student_id": benny["id"],
            "guardian_id": jae["id"],
            "due_at": "2026-01-08T09:00:00Z",
        },
    )
    check_eq("open follow-up for other guardian created", response.status_code, 201)
    jae_fu = response.json()

    e3 = create_event(
        {
            "student_id": benny["id"],
            "guardian_id": mei["id"],
            "result": "Busy",
            "call_time": "2026-01-07T09:00:00Z",
            "ended_at": "2026-01-07T09:00:00Z",
            "follow_up_due_at": "2026-01-09T08:00:00Z",
        }
    )
    check_eq("Busy attempt numbered", e3["attempt_number"], 3)
    response = client.get(f"/api/v1/follow-ups/{open_fu_id}")
    check(
        "caller-supplied follow_up_due_at wins",
        parse_dt(response.json()["due_at"]) == datetime(2026, 1, 9, 8, 0, 0),
    )

    e4 = create_event(
        {
            "student_id": benny["id"],
            "guardian_id": mei["id"],
            "result": "Failed",
            "call_time": "2026-01-08T09:00:00Z",
            "ended_at": "2026-01-08T09:00:00Z",
        }
    )
    check_eq("Failed attempt numbered", e4["attempt_number"], 4)
    response = client.get(f"/api/v1/follow-ups/{open_fu_id}")
    check(
        "Failed upserts open follow-up due next day",
        parse_dt(response.json()["due_at"]) == datetime(2026, 1, 9, 9, 0, 0),
    )

    e5 = create_event(
        {
            "student_id": benny["id"],
            "guardian_id": mei["id"],
            "result": "Connected",
            "duration_seconds": 300,
            "discussed_topics": ["attendance", "homework"],
            "call_time": "2026-01-08T10:00:00Z",
            "ended_at": "2026-01-08T10:00:00Z",
        }
    )
    check_eq("Connected increments attempts", e5["attempt_number"], 5)
    check_eq("Connected discussed topics persisted", e5["discussed_topics"], ["attendance", "homework"])
    response = client.get(f"/api/v1/follow-ups/{open_fu_id}")
    completed = response.json()
    check_eq("Connected completes open follow-up", completed["status"], "completed")
    check("completed_at stamped", completed["completed_at"] is not None)
    check_eq("completed follow-up linked to event", completed["contact_event_id"], e5["id"])
    response = client.get(
        "/api/v1/follow-ups", params={"student_id": benny["id"], "status": "open"}
    )
    check_eq("no open follow-up left for mei", len(response.json()), 1)

    j1 = create_event(
        {
            "student_id": benny["id"],
            "guardian_id": jae["id"],
            "result": "No Answer",
            "call_time": "2026-01-08T10:00:00Z",
            "ended_at": "2026-01-08T10:00:00Z",
        }
    )
    check_eq("per-guardian attempt numbering", j1["attempt_number"], 1)
    response = client.get(f"/api/v1/follow-ups/{jae_fu['id']}")
    check(
        "guardian-specific follow-up upserted",
        parse_dt(response.json()["due_at"]) == datetime(2026, 1, 9, 10, 0, 0),
    )

    j2 = create_event(
        {
            "student_id": benny["id"],
            "guardian_id": jae["id"],
            "result": "Connected",
            "follow_up_id": jae_fu["id"],
            "call_time": "2026-01-08T12:00:00Z",
            "ended_at": "2026-01-08T12:00:00Z",
        }
    )
    check_eq("caller-supplied follow_up_id event attempt", j2["attempt_number"], 2)
    response = client.get(f"/api/v1/follow-ups/{jae_fu['id']}")
    check_eq("caller-supplied follow_up_id closed", response.json()["status"], "completed")

    before = datetime.now(timezone.utc)
    e6 = create_event(
        {
            "student_id": benny["id"],
            "guardian_id": mei["id"],
            "result": "No Answer",
        }
    )
    check_eq("event without ended_at attempt", e6["attempt_number"], 6)
    check("server stamps ended_at when omitted", e6["ended_at"] is not None)
    response = client.get(
        "/api/v1/follow-ups", params={"student_id": benny["id"], "status": "open"}
    )
    mei_fus = [f for f in response.json() if f["guardian_id"] == mei["id"]]
    check_eq("server-stamped ended_at opens follow-up", len(mei_fus), 1)
    due = parse_dt(mei_fus[0]["due_at"])
    check(
        "auto follow-up due about next day",
        timedelta(days=1) - timedelta(minutes=5)
        <= due - before.replace(tzinfo=None)
        <= timedelta(days=1) + timedelta(minutes=5),
    )
    e6_fu_id = mei_fus[0]["id"]

    e7 = create_event(
        {
            "student_id": benny["id"],
            "guardian_id": mei["id"],
            "result": "No Answer",
            "call_time": "2026-01-09T10:00:00Z",
            "ended_at": "2026-01-09T10:00:00Z",
        }
    )
    check_eq("seventh attempt numbered", e7["attempt_number"], 7)
    response = client.patch(
        f"/api/v1/contact-events/{e7['id']}", json={"result": "Connected"}
    )
    check_eq("PATCH /contact-events status", response.status_code, 200)
    response = client.get(f"/api/v1/follow-ups/{e6_fu_id}")
    check_eq("update re-runs follow-up sync", response.json()["status"], "completed")
    check_eq("resynced follow-up linked to patched event", response.json()["contact_event_id"], e7["id"])

    e8 = create_event(
        {
            "student_id": benny["id"],
            "guardian_id": mei["id"],
            "result": "No Answer",
            "call_time": "2026-01-10T10:00:00Z",
            "ended_at": "2026-01-10T10:00:00Z",
        }
    )
    response = client.patch(f"/api/v1/contact-events/{e8['id']}", json={"topic": "math camp"})
    check_eq("PATCH event topic status", response.status_code, 200)
    check_eq("PATCH event topic persisted", response.json()["topic"], "math camp")
    response = client.get(
        "/api/v1/follow-ups", params={"student_id": benny["id"], "status": "open"}
    )
    fu_before_delete = [f for f in response.json() if f["guardian_id"] == mei["id"]][0]
    check(
        "update without result/ended_at does not re-sync",
        parse_dt(fu_before_delete["due_at"]) == datetime(2026, 1, 11, 10, 0, 0),
    )

    response = client.delete(f"/api/v1/contact-events/{e8['id']}")
    check_eq("DELETE /contact-events status", response.status_code, 204)
    response = client.get(f"/api/v1/contact-events/{e8['id']}")
    check_eq("soft-deleted event 404", response.status_code, 404)

    e9 = create_event(
        {
            "student_id": benny["id"],
            "guardian_id": mei["id"],
            "result": "No Answer",
            "call_time": "2026-01-11T10:00:00Z",
            "ended_at": "2026-01-11T10:00:00Z",
        }
    )
    check_eq("soft-deleted events excluded from attempt count", e9["attempt_number"], 8)

    response = client.post(
        "/api/v1/contact-events",
        json={
            "student_id": benny["id"],
            "guardian_id": mei["id"],
            "result": "Voicemail",
        },
    )
    check_eq("invalid event result 400", response.status_code, 400)

    response = client.get(
        "/api/v1/contact-events", params={"student_id": benny["id"], "result": "Connected"}
    )
    check_eq(
        "event list filters by result",
        {e["id"] for e in response.json()},
        {e5["id"], e7["id"], j2["id"]},
    )
    response = client.get(
        "/api/v1/contact-events",
        params={"student_id": benny["id"], "from": "2026-01-05T00:00:00Z", "to": "2026-01-05T23:59:59Z"},
    )
    check_eq("event list filters by date range", [e["id"] for e in response.json()], [e1["id"]])
    response = client.get(f"/api/v1/contact-events/{unknown}")
    check_eq("GET unknown event 404", response.status_code, 404)

    # --- carla: follow-ups / teacher-notes / ai-briefs CRUD -------------------
    response = client.post(
        "/api/v1/students",
        json={
            "name": "Carla Mendes",
            "guardians": [{"name": "Rosa Mendes", "relation": "Mother", "phone": "+15550300"}],
        },
    )
    carla = response.json()
    rosa = carla["guardians"][0]

    response = client.post(
        "/api/v1/follow-ups",
        json={"student_id": carla["id"], "guardian_id": rosa["id"], "due_at": "2026-03-01T09:00:00Z"},
    )
    check_eq("POST /follow-ups status", response.status_code, 201)
    carla_fu = response.json()
    assert_audit_fields("created follow-up", carla_fu)
    response = client.patch(f"/api/v1/follow-ups/{carla_fu['id']}", json={"status": "dismissed"})
    check_eq("PATCH follow-up to dismissed", response.json()["status"], "dismissed")
    response = client.patch(f"/api/v1/follow-ups/{carla_fu['id']}", json={"status": "completed"})
    check_eq("PATCH follow-up to completed", response.json()["status"], "completed")
    check("PATCH follow-up stamps completed_at", response.json()["completed_at"] is not None)
    response = client.post(
        "/api/v1/follow-ups",
        json={"student_id": carla["id"], "guardian_id": rosa["id"], "due_at": "2026-03-02T09:00:00Z"},
    )
    check_eq("new open follow-up after completion allowed", response.status_code, 201)
    carla_fu2 = response.json()
    response = client.delete(f"/api/v1/follow-ups/{carla_fu2['id']}")
    check_eq("DELETE /follow-ups status", response.status_code, 204)
    response = client.get(f"/api/v1/follow-ups/{carla_fu2['id']}")
    check_eq("soft-deleted follow-up 404", response.status_code, 404)
    response = client.post(
        "/api/v1/follow-ups",
        json={"student_id": carla["id"], "guardian_id": rosa["id"], "due_at": "2026-03-03T09:00:00Z"},
    )
    check_eq("open follow-up creatable after delete", response.status_code, 201)
    response = client.get(f"/api/v1/follow-ups/{unknown}")
    check_eq("GET unknown follow-up 404", response.status_code, 404)

    response = client.post(
        "/api/v1/teacher-notes",
        json={"student_id": carla["id"], "content": "Spoke about attendance."},
    )
    check_eq("POST /teacher-notes status", response.status_code, 201)
    note = response.json()
    assert_audit_fields("created teacher note", note)
    check_eq("teacher note default source typed", note["source"], "typed")
    check_eq("teacher note default confirmed false", note["teacher_confirmed"], False)
    response = client.patch(
        f"/api/v1/teacher-notes/{note['id']}",
        json={"content": "Updated content.", "teacher_confirmed": True},
    )
    check_eq("PATCH /teacher-notes status", response.status_code, 200)
    check_eq("teacher note patch persisted", response.json()["content"], "Updated content.")
    check_eq("teacher note confirm persisted", response.json()["teacher_confirmed"], True)
    response = client.post(
        "/api/v1/teacher-notes", json={"student_id": carla["id"], "content": "   "}
    )
    check_eq("empty teacher note 400", response.status_code, 400)
    response = client.post(
        "/api/v1/teacher-notes",
        json={"student_id": carla["id"], "content": "hello", "source": "email"},
    )
    check_eq("invalid teacher note source 400", response.status_code, 400)
    response = client.post(
        "/api/v1/teacher-notes",
        json={"student_id": carla["id"], "content": "Voice summary.", "source": "voice"},
    )
    check_eq("voice teacher note created", response.status_code, 201)
    voice_note = response.json()
    response = client.get("/api/v1/teacher-notes", params={"student_id": carla["id"]})
    check_eq("teacher notes listed per student", len(response.json()), 2)
    response = client.delete(f"/api/v1/teacher-notes/{voice_note['id']}")
    check_eq("DELETE /teacher-notes status", response.status_code, 204)
    response = client.get(f"/api/v1/teacher-notes/{voice_note['id']}")
    check_eq("soft-deleted teacher note 404", response.status_code, 404)
    response = client.get(f"/api/v1/teacher-notes/{unknown}")
    check_eq("GET unknown teacher note 404", response.status_code, 404)

    response = client.post(
        "/api/v1/ai-briefs",
        json={
            "student_id": carla["id"],
            "date_from": "2026-01-01T00:00:00Z",
            "date_to": "2026-01-31T00:00:00Z",
            "key_topics": ["attendance"],
            "parent_concerns": ["late pickup"],
            "recorded_resolutions": ["bus schedule"],
            "open_items": ["homework plan"],
            "suggested_next_step": "Call again next week",
        },
    )
    check_eq("POST /ai-briefs status", response.status_code, 201)
    brief = response.json()
    assert_audit_fields("created ai brief", brief)
    check_eq("ai brief created as draft v1", (brief["status"], brief["version"]), ("draft", 1))
    check("ai brief generated_at present", brief["generated_at"] is not None)
    check("ai brief approved_at empty", brief["approved_at"] is None)
    response = client.post(
        "/api/v1/ai-briefs",
        json={
            "student_id": carla["id"],
            "date_from": "2026-01-01T00:00:00Z",
            "date_to": "2026-01-31T00:00:00Z",
        },
    )
    check_eq("duplicate ai brief version 409", response.status_code, 409)
    response = client.post(
        "/api/v1/ai-briefs",
        json={
            "student_id": carla["id"],
            "date_from": "2026-01-01T00:00:00Z",
            "date_to": "2026-01-31T00:00:00Z",
            "version": 2,
            "open_items": ["spring trip"],
        },
    )
    check_eq("second ai brief version created", response.json()["version"], 2)
    brief_v2 = response.json()
    response = client.patch(
        f"/api/v1/ai-briefs/{brief_v2['id']}", json={"suggested_next_step": "Email summary"}
    )
    check_eq("PATCH /ai-briefs persisted", response.json()["suggested_next_step"], "Email summary")
    response = client.post(f"/api/v1/ai-briefs/{brief_v2['id']}/approve")
    check_eq("approve ai brief status", response.status_code, 200)
    check_eq("approve sets status", response.json()["status"], "approved")
    check("approve stamps approved_at", response.json()["approved_at"] is not None)
    response = client.post(f"/api/v1/ai-briefs/{brief_v2['id']}/supersede")
    check_eq("supersede sets status", response.json()["status"], "superseded")
    response = client.get(
        "/api/v1/ai-briefs", params={"student_id": carla["id"], "latest": "true"}
    )
    check_eq("latest=true returns v1 draft", response.json()["id"], brief["id"])
    response = client.get("/api/v1/ai-briefs", params={"student_id": carla["id"]})
    check_eq("ai brief list per student", len(response.json()), 2)
    response = client.delete(f"/api/v1/ai-briefs/{brief['id']}")
    check_eq("DELETE /ai-briefs status", response.status_code, 204)
    response = client.get(f"/api/v1/ai-briefs/{brief['id']}")
    check_eq("soft-deleted ai brief 404", response.status_code, 404)
    response = client.get(
        "/api/v1/ai-briefs", params={"student_id": carla["id"], "latest": "true"}
    )
    check_eq("latest=true with none remaining 404", response.status_code, 404)
    response = client.get(f"/api/v1/ai-briefs/{unknown}")
    check_eq("GET unknown ai brief 404", response.status_code, 404)

    # --- dana + /data/load ----------------------------------------------------
    response = client.post(
        "/api/v1/students",
        json={
            "name": "Dana Reed",
            "guardians": [{"name": "Ken Reed", "relation": "Father", "phone": "+15550400"}],
        },
    )
    dana = response.json()
    ken = dana["guardians"][0]
    response = client.post(
        "/api/v1/contact-events",
        json={
            "student_id": dana["id"],
            "guardian_id": ken["id"],
            "result": "No Answer",
            "call_time": "2026-02-01T09:00:00Z",
            "ended_at": "2026-02-01T09:00:00Z",
        },
    )
    check_eq("dana event created", response.status_code, 201)
    response = client.post(
        "/api/v1/teacher-notes",
        json={"student_id": dana["id"], "content": "Left a voicemail."},
    )
    check_eq("dana note created", response.status_code, 201)
    response = client.post(
        "/api/v1/ai-briefs",
        json={
            "student_id": dana["id"],
            "date_from": "2026-01-01T00:00:00Z",
            "date_to": "2026-02-01T00:00:00Z",
        },
    )
    check_eq("dana brief created", response.status_code, 201)
    dana_brief = response.json()

    response = client.get("/api/v1/data/load")
    check_eq("GET /data/load status", response.status_code, 200)
    data = response.json()
    check(
        "data/load top-level keys",
        set(data) == {"students", "events", "follow_ups", "teacher_notes", "ai_briefs"},
    )
    loaded_dana = next(s for s in data["students"] if s["id"] == dana["id"])
    check_eq("data/load students include guardians", len(loaded_dana["guardians"]), 1)
    check("data/load includes events", any(e["id"] == e1["id"] for e in data["events"]))
    check(
        "data/load follow_ups only open",
        all(f["status"] == "open" for f in data["follow_ups"]),
    )
    check(
        "data/load ai_briefs exclude superseded",
        any(b["id"] == dana_brief["id"] for b in data["ai_briefs"])
        and all(b["id"] != brief_v2["id"] for b in data["ai_briefs"]),
    )
    check(
        "data/load teacher_notes include dana note",
        any(n["student_id"] == dana["id"] for n in data["teacher_notes"]),
    )

    # --- dashboard summary ----------------------------------------------------
    response = client.get(
        "/api/v1/dashboard/summary",
        params={"from": "2026-01-05T00:00:00Z", "to": "2026-01-13T00:00:00Z"},
    )
    check_eq("GET /dashboard/summary status", response.status_code, 200)
    summary = response.json()
    check_eq(
        "dashboard summary shape",
        set(summary),
        {"call_attempts", "connected", "unsuccessful", "follow_ups_due"},
    )
    check_eq("dashboard call_attempts in range", summary["call_attempts"], 9)
    check_eq("dashboard connected in range", summary["connected"], 3)
    check_eq("dashboard unsuccessful in range", summary["unsuccessful"], 6)
    check_eq("dashboard follow_ups_due in range", summary["follow_ups_due"], 1)
    response = client.get("/api/v1/dashboard/summary")
    check_eq("dashboard summary without range ok", response.status_code, 200)
    check_eq(
        "dashboard summary unfiltered totals",
        (response.json()["call_attempts"], response.json()["connected"]),
        (11, 3),
    )

    # --- import students ------------------------------------------------------
    import_payload = {
        "students": [
            {"student_key": "s1", "first_name": "Emma", "last_name": "Chen"},
            {"student_key": "s2", "name": "Liam Park"},
        ],
        "guardians": [
            {"student_key": "s1", "name": "Ying Chen", "relationship": "Mother", "phone": "+15550500"},
            {"student_key": "s2", "name": "Ho Park", "relationship": "Father"},
        ],
    }
    response = client.post("/api/v1/import/students", json=import_payload)
    check_eq("POST /import/students status", response.status_code, 200)
    check_eq(
        "import counts",
        response.json(),
        {"imported_students": 2, "imported_guardians": 2},
    )
    response = client.get("/api/v1/students", params={"search": "Emma Chen"})
    check_eq("imported student searchable", len(response.json()), 1)
    emma = response.json()[0]
    check_eq("imported student name from first/last", emma["name"], "Emma Chen")
    check_eq("imported student initials computed", emma["initials"], "EC")
    check_eq("imported student guardian embedded", len(emma["guardians"]), 1)
    check_eq(
        "imported guardian relation mapped",
        emma["guardians"][0]["relation"],
        "Mother",
    )
    emma_id = emma["id"]
    response = client.post("/api/v1/import/students", json=import_payload)
    check_eq(
        "import idempotent counts",
        response.json(),
        {"imported_students": 2, "imported_guardians": 2},
    )
    response = client.get("/api/v1/students", params={"search": "Emma Chen"})
    check_eq("import idempotent no duplicate students", len(response.json()), 1)
    check_eq("import idempotent same student id", response.json()[0]["id"], emma_id)
    check_eq(
        "import idempotent no duplicate guardians",
        len(response.json()[0]["guardians"]),
        1,
    )
    response = client.post(
        "/api/v1/import/students",
        json={"students": [], "guardians": [{"student_key": "nope", "name": "X", "relationship": "Other"}]},
    )
    check_eq("import unknown student_key 400", response.status_code, 400)

    # --- voice stubs ----------------------------------------------------------
    response = client.post(
        "/api/v1/voice/uploads",
        json={"student_id": dana["id"], "content_type": "audio/webm"},
    )
    check_eq("POST /voice/uploads status", response.status_code, 200)
    upload = response.json()
    check_eq(
        "upload_url points at files endpoint",
        upload["upload_url"],
        f"/api/v1/voice/files/{upload['object_key']}",
    )
    voice_bytes = b"\x1a\x45\xdf\xa3fake-webm-payload"
    response = client.put(upload["upload_url"], content=voice_bytes)
    check_eq("PUT voice file status", response.status_code, 204)
    voice_path = BACKEND_DIR / "data" / "voice_notes" / upload["object_key"]
    VOICE_FILES.append(voice_path)
    check("voice file stored under backend/data/voice_notes", voice_path.is_file())
    check_eq("voice file bytes match", voice_path.read_bytes(), voice_bytes)
    response = client.put("/api/v1/voice/files/..%2Fevil", content=b"x")
    check_eq("voice encoded path traversal blocked", response.status_code, 404)
    response = client.put("/api/v1/voice/files/bad%20key", content=b"x")
    check_eq("voice invalid object key rejected", response.status_code, 400)
    response = client.post(
        "/api/v1/voice/transcriptions",
        json={"student_id": dana["id"], "object_key": upload["object_key"]},
    )
    check_eq("POST /voice/transcriptions status", response.status_code, 200)
    job_id = response.json()["job_id"]
    response = client.get(f"/api/v1/voice/transcriptions/{job_id}")
    check_eq(
        "voice transcription stub completed",
        response.json(),
        {"status": "completed", "transcript": "(Voice note saved locally. Transcription is not configured.)"},
    )

    # --- ai generate stub -----------------------------------------------------
    response = client.post("/api/v1/ai/contact-brief/generate", json={"student_id": dana["id"]})
    check_eq("ai contact-brief generate 501", response.status_code, 501)
    check_eq(
        "ai contact-brief generate detail",
        response.json()["detail"],
        "AI contact brief provider is not configured.",
    )

    # --- auth behaviors -------------------------------------------------------
    header_user = uuid.uuid4()
    response = client.post(
        "/api/v1/students", json={"name": "Header Auth Kid"}, headers={"X-User-Id": str(header_user)}
    )
    check_eq("X-User-Id stamps created_by", response.json()["created_by"], str(header_user))

    jwt_user = uuid.uuid4()
    token = make_jwt({"sub": str(jwt_user), "role": "authenticated"}, JWT_SECRET)
    response = client.post(
        "/api/v1/students",
        json={"name": "Jwt Auth Kid"},
        headers={"Authorization": f"Bearer {token}"},
    )
    check_eq("bearer JWT sub stamps created_by", response.json()["created_by"], str(jwt_user))

    response = client.post(
        "/api/v1/students",
        json={"name": "Fallback Auth Kid"},
        headers={"X-User-Id": "not-a-uuid", "Authorization": f"Bearer {token}"},
    )
    check_eq("invalid X-User-Id falls back to JWT", response.json()["created_by"], str(jwt_user))

    bad_token = make_jwt({"sub": str(uuid.uuid4())}, "wrong-secret")
    response = client.post(
        "/api/v1/students",
        json={"name": "Bad Token Kid"},
        headers={"Authorization": f"Bearer {bad_token}"},
    )
    check_eq("bad signature token anonymous", response.status_code, 201)
    check("bad signature token created_by null", response.json()["created_by"] is None)

    response = client.post("/api/v1/students", json={"name": "Anonymous Kid"})
    check_eq("anonymous request allowed", response.status_code, 201)
    check("anonymous created_by null", response.json()["created_by"] is None)

    # --- student cascade soft delete -------------------------------------------
    response = client.post(
        "/api/v1/students",
        json={
            "name": "Temp Cascade",
            "guardians": [{"name": "Tmp Guardian", "relation": "Mother", "phone": "+15550999"}],
        },
    )
    temp = response.json()
    temp_guardian = temp["guardians"][0]
    response = client.post(
        "/api/v1/contact-events",
        json={
            "student_id": temp["id"],
            "guardian_id": temp_guardian["id"],
            "result": "No Answer",
            "call_time": "2026-03-01T10:00:00Z",
            "ended_at": "2026-03-01T10:00:00Z",
        },
    )
    temp_event = response.json()
    response = client.post(
        "/api/v1/teacher-notes", json={"student_id": temp["id"], "content": "temp note"}
    )
    temp_note = response.json()
    response = client.post(
        "/api/v1/ai-briefs",
        json={"student_id": temp["id"], "date_from": "2026-01-01T00:00:00Z", "date_to": "2026-02-01T00:00:00Z"},
    )
    temp_brief = response.json()

    response = client.delete(f"/api/v1/students/{temp['id']}")
    check_eq("DELETE /students status", response.status_code, 204)
    check_eq("DELETE /students empty body", response.content, b"")
    response = client.get(f"/api/v1/students/{temp['id']}")
    check_eq("soft-deleted student 404", response.status_code, 404)
    response = client.get("/api/v1/guardians", params={"student_id": temp["id"]})
    check_eq("cascade hides guardians", response.json(), [])
    response = client.get("/api/v1/contact-events", params={"student_id": temp["id"]})
    check_eq("cascade hides contact events", response.json(), [])
    response = client.get("/api/v1/follow-ups", params={"student_id": temp["id"]})
    check_eq("cascade hides follow-ups", response.json(), [])
    response = client.get("/api/v1/teacher-notes", params={"student_id": temp["id"]})
    check_eq("cascade hides teacher notes", response.json(), [])
    response = client.get("/api/v1/ai-briefs", params={"student_id": temp["id"]})
    check_eq("cascade hides ai briefs", response.json(), [])
    response = client.get("/api/v1/students", params={"search": "Benny"})
    check_eq("other students survive cascade", len(response.json()), 1)
    check(
        "other students' events survive cascade",
        any(e["id"] == e1["id"] for e in client.get("/api/v1/contact-events", params={"student_id": benny["id"]}).json()),
    )
    check("temp ids referenced", all(x is not None for x in (temp_event, temp_note, temp_brief)))


if __name__ == "__main__":
    main()
