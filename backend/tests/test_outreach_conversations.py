"""Phase 1: multi-turn outreach QA with persisted Strands sessions."""

from types import SimpleNamespace

import pytest

pytest.importorskip("strands", reason="strands-agents is not installed")

from app.services.outreach_plan_agent import build_outreach_qa_agent  # noqa: E402
from tests.fake_strands_model import FakeModel  # noqa: E402
from tests.test_auth import make_user  # noqa: E402


def _patch_qa_agent(monkeypatch, answers):
    """Patch the QA service to run the real agent loop on a FakeModel."""
    import app.services.outreach_qa as qa_module

    state = {"fakes": [], "answers": list(answers)}

    def fake_build(tools, model=None, owner_id=None, session_manager=None, conversation_manager=None):
        fake = FakeModel(
            turns=[{"type": "text", "text": state["answers"].pop(0)}]
        )
        state["fakes"].append(fake)
        return build_outreach_qa_agent(
            tools,
            model=fake,
            owner_id=owner_id,
            session_manager=session_manager,
            conversation_manager=conversation_manager,
        )

    monkeypatch.setattr(qa_module, "build_outreach_qa_agent", fake_build)
    return state


def _enable_bedrock(monkeypatch):
    monkeypatch.setattr(
        "app.api.v1.outreach_conversations.settings",
        SimpleNamespace(bedrock_model_id="test-model"),
    )


def test_ask_persists_and_restores_conversation(
    client, make_user, make_student, monkeypatch
):
    from tests.test_auth import auth_headers

    state = _patch_qa_agent(monkeypatch, ["Because a follow-up is due.", "Call first."])
    _enable_bedrock(monkeypatch)
    teacher = make_user()
    headers = auth_headers(teacher["token"])
    make_student(headers=headers)

    first = client.post(
        "/api/v1/outreach-plan/ask",
        json={"question": "Why is Emma high priority?"},
        headers=headers,
    )
    assert first.status_code == 200, first.text
    assert first.json()["answer"] == "Because a follow-up is due."

    listing = client.get("/api/v1/outreach-plan/conversation", headers=headers)
    assert listing.status_code == 200
    messages = listing.json()["messages"]
    assert [m["role"] for m in messages] == ["user", "assistant"]
    assert messages[0]["text"] == "Why is Emma high priority?"
    assert messages[1]["text"] == "Because a follow-up is due."

    second = client.post(
        "/api/v1/outreach-plan/ask",
        json={"question": "And what should I do first?"},
        headers=headers,
    )
    assert second.status_code == 200, second.text
    assert second.json()["answer"] == "Call first."

    # The second agent run restored the first Q&A before the new question.
    restored = state["fakes"][1].stream_requests[0]["messages"]
    assert [m["role"] for m in restored] == ["user", "assistant", "user"]
    assert restored[0]["content"][0]["text"] == "Why is Emma high priority?"


def test_conversations_are_isolated_between_teachers(
    client, make_user, make_student, monkeypatch, second_auth
):
    _patch_qa_agent(monkeypatch, ["Answer A."])
    _enable_bedrock(monkeypatch)
    teacher = make_user()
    headers = auth_headers = None
    from tests.test_auth import auth_headers as _ah

    headers = _ah(teacher["token"])
    make_student(headers=headers)

    response = client.post(
        "/api/v1/outreach-plan/ask",
        json={"question": "Who is priority today?"},
        headers=headers,
    )
    assert response.status_code == 200

    # The other teacher sees an empty conversation, not teacher A's.
    other = client.get(
        "/api/v1/outreach-plan/conversation", headers=second_auth["headers"]
    )
    assert other.status_code == 200
    assert other.json()["messages"] == []


def test_reset_conversation_clears_history(
    client, make_user, make_student, monkeypatch
):
    _patch_qa_agent(monkeypatch, ["Answer A."])
    _enable_bedrock(monkeypatch)
    from tests.test_auth import auth_headers

    teacher = make_user()
    headers = auth_headers(teacher["token"])
    make_student(headers=headers)

    assert (
        client.post(
            "/api/v1/outreach-plan/ask",
            json={"question": "Any priorities?"},
            headers=headers,
        ).status_code
        == 200
    )

    deleted = client.delete("/api/v1/outreach-plan/conversation", headers=headers)
    assert deleted.status_code == 204

    listing = client.get("/api/v1/outreach-plan/conversation", headers=headers)
    assert listing.status_code == 200
    assert listing.json()["messages"] == []


def test_ask_requires_bedrock_configuration(client, make_user):
    from tests.test_auth import auth_headers

    teacher = make_user()
    headers = auth_headers(teacher["token"])

    response = client.post(
        "/api/v1/outreach-plan/ask",
        json={"question": "Any priorities?"},
        headers=headers,
    )

    assert response.status_code == 503


def test_ask_requires_authentication(anonymous_client):
    response = anonymous_client.post(
        "/api/v1/outreach-plan/ask",
        json={"question": "Any priorities?"},
    )
    assert response.status_code == 401
