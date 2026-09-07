"""Shared FastAPI dependencies: DB session and optional current-user resolution."""
import base64
import hashlib
import hmac
import json
import uuid
from collections.abc import Generator

from fastapi import Depends, Header
from sqlalchemy.orm import Session

from app.core.config import settings
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


def _b64url_decode(segment: str) -> bytes:
    padding = "=" * (-len(segment) % 4)
    return base64.urlsafe_b64decode(segment + padding)


def _verify_hs256_jwt(token: str, secret: str) -> dict | None:
    try:
        header_b64, payload_b64, signature_b64 = token.split(".")
        header = json.loads(_b64url_decode(header_b64))
        if header.get("alg") != "HS256":
            return None
        signed = f"{header_b64}.{payload_b64}".encode("ascii")
        expected = hmac.new(secret.encode("utf-8"), signed, hashlib.sha256).digest()
        if not hmac.compare_digest(expected, _b64url_decode(signature_b64)):
            return None
        return json.loads(_b64url_decode(payload_b64))
    except Exception:
        return None


def _bearer_token(authorization: str | None) -> str | None:
    scheme, _, token = (authorization or "").partition(" ")
    return token if scheme.lower() == "bearer" and token else None


def get_current_user_id(
    x_user_id: str | None = Header(default=None),
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> uuid.UUID | None:
    """Best-effort actor resolution; never blocks anonymous requests."""
    if x_user_id:
        try:
            return uuid.UUID(x_user_id)
        except ValueError:
            pass
    token = _bearer_token(authorization)
    if token:
        if settings.supabase_jwt_secret:
            claims = _verify_hs256_jwt(token, settings.supabase_jwt_secret)
            if claims and claims.get("sub"):
                try:
                    return uuid.UUID(str(claims["sub"]))
                except ValueError:
                    pass
        user = AuthTokenDAO(db).resolve(token)
        if user is not None:
            return user.id
    return None


def get_current_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> User:
    token = _bearer_token(authorization)
    user = AuthTokenDAO(db).resolve(token) if token else None
    if user is None:
        raise UnauthorizedError("a valid bearer token is required")
    return user
