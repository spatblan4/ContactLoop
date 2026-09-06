import uuid

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.types import GUID
from app.models.base import AuditMixin, Base


class TeacherNote(AuditMixin, Base):
    __tablename__ = "teacher_notes"

    student_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("students.id"), nullable=False
    )
    contact_event_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("contact_events.id")
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str] = mapped_column(String(16), nullable=False, default="typed")
    teacher_confirmed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    student = relationship("Student")
    contact_event = relationship("ContactEvent", uselist=False)
