import uuid

from helpers import parse_dt

def test_create_teacher_note_defaults(client, make_student, auth_user):
    student = make_student(guardians=[])
    response = client.post(
        "/api/v1/teacher-notes",
        json={"student_id": student["id"], "content": "Parent asked about homework."},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["content"] == "Parent asked about homework."
    assert body["source"] == "typed"
    assert body["teacher_confirmed"] is False
    assert body["contact_event_id"] is None
    assert body["created_by"] == auth_user["id"]
    for field in ("id", "created_at", "updated_at", "created_by", "updated_by"):
        assert field in body


def test_create_voice_teacher_note_with_event_link(client, make_student, make_event):
    student = make_student(guardians=[])
    event = make_event(student["id"], result="Connected", call_time="2028-01-10T09:00:00Z")
    response = client.post(
        "/api/v1/teacher-notes",
        json={
            "student_id": student["id"],
            "contact_event_id": event["id"],
            "content": "Voice summary",
            "source": "voice",
            "teacher_confirmed": True,
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["source"] == "voice"
    assert body["teacher_confirmed"] is True
    assert body["contact_event_id"] == event["id"]


def test_list_teacher_notes_filtered_by_student(client, make_student, make_note):
    student_a = make_student(guardians=[])
    student_b = make_student(guardians=[])
    note_a = make_note(student_a["id"])
    make_note(student_b["id"])
    response = client.get("/api/v1/teacher-notes", params={"student_id": student_a["id"]})
    assert response.status_code == 200
    assert [n["id"] for n in response.json()] == [note_a["id"]]


def test_patch_teacher_note_persists_and_restamps(client, make_student, make_note, auth_user):
    note = make_note(make_student(guardians=[])["id"])
    before = parse_dt(note["updated_at"])
    response = client.patch(
        f"/api/v1/teacher-notes/{note['id']}",
        json={"content": "Updated content.", "teacher_confirmed": True},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["content"] == "Updated content."
    assert body["teacher_confirmed"] is True
    assert body["updated_by"] == auth_user["id"]
    assert parse_dt(body["updated_at"]) > before


def test_delete_teacher_note_is_soft(client, make_student, make_note):
    student = make_student(guardians=[])
    note = make_note(student["id"])
    response = client.delete(f"/api/v1/teacher-notes/{note['id']}")
    assert response.status_code == 204
    assert client.get(f"/api/v1/teacher-notes/{note['id']}").status_code == 404
    assert client.get(f"/api/v1/teacher-notes?student_id={student['id']}").json() == []


def test_blank_teacher_note_returns_400(client, make_student):
    student = make_student(guardians=[])
    response = client.post(
        "/api/v1/teacher-notes", json={"student_id": student["id"], "content": "   "}
    )
    assert response.status_code == 400


def test_invalid_teacher_note_source_returns_400(client, make_student):
    student = make_student(guardians=[])
    response = client.post(
        "/api/v1/teacher-notes",
        json={"student_id": student["id"], "content": "hello", "source": "email"},
    )
    assert response.status_code == 400


def test_unknown_teacher_note_returns_404(client):
    unknown = str(uuid.uuid4())
    assert client.get(f"/api/v1/teacher-notes/{unknown}").status_code == 404
    assert client.patch(f"/api/v1/teacher-notes/{unknown}", json={"content": "x"}).status_code == 404
    assert client.delete(f"/api/v1/teacher-notes/{unknown}").status_code == 404
