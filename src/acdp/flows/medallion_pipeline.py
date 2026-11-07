"""Module: Prefect 3.x Medallion Lakehouse Orchestration Pipeline.

Orchestrates the 3 tiers of the ACDP platform:
1. Task 1: Bronze Layer Ingestion (Crawl4AI or offline Markdown fixtures).
2. Task 2: Silver Layer Structured Extraction (Instructor + Pydantic v2).
3. Task 3: Gold Layer Materialization & OLAP Aggregation (DuckDB + Parquet).

Usage:
    # Run pipeline directly via CLI
    uv run python src/acdp/flows/medallion_pipeline.py

    # Start local Prefect UI server on port 4200
    uv run prefect server start
"""

import importlib
from pathlib import Path

import boto3
from prefect import flow, task

from acdp.config import settings

# Dynamic imports for modules with numeric prefixes
analytics_gold = importlib.import_module("acdp.4_analytics_gold")
run_gold_pipeline = analytics_gold.run_gold_pipeline

instruction_mod = importlib.import_module("acdp.2_instruction")
process_bronze_bucket = instruction_mod.process_bronze_bucket


@task(name="1. Ingest Bronze Markdown", retries=1, retry_delay_seconds=5)
def task_ingest_bronze(target_urls: list[str] | None = None) -> int:
    """Task 1: Ingests or verifies raw Markdown content in the Bronze layer."""
    print(">> [PREFECT TASK 1] Checking Bronze Layer Markdown...")
    if settings.bronze_storage_backend == "cloudflare_r2":
        s3 = boto3.client(
            "s3",
            endpoint_url=settings.aws_endpoint_url,
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
            region_name=settings.aws_region or "auto",
        )
        res = s3.list_objects_v2(Bucket=settings.bucket_name, Prefix="bronze/")
        contents = [o for o in res.get("Contents", []) if not o["Key"].endswith("/")]
        if not contents:
            raise RuntimeError(f"No Bronze layer objects found in Cloudflare R2 bucket '{settings.bucket_name}'.")
        print(f">> [PREFECT TASK 1] Verified {len(contents)} objects in Cloudflare R2 bucket '{settings.bucket_name}'.")
        return len(contents)
    else:
        raw_md_dir = Path("data/raw/markdown")
        if not raw_md_dir.exists():
            raw_md_dir.mkdir(parents=True, exist_ok=True)
        md_files = [f for f in raw_md_dir.glob("*.md") if f.name != ".gitkeep"]
        if not md_files:
            raise RuntimeError("No Bronze Markdown files found in data/raw/markdown/.")
        print(f">> [PREFECT TASK 1] Verified {len(md_files)} Bronze Markdown files locally.")
        return len(md_files)


@task(name="2. Verify and Load Silver Layer", retries=0)
def task_extract_silver(bronze_file_count: int, execute_llm: bool = False) -> int:
    """Task 2: Verifies or extracts Silver layer schemas."""
    print(">> [PREFECT TASK 2] Checking Silver Layer Parquet and Schema contracts...")
    extractions_dir = Path("data/extractions")
    silver_dir = Path("data/lakehouse/silver")
    comp_parquet = silver_dir / "competitions.parquet"

    if execute_llm:
        print(">> [PREFECT TASK 2] Executing live LLM schema extraction from Bronze...")
        extractions_dir.mkdir(parents=True, exist_ok=True)
        process_bronze_bucket(
            run_llm=True,
            output_dir=str(extractions_dir),
        )

    # Verify Silver Parquet layer
    if comp_parquet.exists():
        import duckdb
        escaped_path = str(comp_parquet).replace("\\", "/")
        count = duckdb.execute(f"SELECT COUNT(*) FROM read_parquet('{escaped_path}')").fetchone()[0]
        print(f">> [PREFECT TASK 2] Silver layer verified with {count} structured competitions at {comp_parquet}.")
        return count

    extracted_files = list(extractions_dir.glob("*.json")) if extractions_dir.exists() else []
    if not extracted_files:
        raise RuntimeError(
            f"No Silver data found: Neither Silver Parquet '{comp_parquet}' nor JSON extractions in '{extractions_dir}' exist."
        )
    return len(extracted_files)


@task(name="3. Materialize Gold DuckDB Analytics", retries=0)
def task_build_gold_duckdb(silver_count: int) -> str:
    """Task 3: Exports Silver Parquet and builds DuckDB Gold views for Metabase BI."""
    print(f">> [PREFECT TASK 3] Materializing Gold OLAP tables & views in DuckDB from {silver_count} Silver records...")
    run_gold_pipeline()
    db_path = Path("data/lakehouse/acdp.duckdb")
    print(f">> [PREFECT TASK 3] DuckDB Gold Layer updated successfully at {db_path}.")
    return str(db_path)


@flow(name="ACDP Medallion Lakehouse Flow", log_prints=True)
def medallion_lakehouse_flow(execute_llm: bool = False) -> dict:
    """Main Prefect workflow orchestrating the Medallion Data Pipeline."""
    print("🚀 Starting ACDP Medallion Lakehouse Orchestration Pipeline (Zero Fallback)...")

    # 1. Bronze Tier
    bronze_count = task_ingest_bronze()

    # 2. Silver Tier
    silver_count = task_extract_silver(bronze_count, execute_llm=execute_llm)

    # 3. Gold Tier & DuckDB Materialization
    gold_db_path = task_build_gold_duckdb(silver_count)

    print("🎉 ACDP Medallion Lakehouse Flow completed successfully!")
    return {
        "status": "SUCCESS",
        "bronze_files": bronze_count,
        "silver_records": silver_count,
        "gold_database": gold_db_path,
    }


if __name__ == "__main__":
    result = medallion_lakehouse_flow()
    print("\nPrefect Flow Execution Summary:", result)
