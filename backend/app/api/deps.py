"""Shared FastAPI dependencies: DB session and optional current-user resolution."""
import base64
import hashlib
import hmac
import json
import uuid
from collections.abc import Generator

from fastapi import Header
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal


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


def get_current_user_id(
    x_user_id: str | None = Header(default=None),
    authorization: str | None = Header(default=None),
) -> uuid.UUID | None:
    """Best-effort actor resolution; never blocks anonymous requests."""
    if x_user_id:
        try:
            return uuid.UUID(x_user_id)
        except ValueError:
            pass
    if authorization:
        scheme, _, token = authorization.partition(" ")
        if scheme.lower() == "bearer" and token and settings.supabase_jwt_secret:
            claims = _verify_hs256_jwt(token, settings.supabase_jwt_secret)
            if claims and claims.get("sub"):
                try:
                    return uuid.UUID(str(claims["sub"]))
                except ValueError:
                    return None
    return None
