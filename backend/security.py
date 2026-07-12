"""Password hashing and JWT helpers.

Uses the `bcrypt` library directly (avoiding passlib, which is incompatible
with bcrypt>=4.x). All secrets are loaded from the environment.
"""
from __future__ import annotations

import bcrypt
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

from config import settings

# bcrypt hard-limits passwords to 72 bytes.
_MAX_BYTES = 72


def _to_bytes(password: str) -> bytes:
    return password.encode("utf-8")[:_MAX_BYTES]


def hash_password(password: str) -> str:
    return bcrypt.hashpw(_to_bytes(password), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(_to_bytes(plain), hashed.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def create_access_token(subject: str | int, is_admin: bool = False) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {"sub": str(subject), "admin": bool(is_admin), "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError:
        return None


def normalize_phone(raw: str) -> str:
    """Basic E.164-ish normalization: keep digits and a leading +."""
    raw = (raw or "").strip()
    if raw.startswith("+"):
        return "+" + "".join(ch for ch in raw[1:] if ch.isdigit())
    return "".join(ch for ch in raw if ch.isdigit())
