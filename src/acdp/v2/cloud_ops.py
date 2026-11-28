"""TASK-CLD-06: Cloud Keep-Alive, Data Quality Audit & Weekly OLTP pg_dump Backup CLI.

Prevents R1 (Supabase 7d pause, Qdrant Cloud 7d suspend / 28d delete, HF Spaces 48h sleep),
audits Gold/Vector/OLTP data quality invariants, and runs IPv4 Session-Pooler pg_dump backups
to Cloudflare R2 private prefix (`backups/oltp/`) with 30-day retention pruning (R4).
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import subprocess
import sys
import time
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import httpx
from qdrant_client import QdrantClient
from sqlalchemy import text

from acdp.api.db.duckdb_client import _PARQUET_ENTITIES, get_duckdb_conn
from acdp.api.db.postgres import build_async_engine
from acdp.config import AppConfig, settings

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def ping_serving_api(
    api_url: str | None = None,
    timeout: float = 45.0,
    max_retries: int = 2,
    retry_delay: float = 5.0,
    strict_api: bool = False,
    http_client: httpx.Client | None = None,
) -> dict[str, Any]:
    """Wake Hugging Face Spaces / Koyeb / Render Serving API via GET /api/v1/health."""
    raw_url = (api_url or os.getenv("PUBLIC_API_URL") or settings.internal_api_url or "").strip().rstrip("/")
    if not raw_url or "localhost" in raw_url or "127.0.0.1" in raw_url:
        return {
            "status": "skipped",
            "reason": "PUBLIC_API_URL not configured (local URL skipped).",
        }

    health_url = f"{raw_url}/api/v1/health"
    client = http_client or httpx.Client(timeout=timeout, follow_redirects=True)
    close_after = http_client is None
    t0 = time.perf_counter()
    last_error = ""
    try:
        for attempt in range(1, max_retries + 1):
            try:
                resp = client.get(health_url)
                if resp.status_code in {502, 503, 504} and attempt < max_retries:
                    last_error = f"HTTP {resp.status_code}"
                    time.sleep(retry_delay)
                    continue
                resp.raise_for_status()
                payload = resp.json()
                latency_ms = round((time.perf_counter() - t0) * 1000, 1)
                return {
                    "status": "ok" if payload.get("status") == "ok" else "degraded",
                    "url": health_url,
                    "http_status": resp.status_code,
                    "attempts": attempt,
                    "latency_ms": latency_ms,
                    "api_health": payload,
                }
            except Exception as exc:
                last_error = str(exc)
                if attempt < max_retries:
                    time.sleep(retry_delay)
                    continue
        return {
            "status": "failed" if strict_api else "degraded",
            "url": health_url,
            "attempts": max_retries,
            "latency_ms": round((time.perf_counter() - t0) * 1000, 1),
            "error": last_error,
        }
    finally:
        if close_after:
            client.close()


async def _async_keep_alive_and_check_supabase(cfg: AppConfig) -> dict[str, Any]:
    t0 = time.perf_counter()
    engine = build_async_engine(cfg)
    expected_tables = ("users", "user_sessions", "saved_competitions", "chat_sessions", "chat_messages")
    table_counts: dict[str, int] = {}
    try:
        async with engine.connect() as conn:
            ping_val = (await conn.execute(text("SELECT 1"))).scalar()
            existing_rows = (
                await conn.execute(
                    text("SELECT tablename FROM pg_tables WHERE schemaname = current_schema()")
                )
            ).scalars().all()
            existing_set = set(existing_rows)
            for tbl in expected_tables:
                if tbl in existing_set:
                    cnt = (await conn.execute(text(f'SELECT COUNT(*) FROM "{tbl}"'))).scalar()
                    table_counts[tbl] = int(cnt or 0)
        latency_ms = round((time.perf_counter() - t0) * 1000, 1)
        missing_tables = [t for t in expected_tables if t not in table_counts]
        return {
            "status": "ok" if ping_val == 1 and not missing_tables else "degraded",
            "cloud_active": cfg.is_postgres_cloud_active(),
            "select_1": ping_val,
            "latency_ms": latency_ms,
            "table_counts": table_counts,
            "missing_tables": missing_tables,
        }
    except Exception as exc:
        return {
            "status": "failed",
            "cloud_active": cfg.is_postgres_cloud_active(),
            "latency_ms": round((time.perf_counter() - t0) * 1000, 1),
            "error": str(exc),
        }
    finally:
        await engine.dispose()


def keep_alive_and_check_supabase(cfg: AppConfig = settings) -> dict[str, Any]:
    """Execute SELECT 1 + OLTP table counts to prevent Supabase 7-day inactivity pause."""
    return asyncio.run(_async_keep_alive_and_check_supabase(cfg))


def keep_alive_and_check_qdrant(cfg: AppConfig = settings) -> dict[str, Any]:
    """Ping Qdrant Cloud via get_collection + scroll(limit=5) and verify vector/payload DQ."""
    t0 = time.perf_counter()
    endpoint = cfg.get_qdrant_url()
    collection_name = cfg.get_qdrant_collection()
    try:
        qc = QdrantClient(url=endpoint, api_key=cfg.get_qdrant_api_key(), timeout=20)
        info = qc.get_collection(collection_name)
        points, _ = qc.scroll(
            collection_name=collection_name,
            limit=5,
            with_payload=True,
            with_vectors=False,
        )
        points_count = int(getattr(info, "points_count", 0) or 0)
        vec_cfg = getattr(getattr(info, "config", None), "params", None)
        vec_params = getattr(vec_cfg, "vectors", None)
        vector_size = getattr(vec_params, "size", None)

        invalid_samples = 0
        for pt in points:
            payload = pt.payload or {}
            meta = payload.get("metadata") or {}
            content = str(payload.get("page_content") or "").strip()
            domain = str(meta.get("domain") or "").strip()
            source_url = str(meta.get("source_url") or "").strip()
            if not content or not domain or not source_url:
                invalid_samples += 1

        latency_ms = round((time.perf_counter() - t0) * 1000, 1)
        dq_ok = points_count > 0 and (vector_size in (None, 1024)) and invalid_samples == 0
        return {
            "status": "ok" if dq_ok else "degraded",
            "cloud_active": cfg.is_qdrant_cloud_active(),
            "collection": collection_name,
            "points_count": points_count,
            "vector_size": vector_size,
            "sampled_points": len(points),
            "invalid_samples": invalid_samples,
            "latency_ms": latency_ms,
        }
    except Exception as exc:
        return {
            "status": "failed",
            "cloud_active": cfg.is_qdrant_cloud_active(),
            "collection": collection_name,
            "latency_ms": round((time.perf_counter() - t0) * 1000, 1),
            "error": str(exc),
        }


def check_r2_gold_data_quality(cfg: AppConfig = settings) -> dict[str, Any]:
    """Verify all 15 Gold Parquets exist on R2 and pass DuckDB Star Schema DQ invariants."""
    t0 = time.perf_counter()
    bucket = cfg.bucket_name.strip().strip("/")
    if not bucket or not cfg.aws_endpoint_url or not cfg.aws_access_key_id:
        return {
            "status": "skipped",
            "reason": "Cloudflare R2 credentials not configured.",
        }

    try:
        r2 = cfg.create_r2_client()
        missing_parquets: list[str] = []
        total_gold_bytes = 0
        for entity in _PARQUET_ENTITIES:
            key = f"gold/{entity}.parquet"
            try:
                head = r2.head_object(Bucket=bucket, Key=key)
                total_gold_bytes += int(head.get("ContentLength", 0))
            except Exception:
                missing_parquets.append(key)

        with get_duckdb_conn() as con:
            dim_cnt = int(con.execute("SELECT COUNT(*) FROM dim_competition").fetchone()[0])
            mart_cnt = int(con.execute("SELECT COUNT(*) FROM mart_competition_explorer").fetchone()[0])
            kpi_cnt = int(con.execute("SELECT total_competitions FROM mart_kpi_overview LIMIT 1").fetchone()[0])
            null_url_cnt = int(
                con.execute(
                    "SELECT COUNT(*) FROM dim_competition "
                    "WHERE canonical_url IS NULL OR TRIM(canonical_url) = '' OR name IS NULL OR TRIM(name) = ''"
                ).fetchone()[0]
            )
            bridge_violations = int(
                con.execute(
                    """
                    SELECT COUNT(*) FROM (
                        SELECT competition_sk, ABS(SUM(allocation_weight) - 1.0) AS diff
                        FROM bridge_competition_domain
                        GROUP BY competition_sk
                        HAVING ABS(SUM(allocation_weight) - 1.0) > 0.001
                    )
                    """
                ).fetchone()[0]
            )

        latency_ms = round((time.perf_counter() - t0) * 1000, 1)
        dq_ok = (
            not missing_parquets
            and dim_cnt > 0
            and dim_cnt == mart_cnt == kpi_cnt
            and null_url_cnt == 0
            and bridge_violations == 0
        )
        return {
            "status": "ok" if dq_ok else "degraded",
            "bucket": bucket,
            "entities_present": len(_PARQUET_ENTITIES) - len(missing_parquets),
            "entities_expected": len(_PARQUET_ENTITIES),
            "missing_parquets": missing_parquets,
            "total_gold_kb": round(total_gold_bytes / 1024, 2),
            "dim_competition_count": dim_cnt,
            "mart_explorer_count": mart_cnt,
            "mart_kpi_total": kpi_cnt,
            "null_url_or_name_count": null_url_cnt,
            "bridge_weight_violations": bridge_violations,
            "latency_ms": latency_ms,
        }
    except Exception as exc:
        return {
            "status": "failed",
            "latency_ms": round((time.perf_counter() - t0) * 1000, 1),
            "error": str(exc),
        }


def run_oltp_pg_dump_backup(
    output_dir: Path,
    cfg: AppConfig = settings,
    upload_r2: bool = True,
    prune_old: bool = True,
    runner: Callable[[list[str]], subprocess.CompletedProcess[str]] | None = None,
    r2_client: Any | None = None,
) -> dict[str, Any]:
    """Run pg_dump --format=custom over IPv4 Session Pooler (:5432), upload to R2, and prune >30d."""
    t0 = time.perf_counter()
    output_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    dump_filename = f"acdp_oltp_{ts}.dump"
    manifest_filename = f"acdp_oltp_{ts}.manifest.json"
    dump_path = output_dir / dump_filename
    manifest_path = output_dir / manifest_filename

    db_url = cfg.get_pg_dump_database_url()
    cmd = [
        "pg_dump",
        "--format=custom",
        "--no-owner",
        "--no-acl",
        f"--file={dump_path}",
        db_url,
    ]
    exec_fn = runner or (lambda args: subprocess.run(args, check=True, capture_output=True, text=True))
    exec_fn(cmd)

    if not dump_path.exists() or dump_path.stat().st_size == 0:
        raise RuntimeError(f"pg_dump did not produce a non-empty backup file at {dump_path}")

    raw_bytes = dump_path.read_bytes()
    sha256_hex = hashlib.sha256(raw_bytes).hexdigest()
    size_bytes = len(raw_bytes)
    manifest = {
        "created_at_utc": datetime.now(UTC).isoformat(),
        "filename": dump_filename,
        "format": "custom",
        "size_bytes": size_bytes,
        "sha256": sha256_hex,
        "retention_days": cfg.oltp_backup_retention_days,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    prefix = cfg.oltp_backup_r2_prefix.strip().strip("/")
    uploaded_keys: list[str] = []
    pruned_keys: list[str] = []

    if upload_r2 and cfg.aws_endpoint_url and cfg.aws_access_key_id and cfg.bucket_name:
        client = r2_client or cfg.create_r2_client()
        bucket = cfg.bucket_name.strip().strip("/")
        dump_key = f"{prefix}/{dump_filename}"
        manifest_key = f"{prefix}/{manifest_filename}"
        client.upload_file(str(dump_path), bucket, dump_key)
        client.upload_file(str(manifest_path), bucket, manifest_key)
        uploaded_keys = [dump_key, manifest_key]

        if prune_old:
            cutoff = datetime.now(UTC) - timedelta(days=cfg.oltp_backup_retention_days)
            paginator = client.get_paginator("list_objects_v2")
            for page in paginator.paginate(Bucket=bucket, Prefix=f"{prefix}/"):
                for obj in page.get("Contents", []):
                    last_mod = obj.get("LastModified")
                    if last_mod is None:
                        continue
                    if last_mod.tzinfo is None:
                        last_mod = last_mod.replace(tzinfo=UTC)
                    if last_mod < cutoff:
                        client.delete_object(Bucket=bucket, Key=obj["Key"])
                        pruned_keys.append(obj["Key"])

    return {
        "status": "ok",
        "dump_path": str(dump_path),
        "manifest_path": str(manifest_path),
        "size_bytes": size_bytes,
        "sha256": sha256_hex,
        "uploaded_r2_keys": uploaded_keys,
        "pruned_r2_keys": pruned_keys,
        "latency_ms": round((time.perf_counter() - t0) * 1000, 1),
    }


def format_markdown_summary(report: dict[str, Any]) -> str:
    """Format keep-alive, Data Quality, and backup telemetry into GitHub Step Summary Markdown."""
    lines = [
        "## ACDP Cloud Keep-Alive, Data Quality & Backup Report (`TASK-CLD-06`)",
        "",
        f"- **Timestamp (UTC)**: `{report.get('timestamp_utc', '')}`",
        f"- **Overall Status**: `{report.get('overall_status', 'unknown')}`",
        "",
        "| Check | Status | Key Telemetry | Latency |",
        "| :--- | :---: | :--- | :---: |",
    ]
    for name, section in report.get("checks", {}).items():
        status = section.get("status", "unknown")
        latency = f"{section.get('latency_ms', '-')} ms" if "latency_ms" in section else "-"
        if name == "serving_api":
            detail = section.get("url") or section.get("reason", "-")
        elif name == "supabase_oltp":
            detail = f"SELECT 1={section.get('select_1')} | tables={section.get('table_counts', {})}"
        elif name == "qdrant_cloud":
            detail = (
                f"points={section.get('points_count', 0)} | dim={section.get('vector_size')} "
                f"| invalid_samples={section.get('invalid_samples', '-')}"
            )
        elif name == "r2_gold_dq":
            detail = (
                f"parquets={section.get('entities_present', 0)}/{section.get('entities_expected', 15)} "
                f"| dim={section.get('dim_competition_count', 0)} | bridge_bad={section.get('bridge_weight_violations', 0)}"
            )
        elif name == "oltp_pg_dump":
            detail = (
                f"size={section.get('size_bytes', 0)} B | sha256={str(section.get('sha256', ''))[:12]}... "
                f"| r2_keys={len(section.get('uploaded_r2_keys', []))}"
            )
        else:
            detail = section.get("error") or "-"
        lines.append(f"| `{name}` | `{status}` | {detail} | {latency} |")
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="ACDP Cloud Keep-Alive, Data Quality & Backup CLI")
    parser.add_argument("--keep-alive", action="store_true", help="Ping Serving API, Supabase OLTP, and Qdrant Cloud")
    parser.add_argument("--check-dq", action="store_true", help="Run Qdrant and Cloudflare R2 Gold Star Schema DQ checks")
    parser.add_argument("--backup-oltp", action="store_true", help="Run pg_dump --format=custom and upload to R2")
    parser.add_argument("--public-api-url", default="", help="Optional public FastAPI URL (HF Spaces / Koyeb)")
    parser.add_argument("--strict-api", action="store_true", help="Treat unreachable public API as hard failure")
    parser.add_argument("--output-dir", default="./backups", help="Directory to store pg_dump backup files")
    parser.add_argument("--summary-file", default="", help="Optional path to append Markdown summary (e.g., GITHUB_STEP_SUMMARY)")
    args = parser.parse_args(argv)

    if not (args.keep_alive or args.check_dq or args.backup_oltp):
        args.keep_alive = True
        args.check_dq = True

    checks: dict[str, Any] = {}
    if args.keep_alive:
        checks["serving_api"] = ping_serving_api(
            api_url=args.public_api_url or None,
            strict_api=args.strict_api,
        )
        checks["supabase_oltp"] = keep_alive_and_check_supabase(settings)
        checks["qdrant_cloud"] = keep_alive_and_check_qdrant(settings)
    elif args.check_dq:
        checks["qdrant_cloud"] = keep_alive_and_check_qdrant(settings)

    if args.check_dq:
        checks["r2_gold_dq"] = check_r2_gold_data_quality(settings)

    if args.backup_oltp:
        checks["oltp_pg_dump"] = run_oltp_pg_dump_backup(Path(args.output_dir), cfg=settings)

    has_failure = any(c.get("status") == "failed" for c in checks.values())
    has_degraded = any(c.get("status") == "degraded" for c in checks.values())
    overall = "failed" if has_failure else ("degraded" if has_degraded else "ok")

    report = {
        "timestamp_utc": datetime.now(UTC).isoformat(),
        "overall_status": overall,
        "checks": checks,
    }
    print(json.dumps(report, indent=2, ensure_ascii=False))

    if args.summary_file:
        summary_path = Path(args.summary_file)
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        with summary_path.open("a", encoding="utf-8") as fh:
            fh.write(format_markdown_summary(report) + "\n")

    return 1 if has_failure else 0


if __name__ == "__main__":
    raise SystemExit(main())
