"""Shared FastAPI dependencies: DB session and current-user resolution."""
import uuid
from collections.abc import Generator

from fastapi import Depends, Header
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.exceptions import UnauthorizedError
from app.dao import AuthTokenDAO
from app.models import User


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _bearer_token(authorization: str | None) -> str | None:
    scheme, _, token = (authorization or "").partition(" ")
    return token if scheme.lower() == "bearer" and token else None


def get_current_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> User:
    token = _bearer_token(authorization)
    user = AuthTokenDAO(db).resolve(token) if token else None
    if user is None:
        raise UnauthorizedError("a valid bearer token is required")
    return user
