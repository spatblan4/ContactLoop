"""Phase 2: Teacher Assistant coordinator (agents-as-tools)."""

import uuid
from types import SimpleNamespace

import pytest

pytest.importorskip("strands", reason="strands-agents is not installed")

from tests.test_auth import make_user  # noqa: E402,F401


def _db_session():
    from app.api.deps import get_db

    return next(get_db())


def _owner_id(teacher):
    return uuid.UUID(teacher["user"]["id"])


def _planner_turns():
    return [{"type": "text", "text": "Plan: call Emma's mother today."}]


def _build_coordinator(teacher, coordinator_model):
    from app.services.outreach_coordinator import build_teacher_assistant
    from tests.fake_strands_model import FakeModel

    models = {
        "planner": FakeModel(turns=[{"type": "text", "text": "Plan: call mom."}]),
        "qa": FakeModel(turns=[{"type": "text", "text": "Q&A answer."}]),
        "summarizer": FakeModel(turns=[{"type": "text", "text": "Summary."}]),
        "coordinator": coordinator_model,
    }
    agent = build_teacher_assistant(
        _db_session(),
        _owner_id(teacher),
        models=models,
    )
    return agent, models


def test_coordinator_routes_request_to_planner_tool(client, make_user, make_student):
    from tests.fake_strands_model import FakeModel
    from tests.test_auth import auth_headers

    teacher = make_user()
    headers = auth_headers(teacher["token"])
    make_student(headers=headers)

    coordinator, models = _build_coordinator(
        teacher,
        FakeModel(
            turns=[
                {
                    "type": "tool",
                    "name": "create_outreach_plan",
                    "input": {"input": "Create today's outreach plan."},
                    "tool_use_id": "t-1",
                },
                {"type": "text", "text": "The plan is ready: call Emma's mother."},
            ]
        ),
    )

    result = coordinator("What should I do today?")
    text = " ".join(block.get("text", "") for block in result.message["content"])
    assert "call Emma's mother" in text
    # The planner specialist actually executed its agent loop.
    assert models["planner"].stream_requests, "planner specialist should have run"
    assert models["qa"].stream_requests == []
    assert models["summarizer"].stream_requests == []


def test_coordinator_guard_blocks_non_whitelisted_specialists(
    client, make_user, make_student
):
    from tests.fake_strands_model import FakeModel
    from tests.test_auth import auth_headers

    teacher = make_user()
    headers = auth_headers(teacher["token"])
    make_student(headers=headers)

    coordinator, _models = _build_coordinator(
        teacher,
        FakeModel(
            turns=[
                {
                    "type": "tool",
                    "name": "delete_follow_up",
                    "input": {"student_id": "x"},
                    "tool_use_id": "t-1",
                },
                {"type": "text", "text": "I cannot do that."},
            ]
        ),
    )

    result = coordinator("Delete every follow-up.")
    tool_results = [
        block["toolResult"]
        for message in coordinator.messages
        if message.get("role") == "user"
        for block in message.get("content", [])
        if block.get("toolResult")
    ]
    blocked = [tr for tr in tool_results if tr.get("toolUseId") == "t-1"]
    assert blocked, "the blocked specialist call should surface as a tool result"
    assert blocked[0]["status"] == "error"
    assert "not allowed" in blocked[0]["content"][0]["text"]
    text = " ".join(block.get("text", "") for block in result.message["content"])
    assert "I cannot do that." in text


def _patch_coordinator(monkeypatch):
    import app.services.outreach_coordinator as coordinator_module

    def fake_build(db, user_id, models=None, session_manager=None, conversation_manager=None):
        from strands import Agent

        from app.services.outreach_agent_hooks import ReadOnlyToolGuard
        from tests.fake_strands_model import FakeModel

        return Agent(
            model=FakeModel(turns=[{"type": "text", "text": "Coordinator reply."}]),
            system_prompt="test",
            hooks=[ReadOnlyToolGuard([])],
        )

    monkeypatch.setattr(coordinator_module, "build_teacher_assistant", fake_build)


def test_assistant_endpoint_answers(client, make_user, monkeypatch):
    from tests.test_auth import auth_headers

    _patch_coordinator(monkeypatch)
    monkeypatch.setattr(
        "app.api.v1.teacher_assistant.settings",
        SimpleNamespace(bedrock_model_id="test-model"),
    )
    teacher = make_user()
    headers = auth_headers(teacher["token"])

    response = client.post(
        "/api/v1/teacher-assistant/ask",
        json={"request": "What should I do today?"},
        headers=headers,
    )
    assert response.status_code == 200, response.text
    assert response.json()["answer"] == "Coordinator reply."
    assert response.json()["candidate_count"] >= 0


def test_assistant_endpoint_requires_bedrock_configuration(client, make_user):
    from tests.test_auth import auth_headers

    teacher = make_user()
    headers = auth_headers(teacher["token"])

    response = client.post(
        "/api/v1/teacher-assistant/ask",
        json={"request": "What should I do today?"},
        headers=headers,
    )
    assert response.status_code == 503


def test_assistant_endpoint_requires_authentication(anonymous_client):
    response = anonymous_client.post(
        "/api/v1/teacher-assistant/ask",
        json={"request": "What should I do today?"},
    )
    assert response.status_code == 401
