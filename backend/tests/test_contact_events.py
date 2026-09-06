import uuid


def test_create_event_computes_attempt_number_server_side(client, make_student, make_guardian, make_event):
    student = make_student(guardians=[])
    guardian = make_guardian(student["id"])
    event = make_event(student["id"], guardian_id=guardian["id"], result="No Answer")
    assert event["attempt_number"] == 1
    assert event["result"] == "No Answer"
    assert event["student_id"] == student["id"]
    assert event["guardian_id"] == guardian["id"]
    for field in ("id", "created_at", "updated_at", "created_by", "updated_by"):
        assert field in event


def test_caller_supplied_attempt_number_is_ignored(client, make_student):
    student = make_student(guardians=[])
    response = client.post(
        "/api/v1/contact-events",
        json={
            "student_id": student["id"],
            "result": "No Answer",
            "call_time": "2028-01-10T09:00:00Z",
            "ended_at": "2028-01-10T09:00:00Z",
            "attempt_number": 99,
        },
    )
    assert response.status_code == 201
    assert response.json()["attempt_number"] == 1


def test_attempt_numbers_sequence_per_student_and_guardian(client, make_student, make_guardian, make_event):
    student = make_student(guardians=[])
    mom = make_guardian(student["id"])
    dad = make_guardian(student["id"])

    e1 = make_event(student["id"], guardian_id=mom["id"], call_time="2028-01-02T09:00:00Z")
    e2 = make_event(student["id"], guardian_id=mom["id"], call_time="2028-01-03T09:00:00Z")
    e3 = make_event(student["id"], guardian_id=mom["id"], call_time="2028-01-04T09:00:00Z")
    d1 = make_event(student["id"], guardian_id=dad["id"], call_time="2028-01-05T09:00:00Z")
    n1 = make_event(student["id"], guardian_id=None, call_time="2028-01-06T09:00:00Z")
    assert e1["attempt_number"] == 1
    assert e2["attempt_number"] == 2
    assert e3["attempt_number"] == 3
    assert d1["attempt_number"] == 1
    assert n1["attempt_number"] == 1


def test_soft_deleted_events_excluded_from_attempt_count(client, make_student, make_event):
    student = make_student(guardians=[])
    e1 = make_event(student["id"], call_time="2028-01-02T09:00:00Z")
    e2 = make_event(student["id"], call_time="2028-01-03T09:00:00Z")
    client.delete(f"/api/v1/contact-events/{e2['id']}")
    e3 = make_event(student["id"], call_time="2028-01-04T09:00:00Z")
    assert e1["attempt_number"] == 1
    assert e3["attempt_number"] == 2


def test_list_events_filters_by_student_range_and_result(client, make_student, make_guardian, make_event):
    student = make_student(guardians=[])
    other = make_student(guardians=[])
    in_range = make_event(
        student["id"], result="Connected", call_time="2028-01-10T09:00:00Z"
    )
    out_of_range = make_event(
        student["id"], result="No Answer", call_time="2028-02-10T09:00:00Z"
    )
    make_event(other["id"], result="Connected", call_time="2028-01-10T09:00:00Z")

    response = client.get(
        "/api/v1/contact-events",
        params={"student_id": student["id"], "from": "2028-01-01T00:00:00Z", "to": "2028-01-31T23:59:59Z"},
    )
    assert [e["id"] for e in response.json()] == [in_range["id"]]

    response = client.get(
        "/api/v1/contact-events",
        params={"student_id": student["id"], "result": "No Answer"},
    )
    assert [e["id"] for e in response.json()] == [out_of_range["id"]]


def test_get_event_by_id(client, make_student, make_event):
    student = make_student(guardians=[])
    event = make_event(student["id"], result="Busy", topic="quarterly check-in")
    response = client.get(f"/api/v1/contact-events/{event['id']}")
    assert response.status_code == 200
    assert response.json()["topic"] == "quarterly check-in"


def test_patch_event_persists_fields_without_sync_trigger(client, make_student, make_event):
    student = make_student(guardians=[])
    event = make_event(student["id"], result="Connected", call_time="2028-01-10T09:00:00Z")
    response = client.patch(
        f"/api/v1/contact-events/{event['id']}",
        json={"topic": "math camp", "duration_seconds": 300},
        headers={"X-User-Id": str(uuid.uuid4())},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["topic"] == "math camp"
    assert body["duration_seconds"] == 300
    assert body["result"] == "Connected"


def test_delete_event_is_soft(client, make_student, make_event):
    student = make_student(guardians=[])
    event = make_event(student["id"])
    response = client.delete(f"/api/v1/contact-events/{event['id']}")
    assert response.status_code == 204
    assert client.get(f"/api/v1/contact-events/{event['id']}").status_code == 404
    assert client.get(f"/api/v1/contact-events?student_id={student['id']}").json() == []


def test_invalid_result_returns_400(client, make_student):
    student = make_student(guardians=[])
    response = client.post(
        "/api/v1/contact-events",
        json={
            "student_id": student["id"],
            "result": "Invalid Result",
            "call_time": "2028-01-10T09:00:00Z",
            "ended_at": "2028-01-10T09:00:00Z",
        },
    )
    assert response.status_code == 400


def test_unknown_event_returns_404(client):
    unknown = str(uuid.uuid4())
    assert client.get(f"/api/v1/contact-events/{unknown}").status_code == 404
    assert client.patch(f"/api/v1/contact-events/{unknown}", json={"topic": "x"}).status_code == 404
    assert client.delete(f"/api/v1/contact-events/{unknown}").status_code == 404
