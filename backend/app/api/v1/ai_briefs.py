import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.exceptions import NotFoundError
from app.dao import AiContactBriefDAO
from app.models import AiContactBrief, User
from app.schemas.ai_brief import AiBriefCreate, AiBriefRead, AiBriefUpdate
from app.schemas.outreach_plan import OutreachPlanResponse
from app.services.outreach_plan import build_outreach_candidates
from app.services.outreach_plan_client import OutreachAgentUnavailable, invoke_outreach_agent
from app.services.contact_brief_client import (
    ContactBriefUnavailable,
    invoke_contact_brief,
)
from app.services.ownership import require_owned_resource, require_owned_student

router = APIRouter(prefix="/ai-briefs", tags=["ai-briefs"])

ai_router = APIRouter(prefix="/ai", tags=["ai"])


class ContactBriefGenerateRequest(BaseModel):
    student_id: uuid.UUID
    date_from: datetime
    date_to: datetime
    include_notes: bool = True


@ai_router.post("/contact-brief/generate")
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
    candidates = build_outreach_candidates(db, user.id, datetime.now(timezone.utc))
    if not candidates:
        return OutreachPlanResponse(generated_at=datetime.now(timezone.utc), source="agent", items=[])
    try:
        return invoke_outreach_agent(candidates)
    except OutreachAgentUnavailable:
        raise HTTPException(status_code=503, detail="Outreach Agent is temporarily unavailable. Try again shortly.") from None


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
