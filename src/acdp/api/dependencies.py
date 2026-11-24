"""FastAPI dependency injection for DB sessions, DuckDB read-only, and JWT auth."""

from __future__ import annotations

from collections.abc import Iterator
from uuid import UUID

import duckdb
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from acdp.api.db.duckdb_client import get_duckdb_conn
from acdp.api.db.models import User
from acdp.api.db.postgres import get_db_session
from acdp.api.security import decode_access_token
from acdp.config import settings

_bearer_scheme = HTTPBearer(auto_error=False)


def get_duckdb() -> Iterator[duckdb.DuckDBPyConnection]:
    """Yield a per-request read-only DuckDB connection."""
    with get_duckdb_conn() as con:
        yield con


async def _sync_admin_role_if_listed(user: User, db: AsyncSession) -> User:
    """Promote user to 'admin' when their email is listed in ADMIN_EMAILS."""
    if user.email.lower() in settings.get_admin_emails() and user.role != "admin":
        user.role = "admin"
        db.add(user)
        await db.commit()
        await db.refresh(user)
    return user


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    db: AsyncSession = Depends(get_db_session),
) -> User | None:
    """Return authenticated User if valid Bearer JWT is present, otherwise None."""
    if not credentials or not credentials.credentials:
        return None
    payload = decode_access_token(credentials.credentials)
    if not payload or "sub" not in payload:
        return None
    try:
        user_id = UUID(str(payload["sub"]))
    except ValueError:
        return None

    result = await db.execute(select(User).where(User.id == user_id, User.is_active.is_(True)))
    user = result.scalars().first()
    if user is None:
        return None
    return await _sync_admin_role_if_listed(user, db)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    db: AsyncSession = Depends(get_db_session),
) -> User:
    """Require a valid active Bearer JWT user or raise HTTP 401."""
    exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not credentials or not credentials.credentials:
        raise exc
    payload = decode_access_token(credentials.credentials)
    if not payload or "sub" not in payload:
        raise exc
    try:
        user_id = UUID(str(payload["sub"]))
    except ValueError as err:
        raise exc from err

    result = await db.execute(select(User).where(User.id == user_id, User.is_active.is_(True)))
    user = result.scalars().first()
    if user is None:
        raise exc
    return await _sync_admin_role_if_listed(user, db)


async def require_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """Require an authenticated active user with role == 'admin' or raise HTTP 403."""
    if current_user.role != "admin" and current_user.email.lower() not in settings.get_admin_emails():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required.",
        )
    return current_user


async def require_lecturer_or_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """Require an authenticated active user with role in ('lecturer', 'admin') or raise HTTP 403."""
    if (
        current_user.role not in {"lecturer", "admin"}
        and current_user.email.lower() not in settings.get_admin_emails()
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Lecturer or Admin privileges required.",
        )
    return current_user
