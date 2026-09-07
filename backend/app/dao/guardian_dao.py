import uuid

from sqlalchemy import select

from app.dao.base import BaseDAO
from app.models import Guardian, Student


class GuardianDAO(BaseDAO):
    model = Guardian

    def list(
        self,
        student_id: uuid.UUID | None = None,
        owner_id: uuid.UUID | None = None,
    ):
        stmt = self._alive()
        if student_id is not None:
            stmt = stmt.where(Guardian.student_id == student_id)
        if owner_id is not None:
            stmt = stmt.where(
                Guardian.student_id.in_(
                    select(Student.id).where(
                        Student.owner_id == owner_id, Student.deleted_at.is_(None)
                    )
                )
            )
        return self.db.scalars(stmt.order_by(Guardian.name)).all()
