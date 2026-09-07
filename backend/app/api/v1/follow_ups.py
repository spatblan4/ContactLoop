import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.dao import FollowUpDAO
from app.models import FollowUp, User
from app.schemas.follow_up import FollowUpCreate, FollowUpRead, FollowUpUpdate
from app.services.ownership import require_owned_resource, require_owned_student

router = APIRouter(prefix="/follow-ups", tags=["follow-ups"])


@router.get("", response_model=list[FollowUpRead])
def list_follow_ups(
    status: str | None = None,
    student_id: uuid.UUID | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return FollowUpDAO(db).list(status=status, student_id=student_id, owner_id=user.id)


@router.post("", response_model=FollowUpRead, status_code=201)
def create_follow_up(
    payload: FollowUpCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    require_owned_student(db, payload.student_id, user.id)
    follow_up = FollowUpDAO(db).create(payload.model_dump(), actor_id=user.id)
    db.commit()
    return follow_up


@router.get("/{follow_up_id}", response_model=FollowUpRead)
def get_follow_up(follow_up_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return require_owned_resource(db, FollowUp, follow_up_id, user.id, "follow-up")


@router.patch("/{follow_up_id}", response_model=FollowUpRead)
def update_follow_up(
    follow_up_id: uuid.UUID,
    payload: FollowUpUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    follow_up = require_owned_resource(db, FollowUp, follow_up_id, user.id, "follow-up")
    data = payload.model_dump(exclude_unset=True)
    if data.get("status") == "completed":
        if follow_up is not None and follow_up.completed_at is None:
            data["completed_at"] = datetime.now(timezone.utc)
    follow_up = FollowUpDAO(db).update(follow_up, data, actor_id=user.id)
    db.commit()
    return follow_up


@router.delete("/{follow_up_id}", status_code=204)
def delete_follow_up(
    follow_up_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    follow_up = require_owned_resource(db, FollowUp, follow_up_id, user.id, "follow-up")
    FollowUpDAO(db).soft_delete(follow_up, actor_id=user.id)
    db.commit()
