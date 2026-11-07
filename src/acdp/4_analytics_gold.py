"""Module 4: Gold Layer Analytics & DuckDB Materialization Engine.

Conforms to ACDP Data Engineering standards:
1. Transforms Silver extracted competition schemas into normalized Parquet columnar files.
2. Manages persistent DuckDB database at `data/lakehouse/acdp.duckdb`.
3. Materializes analytical SQL views and tables for Metabase BI dashboards:
   - `gold_competitions`: Base normalized competition dimension.
   - `gold_prizes`: 1-to-N normalized prize tiers and valuations.
   - `gold_category_summary`: Aggregated domain distribution and prize pools.
   - `gold_mode_distribution`: Online vs Offline vs Hybrid ratio.
   - `gold_seasonality`: Deadline distribution across timeline quarters and months.

Usage:
    uv run python src/acdp/4_analytics_gold.py --build
    uv run python src/acdp/4_analytics_gold.py --verify
"""

import argparse
import json
import re
from pathlib import Path
from typing import Any

import duckdb
import pyarrow as pa
import pyarrow.parquet as pq

from acdp.config import settings
from acdp.schemas import Competition


def parse_vnd_currency(val_str: str | None) -> float:
    """Helper to parse Vietnamese currency strings to float VND."""
    if not val_str:
        return 0.0
    cleaned = val_str.lower().replace(".", "").replace(",", "").replace(" ", "")
    # Check for 'triệu'
    match_trieu = re.search(r"(\d+(?:\.\d+)?)\s*(?:trieu|triệu|m)", val_str.lower())
    if match_trieu:
        return float(match_trieu.group(1)) * 1_000_000.0
    # Check for 'tỷ'
    match_ty = re.search(r"(\d+(?:\.\d+)?)\s*(?:ty|tỷ|b)", val_str.lower())
    if match_ty:
        return float(match_ty.group(1)) * 1_000_000_000.0
    # Check digits
    digits = re.sub(r"[^\d]", "", cleaned)
    if digits:
        try:
            return float(digits)
        except ValueError:
            return 0.0
    return 0.0


def load_silver_competitions(extractions_dir: Path | None = None) -> list[Competition]:
    """Loads competitions strictly from Silver extracted JSON files without fallback."""
    competitions: list[Competition] = []
    target_dir = extractions_dir or Path("data/extractions")

    if target_dir.exists():
        json_files = list(target_dir.glob("*.json"))
        for jf in json_files:
            try:
                with open(jf, encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, dict):
                    # Check batch format
                    if "results" in data:
                        for item in data["results"]:
                            for c in item.get("competitions", []):
                                competitions.append(Competition.model_validate(c))
                    elif "competitions" in data:
                        for c in data["competitions"]:
                            competitions.append(Competition.model_validate(c))
            except (json.JSONDecodeError, OSError, ValueError) as e:
                print(f"[WARN] Failed to parse {jf.name}: {e}")

    if not competitions:
        raise RuntimeError(
            f"No valid Silver extracted competition records found in '{target_dir.resolve()}'. "
            "Ensure that Silver extraction (src/acdp/2_instruction.py) has completed successfully before building Gold analytics."
        )

    return competitions


def export_silver_parquet(competitions: list[Competition], output_dir: Path) -> tuple[Path, Path]:
    """Exports structured competitions and prizes to Silver Parquet columnar files."""
    output_dir.mkdir(parents=True, exist_ok=True)
    comp_parquet_path = output_dir / "competitions.parquet"
    prizes_parquet_path = output_dir / "prizes.parquet"

    # 1. Flatten competitions table
    comp_rows: list[dict[str, Any]] = []
    prize_rows: list[dict[str, Any]] = []

    for c in competitions:
        # Calculate quantitative prize VND
        calculated_prize_vnd = 0.0
        if c.prizes:
            calculated_prize_vnd = sum(p.estimated_value_vnd or 0.0 for p in c.prizes)
        if calculated_prize_vnd == 0.0 and c.total_prize_pool:
            calculated_prize_vnd = parse_vnd_currency(c.total_prize_pool)

        comp_rows.append({
            "name": c.name,
            "tagline": c.tagline or "",
            "url": c.url or "",
            "summary": c.summary,
            "organizers": c.organizers,
            "partners_and_sponsors": c.partners_and_sponsors,
            "category": c.category,
            "target_audience": str(c.target_audience or ""),
            "team_size_min": c.team_size_min or 1,
            "team_size_max": c.team_size_max or 1,
            "is_team_required": bool(c.team_size_min and c.team_size_min > 1),
            "team_description": c.team_description or "",
            "mode": c.mode,
            "location": c.location or "",
            "participation_fee": c.participation_fee or "Miễn phí",
            "total_prize_pool": c.total_prize_pool or "",
            "total_prize_vnd": calculated_prize_vnd,
            "registration_start": c.registration_start or "",
            "registration_deadline": c.registration_deadline or "",
            "registration_status": c.registration_status,
            "event_start": c.event_start or "",
            "event_end": c.event_end or "",
            "challenge_overview": c.challenge_overview or "",
            "submission_platform": c.submission_platform or "",
        })

        for p in c.prizes:
            prize_rows.append({
                "competition_name": c.name,
                "tier": p.tier,
                "reward": p.reward,
                "estimated_value_vnd": p.estimated_value_vnd or 0.0,
                "is_scholarship": p.is_scholarship,
            })

    # Write competitions parquet
    comp_table = pa.Table.from_pylist(comp_rows)
    pq.write_table(comp_table, comp_parquet_path)
    print(f">> [PARQUET EXPORTED] {len(comp_rows)} competitions -> {comp_parquet_path}")

    # Write prizes parquet
    if prize_rows:
        prize_table = pa.Table.from_pylist(prize_rows)
        pq.write_table(prize_table, prizes_parquet_path)
        print(f">> [PARQUET EXPORTED] {len(prize_rows)} prize tiers -> {prizes_parquet_path}")

    return comp_parquet_path, prizes_parquet_path


def build_gold_views(db_path: Path, comp_parquet: Path, prizes_parquet: Path) -> duckdb.DuckDBPyConnection:
    """Creates persistent DuckDB tables and Gold analytical views."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(db_path))

    comp_escaped = str(comp_parquet).replace("\\", "/")
    prizes_escaped = str(prizes_parquet).replace("\\", "/")

    # Create base tables
    con.execute(f"CREATE OR REPLACE TABLE gold_competitions AS SELECT * FROM read_parquet('{comp_escaped}')")
    con.execute(f"CREATE OR REPLACE TABLE gold_prizes AS SELECT * FROM read_parquet('{prizes_escaped}')")

    # View 1: Domain category summary
    con.execute("""
        CREATE OR REPLACE VIEW gold_category_summary AS
        WITH unnested_cat AS (
            SELECT 
                unnest(category) AS domain_category,
                total_prize_vnd
            FROM gold_competitions
        )
        SELECT 
            domain_category,
            COUNT(*) AS total_competitions,
            COALESCE(SUM(total_prize_vnd), 0) AS total_prize_pool_vnd,
            ROUND(AVG(total_prize_vnd), 0) AS avg_prize_vnd
        FROM unnested_cat
        GROUP BY domain_category
        ORDER BY total_prize_pool_vnd DESC
    """)

    # View 2: Mode distribution (Online vs Offline vs Hybrid)
    con.execute("""
        CREATE OR REPLACE VIEW gold_mode_distribution AS
        SELECT 
            mode,
            COUNT(*) AS count,
            ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) AS percentage
        FROM gold_competitions
        GROUP BY mode
        ORDER BY count DESC
    """)

    # View 3: Registration Seasonality & Deadlines
    con.execute("""
        CREATE OR REPLACE VIEW gold_seasonality AS
        SELECT 
            CASE 
                WHEN registration_deadline LIKE '____-__-__' THEN strftime(strptime(registration_deadline, '%Y-%m-%d'), '%Y-%m')
                ELSE 'Khác'
            END AS deadline_month,
            COUNT(*) AS competition_count,
            STRING_AGG(name, '; ') AS competitions
        FROM gold_competitions
        GROUP BY 1
        ORDER BY 1
    """)

    # View 4: Top Prize Leaderboard
    con.execute("""
        CREATE OR REPLACE VIEW gold_top_prizes AS
        SELECT 
            name,
            total_prize_pool,
            total_prize_vnd,
            mode,
            registration_deadline,
            registration_status,
            url
        FROM gold_competitions
        ORDER BY total_prize_vnd DESC
    """)

    print(f">> [GOLD VIEWS MATERIALIZED] In DuckDB: {db_path}")
    return con


def verify_analytics(con: duckdb.DuckDBPyConnection) -> None:
    """Executes verification queries and displays analytical reports."""
    print("\n" + "=" * 65)
    print("📊 ACDP GOLD LAYER ANALYTICAL REPORT (DuckDB OLAP)")
    print("=" * 65)

    print("\n[1] Thống kê Cuộc thi theo Lĩnh vực (gold_category_summary):")
    print(con.sql("SELECT domain_category, total_competitions, total_prize_pool_vnd FROM gold_category_summary").show())

    print("\n[2] Phân bố Hình thức Tổ chức (gold_mode_distribution):")
    print(con.sql("SELECT mode, count, percentage FROM gold_mode_distribution").show())

    print("\n[3] Bảng Xếp hạng Cuộc thi theo Tổng Giải thưởng (gold_top_prizes):")
    print(con.sql("SELECT name, total_prize_pool, mode, registration_deadline FROM gold_top_prizes LIMIT 5").show())

    print("\n[4] Phân bố Mùa vụ Đăng ký (gold_seasonality):")
    print(con.sql("SELECT deadline_month, competition_count, competitions FROM gold_seasonality").show())
    print("=" * 65)


def run_gold_pipeline() -> None:
    """Executes the complete Gold analytics pipeline."""
    extractions_dir = Path("data/extractions")
    silver_dir = Path("data/lakehouse/silver")
    duckdb_file = Path(settings.duckdb_database_path)

    competitions = load_silver_competitions(extractions_dir)
    comp_parquet, prizes_parquet = export_silver_parquet(competitions, silver_dir)
    con = build_gold_views(duckdb_file, comp_parquet, prizes_parquet)
    verify_analytics(con)
    con.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ACDP Gold Layer Analytics & DuckDB Materialization Engine")
    parser.add_argument("--build", action="store_true", help="Build Silver Parquet and DuckDB Gold views")
    parser.add_argument("--verify", action="store_true", help="Print verification queries from DuckDB")
    args = parser.parse_args()

    run_gold_pipeline()
