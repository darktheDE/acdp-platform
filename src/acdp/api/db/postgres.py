"""Async Supabase/PostgreSQL 18 OLTP engine, session dependency, and idempotent schema initialization."""

from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool
from sqlmodel import SQLModel

from acdp.config import AppConfig, settings


def build_async_engine(cfg: AppConfig = settings) -> AsyncEngine:
    """Create SQLAlchemy AsyncEngine tuned for Supabase Supavisor (:6543) or Session/Local Pool."""
    db_url = cfg.get_database_url()
    connect_args = cfg.get_asyncpg_connect_args()
    if cfg.is_transaction_pooler_active():
        return create_async_engine(
            db_url,
            poolclass=NullPool,
            connect_args=connect_args,
            future=True,
        )
    return create_async_engine(
        db_url,
        pool_size=5,
        max_overflow=5,
        pool_recycle=1800,
        pool_pre_ping=True,
        connect_args=connect_args,
        future=True,
    )


engine: AsyncEngine = build_async_engine(settings)

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
