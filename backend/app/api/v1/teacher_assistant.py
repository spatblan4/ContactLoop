"""Teacher Assistant coordinator endpoint (Phase 2 agents-as-tools)."""

import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.config import settings
from app.models import User
from app.services.outreach_coordinator import ask_teacher_assistant

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/teacher-assistant", tags=["teacher-assistant"])


class AssistantRequest(BaseModel):
    request: str = Field(min_length=1, max_length=2000)


class AssistantResponse(BaseModel):
    answer: str
    candidate_count: int


def _assistant_unavailable() -> HTTPException:
    return HTTPException(
        status_code=503,
        detail="Teacher Assistant is temporarily unavailable. Try again shortly.",
    )


@router.post("/ask", response_model=AssistantResponse)
def ask_assistant(
    payload: AssistantRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not settings.bedrock_model_id:
        raise _assistant_unavailable()
    try:
        return ask_teacher_assistant(db, user.id, payload.request.strip())
    except Exception:
        logger.warning("Teacher Assistant request failed.", exc_info=True)
        raise _assistant_unavailable() from None
