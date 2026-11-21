"""Async PostgreSQL 18 engine, session dependency, and idempotent schema initialization."""

from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlmodel import SQLModel

from acdp.config import settings

engine: AsyncEngine = create_async_engine(
    settings.get_database_url(),
    pool_size=5,
    max_overflow=5,
    pool_recycle=1800,
    pool_pre_ping=True,
    future=True,
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def init_oltp_schema() -> None:
    """Create pgcrypto extension and all OLTP tables idempotently on startup."""
    # Ensure ORM models are imported before metadata.create_all
    from acdp.api.db import models as _models  # noqa: F401

    async with engine.begin() as conn:
        await conn.execute(text('CREATE EXTENSION IF NOT EXISTS "pgcrypto"'))
        await conn.run_sync(SQLModel.metadata.create_all)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async PostgreSQL session."""
    async with async_session_factory() as session:
        yield session
