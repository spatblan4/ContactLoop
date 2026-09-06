import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.types import GUID
from app.models.base import AuditMixin, Base, utc_now


class AiContactBrief(AuditMixin, Base):
    __tablename__ = "ai_contact_briefs"
    __table_args__ = (
        UniqueConstraint(
            "student_id",
            "date_from",
            "date_to",
            "version",
            name="uq_ai_contact_briefs_student_range_version",
        ),
    )

    student_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("students.id"), nullable=False
    )
    date_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    date_to: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="draft")
    key_topics: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    parent_concerns: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    recorded_resolutions: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    open_items: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    suggested_next_step: Mapped[str | None] = mapped_column(Text)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, server_default=func.now(), nullable=False
    )
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    student = relationship("Student")
