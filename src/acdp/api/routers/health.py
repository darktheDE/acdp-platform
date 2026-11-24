"""System healthcheck router (/api/v1/health)."""

from __future__ import annotations

import asyncio
from typing import Literal

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from acdp.api.db.duckdb_client import get_duckdb_conn
from acdp.api.db.postgres import get_db_session
from acdp.api.schemas.analytics import HealthResponse
from acdp.api.services.rag_service import check_qdrant_health

router = APIRouter(tags=["System"])


@router.get("/health", response_model=HealthResponse)
async def health_check(db: AsyncSession = Depends(get_db_session)) -> HealthResponse:
    """Check PostgreSQL 18, DuckDB Gold Star Schema, and Qdrant readiness."""
    pg_status: Literal["up", "down"] = "down"
    try:
        await db.execute(text("SELECT 1"))
        pg_status = "up"
    except Exception:
        pg_status = "down"

    duck_status: Literal["up", "down"] = "down"
    comp_count = 0
    try:
        with get_duckdb_conn() as con:
            row = con.execute("SELECT COUNT(*) FROM dim_competition").fetchone()
            comp_count = int(row[0]) if row else 0
            duck_status = "up"
    except Exception:
        duck_status = "down"

    qdrant_raw = await asyncio.to_thread(check_qdrant_health)
    qdrant_status: Literal["up", "degraded", "down"] = qdrant_raw  # type: ignore[assignment]

    overall: Literal["ok", "degraded"] = (
        "ok" if (pg_status == "up" and duck_status == "up" and qdrant_status == "up") else "degraded"
    )
    return HealthResponse(
        status=overall,
        postgres=pg_status,
        duckdb=duck_status,
        qdrant=qdrant_status,
        gold_competitions_count=comp_count,
    )
