import uuid
from datetime import datetime, timezone
from typing import Any, Mapping

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.models.base import Base

AUDIT_FIELDS = frozenset(
    {"id", "created_at", "updated_at", "created_by", "updated_by", "deleted_at"}
)


class BaseDAO:
    model: type[Base]

    def __init__(self, db: Session) -> None:
        self.db = db

    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc)

    def _alive(self):
        return select(self.model).where(self.model.deleted_at.is_(None))

    def _writable(self, data: Mapping[str, Any]) -> dict[str, Any]:
        allowed = {column.key for column in self.model.__table__.columns} - AUDIT_FIELDS
        return {key: value for key, value in data.items() if key in allowed}

    def _stamp(self, obj, actor_id: uuid.UUID | None = None, created: bool = False):
        now = self._now()
        obj.updated_at = now
        if created:
            obj.created_at = now
        if actor_id is not None:
            obj.updated_by = actor_id
            if created:
                obj.created_by = actor_id

    def _resolve(self, ref):
        if isinstance(ref, self.model):
            return ref
        return self.require(ref)

    def get(self, entity_id):
        return self.db.scalar(self._alive().where(self.model.id == entity_id))

    def require(self, entity_id):
        obj = self.get(entity_id)
        if obj is None:
            raise NotFoundError(f"{self.model.__tablename__} {entity_id} not found")
        return obj

    def create(self, data: Mapping[str, Any], actor_id: uuid.UUID | None = None):
        obj = self.model(**self._writable(data))
        self._stamp(obj, actor_id=actor_id, created=True)
        self.db.add(obj)
        self.db.flush()
        return obj

    def update(self, ref, data: Mapping[str, Any], actor_id: uuid.UUID | None = None):
        obj = self._resolve(ref)
        for key, value in self._writable(data).items():
            setattr(obj, key, value)
        self._stamp(obj, actor_id=actor_id)
        self.db.flush()
        return obj

    def soft_delete(self, ref, actor_id: uuid.UUID | None = None):
        obj = self._resolve(ref)
        obj.deleted_at = self._now()
        self._stamp(obj, actor_id=actor_id)
        self.db.flush()
        return obj
