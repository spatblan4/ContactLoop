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
