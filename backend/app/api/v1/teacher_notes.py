import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.dao import TeacherNoteDAO
from app.models import TeacherNote, User
from app.schemas.teacher_note import (
    TeacherNoteCreate,
    TeacherNoteRead,
    TeacherNoteUpdate,
)
from app.services.ownership import require_owned_resource, require_owned_student

router = APIRouter(prefix="/teacher-notes", tags=["teacher-notes"])


@router.get("", response_model=list[TeacherNoteRead])
def list_teacher_notes(
    student_id: uuid.UUID | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return TeacherNoteDAO(db).list(student_id=student_id, owner_id=user.id)


@router.post("", response_model=TeacherNoteRead, status_code=201)
def create_teacher_note(
    payload: TeacherNoteCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    require_owned_student(db, payload.student_id, user.id)
    note = TeacherNoteDAO(db).create(payload.model_dump(), actor_id=user.id)
    db.commit()
    return note


@router.get("/{note_id}", response_model=TeacherNoteRead)
def get_teacher_note(note_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return require_owned_resource(db, TeacherNote, note_id, user.id, "teacher note")


@router.patch("/{note_id}", response_model=TeacherNoteRead)
def update_teacher_note(
    note_id: uuid.UUID,
    payload: TeacherNoteUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    note = require_owned_resource(db, TeacherNote, note_id, user.id, "teacher note")
    note = TeacherNoteDAO(db).update(
        note, payload.model_dump(exclude_unset=True), actor_id=user.id
    )
    db.commit()
    return note


@router.delete("/{note_id}", status_code=204)
def delete_teacher_note(
    note_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    note = require_owned_resource(db, TeacherNote, note_id, user.id, "teacher note")
    TeacherNoteDAO(db).soft_delete(note, actor_id=user.id)
    db.commit()
