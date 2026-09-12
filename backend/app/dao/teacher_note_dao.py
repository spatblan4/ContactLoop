import uuid

from sqlalchemy import select

from app.dao.base import BaseDAO
from app.models import Student, TeacherNote

TEACHER_NOTE_SOURCES = ("typed", "voice", "ai")


class TeacherNoteDAO(BaseDAO):
    model = TeacherNote

    def list(
        self,
        student_id: uuid.UUID | None = None,
        owner_id: uuid.UUID | None = None,
    ):
        stmt = self._alive()
        if student_id is not None:
            stmt = stmt.where(TeacherNote.student_id == student_id)
        if owner_id is not None:
            stmt = stmt.where(
                TeacherNote.student_id.in_(
                    select(Student.id).where(
                        Student.owner_id == owner_id, Student.deleted_at.is_(None)
                    )
                )
            )
        return self.db.scalars(stmt.order_by(TeacherNote.created_at)).all()

    def create(self, data, actor_id: uuid.UUID | None = None):
        payload = dict(data)
        content = payload.get("content")
        if not isinstance(content, str) or not content.strip():
            raise ValueError("teacher note content must be a non-empty string")
        source = payload.get("source", "typed")
        if source not in TEACHER_NOTE_SOURCES:
            raise ValueError(f"source must be one of {TEACHER_NOTE_SOURCES}")
        return super().create(payload, actor_id=actor_id)
