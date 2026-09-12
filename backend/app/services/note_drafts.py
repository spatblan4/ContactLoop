"""Agent-drafted teacher notes (Phase 2).

Both the voice-note pipeline and the call-summary flow produce DRAFTS only:
``teacher_confirmed`` stays false until a teacher approves the note in the UI.
"""

import logging
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field
from sqlalchemy.orm import Session as DbSession

from app.core.config import settings
from app.dao import TeacherNoteDAO
from app.models import User

logger = logging.getLogger(__name__)


class TeacherNoteDraft(BaseModel):
    content: str = Field(min_length=1, max_length=8000)


DRAFT_PROMPT = """You draft concise teacher notes from call and voice facts.
Use only the supplied facts. Never invent details and never include phone
numbers or personal contact data. This draft is teacher-reviewed only."""

# Strands names the structured-output tool after the model class.
STRUCTURED_DRAFT_TOOL_NAME = TeacherNoteDraft.__name__


def _build_bedrock_model() -> "Any":
    from strands.models import BedrockModel

    config: dict[str, Any] = {
        "model_id": settings.bedrock_model_id,
        "temperature": settings.bedrock_temperature,
    }
    return BedrockModel(region_name=settings.aws_region, **config)


def draft_note_content(facts: dict, cancel_signal: Any = None) -> str:
    """Generate a draft note from minimized facts.

    Raises RuntimeError when the agent is unavailable; callers decide on a
    fallback (e.g. the raw transcript).
    """
    if not settings.bedrock_model_id or not settings.aws_region:
        raise RuntimeError("Bedrock model is not configured.")

    from strands import Agent

    from app.services.outreach_agent_hooks import ReadOnlyToolGuard

    agent = Agent(
        model=_build_bedrock_model(),
        system_prompt=DRAFT_PROMPT,
        hooks=[ReadOnlyToolGuard([STRUCTURED_DRAFT_TOOL_NAME])],
    )
    invoke_kwargs: dict[str, Any] = {"structured_output_model": TeacherNoteDraft}
    if cancel_signal is not None:
        invoke_kwargs["cancel_signal"] = cancel_signal
    result = agent(facts, **invoke_kwargs)
    structured = getattr(result, "structured_output", None)
    if structured is None:
        raise RuntimeError("The agent returned no draft.")
    return TeacherNoteDraft.model_validate(structured).content


def create_teacher_note_draft(
    db: DbSession,
    user: User,
    student_id: Any,
    content: str,
    source: str = "typed",
    contact_event_id: Any = None,
) -> Any:
    from app.services.ownership import require_owned_student

    require_owned_student(db, student_id, user.id)
    note = TeacherNoteDAO(db).create(
        {
            "student_id": student_id,
            "contact_event_id": contact_event_id,
            "content": content,
            "source": source,
            "teacher_confirmed": False,
        },
        actor_id=user.id,
    )
    db.commit()
    logger.info("Created teacher note draft for student %s.", student_id)
    return note
