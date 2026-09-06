import uuid


def test_data_load_returns_aggregate_shape(client, make_student, make_guardian, make_event, make_note, make_brief):
    suffix = uuid.uuid4().hex[:8]
    student = make_student(name=f"Load Shape {suffix}", guardians=[])
    event_guardian = make_guardian(student["id"])
    other_guardian = make_guardian(student["id"])
    event = make_event(
        student["id"],
        guardian_id=event_guardian["id"],
        result="No Answer",
        call_time="2028-01-15T09:00:00Z",
    )
    note = make_note(student["id"])
    draft = make_brief(student["id"])
    superseded = make_brief(
        student["id"], date_from="2028-02-01T00:00:00Z", date_to="2028-02-15T00:00:00Z"
    )
    client.post(f"/api/v1/ai-briefs/{superseded['id']}/supersede")
    completed_fu = client.post(
        "/api/v1/follow-ups",
        json={
            "student_id": student["id"],
            "guardian_id": other_guardian["id"],
            "due_at": "2028-01-20T09:00:00Z",
        },
    ).json()
    client.patch(f"/api/v1/follow-ups/{completed_fu['id']}", json={"status": "completed"})

    response = client.get("/api/v1/data/load")
    assert response.status_code == 200
    body = response.json()
    assert set(body.keys()) == {"students", "events", "follow_ups", "teacher_notes", "ai_briefs"}

    loaded_student = next(s for s in body["students"] if s["id"] == student["id"])
    assert [g["id"] for g in loaded_student["guardians"]] == [event_guardian["id"], other_guardian["id"]]

    assert event["id"] in [e["id"] for e in body["events"]]

    follow_up_ids = [fu["id"] for fu in body["follow_ups"]]
    assert completed_fu["id"] not in follow_up_ids
    assert all(fu["status"] == "open" for fu in body["follow_ups"])

    assert note["id"] in [n["id"] for n in body["teacher_notes"]]

    brief_ids = [b["id"] for b in body["ai_briefs"]]
    assert draft["id"] in brief_ids
    assert superseded["id"] not in brief_ids


def test_dashboard_summary_counts_within_range(client, make_student, make_event):
    student = make_student(guardians=[])
    make_event(student["id"], result="Connected", call_time="2029-06-10T09:00:00Z")
    make_event(student["id"], result="Connected", call_time="2029-06-11T09:00:00Z")
    make_event(student["id"], result="No Answer", call_time="2029-06-12T09:00:00Z")
    make_event(student["id"], result="Busy", call_time="2029-06-13T09:00:00Z")
    make_event(student["id"], result="Failed", call_time="2029-07-10T09:00:00Z")

    outside_student = make_student(guardians=[])
    client.post(
        "/api/v1/follow-ups",
        json={"student_id": outside_student["id"], "due_at": "2029-08-01T09:00:00Z"},
    )

    response = client.get(
        "/api/v1/dashboard/summary",
        params={"from": "2029-06-01T00:00:00Z", "to": "2029-06-30T23:59:59Z"},
    )
    assert response.status_code == 200
    summary = response.json()
    assert set(summary.keys()) == {"call_attempts", "connected", "unsuccessful", "follow_ups_due"}
    assert summary["call_attempts"] == 4
    assert summary["connected"] == 2
    assert summary["unsuccessful"] == 2

    due_limit = "2029-06-30T23:59:59Z"
    open_follow_ups = client.get("/api/v1/follow-ups", params={"status": "open"}).json()
    from helpers import parse_dt

    expected_due = sum(
        1 for fu in open_follow_ups if parse_dt(fu["due_at"]) <= parse_dt(due_limit)
    )
    assert summary["follow_ups_due"] == expected_due
    assert expected_due >= 1

    response = client.get("/api/v1/dashboard/summary")
    assert response.status_code == 200
    assert set(response.json().keys()) == {"call_attempts", "connected", "unsuccessful", "follow_ups_due"}
