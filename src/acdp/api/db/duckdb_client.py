"""Shared-connection DuckDB cursor manager reading Gold Parquet directly from Cloudflare R2 via httpfs."""

from __future__ import annotations

import threading
import time
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

import duckdb

from acdp.api.services.gold_queries import get_gold_mart_cache_stats, invalidate_gold_mart_cache
from acdp.config import settings

_PARQUET_ENTITIES = (
    "dim_competition",
    "dim_date",
    "dim_domain",
    "dim_organizer",
    "fact_competitions",
    "fact_prize_tiers",
    "fact_timeline_stages",
    "bridge_competition_domain",
    "bridge_competition_organizer",
    "mart_kpi_overview",
    "mart_domain_analytics",
    "mart_seasonality_academic",
    "mart_organizer_ecosystem",
    "mart_team_and_mode_matrix",
    "mart_competition_explorer",
)

_conn_lock = threading.Lock()
_shared_con: duckdb.DuckDBPyConnection | None = None


def _hydrate_gold_entities_from_r2(con: duckdb.DuckDBPyConnection) -> None:
    """Load or bind all 15 Gold Parquet entities directly from Cloudflare R2 s3:// URI."""
    bucket = settings.bucket_name.strip().strip("/")
    ddl_kind = "TABLE" if settings.duckdb_r2_table_cache else "VIEW"
    for entity in _PARQUET_ENTITIES:
        s3_uri = f"s3://{bucket}/gold/{entity}.parquet"
        con.execute(f"CREATE OR REPLACE {ddl_kind} {entity} AS SELECT * FROM read_parquet('{s3_uri}')")


def _get_or_init_shared_connection() -> duckdb.DuckDBPyConnection:
    """Initialize a process-wide in-memory DuckDB connection backed by R2 httpfs Gold Parquet."""
    global _shared_con
    if _shared_con is not None:
        return _shared_con

    with _conn_lock:
        if _shared_con is not None:
            return _shared_con
        if not settings.bucket_name:
            raise RuntimeError("BUCKET_NAME is required for DuckDB R2 httpfs Gold queries.")

        con = duckdb.connect(":memory:")
        try:
            con.execute(f"SET memory_limit='{settings.duckdb_memory_limit}'")
            con.execute(f"SET threads={settings.duckdb_threads}")
            settings.configure_duckdb_r2(con)
            _hydrate_gold_entities_from_r2(con)
            _shared_con = con
            return _shared_con
        except Exception:
            con.close()
            raise


def refresh_duckdb_r2_connection() -> dict[str, Any]:
    """Reload all 15 Gold Parquet entities directly from Cloudflare R2 s3:// without restarting API."""
    t0 = time.perf_counter()
    con = _get_or_init_shared_connection()
    with _conn_lock:
        _hydrate_gold_entities_from_r2(con)
        row = con.execute("SELECT COUNT(*) FROM dim_competition").fetchone()
    invalidate_gold_mart_cache()
    elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)
    return {
        "mode": "r2_httpfs_memory_table" if settings.duckdb_r2_table_cache else "r2_httpfs_direct_view",
        "bucket_uri": f"s3://{settings.bucket_name.strip().strip('/')}/gold",
        "entities_loaded": len(_PARQUET_ENTITIES),
        "competitions_count": int(row[0]) if row else 0,
        "refresh_ms": elapsed_ms,
        "gold_mart_cache": get_gold_mart_cache_stats(),
    }


def reset_duckdb_connection() -> None:
    """Close and reset the shared DuckDB connection (used in tests and shutdown)."""
    global _shared_con
    with _conn_lock:
        if _shared_con is not None:
            _shared_con.close()
            _shared_con = None
    invalidate_gold_mart_cache()


@contextmanager
def get_duckdb_conn() -> Iterator[duckdb.DuckDBPyConnection]:
    """Yield an isolated DuckDB cursor over the shared R2-backed Gold Parquet entities."""
    cursor = _get_or_init_shared_connection().cursor()
    try:
        yield cursor
    finally:
        cursor.close()
