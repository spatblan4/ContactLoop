import uuid

from app.dao.base import BaseDAO
from app.models import TeacherNote

TEACHER_NOTE_SOURCES = ("typed", "voice")


class TeacherNoteDAO(BaseDAO):
    model = TeacherNote

    def list(self, student_id: uuid.UUID | None = None):
        stmt = self._alive()
        if student_id is not None:
            stmt = stmt.where(TeacherNote.student_id == student_id)
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
