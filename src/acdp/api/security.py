"""Password hashing (Argon2id via pwdlib) and JWT / Refresh Token helpers."""

from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

import jwt
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash

from acdp.config import settings

_password_hash = PasswordHash.recommended()


def hash_password(plain_password: str) -> str:
    """Hash a plain-text password using Argon2id."""
    return _password_hash.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain-text password against its Argon2id hash."""
    return _password_hash.verify(plain_password, hashed_password)


def create_access_token(user_id: UUID, role: str, expires_delta: timedelta | None = None) -> str:
    """Create a short-lived HS256 JWT access token."""
    now = datetime.now(UTC)
    expire = now + (expires_delta or timedelta(minutes=settings.access_token_expire_minutes))
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict[str, Any] | None:
    """Decode and validate an HS256 JWT access token; return None if invalid or expired."""
    try:
        return jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
    except InvalidTokenError:
        return None


def generate_refresh_token() -> str:
    """Generate a cryptographically random 256-bit URL-safe refresh token."""
    return secrets.token_urlsafe(32)


def hash_refresh_token(raw_token: str) -> str:
    """Return the SHA-256 hex digest of a refresh token for database storage."""
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
