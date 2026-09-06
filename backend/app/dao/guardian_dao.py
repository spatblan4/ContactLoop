import uuid

from app.dao.base import BaseDAO
from app.models import Guardian


class GuardianDAO(BaseDAO):
    model = Guardian

    def list(self, student_id: uuid.UUID | None = None):
        stmt = self._alive()
        if student_id is not None:
            stmt = stmt.where(Guardian.student_id == student_id)
        return self.db.scalars(stmt.order_by(Guardian.name)).all()
