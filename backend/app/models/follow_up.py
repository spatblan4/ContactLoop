import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.types import GUID
from app.models.base import AuditMixin, Base


class FollowUp(AuditMixin, Base):
    __tablename__ = "follow_ups"
    __table_args__ = (
        Index(
            "follow_ups_one_open_per_parent",
            "student_id",
            "guardian_id",
            unique=True,
            sqlite_where=text("status = 'open' AND deleted_at IS NULL"),
            postgresql_where=text("status = 'open' AND deleted_at IS NULL"),
        ),
    )

    student_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("students.id"), nullable=False
    )
    guardian_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), ForeignKey("guardians.id"))
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="open")
    contact_event_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("contact_events.id")
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    student = relationship("Student")
    guardian = relationship("Guardian")
    contact_event = relationship(
        "ContactEvent", foreign_keys="FollowUp.contact_event_id", uselist=False
    )
