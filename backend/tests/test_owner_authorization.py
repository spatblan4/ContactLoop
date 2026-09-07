def test_related_resources_require_login(
    anonymous_client, make_student, make_guardian, make_event, make_follow_up, make_note, make_brief
):
    student = make_student(guardians=[])
    guardian = make_guardian(student["id"])
    event = make_event(student["id"], guardian_id=guardian["id"], result="Connected")
    follow_up = make_follow_up(student["id"], guardian_id=guardian["id"])
    note = make_note(student["id"])
    brief = make_brief(student["id"])

    for collection in (
        "guardians",
        "contact-events",
        "follow-ups",
        "teacher-notes",
        "ai-briefs",
    ):
        assert anonymous_client.get(f"/api/v1/{collection}").status_code == 401

    for collection, resource in (
        ("guardians", guardian),
        ("contact-events", event),
        ("follow-ups", follow_up),
        ("teacher-notes", note),
        ("ai-briefs", brief),
    ):
        path = f"/api/v1/{collection}/{resource['id']}"
        assert anonymous_client.get(path).status_code == 401
        assert anonymous_client.delete(path).status_code == 401


def test_related_resources_are_isolated_by_student_owner(
    client,
    second_auth,
    make_student,
    make_guardian,
    make_event,
    make_follow_up,
    make_note,
    make_brief,
):
    student = make_student(guardians=[])
    guardian = make_guardian(student["id"])
    event = make_event(student["id"], guardian_id=guardian["id"], result="Connected")
    follow_up = make_follow_up(student["id"], guardian_id=guardian["id"])
    note = make_note(student["id"])
    brief = make_brief(student["id"])
    headers = second_auth["headers"]

    for collection in (
        "guardians",
        "contact-events",
        "follow-ups",
        "teacher-notes",
        "ai-briefs",
    ):
        assert client.get(f"/api/v1/{collection}", headers=headers).json() == []

    updates = {
        "guardians": {"name": "Foreign edit"},
        "contact-events": {"teacher_note": "Foreign edit"},
        "follow-ups": {"status": "dismissed"},
        "teacher-notes": {"content": "Foreign edit"},
        "ai-briefs": {"suggested_next_step": "Foreign edit"},
    }
    for collection, resource in (
        ("guardians", guardian),
        ("contact-events", event),
        ("follow-ups", follow_up),
        ("teacher-notes", note),
        ("ai-briefs", brief),
    ):
        path = f"/api/v1/{collection}/{resource['id']}"
        assert client.get(path, headers=headers).status_code == 404
        assert client.patch(path, json=updates[collection], headers=headers).status_code == 404
        assert client.delete(path, headers=headers).status_code == 404

    assert client.post(
        "/api/v1/guardians",
        json={"student_id": student["id"], "name": "Foreign", "relation": "Other"},
        headers=headers,
    ).status_code == 404
    assert client.post(
        "/api/v1/contact-events",
        json={"student_id": student["id"], "result": "Connected"},
        headers=headers,
    ).status_code == 404
    assert client.post(
        "/api/v1/follow-ups",
        json={"student_id": student["id"], "due_at": "2028-04-01T09:00:00Z"},
        headers=headers,
    ).status_code == 404
    assert client.post(
        "/api/v1/teacher-notes",
        json={"student_id": student["id"], "content": "Foreign"},
        headers=headers,
    ).status_code == 404
    assert client.post(
        "/api/v1/ai-briefs",
        json={
            "student_id": student["id"],
            "date_from": "2028-02-01T00:00:00Z",
            "date_to": "2028-02-28T00:00:00Z",
        },
        headers=headers,
    ).status_code == 404
    assert client.post(
        f"/api/v1/ai-briefs/{brief['id']}/approve", headers=headers
    ).status_code == 404
    assert client.post(
        f"/api/v1/ai-briefs/{brief['id']}/supersede", headers=headers
    ).status_code == 404
