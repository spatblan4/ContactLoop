import uuid
from datetime import datetime, timedelta, timezone

from helpers import parse_dt


def open_follow_ups(client, student_id, guardian_id=None):
    params = {"student_id": student_id, "status": "open"}
    if guardian_id is not None:
        params["guardian_id"] = guardian_id
    return [fu for fu in client.get("/api/v1/follow-ups", params=params).json() if fu["guardian_id"] == guardian_id]


def test_no_answer_opens_follow_up_due_next_day(client, make_student, make_guardian, make_event):
    student = make_student(guardians=[])
    guardian = make_guardian(student["id"])
    event = make_event(
        student["id"],
        guardian_id=guardian["id"],
        result="No Answer",
        call_time="2028-01-05T10:00:00Z",
        ended_at="2028-01-05T10:00:00Z",
    )
    follow_ups = open_follow_ups(client, student["id"], guardian["id"])
    assert len(follow_ups) == 1
    fu = follow_ups[0]
    assert fu["status"] == "open"
    assert fu["contact_event_id"] == event["id"]
    assert parse_dt(fu["due_at"]) == datetime(2028, 1, 6, 10, 0, 0)


def test_unsuccessful_results_upsert_single_open_follow_up(client, make_student, make_guardian, make_event):
    student = make_student(guardians=[])
    guardian = make_guardian(student["id"])

    make_event(student["id"], guardian_id=guardian["id"], result="No Answer", call_time="2028-01-06T11:00:00Z")
    first = open_follow_ups(client, student["id"], guardian["id"])[0]
    assert parse_dt(first["due_at"]) == datetime(2028, 1, 7, 11, 0, 0)

    make_event(student["id"], guardian_id=guardian["id"], result="Busy", call_time="2028-01-07T09:00:00Z")
    follow_ups = open_follow_ups(client, student["id"], guardian["id"])
    assert len(follow_ups) == 1
    assert follow_ups[0]["id"] == first["id"]
    assert parse_dt(follow_ups[0]["due_at"]) == datetime(2028, 1, 8, 9, 0, 0)

    third = make_event(student["id"], guardian_id=guardian["id"], result="Failed", call_time="2028-01-08T09:00:00Z")
    follow_ups = open_follow_ups(client, student["id"], guardian["id"])
    assert len(follow_ups) == 1
    assert follow_ups[0]["id"] == first["id"]
    assert follow_ups[0]["contact_event_id"] == third["id"]
    assert parse_dt(follow_ups[0]["due_at"]) == datetime(2028, 1, 9, 9, 0, 0)


def test_caller_supplied_follow_up_due_at_wins(client, make_student, make_guardian, make_event):
    student = make_student(guardians=[])
    guardian = make_guardian(student["id"])
    event = make_event(
        student["id"],
        guardian_id=guardian["id"],
        result="Busy",
        call_time="2028-01-07T09:00:00Z",
        ended_at="2028-01-07T09:00:00Z",
        follow_up_due_at="2028-01-09T08:00:00Z",
    )
    follow_ups = open_follow_ups(client, student["id"], guardian["id"])
    assert len(follow_ups) == 1
    assert follow_ups[0]["contact_event_id"] == event["id"]
    assert parse_dt(follow_ups[0]["due_at"]) == datetime(2028, 1, 9, 8, 0, 0)


def test_connected_completes_open_follow_up_with_completed_at(client, make_student, make_guardian, make_event):
    student = make_student(guardians=[])
    guardian = make_guardian(student["id"])
    make_event(student["id"], guardian_id=guardian["id"], result="No Answer", call_time="2028-01-08T09:00:00Z")
    open_fu = open_follow_ups(client, student["id"], guardian["id"])[0]
    assert open_fu["completed_at"] is None

    connected = make_event(
        student["id"],
        guardian_id=guardian["id"],
        result="Connected",
        call_time="2028-01-09T10:00:00Z",
        ended_at="2028-01-09T10:00:00Z",
        discussed_topics=["attendance", "homework"],
    )
    assert connected["discussed_topics"] == ["attendance", "homework"]

    assert open_follow_ups(client, student["id"], guardian["id"]) == []
    response = client.get(f"/api/v1/follow-ups/{open_fu['id']}")
    assert response.status_code == 200
    completed = response.json()
    assert completed["status"] == "completed"
    assert completed["completed_at"] is not None
    assert completed["contact_event_id"] == connected["id"]


def test_connected_without_open_follow_up_creates_none(client, make_student, make_guardian, make_event):
    student = make_student(guardians=[])
    guardian = make_guardian(student["id"])
    make_event(student["id"], guardian_id=guardian["id"], result="Connected", call_time="2028-01-09T10:00:00Z")
    assert open_follow_ups(client, student["id"], guardian["id"]) == []


def test_open_follow_up_per_guardian_is_isolated(client, make_student, make_guardian, make_event):
    student = make_student(guardians=[])
    mom = make_guardian(student["id"])
    dad = make_guardian(student["id"])
    make_event(student["id"], guardian_id=mom["id"], result="No Answer", call_time="2028-01-05T10:00:00Z")
    response = client.post(
        "/api/v1/follow-ups",
        json={"student_id": student["id"], "guardian_id": dad["id"], "due_at": "2028-01-20T09:00:00Z"},
    )
    assert response.status_code == 201
    assert len(open_follow_ups(client, student["id"], mom["id"])) == 1
    assert len(open_follow_ups(client, student["id"], dad["id"])) == 1


def test_duplicate_open_follow_up_returns_409(client, make_student, make_guardian, make_event):
    student = make_student(guardians=[])
    guardian = make_guardian(student["id"])
    response = client.post(
        "/api/v1/follow-ups",
        json={"student_id": student["id"], "guardian_id": guardian["id"], "due_at": "2028-01-15T09:00:00Z"},
    )
    assert response.status_code == 201
    response = client.post(
        "/api/v1/follow-ups",
        json={"student_id": student["id"], "guardian_id": guardian["id"], "due_at": "2028-01-16T09:00:00Z"},
    )
    assert response.status_code == 409
    assert "detail" in response.json()


def test_new_open_follow_up_allowed_after_completion(client, make_student, make_guardian, make_event):
    student = make_student(guardians=[])
    guardian = make_guardian(student["id"])
    make_event(student["id"], guardian_id=guardian["id"], result="Connected", call_time="2028-01-09T10:00:00Z")
    response = client.post(
        "/api/v1/follow-ups",
        json={"student_id": student["id"], "guardian_id": guardian["id"], "due_at": "2028-01-25T09:00:00Z"},
    )
    assert response.status_code == 201


def test_caller_supplied_follow_up_id_is_closed(client, make_student, make_guardian, make_event):
    student = make_student(guardians=[])
    guardian = make_guardian(student["id"])
    follow_up = client.post(
        "/api/v1/follow-ups",
        json={"student_id": student["id"], "guardian_id": guardian["id"], "due_at": "2028-01-12T09:00:00Z"},
    ).json()

    event = make_event(
        student["id"],
        guardian_id=guardian["id"],
        result="Connected",
        call_time="2028-01-11T10:00:00Z",
        ended_at="2028-01-11T10:00:00Z",
    )
    response = client.patch(
        f"/api/v1/contact-events/{event['id']}",
        json={"follow_up_id": follow_up["id"], "result": "Connected"},
    )
    assert response.status_code == 200
    completed = client.get(f"/api/v1/follow-ups/{follow_up['id']}").json()
    assert completed["status"] == "completed"
    assert completed["completed_at"] is not None
    assert completed["contact_event_id"] == event["id"]


def test_patch_event_re_runs_follow_up_sync(client, make_student, make_guardian, make_event):
    student = make_student(guardians=[])
    guardian = make_guardian(student["id"])
    event = make_event(
        student["id"],
        guardian_id=guardian["id"],
        result="No Answer",
        call_time="2028-01-10T09:00:00Z",
        ended_at="2028-01-10T09:00:00Z",
    )
    open_fu = open_follow_ups(client, student["id"], guardian["id"])[0]

    response = client.patch(
        f"/api/v1/contact-events/{event['id']}",
        json={"result": "Connected", "ended_at": "2028-01-10T09:05:00Z"},
    )
    assert response.status_code == 200
    completed = client.get(f"/api/v1/follow-ups/{open_fu['id']}").json()
    assert completed["status"] == "completed"
    assert completed["contact_event_id"] == event["id"]
    assert open_follow_ups(client, student["id"], guardian["id"]) == []


def test_server_stamped_ended_at_opens_follow_up_due_next_day(client, make_student):
    student = make_student(guardians=[])
    before = datetime.now(timezone.utc).replace(tzinfo=None)
    response = client.post(
        "/api/v1/contact-events",
        json={"student_id": student["id"], "result": "No Answer"},
    )
    assert response.status_code == 201
    follow_ups = open_follow_ups(client, student["id"], None)
    assert len(follow_ups) == 1
    due = parse_dt(follow_ups[0]["due_at"])
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    assert before + timedelta(days=1) <= due <= now + timedelta(days=1)
