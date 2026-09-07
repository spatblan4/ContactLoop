import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.dao.base import BaseDAO
from app.models import AuthToken, User

TOKEN_TTL_DAYS = 30


class AuthTokenDAO(BaseDAO):
    model = AuthToken

    @staticmethod
    def _hash_token(token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    def issue(
        self,
        user_id: uuid.UUID,
        ttl_days: int = TOKEN_TTL_DAYS,
        actor_id: uuid.UUID | None = None,
    ) -> str:
        token = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(days=ttl_days)
        self.create(
            {"user_id": user_id, "token_hash": self._hash_token(token), "expires_at": expires_at},
            actor_id=actor_id,
        )
        return token

    def resolve(self, token: str):
        if not token:
            return None
        stmt = (
            select(User)
            .join(AuthToken, AuthToken.user_id == User.id)
            .where(
                AuthToken.token_hash == self._hash_token(token),
                AuthToken.deleted_at.is_(None),
                User.deleted_at.is_(None),
            )
        )
        row = self.db.scalar(stmt)
        if row is None:
            return None
        token_row = self.db.scalar(
            select(AuthToken).where(AuthToken.token_hash == self._hash_token(token))
        )
        expires_at = token_row.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at <= datetime.now(timezone.utc):
            return None
        return row

    def revoke(self, token: str, actor_id: uuid.UUID | None = None):
        if not token:
            return False
        row = self.db.scalar(
            select(AuthToken).where(
                AuthToken.token_hash == self._hash_token(token),
                AuthToken.deleted_at.is_(None),
            )
        )
        if row is None:
            return False
        self.soft_delete(row, actor_id=actor_id)
        return True
