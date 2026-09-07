import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.dao import GuardianDAO
from app.models import Guardian, User
from app.schemas.guardian import GuardianCreate, GuardianRead, GuardianUpdate
from app.services.ownership import require_owned_resource, require_owned_student

router = APIRouter(prefix="/guardians", tags=["guardians"])


@router.get("", response_model=list[GuardianRead])
def list_guardians(
    student_id: uuid.UUID | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return GuardianDAO(db).list(student_id=student_id, owner_id=user.id)


@router.post("", response_model=GuardianRead, status_code=201)
def create_guardian(
    payload: GuardianCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    require_owned_student(db, payload.student_id, user.id)
    guardian = GuardianDAO(db).create(payload.model_dump(), actor_id=user.id)
    db.commit()
    return guardian


@router.get("/{guardian_id}", response_model=GuardianRead)
def get_guardian(guardian_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return require_owned_resource(db, Guardian, guardian_id, user.id, "guardian")


@router.patch("/{guardian_id}", response_model=GuardianRead)
def update_guardian(
    guardian_id: uuid.UUID,
    payload: GuardianUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    guardian = require_owned_resource(db, Guardian, guardian_id, user.id, "guardian")
    guardian = GuardianDAO(db).update(
        guardian, payload.model_dump(exclude_unset=True), actor_id=user.id
    )
    db.commit()
    return guardian


@router.delete("/{guardian_id}", status_code=204)
def delete_guardian(
    guardian_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    guardian = require_owned_resource(db, Guardian, guardian_id, user.id, "guardian")
    GuardianDAO(db).soft_delete(guardian, actor_id=user.id)
    db.commit()
