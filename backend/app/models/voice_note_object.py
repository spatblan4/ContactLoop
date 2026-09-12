import uuid

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.types import GUID
from app.models.base import AuditMixin, Base


class VoiceNoteObject(AuditMixin, Base):
    """Server-side record binding an upload object key to its owner and student."""

    __tablename__ = "voice_note_objects"

    object_key: Mapped[str] = mapped_column(
        String(64), unique=True, index=True, nullable=False
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
