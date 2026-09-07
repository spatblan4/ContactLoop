import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_id, get_db
from app.dao import GuardianDAO, StudentDAO
from app.schemas.student import StudentCreate, StudentRead, StudentUpdate

router = APIRouter(prefix="/students", tags=["students"])


@router.get("", response_model=list[StudentRead])
def list_students(
    search: str | None = Query(default=None),
    db: Session = Depends(get_db),
    user_id: uuid.UUID | None = Depends(get_current_user_id),
):
    return StudentDAO(db).list(search=search, owner_id=user_id)


@router.post("", response_model=StudentRead, status_code=201)
def create_student(
    payload: StudentCreate,
    db: Session = Depends(get_db),
    user_id: uuid.UUID | None = Depends(get_current_user_id),
):
    dao = StudentDAO(db)
    data = {
        key: value
        for key, value in payload.model_dump(exclude={"guardians"}).items()
        if value is not None
    }
    if user_id is not None:
        data["owner_id"] = user_id
    student = dao.create(data, actor_id=user_id)
    guardian_dao = GuardianDAO(db)
    for guardian in payload.guardians:
        guardian_dao.create(
            {**guardian.model_dump(exclude_none=True), "student_id": student.id},
            actor_id=user_id,
        )
    db.commit()
    return dao.get(student.id)


@router.get("/{student_id}", response_model=StudentRead)
def get_student(student_id: uuid.UUID, db: Session = Depends(get_db)):
    return StudentDAO(db).require(student_id)


@router.patch("/{student_id}", response_model=StudentRead)
def update_student(
    student_id: uuid.UUID,
    payload: StudentUpdate,
    db: Session = Depends(get_db),
    user_id: uuid.UUID | None = Depends(get_current_user_id),
):
    student = StudentDAO(db).update(
        student_id, payload.model_dump(exclude_unset=True), actor_id=user_id
    )
    db.commit()
    return student


@router.delete("/{student_id}", status_code=204)
def delete_student(
    student_id: uuid.UUID,
    db: Session = Depends(get_db),
    user_id: uuid.UUID | None = Depends(get_current_user_id),
):
    StudentDAO(db).soft_delete(student_id, actor_id=user_id)
    db.commit()
