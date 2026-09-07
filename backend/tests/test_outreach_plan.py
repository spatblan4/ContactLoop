from datetime import datetime, timezone

from tests.test_auth import make_user


def test_candidate_builder_keeps_only_current_teachers_students(
    client, make_user, make_student, make_event, make_follow_up
):
    from tests.test_auth import auth_headers
    from app.api.deps import get_db
    from app.services.outreach_plan import build_outreach_candidates

    teacher_a = make_user()
    teacher_b = make_user()
    mine = make_student(headers=auth_headers(teacher_a["token"]))
    other = make_student(headers=auth_headers(teacher_b["token"]))
    make_follow_up(mine["id"], due_at="2026-09-06T09:00:00Z")
    make_event(mine["id"], headers=auth_headers(teacher_a["token"]), result="No Answer")
    db = next(get_db())
    candidates = build_outreach_candidates(
        db, teacher_a["user"]["id"], datetime.now(timezone.utc)
    )

    assert [item["student_id"] for item in candidates] == [mine["id"]]
    assert other["id"] not in str(candidates)


def test_candidate_builder_fails_closed_without_an_owner(
    make_user, make_student
):
    from tests.test_auth import auth_headers
    from app.api.deps import get_db
    from app.services.outreach_plan import build_outreach_candidates

    first_teacher = make_user()
    second_teacher = make_user()
    make_student(headers=auth_headers(first_teacher["token"]))
    make_student(headers=auth_headers(second_teacher["token"]))

    db = next(get_db())
    candidates = build_outreach_candidates(db, None, datetime.now(timezone.utc))

    assert candidates == []


def test_candidate_builder_returns_minimized_latest_confirmed_facts(
    client,
    make_user,
    make_student,
    make_guardian,
    make_follow_up,
    make_note,
):
    from tests.test_auth import auth_headers
    from app.api.deps import get_db
    from app.services.outreach_plan import build_outreach_candidates

    teacher = make_user()
    headers = auth_headers(teacher["token"])
    student = make_student(headers=headers, guardians=[])
    first_guardian = make_guardian(student["id"])
    second_guardian = make_guardian(student["id"])
    make_follow_up(
        student["id"],
        guardian_id=first_guardian["id"],
        due_at="2026-09-07T09:00:00Z",
    )
    make_follow_up(
        student["id"],
        guardian_id=second_guardian["id"],
        due_at="2026-09-06T09:00:00Z",
    )
    for result, call_time in (
        ("No Answer", "2026-09-06T08:00:00Z"),
        ("Connected", "2026-09-06T10:00:00Z"),
    ):
        response = client.post(
            "/api/v1/contact-events",
            json={
                "student_id": student["id"],
                "result": result,
                "call_time": call_time,
            },
            headers=headers,
        )
        assert response.status_code == 201, response.text
    make_note(student["id"], content="Confirmed context", teacher_confirmed=True)
    make_note(student["id"], content="Do not share", teacher_confirmed=False)

    db = next(get_db())
    candidate = next(
        item
        for item in build_outreach_candidates(
            db, teacher["user"]["id"], datetime.now(timezone.utc)
        )
        if item["student_id"] == student["id"]
    )

    assert set(candidate) == {
        "student_id",
        "student_name",
        "last_contact_result",
        "last_contact_at",
        "open_follow_up_due_at",
        "teacher_confirmed_notes",
    }
    assert candidate["last_contact_result"] == "Connected"
    assert candidate["last_contact_at"] == "2026-09-06T10:00:00"
    assert candidate["open_follow_up_due_at"] == "2026-09-06T09:00:00"
    assert candidate["teacher_confirmed_notes"] == ["Confirmed context"]
