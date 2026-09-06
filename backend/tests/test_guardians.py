import uuid

from helpers import parse_dt

ACTOR = str(uuid.uuid4())
EDITOR = str(uuid.uuid4())


def test_create_guardian_with_actor_header(client, make_student):
    student = make_student(guardians=[])
    response = client.post(
        "/api/v1/guardians",
        json={
            "student_id": student["id"],
            "name": "Sarah Johnson",
            "relation": "Mom",
            "phone": "555-0100",
            "email": "sarah@example.com",
        },
        headers={"X-User-Id": ACTOR},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["student_id"] == student["id"]
    assert body["name"] == "Sarah Johnson"
    assert body["created_by"] == ACTOR
    assert body["updated_by"] == ACTOR


def test_list_guardians_filters_by_student(client, make_student, make_guardian):
    student_a = make_student(guardians=[])
    student_b = make_student(guardians=[])
    guardian_a = make_guardian(student_a["id"])
    make_guardian(student_b["id"])

    response = client.get("/api/v1/guardians", params={"student_id": student_a["id"]})
    assert response.status_code == 200
    assert [g["id"] for g in response.json()] == [guardian_a["id"]]


def test_get_guardian_by_id(client, make_student, make_guardian):
    guardian = make_guardian(make_student(guardians=[])["id"], name="Derek Noel")
    response = client.get(f"/api/v1/guardians/{guardian['id']}")
    assert response.status_code == 200
    assert response.json()["name"] == "Derek Noel"


def test_patch_guardian_persists_and_restamps_audit(client, make_student, make_guardian):
    guardian = make_guardian(make_student(guardians=[])["id"])
    before = parse_dt(guardian["updated_at"])
    response = client.patch(
        f"/api/v1/guardians/{guardian['id']}",
        json={"preferred_contact_method": "phone", "phone": "555-0999"},
        headers={"X-User-Id": EDITOR},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["preferred_contact_method"] == "phone"
    assert body["phone"] == "555-0999"
    assert body["updated_by"] == EDITOR
    assert parse_dt(body["updated_at"]) > before


def test_delete_guardian_is_soft(client, make_student, make_guardian):
    student = make_student(guardians=[])
    guardian = make_guardian(student["id"], name="Gone Soon", phone="555-0777")
    response = client.delete(f"/api/v1/guardians/{guardian['id']}")
    assert response.status_code == 204
    assert client.get(f"/api/v1/guardians/{guardian['id']}").status_code == 404
    assert client.get(f"/api/v1/guardians?student_id={student['id']}").json() == []
    listed = client.get("/api/v1/students", params={"search": "Gone Soon"}).json()
    assert listed == []


def test_student_search_ignores_soft_deleted_guardian_phone(client, make_student, make_guardian):
    student = make_student(guardians=[])
    guardian = make_guardian(student["id"], phone="555-0666")
    client.delete(f"/api/v1/guardians/{guardian['id']}")
    listed = client.get("/api/v1/students", params={"search": "555-0666"}).json()
    assert listed == []


def test_unknown_guardian_returns_404(client):
    unknown = str(uuid.uuid4())
    assert client.get(f"/api/v1/guardians/{unknown}").status_code == 404
    assert client.patch(f"/api/v1/guardians/{unknown}", json={"name": "x"}).status_code == 404
    assert client.delete(f"/api/v1/guardians/{unknown}").status_code == 404
