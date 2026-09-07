import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.core.exceptions import ConflictError
from app.dao.base import BaseDAO
from app.models import AiContactBrief, Student

AI_BRIEF_STATUSES = ("draft", "approved", "superseded")


class AiContactBriefDAO(BaseDAO):
    model = AiContactBrief

    def list(
        self,
        student_id: uuid.UUID | None = None,
        latest: bool = False,
        owner_id: uuid.UUID | None = None,
    ):
        stmt = self._alive()
        if student_id is not None:
            stmt = stmt.where(AiContactBrief.student_id == student_id)
        if owner_id is not None:
            stmt = stmt.where(
                AiContactBrief.student_id.in_(
                    select(Student.id).where(
                        Student.owner_id == owner_id, Student.deleted_at.is_(None)
                    )
                )
            )
        stmt = stmt.order_by(
            AiContactBrief.date_to.desc(),
            AiContactBrief.version.desc(),
            AiContactBrief.created_at.desc(),
        )
        if latest:
            stmt = stmt.where(AiContactBrief.status != "superseded").limit(1)
            return self.db.scalar(stmt)
        return self.db.scalars(stmt).all()

    def create(self, data, actor_id: uuid.UUID | None = None):
        payload = dict(data)
        version = payload.get("version", 1)
        if not isinstance(version, int) or isinstance(version, bool) or version < 1:
            raise ValueError("version must be a positive integer")
        status = payload.get("status", "draft")
        if status not in AI_BRIEF_STATUSES:
            raise ValueError(f"status must be one of {AI_BRIEF_STATUSES}")
        try:
            return super().create(payload, actor_id=actor_id)
        except IntegrityError as exc:
            self.db.rollback()
            text = str(getattr(exc, "orig", exc))
            if "UNIQUE constraint failed" in text or "uq_ai_contact_briefs" in text:
                raise ConflictError(
                    "an ai brief already exists for this student, date range, and version"
                ) from None
            raise

    def approve(self, ref, actor_id: uuid.UUID | None = None):
        return self.update(
            ref, {"status": "approved", "approved_at": self._now()}, actor_id=actor_id
        )

    def supersede(self, ref, actor_id: uuid.UUID | None = None):
        return self.update(ref, {"status": "superseded"}, actor_id=actor_id)
