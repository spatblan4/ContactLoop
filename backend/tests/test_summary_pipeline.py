"""Phase 2: draft -> judge -> finalize quality pipeline (Strands Graph)."""

import pytest

pytest.importorskip("strands", reason="strands-agents is not installed")

from tests.fake_strands_model import FakeModel  # noqa: E402
from tests.test_auth import make_user  # noqa: E402,F401


def _draft_agent(turns):
    from app.services.note_drafts import build_note_draft_agent

    return build_note_draft_agent(model=FakeModel(turns=turns))


def _review_agent(turns):
    from strands import Agent

    from app.services.outreach_agent_hooks import ReadOnlyToolGuard

    return Agent(
        model=FakeModel(turns=turns),
        system_prompt="review",
        hooks=[ReadOnlyToolGuard([])],
    )


def _run(draft_turns, judge_turns, final_turns=None, max_executions=6):
    from app.services.summary_pipeline import run_summary_quality_pipeline

    final_turns = final_turns or [{"type": "text", "text": "Final note."}]
    draft = _draft_agent(list(draft_turns))
    judge = _review_agent(list(judge_turns))
    final = _review_agent(list(final_turns))
    return run_summary_quality_pipeline(
        "Draft a note from facts",
        draft_agent=draft,
        judge_agent=judge,
        final_agent=final,
        max_node_executions=max_executions,
    )


def test_judge_verdict_parses_approve_and_revise():
    from app.services.summary_pipeline import judge_verdict

    assert judge_verdict("APPROVED") == (True, "")
    assert judge_verdict("  APPROVED  ") == (True, "")
    approved, _ = judge_verdict("REVISE: make it shorter")
    assert approved is False
    assert judge_verdict("make it shorter")[0] is False
    assert judge_verdict("")[0] is False


def test_pipeline_approves_on_first_pass():
    result = _run(
        draft_turns=[{"type": "text", "text": "Called mom, no answer."}],
        judge_turns=[{"type": "text", "text": "APPROVED"}],
    )
    assert result == "Final note."


def test_pipeline_revises_draft_before_finalizing():
    result = _run(
        draft_turns=[
            {"type": "text", "text": "Verbose draft."},
            {"type": "text", "text": "Tighter draft."},
        ],
        judge_turns=[
            {"type": "text", "text": "REVISE: make it shorter"},
            {"type": "text", "text": "APPROVED"},
        ],
    )
    assert result == "Final note."


def test_pipeline_fails_closed_when_judge_never_approves():
    with pytest.raises(RuntimeError):
        _run(
            draft_turns=[{"type": "text", "text": "Draft."}] * 3,
            judge_turns=[{"type": "text", "text": "REVISE: again"}] * 3,
            max_executions=6,
        )


def test_pipeline_fails_closed_on_unclear_judge_reply():
    with pytest.raises(RuntimeError):
        _run(
            draft_turns=[{"type": "text", "text": "Draft."}] * 2,
            judge_turns=[{"type": "text", "text": "looks fine to me"}] * 2,
            max_executions=4,
        )


def test_draft_note_content_bounded_times_out_and_cancels(monkeypatch):
    import time
    from types import SimpleNamespace

    import app.services.note_drafts as note_drafts_module

    observed = {}

    def slow_draft(_facts, cancel_signal=None):
        observed["cancel_signal"] = cancel_signal
        for _ in range(50):
            time.sleep(0.05)
            if cancel_signal is not None and cancel_signal.is_set():
                observed["cancelled"] = True
                return "late draft"

    monkeypatch.setattr(
        note_drafts_module,
        "settings",
        SimpleNamespace(outreach_agent_timeout_seconds=0.05),
    )
    monkeypatch.setattr(
        note_drafts_module, "draft_note_content", slow_draft, raising=False
    )

    with pytest.raises(TimeoutError):
        note_drafts_module.draft_note_content_bounded({"result": "Connected"})

    # The cancel signal must be set so the underlying agent call can abort.
    assert observed.get("cancel_signal") is not None
    for _ in range(60):
        if observed.get("cancelled"):
            break
        time.sleep(0.05)
    assert observed.get("cancelled") is True


def test_call_summary_endpoint_uses_pipeline_when_enabled(
    client, make_user, make_student, make_event, monkeypatch
):
    from types import SimpleNamespace

    import app.services.note_drafts as note_drafts_module
    from tests.test_auth import auth_headers

    monkeypatch.setattr(
        note_drafts_module,
        "settings",
        SimpleNamespace(
            bedrock_model_id="test-model",
            aws_region="us-east-2",
            bedrock_temperature=0.1,
            call_summary_quality_pipeline=True,
        ),
    )
    monkeypatch.setattr(
        "app.api.v1.ai_briefs.settings",
        SimpleNamespace(bedrock_model_id="test-model", aws_region="us-east-2"),
    )

    calls = {}

    def fake_pipeline(facts):
        calls["facts"] = facts
        return "Pipelined summary."

    monkeypatch.setattr(note_drafts_module, "_run_quality_pipeline", fake_pipeline)

    teacher = make_user()
    headers = auth_headers(teacher["token"])
    student = make_student(headers=headers)
    event = make_event(student["id"], headers=headers, result="Connected")

    response = client.post(
        "/api/v1/ai/call-summary/generate",
        json={"contact_event_id": event["id"]},
        headers=headers,
    )
    assert response.status_code == 200, response.text
    assert response.json()["content"] == "Pipelined summary."
    assert response.json()["teacher_confirmed"] is False
    assert calls["facts"]["result"] == "Connected"


def test_call_summary_endpoint_fails_closed_when_pipeline_fails(
    client, make_user, make_student, make_event, monkeypatch
):
    from types import SimpleNamespace

    import app.services.note_drafts as note_drafts_module
    from tests.test_auth import auth_headers

    monkeypatch.setattr(
        note_drafts_module,
        "settings",
        SimpleNamespace(
            bedrock_model_id="test-model",
            aws_region="us-east-2",
            bedrock_temperature=0.1,
            call_summary_quality_pipeline=True,
        ),
    )
    monkeypatch.setattr(
        "app.api.v1.ai_briefs.settings",
        SimpleNamespace(bedrock_model_id="test-model", aws_region="us-east-2"),
    )

    def failing_pipeline(facts):
        raise RuntimeError("no final note")

    monkeypatch.setattr(note_drafts_module, "_run_quality_pipeline", failing_pipeline)

    teacher = make_user()
    headers = auth_headers(teacher["token"])
    student = make_student(headers=headers)
    event = make_event(student["id"], headers=headers, result="Connected")

    response = client.post(
        "/api/v1/ai/call-summary/generate",
        json={"contact_event_id": event["id"]},
        headers=headers,
    )
    assert response.status_code == 503
