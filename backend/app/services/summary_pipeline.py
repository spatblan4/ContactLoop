"""Draft -> judge -> finalize quality pipeline for agent note drafts (Phase 2).

A Strands Graph runs the draft agent, an LLM-as-judge self-review, and a
finalizer in a directed cycle: the judge either approves the draft (edge to
``final``) or asks for a revision (edge back to ``draft``). A node-execution
cap bounds the cycle, and any outcome without a finalized note fails closed.
"""

import logging
from typing import Any

from app.core.config import settings

logger = logging.getLogger(__name__)

DRAFT_NODE = "draft"
JUDGE_NODE = "judge"
FINAL_NODE = "final"

APPROVED = "APPROVED"
REVISE_PREFIX = "REVISE:"

JUDGE_PROMPT = """You review a drafted teacher note for safety and accuracy.
Check that the draft uses only the supplied facts, contains no phone numbers
or personal contact data, and never invents student facts.
Reply with exactly "APPROVED" when the draft is safe to keep, otherwise reply
with "REVISE: " followed by one short instruction."""

FINAL_PROMPT = """You produce the final teacher note from a reviewed draft.
Apply the reviewer's instruction when one is present and change nothing else.
Use only the supplied content and never include phone numbers or personal
contact data."""

DEFAULT_MAX_NODE_EXECUTIONS = 6


def judge_verdict(text: str) -> tuple[bool, str]:
    """Parse the judge's reply into (approved, feedback)."""
    stripped = (text or "").strip()
    if stripped.startswith(APPROVED):
        return True, ""
    feedback = stripped
    if feedback.startswith(REVISE_PREFIX):
        feedback = feedback[len(REVISE_PREFIX):].strip()
    return False, feedback


def node_text(state: Any, node_id: str) -> str:
    node_result = (getattr(state, "results", None) or {}).get(node_id)
    if node_result is None:
        return ""
    message = getattr(node_result.result, "message", None) or {}
    return " ".join(
        block.get("text", "")
        for block in message.get("content", [])
        if isinstance(block, dict)
    ).strip()


def _judge_approved(state: Any) -> bool:
    return judge_verdict(node_text(state, JUDGE_NODE))[0]


def _judge_needs_revision(state: Any) -> bool:
    return not _judge_approved(state)


def build_summary_quality_graph(
    draft_agent: Any,
    judge_agent: Any,
    final_agent: Any,
    max_node_executions: int = DEFAULT_MAX_NODE_EXECUTIONS,
) -> Any:
    """Wire the draft/judge/final agents into a conditional Strands Graph."""
    from strands.multiagent.graph import GraphBuilder

    builder = GraphBuilder()
    builder.add_node(draft_agent, DRAFT_NODE)
    builder.add_node(judge_agent, JUDGE_NODE)
    builder.add_node(final_agent, FINAL_NODE)
    builder.set_entry_point(DRAFT_NODE)
    builder.add_edge(DRAFT_NODE, JUDGE_NODE)
    builder.add_edge(JUDGE_NODE, FINAL_NODE, condition=_judge_approved)
    builder.add_edge(JUDGE_NODE, DRAFT_NODE, condition=_judge_needs_revision)
    builder.set_max_node_executions(max_node_executions)
    return builder.build()


def run_summary_quality_pipeline(
    task: str,
    draft_agent: Any,
    judge_agent: Any,
    final_agent: Any,
    max_node_executions: int = DEFAULT_MAX_NODE_EXECUTIONS,
) -> str:
    """Run the graph and return the finalized note text (fail-closed).

    Raises RuntimeError when the pipeline produces no finalized note (judge
    never approved, execution cap reached, or graph failure).
    """
    graph = build_summary_quality_graph(
        draft_agent, judge_agent, final_agent, max_node_executions=max_node_executions
    )
    result = graph(task)
    status = str(getattr(getattr(result, "status", None), "value", None) or "")
    final_text = node_text(graph.state, FINAL_NODE)
    if status.lower() != "completed" or not final_text:
        logger.warning(
            "Summary quality pipeline finished with status=%s final=%r",
            status or "unknown",
            bool(final_text),
        )
        raise RuntimeError("The summary quality pipeline produced no final note.")
    return final_text
