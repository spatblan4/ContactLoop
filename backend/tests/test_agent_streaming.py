"""Phase 1 SSE streaming tests."""

from types import SimpleNamespace

import pytest

from tests.test_auth import make_user  # noqa: E402

pytest.importorskip("strands", reason="strands-agents is not installed")


def _parse_sse(body: str) -> list[tuple[str, dict]]:
    import json

    events = []
    for block in body.strip().split("\n\n"):
        lines = block.strip().split("\n")
        if not lines or not lines[0].startswith("event: "):
            continue
        event = lines[0][len("event: "):]
        data = json.loads(lines[1][len("data: "):]) if len(lines) > 1 else {}
        events.append((event, data))
    return events


def test_outreach_plan_generate_stream_emits_plan(
    client, make_user, make_student, monkeypatch
):
    from tests.test_auth import auth_headers

    teacher = make_user()
    headers = auth_headers(teacher["token"])
    mine = make_student(headers=headers)
    student_id = str(__import__("uuid").UUID(mine["id"]))

    def fake_build(candidates, model=None, owner_id=None, cancel_signal=None):
        from app.services.outreach_plan_agent import build_outreach_agent
        from tests.fake_strands_model import FakeModel

        return build_outreach_agent(
            candidates,
            model=FakeModel(
                turns=[
                    {
                        "type": "tool",
                        "name": "get_outreach_candidates",
                        "tool_use_id": "t-1",
                    },
                    {
                        "type": "tool",
                        "name": "OutreachPlanAgentOutput",
                        "input": {
                            "items": [
                                {
                                    "student_id": student_id,
                                    "priority": "high",
                                    "reason": "Follow-up due.",
                                    "suggested_next_step": "Call today.",
                                }
                            ]
                        },
                        "tool_use_id": "t-2",
                    },
                ]
            ),
            owner_id=owner_id,
        )

    monkeypatch.setattr(
        "app.api.v1.ai_briefs.settings",
        SimpleNamespace(bedrock_model_id="test-model", aws_region="us-east-2"),
    )
    monkeypatch.setattr("app.api.v1.ai_briefs.build_outreach_agent", fake_build)

    response = client.post(
        "/api/v1/ai/outreach-plan/generate/stream", headers=headers
    )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")

    events = _parse_sse(response.text)
    names = [name for name, _data in events]
    assert "candidates" in names
    assert "plan" in names
    plan = dict(events)["plan"]
    assert plan["source"] == "agent"
    assert [item["student_id"] for item in plan["items"]] == [student_id]


def test_outreach_plan_generate_stream_rejects_unauthorized_student(
    client, make_user, make_student, monkeypatch
):
    from tests.test_auth import auth_headers

    teacher = make_user()
    headers = auth_headers(teacher["token"])
    make_student(headers=headers)

    def fake_build(candidates, model=None, owner_id=None, cancel_signal=None):
        from app.services.outreach_plan_agent import build_outreach_agent
        from tests.fake_strands_model import FakeModel

        return build_outreach_agent(
            candidates,
            model=FakeModel(
                turns=[
                    {
                        "type": "tool",
                        "name": "OutreachPlanAgentOutput",
                        "input": {
                            "items": [
                                {
                                    "student_id": "99999999-9999-4999-8999-999999999999",
                                    "priority": "low",
                                    "reason": "Unknown.",
                                    "suggested_next_step": "Nothing.",
                                }
                            ]
                        },
                        "tool_use_id": "t-1",
                    },
                ]
            ),
            owner_id=owner_id,
        )

    monkeypatch.setattr(
        "app.api.v1.ai_briefs.settings",
        SimpleNamespace(bedrock_model_id="test-model", aws_region="us-east-2"),
    )
    monkeypatch.setattr("app.api.v1.ai_briefs.build_outreach_agent", fake_build)

    response = client.post(
        "/api/v1/ai/outreach-plan/generate/stream", headers=headers
    )
    assert response.status_code == 200
    events = _parse_sse(response.text)
    names = [name for name, _data in events]
    assert "plan" not in names
    assert "error" in names
