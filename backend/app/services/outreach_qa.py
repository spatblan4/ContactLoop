"""Multi-turn outreach QA service backed by persisted Strands sessions."""

import concurrent.futures
import logging
import threading
from typing import Any

from sqlalchemy.orm import Session as DbSession

from app.core.config import (
    DEFAULT_AGENT_PRESERVE_RECENT_MESSAGES,
    DEFAULT_AGENT_TIMEOUT_SECONDS,
    settings,
)
from app.services.agent_session_repository import SqlAgentSessionRepository
from app.services.outreach_mcp import ReadonlyMcpTools
from app.services.outreach_plan import build_outreach_candidates
from app.services.outreach_plan_agent import build_outreach_qa_agent

logger = logging.getLogger(__name__)

QA_AGENT_ID = "outreach-qa"


def qa_session_id(user_id: Any) -> str:
    return f"outreach-qa-{user_id}"


def _run_qa_agent(agent: Any, question: str) -> str:
    timeout = getattr(
        settings, "outreach_agent_timeout_seconds", DEFAULT_AGENT_TIMEOUT_SECONDS
    )
    cancel_signal = threading.Event()
    pool = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    try:
        future = pool.submit(agent, question, cancel_signal=cancel_signal)
        try:
            result = future.result(timeout=timeout)
            return _answer_text(result)
        except TimeoutError:
            cancel_signal.set()
            logger.warning("Outreach QA agent timed out after %s seconds.", timeout)
            raise
    finally:
        pool.shutdown(wait=False, cancel_futures=True)


def _answer_text(result: Any) -> str:
    message = getattr(result, "message", None) or {}
    parts = [
        block.get("text", "")
        for block in message.get("content", [])
        if isinstance(block, dict) and block.get("text")
    ]
    return "\n".join(part for part in parts if part).strip()


def ask_outreach_question(
    db: DbSession,
    user_id: Any,
    question: str,
    model: Any = None,
) -> dict:
    """Answer a teacher's question about the outreach plan with the QA agent.

    The conversation persists per teacher in the agent_sessions tables; the
    agent restores its history through the Strands session manager. When an
    MCP server is configured, its allowlisted read-only tools are attached
    for the duration of the question.
    """
    from strands.session import RepositorySessionManager

    candidates = build_outreach_candidates(db, user_id)
    from app.services.outreach_tools import build_outreach_tools

    with ReadonlyMcpTools() as mcp:
        tools = build_outreach_tools(
            db, user_id, [candidate.model_dump(mode="json") for candidate in candidates]
        ) + [(tool, tool.tool_name) for tool in mcp.tools]
        repository = SqlAgentSessionRepository(db, user_id)
        session_manager = RepositorySessionManager(
            session_id=qa_session_id(user_id), session_repository=repository
        )

        from strands.agent.conversation_manager import (
            SummarizingConversationManager,
        )

        agent = build_outreach_qa_agent(
            [tool for tool, _name in tools],
            model=model,
            owner_id=user_id,
            session_manager=session_manager,
            conversation_manager=SummarizingConversationManager(
                preserve_recent_messages=getattr(
                    settings,
                    "agent_preserve_recent_messages",
                    DEFAULT_AGENT_PRESERVE_RECENT_MESSAGES,
                )
            ),
        )
        answer = _run_qa_agent(agent, question)
    return {"answer": answer, "candidate_count": len(candidates)}
