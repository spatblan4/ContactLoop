import uuid

from sqlalchemy import and_, or_, select

from app.dao.base import BaseDAO
from app.models import AiContactBrief, ContactEvent, FollowUp, Guardian, Student, TeacherNote


class StudentDAO(BaseDAO):
    model = Student

    def list(self, search: str | None = None, owner_id: uuid.UUID | None = None):
        stmt = self._alive()
        if owner_id is not None:
            stmt = stmt.where(Student.owner_id == owner_id)
        if search:
            pattern = f"%{search.strip()}%"
            stmt = (
                stmt.outerjoin(
                    Guardian,
                    and_(Guardian.student_id == Student.id, Guardian.deleted_at.is_(None)),
                )
                .where(
                    or_(
                        Student.name.ilike(pattern),
                        Student.first_name.ilike(pattern),
                        Student.last_name.ilike(pattern),
                        Student.initials.ilike(pattern),
                        Guardian.name.ilike(pattern),
                        Guardian.phone.ilike(pattern),
                    )
                )
                .distinct()
            )
        return self.db.scalars(stmt.order_by(Student.name)).all()

    def get_with_guardians(self, student_id):
        return self.get(student_id)

    def soft_delete(self, ref, actor_id: uuid.UUID | None = None):
        student = self._resolve(ref)
        now = self._now()
        for model in (Guardian, ContactEvent, FollowUp, TeacherNote, AiContactBrief):
            rows = self.db.scalars(
                select(model).where(
                    model.student_id == student.id, model.deleted_at.is_(None)
                )
            ).all()
            for row in rows:
                row.deleted_at = now
                self._stamp(row, actor_id=actor_id)
        student.deleted_at = now
        self._stamp(student, actor_id=actor_id)
        self.db.flush()
        return student
