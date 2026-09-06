import uuid

from sqlalchemy.exc import IntegrityError

from app.core.exceptions import ConflictError
from app.dao.base import BaseDAO
from app.models import FollowUp

FOLLOW_UP_STATUSES = ("open", "completed", "dismissed")


class FollowUpDAO(BaseDAO):
    model = FollowUp

    def list(
        self,
        status: str | None = None,
        student_id: uuid.UUID | None = None,
    ):
        stmt = self._alive()
        if status is not None:
            stmt = stmt.where(FollowUp.status == status)
        if student_id is not None:
            stmt = stmt.where(FollowUp.student_id == student_id)
        return self.db.scalars(stmt.order_by(FollowUp.due_at)).all()

    def get_open(self, student_id, guardian_id: uuid.UUID | None):
        stmt = self._alive().where(
            FollowUp.status == "open",
            FollowUp.student_id == student_id,
        )
        if guardian_id is None:
            stmt = stmt.where(FollowUp.guardian_id.is_(None))
        else:
            stmt = stmt.where(FollowUp.guardian_id == guardian_id)
        return self.db.scalar(stmt)

    def create(self, data, actor_id: uuid.UUID | None = None):
        payload = dict(data)
        status = payload.get("status", "open")
        if status not in FOLLOW_UP_STATUSES:
            raise ValueError(f"status must be one of {FOLLOW_UP_STATUSES}")
        if status == "open":
            existing = self.get_open(payload["student_id"], payload.get("guardian_id"))
            if existing is not None:
                raise ConflictError(
                    "an open follow-up already exists for this student and guardian"
                )
        try:
            return super().create(payload, actor_id=actor_id)
        except IntegrityError as exc:
            self.db.rollback()
            if _is_unique_violation(exc):
                raise ConflictError(
                    "an open follow-up already exists for this student and guardian"
                ) from None
            raise

    def complete(
        self,
        ref,
        contact_event_id: uuid.UUID | None = None,
        actor_id: uuid.UUID | None = None,
    ):
        payload = {"status": "completed", "completed_at": self._now()}
        if contact_event_id is not None:
            payload["contact_event_id"] = contact_event_id
        return self.update(ref, payload, actor_id=actor_id)


def _is_unique_violation(exc: Exception) -> bool:
    text = str(getattr(exc, "orig", exc))
    return "UNIQUE constraint failed" in text or "follow_ups_one_open_per_parent" in text
