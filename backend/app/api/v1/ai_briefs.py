import asyncio
import json
import logging
import threading
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.config import settings
from app.core.exceptions import NotFoundError
from app.dao import AiContactBriefDAO
from app.models import AiContactBrief, User
from app.schemas.ai_brief import AiBriefCreate, AiBriefRead, AiBriefUpdate
from app.schemas.outreach_plan import OutreachPlanAgentOutput, OutreachPlanResponse
from app.services.agent_telemetry import configure_strands_telemetry
from app.services.outreach_plan import build_outreach_candidates
from app.services.outreach_plan_agent import build_outreach_agent
from app.services.outreach_plan_client import (
    OutreachAgentUnavailable,
    invoke_outreach_agent,
    unauthorized_students_present,
)
from app.services.contact_brief_client import (
    ContactBriefUnavailable,
    invoke_contact_brief,
)
from app.services.ownership import require_owned_resource, require_owned_student

router = APIRouter(prefix="/ai-briefs", tags=["ai-briefs"])

ai_router = APIRouter(prefix="/ai", tags=["ai"])

logger = logging.getLogger(__name__)


class ContactBriefGenerateRequest(BaseModel):
    student_id: uuid.UUID
    date_from: datetime
    date_to: datetime
    include_notes: bool = True


class ContactBriefGenerateResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    provider: str | None = None
    review_status: str | None = None
    stats: dict[str, Any] = Field(default_factory=dict)
    brief: dict[str, Any] = Field(default_factory=dict)


class CallSummaryRequest(BaseModel):
    contact_event_id: uuid.UUID


class CallSummaryResponse(BaseModel):
    note_id: uuid.UUID
    content: str
    teacher_confirmed: bool = False


@ai_router.post("/contact-brief/generate", response_model=ContactBriefGenerateResponse)
def generate_contact_brief(
    payload: ContactBriefGenerateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    require_owned_student(db, payload.student_id, user.id)
    try:
        return invoke_contact_brief(payload.model_dump(mode="json"))
    except ContactBriefUnavailable as error:
        raise HTTPException(status_code=502, detail=str(error)) from error


@ai_router.post("/outreach-plan/generate", response_model=OutreachPlanResponse)
def generate_outreach_plan(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    candidates = build_outreach_candidates(db, user.id)
    if not candidates:
        return OutreachPlanResponse(generated_at=datetime.now(timezone.utc), source="agent", items=[])
    try:
        return invoke_outreach_agent(candidates, owner_id=user.id)
    except OutreachAgentUnavailable:
        raise HTTPException(status_code=503, detail="Outreach Agent is temporarily unavailable. Try again shortly.") from None


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def _message_text(message: dict) -> str:
    parts = [
        block.get("text", "")
        for block in message.get("content", [])
        if isinstance(block, dict) and block.get("text")
    ]
    return " ".join(parts).strip()


@ai_router.post("/call-summary/generate", response_model=CallSummaryResponse)
def generate_call_summary(
    payload: CallSummaryRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Create an unconfirmed teacher-note draft summarizing a completed call."""
    from app.models import ContactEvent
    from app.services.note_drafts import (
        create_teacher_note_draft,
        draft_note_content_bounded,
    )

    event = require_owned_resource(
        db, ContactEvent, payload.contact_event_id, user.id, "contact event"
    )
    facts = {
        "result": event.result,
        "call_time": (event.call_time or event.created_at).isoformat(),
        "duration_seconds": event.duration_seconds,
        "topic": event.topic,
        "discussed_topics": list(event.discussed_topics or []),
    }
    if not settings.bedrock_model_id or not settings.aws_region:
        raise HTTPException(
            status_code=503,
            detail="Call summary Agent is temporarily unavailable. Try again shortly.",
        )
    try:
        content = draft_note_content_bounded(facts)
    except Exception:
        logger.warning("Call summary generation failed.", exc_info=True)
        raise HTTPException(
            status_code=503,
            detail="Call summary Agent is temporarily unavailable. Try again shortly.",
        ) from None
    note = create_teacher_note_draft(
        db, user, event.student_id, content, source="ai", contact_event_id=event.id
    )
    return CallSummaryResponse(
        note_id=note.id, content=note.content, teacher_confirmed=False
    )


@ai_router.post("/outreach-plan/generate/stream")
async def generate_outreach_plan_stream(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Stream outreach plan generation as server-sent events.

    Events: ``candidates`` (authorized candidate count), ``message`` (agent
    progress), ``plan`` (validated final plan) and ``error``.
    """
    candidates = build_outreach_candidates(db, user.id)
    authorized_student_ids = {str(candidate.student_id) for candidate in candidates}
    candidate_payload = [
        candidate.model_dump(mode="json") for candidate in candidates
    ]
    timeout = getattr(settings, "outreach_agent_timeout_seconds", 90.0)

    async def event_stream():
        yield _sse("candidates", {"count": len(candidates)})
        if not candidates:
            response = OutreachPlanResponse(
                generated_at=datetime.now(timezone.utc), source="agent", items=[]
            )
            yield _sse("plan", response.model_dump(mode="json"))
            return
        if not settings.bedrock_model_id:
            yield _sse(
                "error",
                {
                    "detail": "Outreach Agent is temporarily unavailable. Try again shortly."
                },
            )
            return

        configure_strands_telemetry()
        cancel_signal = threading.Event()
        agent = build_outreach_agent(candidate_payload, owner_id=user.id)
        result = None
        try:
            async with asyncio.timeout(timeout):
                async for event in agent.stream_async(
                    "Create today's outreach plan.",
                    structured_output_model=OutreachPlanAgentOutput,
                    cancel_signal=cancel_signal,
                ):
                    if "message" in event:
                        text = _message_text(event["message"])
                        if text:
                            yield _sse(
                                "message",
                                {"role": event["message"].get("role"), "text": text[:200]},
                            )
                    elif "result" in event:
                        result = event["result"]
        except TimeoutError:
            cancel_signal.set()
            logger.warning("Outreach plan streaming timed out.")
            yield _sse(
                "error",
                {
                    "detail": "Outreach Agent is temporarily unavailable. Try again shortly."
                },
            )
            return
        except Exception:
            logger.warning("Outreach plan streaming failed.", exc_info=True)
            yield _sse(
                "error",
                {
                    "detail": "Outreach Agent is temporarily unavailable. Try again shortly."
                },
            )
            return

        structured = getattr(result, "structured_output", None) if result else None
        if structured is None:
            yield _sse("error", {"detail": "The Outreach Agent returned no plan."})
            return
        items = structured.model_dump(mode="json")["items"]
        if unauthorized_students_present(items, authorized_student_ids):
            yield _sse(
                "error",
                {
                    "detail": "Outreach Agent is temporarily unavailable. Try again shortly."
                },
            )
            return
        response = OutreachPlanResponse(
            generated_at=datetime.now(timezone.utc), source="agent", items=items
        )
        yield _sse("plan", response.model_dump(mode="json"))

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.get("", response_model=list[AiBriefRead] | AiBriefRead)
def list_ai_briefs(
    student_id: uuid.UUID | None = None,
    latest: bool = False,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    dao = AiContactBriefDAO(db)
    if latest:
        brief = dao.list(student_id=student_id, latest=True, owner_id=user.id)
        if brief is None:
            raise NotFoundError("ai_contact_briefs latest not found")
        return brief
    return dao.list(student_id=student_id, owner_id=user.id)


@router.post("", response_model=AiBriefRead, status_code=201)
def create_ai_brief(
    payload: AiBriefCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    require_owned_student(db, payload.student_id, user.id)
    brief = AiContactBriefDAO(db).create(payload.model_dump(), actor_id=user.id)
    db.commit()
    return brief


@router.get("/{brief_id}", response_model=AiBriefRead)
def get_ai_brief(brief_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return require_owned_resource(db, AiContactBrief, brief_id, user.id, "ai brief")


@router.patch("/{brief_id}", response_model=AiBriefRead)
def update_ai_brief(
    brief_id: uuid.UUID,
    payload: AiBriefUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    brief = require_owned_resource(db, AiContactBrief, brief_id, user.id, "ai brief")
    brief = AiContactBriefDAO(db).update(
        brief, payload.model_dump(exclude_unset=True), actor_id=user.id
    )
    db.commit()
    return brief


@router.delete("/{brief_id}", status_code=204)
def delete_ai_brief(
    brief_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    brief = require_owned_resource(db, AiContactBrief, brief_id, user.id, "ai brief")
    AiContactBriefDAO(db).soft_delete(brief, actor_id=user.id)
    db.commit()


@router.post("/{brief_id}/approve", response_model=AiBriefRead)
def approve_ai_brief(
    brief_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    brief = require_owned_resource(db, AiContactBrief, brief_id, user.id, "ai brief")
    brief = AiContactBriefDAO(db).approve(brief, actor_id=user.id)
    db.commit()
    return brief


@router.post("/{brief_id}/supersede", response_model=AiBriefRead)
def supersede_ai_brief(
    brief_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    brief = require_owned_resource(db, AiContactBrief, brief_id, user.id, "ai brief")
    brief = AiContactBriefDAO(db).supersede(brief, actor_id=user.id)
    db.commit()
    return brief
