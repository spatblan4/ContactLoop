"""Multi-turn outreach conversation endpoints (Phase 1)."""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.config import settings
from app.models import AgentSessionMessage, User
from app.services.agent_session_repository import SqlAgentSessionRepository
from app.services.outreach_qa import ask_outreach_question, qa_session_id

router = APIRouter(prefix="/outreach-plan", tags=["outreach-plan"])


class OutreachQuestionRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)


class OutreachAnswerResponse(BaseModel):
    answer: str
    candidate_count: int


class ConversationMessage(BaseModel):
    message_id: int
    role: str
    text: str


class ConversationResponse(BaseModel):
    session_id: str
    messages: list[ConversationMessage]


def _outreach_unavailable() -> HTTPException:
    return HTTPException(
        status_code=503,
        detail="Outreach Agent is temporarily unavailable. Try again shortly.",
    )


@router.post("/ask", response_model=OutreachAnswerResponse)
def ask_outreach_plan(
    payload: OutreachQuestionRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not settings.bedrock_model_id:
        raise _outreach_unavailable()
    try:
        result = ask_outreach_question(db, user.id, payload.question.strip())
    except TimeoutError:
        raise _outreach_unavailable() from None
    except Exception:
        raise _outreach_unavailable() from None
    return result


@router.get("/conversation", response_model=ConversationResponse)
def get_outreach_conversation(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    session_id = qa_session_id(user.id)
    messages = []
    for row in db.scalars(
        select(AgentSessionMessage)
        .where(AgentSessionMessage.session_id == session_id)
        .order_by(AgentSessionMessage.message_id.asc())
    ):
        text = " ".join(
            block.get("text", "")
            for block in (row.message or {}).get("content", [])
            if isinstance(block, dict)
        ).strip()
        messages.append(
            ConversationMessage(
                message_id=row.message_id,
                role=(row.message or {}).get("role", "unknown"),
                text=text,
            )
        )
    return ConversationResponse(session_id=session_id, messages=messages)


@router.delete("/conversation", status_code=204)
def reset_outreach_conversation(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    repository = SqlAgentSessionRepository(db, user.id)
    repository.soft_delete_session(qa_session_id(user.id))
    return None
