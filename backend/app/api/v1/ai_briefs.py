import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_id, get_db
from app.core.exceptions import NotFoundError
from app.dao import AiContactBriefDAO
from app.schemas.ai_brief import AiBriefCreate, AiBriefRead, AiBriefUpdate

router = APIRouter(prefix="/ai-briefs", tags=["ai-briefs"])

ai_router = APIRouter(prefix="/ai", tags=["ai"])


@ai_router.post("/contact-brief/generate", status_code=501)
def generate_contact_brief():
    raise HTTPException(
        status_code=501, detail="AI contact brief provider is not configured."
    )


@router.get("", response_model=list[AiBriefRead] | AiBriefRead)
def list_ai_briefs(
    student_id: uuid.UUID | None = None,
    latest: bool = False,
    db: Session = Depends(get_db),
):
    dao = AiContactBriefDAO(db)
    if latest:
        brief = dao.list(student_id=student_id, latest=True)
        if brief is None:
            raise NotFoundError("ai_contact_briefs latest not found")
        return brief
    return dao.list(student_id=student_id)


@router.post("", response_model=AiBriefRead, status_code=201)
def create_ai_brief(
    payload: AiBriefCreate,
    db: Session = Depends(get_db),
    user_id: uuid.UUID | None = Depends(get_current_user_id),
):
    brief = AiContactBriefDAO(db).create(payload.model_dump(), actor_id=user_id)
    db.commit()
    return brief


@router.get("/{brief_id}", response_model=AiBriefRead)
def get_ai_brief(brief_id: uuid.UUID, db: Session = Depends(get_db)):
    return AiContactBriefDAO(db).require(brief_id)


@router.patch("/{brief_id}", response_model=AiBriefRead)
def update_ai_brief(
    brief_id: uuid.UUID,
    payload: AiBriefUpdate,
    db: Session = Depends(get_db),
    user_id: uuid.UUID | None = Depends(get_current_user_id),
):
    brief = AiContactBriefDAO(db).update(
        brief_id, payload.model_dump(exclude_unset=True), actor_id=user_id
    )
    db.commit()
    return brief


@router.delete("/{brief_id}", status_code=204)
def delete_ai_brief(
    brief_id: uuid.UUID,
    db: Session = Depends(get_db),
    user_id: uuid.UUID | None = Depends(get_current_user_id),
):
    AiContactBriefDAO(db).soft_delete(brief_id, actor_id=user_id)
    db.commit()


@router.post("/{brief_id}/approve", response_model=AiBriefRead)
def approve_ai_brief(
    brief_id: uuid.UUID,
    db: Session = Depends(get_db),
    user_id: uuid.UUID | None = Depends(get_current_user_id),
):
    brief = AiContactBriefDAO(db).approve(brief_id, actor_id=user_id)
    db.commit()
    return brief


@router.post("/{brief_id}/supersede", response_model=AiBriefRead)
def supersede_ai_brief(
    brief_id: uuid.UUID,
    db: Session = Depends(get_db),
    user_id: uuid.UUID | None = Depends(get_current_user_id),
):
    brief = AiContactBriefDAO(db).supersede(brief_id, actor_id=user_id)
    db.commit()
    return brief
