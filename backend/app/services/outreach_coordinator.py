"""Agents-as-Tools coordinator: the Teacher Assistant (Phase 2).

A coordinator agent combines the outreach planner, the multi-turn QA agent
and the call-note summarizer as Strands agents-as-tools. The teacher's request
is routed to exactly one specialist; every specialist keeps its own read-only
tool guard and owner scoping, so delegation never widens the safety boundary.
"""

import logging
from typing import Any

from sqlalchemy.orm import Session as DbSession

from app.core.config import settings

logger = logging.getLogger(__name__)

COORDINATOR_PROMPT = """You are the Teacher Assistant coordinator for ContactLoop.
Route the teacher's request to exactly one specialist tool:
- create_outreach_plan: prioritize today's outreach from authorized candidate facts
- answer_outreach_questions: answer questions about the teacher's students
- draft_call_summary: draft an unconfirmed note summarizing a completed call
Use only information returned by the tools. Never invent student facts and never
include phone numbers or personal contact data. Keep answers concise."""

PLANNER_TOOL_NAME = "create_outreach_plan"
QA_TOOL_NAME = "answer_outreach_questions"
SUMMARY_TOOL_NAME = "draft_call_summary"

DEFAULT_AGENT_TIMEOUT_SECONDS = 90.0


def assistant_session_id(user_id: Any) -> str:
    return f"teacher-assistant-{user_id}"


def _build_bedrock_model() -> "Any":
    from app.services.outreach_plan_agent import _build_bedrock_model

    return _build_bedrock_model()


def build_teacher_assistant(
    db: DbSession,
    user_id: Any,
    models: dict[str, Any] | None = None,
    session_manager: Any = None,
    conversation_manager: Any = None,
    candidates: list[Any] | None = None,
) -> Any:
    """Construct the Teacher Assistant coordinator agent.

    ``models`` maps specialist names (planner / qa / summarizer / coordinator)
    to model instances and exists so tests can drive the real agent loop with
    scripted fake models. ``candidates`` lets a caller that already built the
    outreach candidates reuse them instead of re-querying.
    """
    from strands import Agent

    from app.services.note_drafts import build_note_draft_agent
    from app.services.outreach_agent_hooks import ReadOnlyToolGuard
    from app.services.outreach_plan import build_outreach_candidates
    from app.services.outreach_plan_agent import (
        build_outreach_agent,
        build_outreach_qa_agent,
    )
    from app.services.outreach_tools import build_outreach_tools

    models = models or {}
    if candidates is None:
        candidates = build_outreach_candidates(db, user_id)
    candidate_payload = [
        candidate.model_dump(mode="json") for candidate in candidates
    ]

    planner = build_outreach_agent(
        candidate_payload, model=models.get("planner"), owner_id=user_id
    )
    qa_tools = build_outreach_tools(db, user_id, candidate_payload)
    qa = build_outreach_qa_agent(
        [tool for tool, _name in qa_tools],
        model=models.get("qa"),
        owner_id=user_id,
    )
    summarizer = build_note_draft_agent(model=models.get("summarizer"))

    tools = [
        planner.as_tool(
            name=PLANNER_TOOL_NAME,
            description=(
                "Create today's outreach plan from the authorized candidate facts."
            ),
        ),
        qa.as_tool(
            name=QA_TOOL_NAME,
            description=(
                "Answer the teacher's question about their students using "
                "read-only tools."
            ),
        ),
        summarizer.as_tool(
            name=SUMMARY_TOOL_NAME,
            description=(
                "Draft an unconfirmed teacher note summarizing a completed call "
                "from its facts."
            ),
        ),
    ]

    agent_kwargs: dict[str, Any] = {
        "agent_id": "teacher-assistant",
        "model": models.get("coordinator")
        if models.get("coordinator") is not None
        else _build_bedrock_model(),
        "tools": tools,
        "system_prompt": COORDINATOR_PROMPT,
        "hooks": [ReadOnlyToolGuard([tool.tool_name for tool in tools])],
        "trace_attributes": {
            "contactloop.agent": "teacher_assistant",
            "contactloop.owner_id": str(user_id),
        },
    }
    if session_manager is not None:
        agent_kwargs["session_manager"] = session_manager
    if conversation_manager is not None:
        agent_kwargs["conversation_manager"] = conversation_manager
    return Agent(**agent_kwargs)


def ask_teacher_assistant(
    db: DbSession,
    user_id: Any,
    request: str,
    models: dict[str, Any] | None = None,
) -> dict:
    """Route a teacher's request through the Teacher Assistant coordinator.

    The coordinator conversation persists per teacher in the agent_sessions
    tables, mirroring the outreach QA flow.
    """
    from strands.agent.conversation_manager import SummarizingConversationManager
    from strands.session import RepositorySessionManager

    from app.services.agent_session_repository import SqlAgentSessionRepository
    from app.services.outreach_plan import build_outreach_candidates
    from app.services.outreach_qa import _run_qa_agent

    repository = SqlAgentSessionRepository(db, user_id)
    session_manager = RepositorySessionManager(
        session_id=assistant_session_id(user_id), session_repository=repository
    )
    candidates = build_outreach_candidates(db, user_id)
    agent = build_teacher_assistant(
        db,
        user_id,
        models=models,
        session_manager=session_manager,
        conversation_manager=SummarizingConversationManager(
            preserve_recent_messages=10
        ),
        candidates=candidates,
    )
    answer = _run_qa_agent(agent, request)
    return {"answer": answer, "candidate_count": len(candidates)}
