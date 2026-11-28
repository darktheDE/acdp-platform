"""Shared fixtures for FastAPI + PostgreSQL 18 + DuckDB Gold API tests."""

from __future__ import annotations

from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool
from sqlmodel import SQLModel

from acdp.api.db import models as _models  # noqa: F401
from acdp.api.db.postgres import get_db_session
from acdp.api.main import app
from acdp.api.middleware.security import reset_rate_limiter
from acdp.config import settings


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
async def api_client() -> AsyncGenerator[AsyncClient, None]:
    """Yield an AsyncClient wired to a NullPool OLTP session (Supabase/PG18) and real R2 DuckDB Gold."""
    test_engine = create_async_engine(
        settings.get_database_url(),
        poolclass=NullPool,
        connect_args=settings.get_asyncpg_connect_args(),
        future=True,
    )
    session_maker = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)

    async with test_engine.begin() as conn:
        await conn.execute(text('CREATE EXTENSION IF NOT EXISTS "pgcrypto"'))
        await conn.run_sync(SQLModel.metadata.create_all)

    async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with session_maker() as session:
            yield session

    app.dependency_overrides[get_db_session] = _override_get_db
    reset_rate_limiter()
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            yield client
    finally:
        reset_rate_limiter()
        app.dependency_overrides.clear()
        async with test_engine.begin() as conn:
            await conn.execute(text("DELETE FROM users WHERE email LIKE 'test_%@hcmute.edu.vn'"))
        await test_engine.dispose()
