"""Module: Prefect 3.x Medallion Lakehouse Orchestration Pipeline (Cloudflare R2 Exclusive).

Orchestrates the ACDP data tiers strictly on Cloudflare R2 (Zero Local Persistence):
1. Task 1: Bronze Layer Verification (`s3://<bucket>/bronze/`).
2. Task 2: Silver Layer Structured Extraction (`s3://<bucket>/silver/extractions/`).
3. Task 3: Gold Layer Star Schema & Parquet Materialization (`s3://<bucket>/gold/`).
4. Task 4 (Optional): Qdrant Vector Indexing (`src/acdp/3_ingest_to_qdrant.py`).

Usage:
    # Run pipeline directly via CLI (verify Bronze/Silver + rebuild Gold on R2)
    uv run python src/acdp/flows/medallion_pipeline.py

    # Start local Prefect UI server on port 4200
    uv run prefect server start
"""

import importlib
import re

from prefect import flow, task

from acdp.config import settings

# Dynamic imports for modules with numeric prefixes
analytics_gold = importlib.import_module("acdp.4_analytics_gold")
run_gold_pipeline = analytics_gold.run_gold_pipeline

instruction_mod = importlib.import_module("acdp.2_instruction")
process_bronze_bucket = instruction_mod.process_bronze_bucket

SILVER_KEY_PATTERN = re.compile(
    r"^silver/extractions/([^/]+)/year=(\d{4})/month=(\d{2})/day=(\d{2})/(\d+)\.json$"
)


def _list_r2_keys(prefix: str) -> list[str]:
    """List non-directory object keys under an R2 prefix using pagination."""
    if not settings.bucket_name:
        raise RuntimeError("BUCKET_NAME is required in .env for Cloudflare R2 pipeline execution.")
    s3 = settings.create_r2_client()
    paginator = s3.get_paginator("list_objects_v2")
    keys: list[str] = []
    for page in paginator.paginate(Bucket=settings.bucket_name, Prefix=prefix):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            if not key.endswith("/") and obj.get("Size", 0) > 0:
                keys.append(key)
    return keys


@task(name="1. Verify Bronze Markdown on R2", retries=1, retry_delay_seconds=5)
def task_ingest_bronze() -> int:
    """Task 1: Verifies raw Markdown snapshots exist in Cloudflare R2 Bronze layer."""
    print(">> [PREFECT TASK 1] Checking Bronze Layer Markdown on Cloudflare R2...")
    keys = _list_r2_keys("bronze/")
    if not keys:
        raise RuntimeError(f"No Bronze layer objects found in Cloudflare R2 bucket '{settings.bucket_name}'.")
    print(f">> [PREFECT TASK 1] Verified {len(keys)} objects in s3://{settings.bucket_name}/bronze/.")
    return len(keys)


@task(name="2. Extract & Verify Silver JSON on R2", retries=0)
def task_extract_silver(bronze_file_count: int, execute_llm: bool = False) -> int:
    """Task 2: Runs Instructor extraction (optional) and verifies Silver JSON objects on R2."""
    print(f">> [PREFECT TASK 2] Checking Silver Layer on R2 (Bronze count={bronze_file_count})...")
    if execute_llm:
        print(">> [PREFECT TASK 2] Executing live LLM schema extraction from Bronze -> Silver R2...")
        process_bronze_bucket(run_llm=True)

    silver_keys = [k for k in _list_r2_keys("silver/extractions/") if SILVER_KEY_PATTERN.match(k)]
    if not silver_keys:
        raise RuntimeError(
            f"No Silver JSON extractions found in s3://{settings.bucket_name}/silver/extractions/. "
            "Run with execute_llm=True or execute src/acdp/2_instruction.py --extract first."
        )
    domains = {SILVER_KEY_PATTERN.match(k).group(1) for k in silver_keys}  # type: ignore[union-attr]
    print(
        f">> [PREFECT TASK 2] Verified {len(silver_keys)} Silver JSON objects "
        f"({len(domains)} unique domains) on R2."
    )
    return len(domains)


@task(name="3. Materialize Gold Parquet on R2", retries=0)
def task_build_gold_r2(silver_domain_count: int) -> str:
    """Task 3: Builds Kimball Star Schema in-memory DuckDB and exports Parquet directly to R2."""
    print(f">> [PREFECT TASK 3] Materializing Gold Star Schema Parquet on R2 from {silver_domain_count} domains...")
    run_gold_pipeline()
    gold_uri = f"s3://{settings.bucket_name}/gold/"
    print(f">> [PREFECT TASK 3] Gold Layer Parquet updated on Cloudflare R2 at {gold_uri}.")
    return gold_uri


@task(name="4. Ingest Bronze to Qdrant Vector DB", retries=0)
def task_ingest_qdrant(bronze_file_count: int) -> str:
    """Task 4 (Optional): Chunks Bronze Markdown and upserts BGE-M3 vectors to Qdrant Cloud."""
    print(f">> [PREFECT TASK 4] Ingesting Bronze snapshots ({bronze_file_count} objects) into Qdrant...")
    qdrant_mod = importlib.import_module("acdp.3_ingest_to_qdrant")
    qdrant_mod.ingest()
    return qdrant_mod.QDRANT_COLLECTION


@flow(name="ACDP Medallion Lakehouse Flow", log_prints=True)
def medallion_lakehouse_flow(execute_llm: bool = False, ingest_qdrant: bool = False) -> dict:
    """Main Prefect workflow orchestrating the R2-only Medallion Data Pipeline."""
    print("🚀 Starting ACDP Medallion Lakehouse Orchestration Pipeline (Cloudflare R2 Exclusive)...")

    # 1. Bronze Tier
    bronze_count = task_ingest_bronze()

    # 2. Silver Tier
    silver_domains = task_extract_silver(bronze_count, execute_llm=execute_llm)

    # 3. Gold Tier & R2 Parquet Materialization
    gold_uri = task_build_gold_r2(silver_domains)

    # 4. Optional Vector Indexing Tier
    qdrant_collection = task_ingest_qdrant(bronze_count) if ingest_qdrant else None

    print("🎉 ACDP Medallion Lakehouse Flow completed successfully!")
    return {
        "status": "SUCCESS",
        "bronze_objects": bronze_count,
        "silver_domains": silver_domains,
        "gold_uri": gold_uri,
        "qdrant_collection": qdrant_collection,
    }


if __name__ == "__main__":
    result = medallion_lakehouse_flow()
    print("\nPrefect Flow Execution Summary:", result)
