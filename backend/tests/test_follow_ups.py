import uuid

from helpers import parse_dt

ACTOR = str(uuid.uuid4())


def test_create_follow_up_with_defaults_and_actor(client, make_student, make_guardian):
    student = make_student(guardians=[])
    guardian = make_guardian(student["id"])
    response = client.post(
        "/api/v1/follow-ups",
        json={"student_id": student["id"], "guardian_id": guardian["id"], "due_at": "2028-03-01T09:00:00Z"},
        headers={"X-User-Id": ACTOR},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "open"
    assert body["completed_at"] is None
    assert body["created_by"] == ACTOR
    assert body["updated_by"] == ACTOR
    for field in ("id", "created_at", "updated_at", "created_by", "updated_by"):
        assert field in body


def test_list_follow_ups_filters_by_status_and_student(client, make_student, make_guardian):
    student = make_student(guardians=[])
    guardian = make_guardian(student["id"])
    open_fu = client.post(
        "/api/v1/follow-ups",
        json={"student_id": student["id"], "due_at": "2028-03-01T09:00:00Z"},
    ).json()
    done_fu = client.post(
        "/api/v1/follow-ups",
        json={"student_id": student["id"], "guardian_id": guardian["id"], "due_at": "2028-03-02T09:00:00Z"},
    ).json()
    client.patch(f"/api/v1/follow-ups/{done_fu['id']}", json={"status": "completed"})

    response = client.get("/api/v1/follow-ups", params={"student_id": student["id"], "status": "open"})
    assert [fu["id"] for fu in response.json()] == [open_fu["id"]]

    response = client.get("/api/v1/follow-ups", params={"student_id": student["id"], "status": "completed"})
    assert [fu["id"] for fu in response.json()] == [done_fu["id"]]


def test_get_follow_up_by_id(client, make_student):
    student = make_student(guardians=[])
    follow_up = client.post(
        "/api/v1/follow-ups",
        json={"student_id": student["id"], "due_at": "2028-03-01T09:00:00Z"},
    ).json()
    response = client.get(f"/api/v1/follow-ups/{follow_up['id']}")
    assert response.status_code == 200
    assert response.json()["id"] == follow_up["id"]


def test_patch_follow_up_status_transitions_stamp_completed_at(client, make_student):
    student = make_student(guardians=[])
    follow_up = client.post(
        "/api/v1/follow-ups",
        json={"student_id": student["id"], "due_at": "2028-03-01T09:00:00Z"},
    ).json()

    response = client.patch(f"/api/v1/follow-ups/{follow_up['id']}", json={"status": "dismissed"})
    assert response.status_code == 200
    assert response.json()["status"] == "dismissed"
    assert response.json()["completed_at"] is None

    dismissed = client.post(
        "/api/v1/follow-ups",
        json={"student_id": student["id"], "due_at": "2028-03-05T09:00:00Z"},
    ).json()
    response = client.patch(f"/api/v1/follow-ups/{dismissed['id']}", json={"status": "completed"})
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "completed"
    assert parse_dt(body["completed_at"]) is not None
    assert parse_dt(body["updated_at"]) >= parse_dt(body["created_at"])


def test_delete_follow_up_is_soft_and_allows_new_open(client, make_student):
    student = make_student(guardians=[])
    follow_up = client.post(
        "/api/v1/follow-ups",
        json={"student_id": student["id"], "due_at": "2028-03-01T09:00:00Z"},
    ).json()
    response = client.delete(f"/api/v1/follow-ups/{follow_up['id']}")
    assert response.status_code == 204
    assert client.get(f"/api/v1/follow-ups/{follow_up['id']}").status_code == 404

    response = client.post(
        "/api/v1/follow-ups",
        json={"student_id": student["id"], "due_at": "2028-03-10T09:00:00Z"},
    )
    assert response.status_code == 201


def test_unknown_follow_up_returns_404(client):
    unknown = str(uuid.uuid4())
    assert client.get(f"/api/v1/follow-ups/{unknown}").status_code == 404
    assert client.patch(f"/api/v1/follow-ups/{unknown}", json={"status": "open"}).status_code == 404
    assert client.delete(f"/api/v1/follow-ups/{unknown}").status_code == 404
