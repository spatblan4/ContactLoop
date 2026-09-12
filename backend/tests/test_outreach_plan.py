from types import SimpleNamespace

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
    make_follow_up(mine["id"], due_at="2026-09-06T09:00:00Z", headers=auth_headers(teacher_a["token"]))
    make_event(mine["id"], headers=auth_headers(teacher_a["token"]), result="No Answer")
    db = next(get_db())
    candidates = build_outreach_candidates(db, teacher_a["user"]["id"])

    assert [str(item.student_id) for item in candidates] == [mine["id"]]
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
    candidates = build_outreach_candidates(db, None)

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
    first_guardian = make_guardian(student["id"], headers=headers)
    second_guardian = make_guardian(student["id"], headers=headers)
    make_follow_up(
        student["id"],
        guardian_id=first_guardian["id"],
        due_at="2026-09-07T09:00:00Z",
        headers=headers,
    )
    make_follow_up(
        student["id"],
        guardian_id=second_guardian["id"],
        due_at="2026-09-06T09:00:00Z",
        headers=headers,
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
    make_note(student["id"], content="Confirmed context", teacher_confirmed=True, headers=headers)
    make_note(student["id"], content="Do not share", teacher_confirmed=False, headers=headers)

    db = next(get_db())
    candidate = next(
        item
        for item in build_outreach_candidates(db, teacher["user"]["id"])
        if str(item.student_id) == student["id"]
    )

    assert set(candidate.model_dump()) == {
        "student_id",
        "student_name",
        "last_contact_result",
        "last_contact_at",
        "open_follow_up_due_at",
        "teacher_confirmed_notes",
    }
    assert candidate.last_contact_result == "Connected"
    assert candidate.last_contact_at.isoformat() == "2026-09-06T10:00:00"
    assert candidate.open_follow_up_due_at.isoformat() == "2026-09-06T09:00:00"
    assert candidate.teacher_confirmed_notes == ["Confirmed context"]


def test_outreach_plan_requires_login(anonymous_client):
    response = anonymous_client.post("/api/v1/ai/outreach-plan/generate")

    assert response.status_code == 401


def test_outreach_plan_forwards_only_authorized_candidates(
    monkeypatch, client, make_user, make_student
):
    from tests.test_auth import auth_headers

    teacher = make_user()
    other_teacher = make_user()
    headers = auth_headers(teacher["token"])
    mine = make_student(headers=headers)
    make_student(headers=auth_headers(other_teacher["token"]))
    captured = {}

    def fake_agent(candidates):
        captured["candidates"] = candidates
        return {
            "generated_at": "2026-09-06T00:00:00Z",
            "source": "agent",
            "items": [],
        }

    monkeypatch.setattr("app.api.v1.ai_briefs.invoke_outreach_agent", fake_agent)

    response = client.post("/api/v1/ai/outreach-plan/generate", headers=headers)

    assert response.status_code == 200
    assert [str(candidate.student_id) for candidate in captured["candidates"]] == [
        mine["id"]
    ]
    assert set(response.json()) == {"generated_at", "source", "items"}


def test_outreach_plan_uses_the_local_agent_without_an_external_endpoint(
    monkeypatch, client, make_user, make_student
):
    """The FastAPI server owns the local Bedrock call; no Lambda URL is required."""
    from tests.test_auth import auth_headers

    teacher = make_user()
    headers = auth_headers(teacher["token"])
    mine = make_student(headers=headers)
    captured = {}

    def fake_local_agent(candidates):
        captured["candidates"] = candidates
        return {
            "items": [
                {
                    "student_id": mine["id"],
                    "priority": "high",
                    "reason": "An open follow-up is due.",
                    "suggested_next_step": "Call today.",
                }
            ]
        }

    monkeypatch.setattr(
        "app.services.outreach_plan_client.settings",
        SimpleNamespace(bedrock_model_id="test-model"),
    )
    monkeypatch.setattr(
        "app.services.outreach_plan_client.generate_plan",
        fake_local_agent,
        raising=False,
    )

    response = client.post("/api/v1/ai/outreach-plan/generate", headers=headers)

    assert response.status_code == 200
    assert response.json()["source"] == "agent"
    assert captured["candidates"][0]["student_id"] == mine["id"]


def test_outreach_plan_rejects_agent_student_outside_authorized_candidates(
    monkeypatch, client, make_user, make_student
):
    from tests.test_auth import auth_headers

    teacher = make_user()
    headers = auth_headers(teacher["token"])
    make_student(headers=headers)

    monkeypatch.setattr(
        "app.services.outreach_plan_client.settings",
        SimpleNamespace(bedrock_model_id="test-model"),
    )
    monkeypatch.setattr(
        "app.services.outreach_plan_client.generate_plan",
        lambda _candidates: {
            "items": [
                {
                    "student_id": "99999999-9999-4999-8999-999999999999",
                    "priority": "high",
                    "reason": "Invented recommendation.",
                    "suggested_next_step": "Call today.",
                }
            ]
        },
    )

    response = client.post("/api/v1/ai/outreach-plan/generate", headers=headers)

    assert response.status_code == 503
    assert response.json()["detail"] == (
        "Outreach Agent is temporarily unavailable. Try again shortly."
    )


def test_outreach_plan_returns_empty_plan_without_invoking_agent(
    monkeypatch, client, make_user
):
    from tests.test_auth import auth_headers

    def fail_if_called(_candidates):
        raise AssertionError("agent must not be invoked without candidates")

    monkeypatch.setattr("app.api.v1.ai_briefs.invoke_outreach_agent", fail_if_called)

    response = client.post(
        "/api/v1/ai/outreach-plan/generate",
        headers=auth_headers(make_user()["token"]),
    )

    assert response.status_code == 200
    assert response.json()["source"] == "agent"
    assert response.json()["items"] == []


def test_outreach_plan_hides_upstream_failure(client, monkeypatch, make_user, make_student):
    from tests.test_auth import auth_headers

    from app.services.outreach_plan_client import OutreachAgentUnavailable

    def raise_timeout(_candidates):
        raise OutreachAgentUnavailable()

    monkeypatch.setattr("app.api.v1.ai_briefs.invoke_outreach_agent", raise_timeout)
    teacher = make_user()
    headers = auth_headers(teacher["token"])
    make_student(headers=headers)

    response = client.post(
        "/api/v1/ai/outreach-plan/generate",
        headers=headers,
    )

    assert response.status_code == 503
    assert response.json()["detail"] == (
        "Outreach Agent is temporarily unavailable. Try again shortly."
    )
