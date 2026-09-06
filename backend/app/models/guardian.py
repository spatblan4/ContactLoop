import uuid

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.types import GUID
from app.models.base import AuditMixin, Base


class Guardian(AuditMixin, Base):
    __tablename__ = "guardians"

    student_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("students.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    relation: Mapped[str] = mapped_column(String(64), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(64))
    email: Mapped[str | None] = mapped_column(String(255))
    preferred_contact_method: Mapped[str | None] = mapped_column(String(32))

    student = relationship("Student")
