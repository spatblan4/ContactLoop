import uuid

from helpers import make_jwt

JWT_SECRET = "pytest-jwt-secret"


def test_x_user_id_header_records_actor(client, make_student):
    actor = str(uuid.uuid4())
    student = make_student(headers={"X-User-Id": actor})
    assert student["created_by"] == actor
    assert student["updated_by"] == actor


def test_bearer_jwt_sub_records_actor(client):
    student_id = uuid.uuid4()
    guardian_id = uuid.uuid4()
    token = make_jwt({"sub": str(student_id)}, JWT_SECRET)
    response = client.post(
        "/api/v1/guardians",
        json={"student_id": str(guardian_id), "name": "Token Mom", "relation": "Mom"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    assert response.json()["created_by"] == str(student_id)


def test_invalid_x_user_id_falls_back_to_jwt_sub(client):
    jwt_user = uuid.uuid4()
    token = make_jwt({"sub": str(jwt_user)}, JWT_SECRET)
    response = client.post(
        "/api/v1/teacher-notes",
        json={"student_id": str(uuid.uuid4()), "content": "jwt actor note"},
        headers={"X-User-Id": "not-a-uuid", "Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    assert response.json()["created_by"] == str(jwt_user)


def test_invalid_x_user_id_without_jwt_is_anonymous(client, make_student):
    student = make_student(headers={"X-User-Id": "not-a-uuid"})
    assert student["created_by"] is None
    assert student["updated_by"] is None


def test_bad_signature_jwt_is_anonymous(client, make_student):
    token = make_jwt({"sub": str(uuid.uuid4())}, "wrong-secret")
    student = make_student(headers={"Authorization": f"Bearer {token}"})
    assert student["created_by"] is None


def test_ai_contact_brief_generate_returns_501(client):
    response = client.post(
        "/api/v1/ai/contact-brief/generate",
        json={"student_id": str(uuid.uuid4()), "date_from": "2028-01-01", "date_to": "2028-01-31"},
    )
    assert response.status_code == 501
    assert "detail" in response.json()
