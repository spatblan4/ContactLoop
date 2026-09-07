import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_id, get_db
from app.dao import TeacherNoteDAO
from app.schemas.teacher_note import (
    TeacherNoteCreate,
    TeacherNoteRead,
    TeacherNoteUpdate,
)

router = APIRouter(prefix="/teacher-notes", tags=["teacher-notes"])


@router.get("", response_model=list[TeacherNoteRead])
def list_teacher_notes(
    student_id: uuid.UUID | None = None,
    db: Session = Depends(get_db),
    user_id: uuid.UUID | None = Depends(get_current_user_id),
):
    return TeacherNoteDAO(db).list(student_id=student_id, owner_id=user_id)


@router.post("", response_model=TeacherNoteRead, status_code=201)
def create_teacher_note(
    payload: TeacherNoteCreate,
    db: Session = Depends(get_db),
    user_id: uuid.UUID | None = Depends(get_current_user_id),
):
    note = TeacherNoteDAO(db).create(payload.model_dump(), actor_id=user_id)
    db.commit()
    return note


@router.get("/{note_id}", response_model=TeacherNoteRead)
def get_teacher_note(note_id: uuid.UUID, db: Session = Depends(get_db)):
    return TeacherNoteDAO(db).require(note_id)


@router.patch("/{note_id}", response_model=TeacherNoteRead)
def update_teacher_note(
    note_id: uuid.UUID,
    payload: TeacherNoteUpdate,
    db: Session = Depends(get_db),
    user_id: uuid.UUID | None = Depends(get_current_user_id),
):
    note = TeacherNoteDAO(db).update(
        note_id, payload.model_dump(exclude_unset=True), actor_id=user_id
    )
    db.commit()
    return note


@router.delete("/{note_id}", status_code=204)
def delete_teacher_note(
    note_id: uuid.UUID,
    db: Session = Depends(get_db),
    user_id: uuid.UUID | None = Depends(get_current_user_id),
):
    TeacherNoteDAO(db).soft_delete(note_id, actor_id=user_id)
    db.commit()
