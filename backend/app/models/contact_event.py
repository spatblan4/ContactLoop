import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.types import GUID
from app.models.base import AuditMixin, Base, utc_now


class ContactEvent(AuditMixin, Base):
    __tablename__ = "contact_events"

    student_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("students.id"), nullable=False
    )
    guardian_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), ForeignKey("guardians.id"))
    call_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, server_default=func.now(), nullable=False
    )
    duration_seconds: Mapped[int | None] = mapped_column(Integer)
    result: Mapped[str] = mapped_column(String(16), nullable=False)
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False)
    topic: Mapped[str | None] = mapped_column(Text)
    planned_topic: Mapped[str | None] = mapped_column(Text)
    discussed_topics: Mapped[list[str]] = mapped_column(
        JSON().with_variant(ARRAY(Text), "postgresql"), nullable=False, default=list
    )
    teacher_note: Mapped[str | None] = mapped_column(Text)
    follow_up_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(),
        ForeignKey("follow_ups.id", use_alter=True, name="fk_contact_events_follow_up_id"),
    )
    provider: Mapped[str | None] = mapped_column(String(64))
    provider_call_id: Mapped[str | None] = mapped_column(String(255))
    provider_status: Mapped[str | None] = mapped_column(String(64))
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    student = relationship("Student")
    guardian = relationship("Guardian")
    follow_up = relationship(
        "FollowUp", foreign_keys="ContactEvent.follow_up_id", uselist=False
    )
