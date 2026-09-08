def test_start_call_requires_login(anonymous_client, make_student):
    student = make_student(guardians=[])

    response = anonymous_client.post(
        "/api/v1/telephony/calls",
        json={"student_id": student["id"], "planned_topic": "Behavior"},
    )

    assert response.status_code == 401


def test_call_status_sync_requires_login(anonymous_client):
    response = anonymous_client.post(
        "/api/v1/telephony/call-status-sync",
        json={},
    )

    assert response.status_code == 401


def test_start_call_rejects_other_users_student(client, second_auth, make_student):
    student = make_student(guardians=[])

    response = client.post(
        "/api/v1/telephony/calls",
        json={"student_id": student["id"]},
        headers=second_auth["headers"],
    )

    assert response.status_code == 404


def test_start_call_forwards_owned_student_without_calling_twilio(
    client, make_student, monkeypatch
):
    from app.api.v1 import telephony

    student = make_student(guardians=[])
    captured = {}

    def fake_start_call(student_id, planned_topic):
        captured["student_id"] = student_id
        captured["planned_topic"] = planned_topic
        return {"eventId": "event-1", "providerCallId": "call-1"}

    monkeypatch.setattr(telephony, "invoke_start_call", fake_start_call)

    response = client.post(
        "/api/v1/telephony/calls",
        json={"student_id": student["id"], "planned_topic": "Behavior"},
    )

    assert response.status_code == 200
    assert response.json() == {"eventId": "event-1", "providerCallId": "call-1"}
    assert str(captured["student_id"]) == student["id"]
    assert captured["planned_topic"] == "Behavior"


def test_call_status_sync_rejects_another_users_event(client, second_auth, make_student, make_event):
    student = make_student(guardians=[])
    event = make_event(student["id"])

    response = client.post(
        "/api/v1/telephony/call-status-sync",
        json={"event_id": event["id"]},
        headers=second_auth["headers"],
    )

    assert response.status_code == 404


def test_call_status_sync_forwards_only_an_owned_event(client, make_student, make_event, monkeypatch):
    from app.api.v1 import telephony

    student = make_student(guardians=[])
    event = make_event(student["id"])
    captured = {}

    def fake_sync(event_id):
        captured["event_id"] = event_id
        return {"synced": [{"id": str(event_id), "status": "completed"}]}

    monkeypatch.setattr(telephony, "invoke_call_status_sync", fake_sync)

    response = client.post(
        "/api/v1/telephony/call-status-sync",
        json={"event_id": event["id"]},
    )

    assert response.status_code == 200
    assert response.json()["synced"][0]["id"] == event["id"]
    assert str(captured["event_id"]) == event["id"]
