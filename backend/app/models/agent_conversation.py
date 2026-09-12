import uuid

from sqlalchemy import ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.types import GUID, JSONType
from app.models.base import AuditMixin, Base


class AgentSession(AuditMixin, Base):
    """A persisted Strands conversation, scoped to one teacher."""

    __tablename__ = "agent_sessions"

    session_id: Mapped[str] = mapped_column(
        String(128), unique=True, index=True, nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    kind: Mapped[str] = mapped_column(String(32), nullable=False)


class AgentSessionAgent(AuditMixin, Base):
    """Persisted per-agent state inside a session (state, conversation manager)."""

    __tablename__ = "agent_session_agents"
    __table_args__ = (
        UniqueConstraint("session_id", "agent_id", name="uq_agent_session_agent"),
    )

    session_id: Mapped[str] = mapped_column(
        String(128),
        ForeignKey("agent_sessions.session_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    agent_id: Mapped[str] = mapped_column(String(128), nullable=False)
    state: Mapped[dict] = mapped_column(JSONType, nullable=False, default=dict)
    conversation_manager_state: Mapped[dict] = mapped_column(
        JSONType, nullable=False, default=dict
    )
    internal_state: Mapped[dict] = mapped_column(JSONType, nullable=False, default=dict)


class AgentSessionMessage(AuditMixin, Base):
    """One persisted conversation message inside a session agent."""

    __tablename__ = "agent_session_messages"
    __table_args__ = (
        UniqueConstraint(
            "session_id", "agent_id", "message_id", name="uq_agent_session_message"
        ),
    )

    session_id: Mapped[str] = mapped_column(
        String(128),
        ForeignKey("agent_sessions.session_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    agent_id: Mapped[str] = mapped_column(String(128), nullable=False)
    message_id: Mapped[int] = mapped_column(Integer, nullable=False)
    message: Mapped[dict] = mapped_column(JSONType, nullable=False)
    redact_message: Mapped[dict | None] = mapped_column(JSONType)

    def preview(self) -> str:
        for block in self.message.get("content", []):
            if "text" in block:
                return block["text"][:120]
        return ""
