import uuid

import pytest

from tests.helpers import make_email, make_password


@pytest.fixture
def make_user(client):
    def _make(email=None, password=None, name=None):
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": email or make_email(),
                "password": password or make_password(),
                "name": name,
            },
        )
        assert response.status_code == 201, response.text
        return response.json()

    return _make


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


def test_register_returns_user_and_token(make_user):
    result = make_user(name="Test Teacher")
    assert result["user"]["email"]
    assert result["user"]["name"] == "Test Teacher"
    assert result["user"]["id"]
    assert result["token"]
    assert result["user"]["created_at"]
    assert result["user"]["updated_at"]


def test_register_rejects_duplicate_email(client, make_user):
    email = make_email()
    make_user(email=email)
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": make_password()},
    )
    assert response.status_code == 409


def test_register_rejects_short_password(client):
    response = client.post(
        "/api/v1/auth/register",
        json={"email": make_email(), "password": "123"},
    )
    assert response.status_code == 400


def test_register_rejects_invalid_email(client):
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "not-an-email", "password": make_password()},
    )
    assert response.status_code == 400


def test_login_success(client, make_user):
    email = make_email()
    password = make_password()
    make_user(email=email, password=password)
    response = client.post(
        "/api/v1/auth/login", json={"email": email, "password": password}
    )
    assert response.status_code == 200, response.text
    assert response.json()["token"]
    assert response.json()["user"]["email"] == email


def test_login_rejects_wrong_password(client, make_user):
    email = make_email()
    make_user(email=email, password=make_password())
    response = client.post(
        "/api/v1/auth/login", json={"email": email, "password": "wrong-pass"}
    )
    assert response.status_code == 401


def test_me_requires_token(anonymous_client):
    response = anonymous_client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_me_with_token(client, make_user):
    result = make_user()
    response = client.get("/api/v1/auth/me", headers=auth_headers(result["token"]))
    assert response.status_code == 200
    assert response.json()["id"] == result["user"]["id"]


def test_logout_revokes_token(client, make_user):
    result = make_user()
    headers = auth_headers(result["token"])
    assert client.get("/api/v1/auth/me", headers=headers).status_code == 200
    assert client.post("/api/v1/auth/logout", headers=headers).status_code == 204
    assert client.get("/api/v1/auth/me", headers=headers).status_code == 401


def test_authenticated_user_sees_only_own_students(client, make_user, make_student):
    owner = make_user()
    other = make_user()
    headers = auth_headers(owner["token"])
    own_student = make_student(name="Owned Student", headers=headers)
    make_student(name="Other Student", headers=auth_headers(other["token"]))
    make_student(name="Anonymous Student")

    listed = client.get("/api/v1/students", headers=headers).json()
    assert [s["id"] for s in listed] == [own_student["id"]]

    data = client.get("/api/v1/data/load", headers=headers).json()
    assert [s["id"] for s in data["students"]] == [own_student["id"]]

    summary = client.get("/api/v1/dashboard/summary", headers=headers).json()
    assert summary["call_attempts"] == 0


def test_authenticated_creates_students_owned_by_self(client, make_user, make_student):
    user = make_user()
    headers = auth_headers(user["token"])
    student = make_student(headers=headers)
    fetched = client.get(f"/api/v1/students/{student['id']}", headers=headers).json()
    assert fetched["owner_id"] == user["user"]["id"]


def test_created_by_records_auth_user(client, make_user, make_student):
    user = make_user()
    headers = auth_headers(user["token"])
    student = make_student(headers=headers)
    assert student["created_by"] == user["user"]["id"]
    assert student["updated_by"] == user["user"]["id"]


def test_users_table_has_audit_columns(client, make_user):
    result = make_user()
    me = client.get("/api/v1/auth/me", headers=auth_headers(result["token"])).json()
    for field in ("created_at", "updated_at"):
        assert me[field]


def test_two_users_same_student_name_do_not_conflict(client, make_user, make_student):
    suffix = uuid.uuid4().hex[:8]
    make_student(
        name=f"Twin {suffix}", headers=auth_headers(make_user()["token"])
    )
    make_student(
        name=f"Twin {suffix}", headers=auth_headers(make_user()["token"])
    )
    assert len(client.get("/api/v1/students").json()) >= 2
