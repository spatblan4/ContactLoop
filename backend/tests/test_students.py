import uuid

from helpers import parse_dt

def test_create_student_with_nested_guardians(client, make_student, auth_user):
    student = make_student(
        name="Amara Okafor",
        initials="AO",
        accent="lavender",
        guardians=[
            {"name": "Chidi Okafor", "relation": "Dad", "phone": "555-0101"},
            {"name": "Ngozi Okafor", "relation": "Mom", "phone": "555-0102", "email": "ngozi@example.com"},
        ],
    )
    assert student["name"] == "Amara Okafor"
    assert student["initials"] == "AO"
    assert student["accent"] == "lavender"
    assert len(student["guardians"]) == 2
    assert student["guardians"][0]["name"] == "Chidi Okafor"
    assert student["guardians"][1]["email"] == "ngozi@example.com"
    for field in ("id", "created_at", "updated_at", "created_by", "updated_by"):
        assert field in student
    assert student["created_by"] == auth_user["id"]
    assert student["updated_by"] == auth_user["id"]


def test_audit_fields_record_authenticated_create(make_student, auth_user):
    student = make_student()
    for field in ("id", "created_at", "updated_at", "created_by", "updated_by"):
        assert field in student
    assert student["created_by"] == auth_user["id"]
    assert student["updated_by"] == auth_user["id"]


def test_get_student_includes_guardians(client, make_student):
    student = make_student(guardians=[{"name": "Rosa Diaz", "relation": "Mom", "phone": "555-0203"}])
    response = client.get(f"/api/v1/students/{student['id']}")
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == student["id"]
    assert [g["name"] for g in body["guardians"]] == ["Rosa Diaz"]


def test_patch_student_updates_name_stamps_updated_at_and_actor(client, make_student, auth_user):
    student = make_student(name="Amara Okafor")
    before = parse_dt(student["updated_at"])
    response = client.patch(
        f"/api/v1/students/{student['id']}",
        json={"name": "Amara Okafor-Smith"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "Amara Okafor-Smith"
    assert body["created_by"] == auth_user["id"]
    assert body["updated_by"] == auth_user["id"]
    assert parse_dt(body["updated_at"]) > before
    assert parse_dt(body["created_at"]) == parse_dt(student["created_at"])


def test_student_search_matches_name_initials_guardian_name_and_phone(client, make_student):
    suffix = uuid.uuid4().hex[:6]
    student = make_student(
        name=f"Maya Lin {suffix}",
        initials="ML",
        guardians=[{"name": f"Grace Lin {suffix}", "relation": "Mom", "phone": f"555-{suffix}"}],
    )
    student_id = student["id"]

    response = client.get("/api/v1/students", params={"search": f"Maya Lin {suffix}"})
    assert [s["id"] for s in response.json()] == [student_id]

    response = client.get("/api/v1/students", params={"search": "ML"})
    assert student_id in [s["id"] for s in response.json()]

    response = client.get("/api/v1/students", params={"search": f"Grace Lin {suffix}"})
    assert [s["id"] for s in response.json()] == [student_id]

    response = client.get("/api/v1/students", params={"search": f"555-{suffix}"})
    assert [s["id"] for s in response.json()] == [student_id]

    response = client.get("/api/v1/students", params={"search": "no-such-student-xyz"})
    assert response.json() == []


def test_delete_student_is_soft_and_hides_row(client, make_student):
    student = make_student()
    response = client.delete(f"/api/v1/students/{student['id']}")
    assert response.status_code == 204
    assert response.content == b""

    assert client.get(f"/api/v1/students/{student['id']}").status_code == 404
    listed = client.get("/api/v1/students", params={"search": student["name"]}).json()
    assert listed == []


def test_delete_student_cascades_to_all_child_entities(
    client, make_student, make_guardian, make_event, make_note, make_brief
):
    suffix = uuid.uuid4().hex[:8]
    student = make_student(name=f"Cascade {suffix}", guardians=[])
    guardian = make_guardian(student["id"], name=f"Casc Guardian {suffix}")
    event = make_event(student["id"], guardian_id=guardian["id"], result="No Answer")
    note = make_note(student["id"])
    brief = make_brief(student["id"])

    other = make_student(name=f"Survivor {suffix}")
    other_note = make_note(other["id"])

    response = client.delete(f"/api/v1/students/{student['id']}")
    assert response.status_code == 204

    assert client.get(f"/api/v1/guardians?student_id={student['id']}").json() == []
    assert client.get(f"/api/v1/contact-events?student_id={student['id']}").json() == []
    assert client.get(f"/api/v1/follow-ups?student_id={student['id']}").json() == []
    assert client.get(f"/api/v1/teacher-notes?student_id={student['id']}").json() == []
    assert client.get(f"/api/v1/ai-briefs?student_id={student['id']}").json() == []
    assert client.get(f"/api/v1/teacher-notes?student_id={other['id']}").json()[0]["id"] == other_note["id"]


def test_create_student_missing_name_returns_400(client):
    response = client.post("/api/v1/students", json={"guardians": []})
    assert response.status_code == 400
    assert "detail" in response.json()


def test_unknown_student_returns_404_for_get_patch_delete(client):
    unknown = str(uuid.uuid4())
    assert client.get(f"/api/v1/students/{unknown}").status_code == 404
    assert client.patch(f"/api/v1/students/{unknown}", json={"name": "x"}).status_code == 404
    assert client.delete(f"/api/v1/students/{unknown}").status_code == 404
    assert "detail" in client.get(f"/api/v1/students/{unknown}").json()


def test_malformed_student_id_returns_400(client):
    response = client.get("/api/v1/students/not-a-uuid")
    assert response.status_code == 400


def test_students_require_login(anonymous_client, make_student):
    student = make_student()
    unknown = str(uuid.uuid4())

    assert anonymous_client.get("/api/v1/students").status_code == 401
    assert anonymous_client.post(
        "/api/v1/students", json={"name": "Anonymous", "guardians": []}
    ).status_code == 401
    assert anonymous_client.get(f"/api/v1/students/{student['id']}").status_code == 401
    assert anonymous_client.patch(
        f"/api/v1/students/{student['id']}", json={"name": "Anonymous edit"}
    ).status_code == 401
    assert anonymous_client.delete(f"/api/v1/students/{student['id']}").status_code == 401
    assert anonymous_client.get(f"/api/v1/students/{unknown}").status_code == 401


def test_student_ids_are_isolated_by_owner(client, make_student, second_auth):
    student = make_student(name="Private Student")
    foreign_headers = second_auth["headers"]

    assert client.get("/api/v1/students", headers=foreign_headers).json() == []
    assert client.get(
        f"/api/v1/students/{student['id']}", headers=foreign_headers
    ).status_code == 404
    assert client.patch(
        f"/api/v1/students/{student['id']}",
        json={"name": "Foreign edit"},
        headers=foreign_headers,
    ).status_code == 404
    assert client.delete(
        f"/api/v1/students/{student['id']}", headers=foreign_headers
    ).status_code == 404


def test_x_user_id_cannot_spoof_student_owner(client, make_student, auth_user, second_auth):
    student = make_student(headers={"X-User-Id": second_auth["user"]["id"]})

    assert student["owner_id"] == auth_user["id"]
    assert student["created_by"] == auth_user["id"]
    assert client.get(
        f"/api/v1/students/{student['id']}", headers=second_auth["headers"]
    ).status_code == 404
