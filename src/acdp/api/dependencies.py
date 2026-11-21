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

_bearer_scheme = HTTPBearer(auto_error=False)


def get_duckdb() -> Iterator[duckdb.DuckDBPyConnection]:
    """Yield a per-request read-only DuckDB connection."""
    with get_duckdb_conn() as con:
        yield con


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
    return result.scalars().first()


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
    return user
