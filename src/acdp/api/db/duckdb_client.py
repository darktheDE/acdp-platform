"""Shared-connection DuckDB cursor manager reading Gold Parquet directly from Cloudflare R2 via httpfs."""

from __future__ import annotations

import threading
from collections.abc import Iterator
from contextlib import contextmanager

import duckdb

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


def _get_or_init_shared_connection() -> duckdb.DuckDBPyConnection:
    """Initialize a process-wide in-memory DuckDB connection with R2 httpfs views once."""
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

            bucket = settings.bucket_name.strip().strip("/")
            for entity in _PARQUET_ENTITIES:
                s3_uri = f"s3://{bucket}/gold/{entity}.parquet"
                con.execute(f"CREATE OR REPLACE VIEW {entity} AS SELECT * FROM read_parquet('{s3_uri}')")
            _shared_con = con
            return _shared_con
        except Exception:
            con.close()
            raise


@contextmanager
def get_duckdb_conn() -> Iterator[duckdb.DuckDBPyConnection]:
    """Yield an isolated DuckDB cursor over the shared R2-backed Gold Parquet views."""
    cursor = _get_or_init_shared_connection().cursor()
    try:
        yield cursor
    finally:
        cursor.close()
