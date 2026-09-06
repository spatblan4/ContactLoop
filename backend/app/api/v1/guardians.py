import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_id, get_db
from app.dao import GuardianDAO
from app.schemas.guardian import GuardianCreate, GuardianRead, GuardianUpdate

router = APIRouter(prefix="/guardians", tags=["guardians"])


@router.get("", response_model=list[GuardianRead])
def list_guardians(
    student_id: uuid.UUID | None = None,
    db: Session = Depends(get_db),
):
    return GuardianDAO(db).list(student_id=student_id)


@router.post("", response_model=GuardianRead, status_code=201)
def create_guardian(
    payload: GuardianCreate,
    db: Session = Depends(get_db),
    user_id: uuid.UUID | None = Depends(get_current_user_id),
):
    guardian = GuardianDAO(db).create(payload.model_dump(), actor_id=user_id)
    db.commit()
    return guardian


@router.get("/{guardian_id}", response_model=GuardianRead)
def get_guardian(guardian_id: uuid.UUID, db: Session = Depends(get_db)):
    return GuardianDAO(db).require(guardian_id)


@router.patch("/{guardian_id}", response_model=GuardianRead)
def update_guardian(
    guardian_id: uuid.UUID,
    payload: GuardianUpdate,
    db: Session = Depends(get_db),
    user_id: uuid.UUID | None = Depends(get_current_user_id),
):
    guardian = GuardianDAO(db).update(
        guardian_id, payload.model_dump(exclude_unset=True), actor_id=user_id
    )
    db.commit()
    return guardian


@router.delete("/{guardian_id}", status_code=204)
def delete_guardian(
    guardian_id: uuid.UUID,
    db: Session = Depends(get_db),
    user_id: uuid.UUID | None = Depends(get_current_user_id),
):
    GuardianDAO(db).soft_delete(guardian_id, actor_id=user_id)
    db.commit()
