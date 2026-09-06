import os
import shutil
import sys
import tempfile
import uuid
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

TMP_DIR = Path(tempfile.mkdtemp(prefix="contactloop_pytest_"))
os.environ.pop("SUPABASE_DB_URL", None)
os.environ.pop("DATABASE_URL", None)
os.environ["SQLITE_PATH"] = (TMP_DIR / "contactloop-test.db").as_posix()
os.environ["APP_ENV"] = "test"
os.environ.setdefault("SUPABASE_JWT_SECRET", "pytest-jwt-secret")

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def make_student(client):
    def _make(name=None, guardians=None, headers=None, **extra):
        suffix = uuid.uuid4().hex[:8]
        if guardians is None:
            guardians = [
                {
                    "name": f"Guardian {suffix}",
                    "relation": "Mom",
                    "phone": f"555-{suffix}",
                }
            ]
        payload = {"name": name or f"Student {suffix}", "guardians": guardians}
        payload.update(extra)
        response = client.post("/api/v1/students", json=payload, headers=headers)
        assert response.status_code == 201, response.text
        return response.json()

    return _make


@pytest.fixture
def make_guardian(client):
    def _make(student_id, name=None, **extra):
        suffix = uuid.uuid4().hex[:8]
        payload = {
            "student_id": student_id,
            "name": name or f"Guardian {suffix}",
            "relation": "Dad",
            "phone": f"555-{suffix}",
        }
        payload.update(extra)
        response = client.post("/api/v1/guardians", json=payload)
        assert response.status_code == 201, response.text
        return response.json()

    return _make


@pytest.fixture
def make_event(client):
    def _make(
        student_id,
        guardian_id=None,
        result="No Answer",
        call_time="2028-01-10T09:00:00Z",
        ended_at=None,
        headers=None,
        **extra,
    ):
        payload = {
            "student_id": student_id,
            "guardian_id": guardian_id,
            "result": result,
            "call_time": call_time,
            "ended_at": ended_at or call_time,
        }
        payload.update(extra)
        response = client.post("/api/v1/contact-events", json=payload, headers=headers)
        assert response.status_code == 201, response.text
        return response.json()

    return _make


@pytest.fixture
def make_follow_up(client):
    def _make(student_id, guardian_id=None, due_at="2028-03-01T09:00:00Z", **extra):
        payload = {
            "student_id": student_id,
            "guardian_id": guardian_id,
            "due_at": due_at,
        }
        payload.update(extra)
        response = client.post("/api/v1/follow-ups", json=payload)
        assert response.status_code == 201, response.text
        return response.json()

    return _make


@pytest.fixture
def make_note(client):
    def _make(student_id, content=None, **extra):
        payload = {
            "student_id": student_id,
            "content": content or f"Note {uuid.uuid4().hex[:8]}",
        }
        payload.update(extra)
        response = client.post("/api/v1/teacher-notes", json=payload)
        assert response.status_code == 201, response.text
        return response.json()

    return _make


@pytest.fixture
def make_brief(client):
    def _make(student_id, date_from="2028-01-01T00:00:00Z", date_to="2028-01-31T00:00:00Z", **extra):
        payload = {
            "student_id": student_id,
            "date_from": date_from,
            "date_to": date_to,
        }
        payload.update(extra)
        response = client.post("/api/v1/ai-briefs", json=payload)
        assert response.status_code == 201, response.text
        return response.json()

    return _make


def pytest_sessionfinish(session, exitstatus):
    shutil.rmtree(TMP_DIR, ignore_errors=True)
