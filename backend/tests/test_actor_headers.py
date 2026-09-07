import uuid


def test_x_user_id_cannot_override_authenticated_actor(client, make_student, auth_user):
    student = make_student(headers={"X-User-Id": str(uuid.uuid4())})
    assert student["created_by"] == auth_user["id"]
    assert student["updated_by"] == auth_user["id"]


def test_invalid_bearer_token_is_rejected(anonymous_client):
    response = anonymous_client.get(
        "/api/v1/students",
        headers={"Authorization": "Bearer invalid-token"},
    )
    assert response.status_code == 401


def test_ai_contact_brief_generate_returns_501(client):
    response = client.post(
        "/api/v1/ai/contact-brief/generate",
        json={"student_id": str(uuid.uuid4()), "date_from": "2028-01-01", "date_to": "2028-01-31"},
    )
    assert response.status_code == 501
    assert "detail" in response.json()
