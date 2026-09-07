import uuid

from helpers import parse_dt

def test_create_ai_brief_defaults_and_audit(client, make_student, auth_user):
    student = make_student(guardians=[])
    response = client.post(
        "/api/v1/ai-briefs",
        json={
            "student_id": student["id"],
            "date_from": "2028-01-01T00:00:00Z",
            "date_to": "2028-01-31T00:00:00Z",
            "key_topics": ["Homework"],
            "open_items": ["Share study plan"],
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "draft"
    assert body["version"] == 1
    assert body["key_topics"] == ["Homework"]
    assert body["open_items"] == ["Share study plan"]
    assert body["approved_at"] is None
    assert body["generated_at"] is not None
    assert body["created_by"] == auth_user["id"]
    for field in ("id", "created_at", "updated_at", "created_by", "updated_by"):
        assert field in body


def test_duplicate_brief_version_returns_409(client, make_student):
    student = make_student(guardians=[])
    payload = {
        "student_id": student["id"],
        "date_from": "2028-01-01T00:00:00Z",
        "date_to": "2028-01-31T00:00:00Z",
    }
    assert client.post("/api/v1/ai-briefs", json=payload).status_code == 201
    response = client.post("/api/v1/ai-briefs", json=payload)
    assert response.status_code == 409
    assert "detail" in response.json()

    response = client.post("/api/v1/ai-briefs", json={**payload, "version": 2})
    assert response.status_code == 201
    assert response.json()["version"] == 2


def test_list_and_latest_filtering(client, make_student, make_brief):
    student = make_student(guardians=[])
    first = make_brief(student["id"], date_from="2028-01-01T00:00:00Z", date_to="2028-01-15T00:00:00Z")
    second = make_brief(student["id"], date_from="2028-01-16T00:00:00Z", date_to="2028-01-31T00:00:00Z")

    response = client.get("/api/v1/ai-briefs", params={"student_id": student["id"]})
    assert response.status_code == 200
    assert [b["id"] for b in response.json()] == [second["id"], first["id"]]

    response = client.get(
        "/api/v1/ai-briefs", params={"student_id": student["id"], "latest": "true"}
    )
    assert response.status_code == 200
    assert response.json()["id"] == second["id"]

    client.post(f"/api/v1/ai-briefs/{second['id']}/supersede")
    response = client.get(
        "/api/v1/ai-briefs", params={"student_id": student["id"], "latest": "true"}
    )
    assert response.json()["id"] == first["id"]


def test_patch_ai_brief_persists_fields(client, make_student, make_brief):
    brief = make_brief(make_student(guardians=[])["id"])
    response = client.patch(
        f"/api/v1/ai-briefs/{brief['id']}",
        json={"suggested_next_step": "Email summary", "parent_concerns": ["Attendance"]},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["suggested_next_step"] == "Email summary"
    assert body["parent_concerns"] == ["Attendance"]


def test_approve_and_supersede_transitions(client, make_student, make_brief):
    student = make_student(guardians=[])
    brief = make_brief(student["id"])
    other = make_brief(student["id"], date_from="2028-02-01T00:00:00Z", date_to="2028-02-15T00:00:00Z")

    response = client.post(f"/api/v1/ai-briefs/{brief['id']}/approve", headers={"X-User-Id": str(uuid.uuid4())})
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "approved"
    assert parse_dt(body["approved_at"]) is not None

    response = client.post(f"/api/v1/ai-briefs/{other['id']}/supersede")
    assert response.status_code == 200
    assert response.json()["status"] == "superseded"


def test_delete_ai_brief_is_soft(client, make_student, make_brief):
    student = make_student(guardians=[])
    brief = make_brief(student["id"])
    response = client.delete(f"/api/v1/ai-briefs/{brief['id']}")
    assert response.status_code == 204
    assert client.get(f"/api/v1/ai-briefs/{brief['id']}").status_code == 404
    assert client.get(f"/api/v1/ai-briefs?student_id={student['id']}").json() == []


def test_latest_true_without_briefs_returns_404(client, make_student):
    student = make_student(guardians=[])
    response = client.get(
        "/api/v1/ai-briefs", params={"student_id": student["id"], "latest": "true"}
    )
    assert response.status_code == 404


def test_unknown_ai_brief_returns_404(client):
    unknown = str(uuid.uuid4())
    assert client.get(f"/api/v1/ai-briefs/{unknown}").status_code == 404
    assert client.patch(f"/api/v1/ai-briefs/{unknown}", json={"status": "draft"}).status_code == 404
    assert client.delete(f"/api/v1/ai-briefs/{unknown}").status_code == 404
