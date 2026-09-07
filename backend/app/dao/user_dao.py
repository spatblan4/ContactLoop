import re
import uuid

from sqlalchemy import select

from app.core.exceptions import ConflictError
from app.core.security import hash_password, verify_password
from app.dao.base import BaseDAO
from app.models import User

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MIN_PASSWORD_LENGTH = 6


class UserDAO(BaseDAO):
    model = User

    def get_by_email(self, email: str):
        stmt = self._alive().where(User.email == email.strip().lower())
        return self.db.scalar(stmt)

    def register(
        self,
        email: str,
        password: str,
        name: str | None = None,
        actor_id: uuid.UUID | None = None,
    ):
        email = (email or "").strip().lower()
        if not EMAIL_RE.match(email):
            raise ValueError("a valid email address is required")
        if not isinstance(password, str) or len(password) < MIN_PASSWORD_LENGTH:
            raise ValueError(f"password must be at least {MIN_PASSWORD_LENGTH} characters")
        if self.get_by_email(email) is not None:
            raise ConflictError("an account with this email already exists")
        return self.create(
            {
                "email": email,
                "name": (name or "").strip() or None,
                "password_hash": hash_password(password),
            },
            actor_id=actor_id,
        )

    def verify(self, email: str, password: str):
        user = self.get_by_email(email or "")
        if user is None or not verify_password(password or "", user.password_hash):
            return None
        return user
