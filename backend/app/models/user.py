import uuid

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.types import GUID
from app.models.base import AuditMixin, Base


class User(AuditMixin, Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False, index=True)
    name: Mapped[str | None] = mapped_column(String(255))
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)

    auth_tokens = relationship(
        "AuthToken",
        primaryjoin="and_(User.id == AuthToken.user_id, AuthToken.deleted_at.is_(None))",
        viewonly=True,
    )
