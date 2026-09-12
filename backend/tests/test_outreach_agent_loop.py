"""Tests that drive the real Strands agent loop with a scripted fake model.

These verify the Phase 0 safety and observability pieces end-to-end:
the read-only tool guard blocks non-whitelisted tools inside the event loop,
whitelisted tools run, and structured output is delivered through the
SDK's structured-output tool.
"""

import pytest

pytest.importorskip("strands", reason="strands-agents is not installed")

from pydantic import BaseModel  # noqa: E402

from app.services.outreach_agent_hooks import ReadOnlyToolGuard  # noqa: E402
from tests.fake_strands_model import FakeModel  # noqa: E402

STUDENT_ID = "11111111-1111-4111-8111-111111111111"


class StructuredPlanOutput(BaseModel):
    items: list[dict]

CANDIDATES = [
    {
        "student_id": STUDENT_ID,
        "student_name": "Emma Johnson",
        "last_contact_result": "No Answer",
        "last_contact_at": "2026-09-06T08:00:00",
        "open_follow_up_due_at": "2026-09-07T09:00:00",
        "teacher_confirmed_notes": [],
    }
]

PLANNED_ITEMS = [
    {
        "student_id": STUDENT_ID,
        "priority": "high",
        "reason": "An open follow-up is due.",
        "suggested_next_step": "Call today.",
    }
]


def _build_agent(fake_model):
    from strands import Agent, tool

    executed = {"allowed": 0, "forbidden": 0}

    @tool
    def get_outreach_candidates() -> list[dict]:
        """Get the teacher-authorized candidate facts for today's outreach plan."""
        executed["allowed"] += 1
        return CANDIDATES

    @tool
    def write_follow_up(student_id: str, due_at: str) -> str:
        """Create a follow-up for a student (must never run in this agent)."""
        executed["forbidden"] += 1
        return "written"

    agent = Agent(
        model=fake_model,
        tools=[get_outreach_candidates, write_follow_up],
        system_prompt="You prioritize parent outreach.",
        hooks=[ReadOnlyToolGuard(["get_outreach_candidates", "StructuredPlanOutput"])],
    )
    return agent, executed


def _structured_turn():
    return {
        "type": "tool",
        "name": "StructuredPlanOutput",
        "input": {"items": PLANNED_ITEMS},
        "tool_use_id": "t-final",
    }


def test_agent_loop_runs_whitelisted_tool_and_returns_structured_output():
    fake_model = FakeModel(
        turns=[
            {"type": "tool", "name": "get_outreach_candidates", "tool_use_id": "t-1"},
            _structured_turn(),
        ]
    )
    agent, executed = _build_agent(fake_model)

    result = agent(
        "Create today's outreach plan.",
        structured_output_model=StructuredPlanOutput,
    )

    assert executed == {"allowed": 1, "forbidden": 0}
    tool_names = {spec["name"] for spec in fake_model.stream_requests[0]["tool_specs"]}
    assert "get_outreach_candidates" in tool_names
    assert result.structured_output is not None
    assert result.structured_output.items[0]["student_id"] == STUDENT_ID


def test_agent_loop_blocks_non_whitelisted_tool_before_execution():
    fake_model = FakeModel(
        turns=[
            {
                "type": "tool",
                "name": "write_follow_up",
                "input": {"student_id": STUDENT_ID, "due_at": "2026-09-13T09:00:00Z"},
                "tool_use_id": "t-1",
            },
            _structured_turn(),
        ]
    )
    agent, executed = _build_agent(fake_model)

    result = agent(
        "Create today's outreach plan.",
        structured_output_model=StructuredPlanOutput,
    )

    # The forbidden tool never ran, and the loop saw an error tool result.
    assert executed == {"allowed": 0, "forbidden": 0}
    tool_results = [
        block
        for message in agent.messages
        if message.get("role") == "user"
        for block in message.get("content", [])
        if block.get("toolResult")
    ]
    blocked = [
        block
        for block in tool_results
        if block["toolResult"].get("toolUseId") == "t-1"
    ]
    assert blocked, "the blocked tool call should surface as a tool result"
    assert blocked[0]["toolResult"]["status"] == "error"
    assert "not allowed" in blocked[0]["toolResult"]["content"][0]["text"]
    # The agent still produced its structured plan after the blocked attempt.
    assert result.structured_output is not None


def test_production_agent_wiring_allows_structured_output_tool():
    from app.schemas.outreach_plan import OutreachPlanAgentOutput
    from app.services.outreach_plan_agent import build_outreach_agent

    fake_model = FakeModel(
        turns=[
            {"type": "tool", "name": "get_outreach_candidates", "tool_use_id": "t-1"},
            {
                "type": "tool",
                "name": "OutreachPlanAgentOutput",
                "input": {"items": PLANNED_ITEMS},
                "tool_use_id": "t-final",
            },
        ]
    )
    agent = build_outreach_agent(CANDIDATES, model=fake_model, owner_id="teacher-1")

    result = agent(
        "Create today's outreach plan.",
        structured_output_model=OutreachPlanAgentOutput,
    )

    # The production whitelist must include the SDK's structured-output tool,
    # otherwise the guard would block the agent's own final answer.
    assert result.structured_output is not None
    assert str(result.structured_output.items[0].student_id) == STUDENT_ID
    tool_names = {spec["name"] for spec in fake_model.stream_requests[0]["tool_specs"]}
    assert "get_outreach_candidates" in tool_names


def test_read_only_guard_allows_only_explicit_whitelist():
    guard = ReadOnlyToolGuard(["get_outreach_candidates", "OutreachPlanAgentOutput"])

    assert guard.allowed_tools == frozenset(
        ["get_outreach_candidates", "OutreachPlanAgentOutput"]
    )

    class _Event:
        tool_use = {"name": "get_outreach_candidates"}
        cancel_tool = None

    event = _Event()
    guard._before_tool_call(event)
    assert event.cancel_tool is None

    class _BlockedEvent:
        tool_use = {"name": "delete_student"}
        cancel_tool = None

    blocked = _BlockedEvent()
    guard._before_tool_call(blocked)
    assert "not allowed" in blocked.cancel_tool
