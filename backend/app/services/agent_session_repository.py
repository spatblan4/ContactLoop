"""SQLAlchemy-backed Strands SessionRepository.

Implements the Strands Agents SDK repository interface on the project's dual
database (SQLite / Supabase Postgres), so conversations persist across requests
and stay scoped to the owning teacher.
"""

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session as DbSession

from app.models import AgentSession, AgentSessionAgent, AgentSessionMessage


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _json_safe(value: Any) -> dict:
    """Best-effort conversion of a message/state mapping into a JSON dict."""
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    try:
        return dict(value)
    except TypeError:
        return {"value": str(value)}


def _sdk_types():
    from strands.session.session_repository import (
        Session,
        SessionAgent,
        SessionMessage,
    )

    return Session, SessionAgent, SessionMessage


class SqlAgentSessionRepository:
    """Strands ``SessionRepository`` persisted in the ContactLoop database."""

    def __init__(self, db: DbSession, user_id: uuid.UUID):
        self.db = db
        self.user_id = user_id

    # -- Session ------------------------------------------------------------

    def create_session(self, session, **kwargs):
        SessionType = self._session_type()
        self.db.add(
            AgentSession(
                session_id=session.session_id,
                user_id=self.user_id,
                kind=getattr(session, "session_type", SessionType.AGENT)
                or SessionType.AGENT,
                created_by=self.user_id,
                updated_by=self.user_id,
            )
        )
        self.db.commit()
        return session

    def read_session(self, session_id: str, **kwargs):
        row = self.db.scalar(
            select(AgentSession).where(
                AgentSession.session_id == session_id,
                AgentSession.user_id == self.user_id,
                AgentSession.deleted_at.is_(None),
            )
        )
        if row is None:
            return None
        Session, _Agent, _Message = _sdk_types()
        return Session(
            session_id=row.session_id,
            session_type=row.kind,
            created_at=row.created_at.isoformat() if row.created_at else "",
            updated_at=row.updated_at.isoformat() if row.updated_at else "",
        )

    @staticmethod
    def _session_type():
        from strands.types.session import SessionType

        return SessionType

    # -- Agent ---------------------------------------------------------------

    def create_agent(self, session_id: str, session_agent, **kwargs) -> None:
        self.db.add(
            AgentSessionAgent(
                session_id=session_id,
                agent_id=session_agent.agent_id,
                state=_json_safe(session_agent.state),
                conversation_manager_state=_json_safe(
                    session_agent.conversation_manager_state
                ),
                internal_state=_json_safe(session_agent._internal_state),
                created_by=self.user_id,
                updated_by=self.user_id,
            )
        )
        self.db.commit()

    def read_agent(self, session_id: str, agent_id: str, **kwargs):
        row = self.db.scalar(
            select(AgentSessionAgent).where(
                AgentSessionAgent.session_id == session_id,
                AgentSessionAgent.agent_id == agent_id,
                AgentSessionAgent.deleted_at.is_(None),
            )
        )
        if row is None:
            return None
        _Session, SessionAgent, _Message = _sdk_types()
        return SessionAgent(
            agent_id=row.agent_id,
            state=dict(row.state or {}),
            conversation_manager_state=dict(row.conversation_manager_state or {}),
            _internal_state=dict(row.internal_state or {}),
        )

    def update_agent(self, session_id: str, session_agent, **kwargs) -> None:
        row = self.db.scalar(
            select(AgentSessionAgent).where(
                AgentSessionAgent.session_id == session_id,
                AgentSessionAgent.agent_id == session_agent.agent_id,
                AgentSessionAgent.deleted_at.is_(None),
            )
        )
        if row is None:
            return
        row.state = _json_safe(session_agent.state)
        row.conversation_manager_state = _json_safe(
            session_agent.conversation_manager_state
        )
        row.internal_state = _json_safe(session_agent._internal_state)
        row.updated_at = _utcnow()
        self.db.commit()

    # -- Messages ------------------------------------------------------------

    def create_message(self, session_id: str, agent_id: str, session_message, **kwargs) -> None:
        self.db.add(
            AgentSessionMessage(
                session_id=session_id,
                agent_id=agent_id,
                message_id=session_message.message_id,
                message=_json_safe(session_message.message),
                redact_message=_json_safe(session_message.redact_message)
                if session_message.redact_message is not None
                else None,
                created_by=self.user_id,
                updated_by=self.user_id,
            )
        )
        self.db.commit()

    def read_message(self, session_id: str, agent_id: str, message_id: int, **kwargs):
        row = self._get_message_row(session_id, agent_id, message_id)
        if row is None:
            return None
        return self._to_session_message(row)

    def update_message(self, session_id: str, agent_id: str, session_message, **kwargs) -> None:
        row = self._get_message_row(
            session_id, agent_id, session_message.message_id
        )
        if row is None:
            return
        row.message = _json_safe(session_message.message)
        row.redact_message = (
            _json_safe(session_message.redact_message)
            if session_message.redact_message is not None
            else None
        )
        row.updated_at = _utcnow()
        self.db.commit()

    def _get_message_row(self, session_id: str, agent_id: str, message_id: int):
        return self.db.scalar(
            select(AgentSessionMessage).where(
                AgentSessionMessage.session_id == session_id,
                AgentSessionMessage.agent_id == agent_id,
                AgentSessionMessage.message_id == message_id,
            )
        )

    def list_messages(
        self, session_id: str, agent_id: str, limit: int | None = None, offset: int = 0, **kwargs
    ):
        statement = (
            select(AgentSessionMessage)
            .where(
                AgentSessionMessage.session_id == session_id,
                AgentSessionMessage.agent_id == agent_id,
            )
            .order_by(AgentSessionMessage.message_id.asc())
            .offset(offset)
        )
        if limit is not None:
            statement = statement.limit(limit)
        return [self._to_session_message(row) for row in self.db.scalars(statement)]

    @staticmethod
    def _to_session_message(row):
        _Session, _Agent, SessionMessage = _sdk_types()
        return SessionMessage(
            message=dict(row.message or {}),
            message_id=row.message_id,
            redact_message=dict(row.redact_message) if row.redact_message else None,
        )

    # -- App-level helpers ----------------------------------------------------

    def soft_delete_session(self, session_id: str) -> bool:
        row = self.db.scalar(
            select(AgentSession).where(
                AgentSession.session_id == session_id,
                AgentSession.user_id == self.user_id,
                AgentSession.deleted_at.is_(None),
            )
        )
        if row is None:
            return False
        # Drop the conversation content; keep a renamed tombstone row so a
        # fresh conversation can reuse the well-known session id without
        # violating the unique constraint on session_id.
        for model in (AgentSessionMessage, AgentSessionAgent):
            for child in self.db.scalars(
                select(model).where(model.session_id == session_id)
            ):
                self.db.delete(child)
        row.session_id = f"{session_id}#deleted-{uuid.uuid4().hex[:12]}"
        row.deleted_at = _utcnow()
        self.db.commit()
        return True

    def count_messages(self, session_id: str) -> int:
        return self.db.scalar(
            select(func.count(AgentSessionMessage.id)).where(
                AgentSessionMessage.session_id == session_id
            )
        )
