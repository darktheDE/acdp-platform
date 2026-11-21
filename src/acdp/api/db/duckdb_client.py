"""Per-request DuckDB read-only connection manager with Parquet fallback (SPEC-0004 EC-A1)."""

from __future__ import annotations

import random
import time
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

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


def _open_parquet_fallback(gold_dir: Path) -> duckdb.DuckDBPyConnection:
    """Open an in-memory DuckDB connection backed by Gold Parquet files."""
    con = duckdb.connect(":memory:")
    con.execute(f"SET memory_limit='{settings.duckdb_memory_limit}'")
    con.execute(f"SET threads={settings.duckdb_threads}")
    for entity in _PARQUET_ENTITIES:
        pq_path = gold_dir / f"{entity}.parquet"
        if pq_path.exists():
            escaped = str(pq_path).replace("\\", "/")
            con.execute(f"CREATE OR REPLACE VIEW {entity} AS SELECT * FROM read_parquet('{escaped}')")
    return con


@contextmanager
def get_duckdb_conn() -> Iterator[duckdb.DuckDBPyConnection]:
    """Open DuckDB in read_only=True mode with 256MB cap and EC-A1 Parquet fallback."""
    db_path = Path(settings.duckdb_database_path)
    gold_dir = db_path.parent / "gold"

    con: duckdb.DuckDBPyConnection | None = None
    last_exc: Exception | None = None

    if db_path.exists():
        for attempt in range(3):
            try:
                con = duckdb.connect(str(db_path), read_only=True)
                con.execute(f"SET memory_limit='{settings.duckdb_memory_limit}'")
                con.execute(f"SET threads={settings.duckdb_threads}")
                break
            except duckdb.IOException as exc:
                last_exc = exc
                time.sleep(0.05 + random.uniform(0.0, 0.03))

    if con is None:
        if gold_dir.exists() and any(gold_dir.glob("*.parquet")):
            con = _open_parquet_fallback(gold_dir)
        else:
            raise RuntimeError(f"DuckDB lakehouse unavailable at {db_path}") from last_exc

    try:
        yield con
    finally:
        con.close()
