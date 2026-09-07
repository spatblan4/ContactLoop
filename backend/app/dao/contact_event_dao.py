import uuid
from datetime import datetime, timedelta
from typing import Any, Mapping

from sqlalchemy import func, select

from app.dao.base import BaseDAO
from app.dao.follow_up_dao import FollowUpDAO
from app.models import ContactEvent, Student

CONNECTED = "Connected"
UNSUCCESSFUL_RESULTS = ("No Answer", "Busy", "Failed")
CONTACT_EVENT_RESULTS = (CONNECTED,) + UNSUCCESSFUL_RESULTS


class ContactEventDAO(BaseDAO):
    model = ContactEvent

    def list(
        self,
        student_id: uuid.UUID | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        result: str | None = None,
        owner_id: uuid.UUID | None = None,
    ):
        stmt = self._alive()
        if student_id is not None:
            stmt = stmt.where(ContactEvent.student_id == student_id)
        if owner_id is not None:
            stmt = stmt.where(
                ContactEvent.student_id.in_(
                    select(Student.id).where(
                        Student.owner_id == owner_id, Student.deleted_at.is_(None)
                    )
                )
            )
        if date_from is not None:
            stmt = stmt.where(ContactEvent.call_time >= date_from)
        if date_to is not None:
            stmt = stmt.where(ContactEvent.call_time <= date_to)
        if result is not None:
            stmt = stmt.where(ContactEvent.result == result)
        return self.db.scalars(stmt.order_by(ContactEvent.call_time)).all()

    def _next_attempt_number(self, student_id, guardian_id: uuid.UUID | None) -> int:
        stmt = (
            select(func.count())
            .select_from(ContactEvent)
            .where(
                ContactEvent.deleted_at.is_(None),
                ContactEvent.student_id == student_id,
            )
        )
        if guardian_id is None:
            stmt = stmt.where(ContactEvent.guardian_id.is_(None))
        else:
            stmt = stmt.where(ContactEvent.guardian_id == guardian_id)
        return (self.db.scalar(stmt) or 0) + 1

    def create(
        self,
        data: Mapping[str, Any],
        actor_id: uuid.UUID | None = None,
        follow_up_due_at: datetime | None = None,
    ):
        payload = dict(data)
        if payload.get("result") not in CONTACT_EVENT_RESULTS:
            raise ValueError(f"result must be one of {CONTACT_EVENT_RESULTS}")
        payload.pop("attempt_number", None)
        payload["attempt_number"] = self._next_attempt_number(
            payload["student_id"], payload.get("guardian_id")
        )
        payload.setdefault("discussed_topics", [])
        event = super().create(payload, actor_id=actor_id)
        self._sync_follow_up(event, actor_id=actor_id, follow_up_due_at=follow_up_due_at)
        return event

    def update(
        self,
        ref,
        data: Mapping[str, Any],
        actor_id: uuid.UUID | None = None,
        follow_up_due_at: datetime | None = None,
    ):
        payload = dict(data)
        if "result" in payload and payload["result"] not in CONTACT_EVENT_RESULTS:
            raise ValueError(f"result must be one of {CONTACT_EVENT_RESULTS}")
        payload.pop("attempt_number", None)
        event = super().update(ref, payload, actor_id=actor_id)
        if any(key in payload for key in ("result", "ended_at", "follow_up_id")):
            self._sync_follow_up(event, actor_id=actor_id, follow_up_due_at=follow_up_due_at)
        return event

    def _sync_follow_up(
        self,
        event,
        actor_id: uuid.UUID | None = None,
        follow_up_due_at: datetime | None = None,
    ):
        """Replicates the old Postgres sync_follow_up_for_contact_event trigger."""
        if event.ended_at is None or event.result not in CONTACT_EVENT_RESULTS:
            return
        follow_ups = FollowUpDAO(self.db)
        target = follow_ups.get(event.follow_up_id) if event.follow_up_id else None
        if target is None or target.status != "open":
            target = follow_ups.get_open(event.student_id, event.guardian_id)
        if event.result == CONNECTED:
            if target is not None:
                follow_ups.complete(target, contact_event_id=event.id, actor_id=actor_id)
            return
        due_at = follow_up_due_at or (event.ended_at + timedelta(days=1))
        if target is not None:
            follow_ups.update(
                target,
                {"due_at": due_at, "contact_event_id": event.id},
                actor_id=actor_id,
            )
        else:
            follow_ups.create(
                {
                    "student_id": event.student_id,
                    "guardian_id": event.guardian_id,
                    "due_at": due_at,
                    "status": "open",
                    "contact_event_id": event.id,
                },
                actor_id=actor_id,
            )
