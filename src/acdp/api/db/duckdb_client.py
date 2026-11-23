"""Per-request DuckDB in-memory connection manager reading Gold Parquet directly from Cloudflare R2 via httpfs."""

from __future__ import annotations

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


def _open_r2_parquet_connection() -> duckdb.DuckDBPyConnection:
    """Open an in-memory DuckDB connection backed by Gold Parquet files on Cloudflare R2 via httpfs."""
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
        return con
    except Exception:
        con.close()
        raise


@contextmanager
def get_duckdb_conn() -> Iterator[duckdb.DuckDBPyConnection]:
    """Open an in-memory DuckDB connection over Cloudflare R2 Gold Parquet with 256MB memory cap."""
    con = _open_r2_parquet_connection()
    try:
        yield con
    finally:
        con.close()
