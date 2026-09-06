import uuid

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.types import GUID
from app.models.base import AuditMixin, Base


class Student(AuditMixin, Base):
    __tablename__ = "students"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    first_name: Mapped[str | None] = mapped_column(String(255))
    last_name: Mapped[str | None] = mapped_column(String(255))
    initials: Mapped[str] = mapped_column(String(16), nullable=False, default="")
    accent: Mapped[str] = mapped_column(String(32), nullable=False, default="sage")
    owner_id: Mapped[uuid.UUID | None] = mapped_column(GUID())

    guardians = relationship(
        "Guardian",
        primaryjoin="and_(Student.id == Guardian.student_id, Guardian.deleted_at.is_(None))",
        viewonly=True,
    )
