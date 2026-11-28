"""TASK-DQ-01: Bronze Layer Validation, Metadata Backfill & Idempotency CLI (ACDP v2).

Validates the Bronze layer on Cloudflare R2 (`s3://<bucket>/bronze/`) across 7 gates:
1. Key Taxonomy (`bronze/{domain}/year=YYYY/month=MM/day=DD/{ts}.html`)
2. Completeness & Non-Empty Payload (`size_bytes > 0`, `text/html; charset=utf-8`)
3. Strict UTF-8 Encoding & `ACDP_PAGE_BOUNDARY` Integrity
4. Full Provenance Metadata (`content_hash`, `source_url`, `crawled_at`, `http_status`, ...)
5. Cryptographic SHA-256 Content Integrity (`computed_sha256 == metadata["content_hash"]`)
6. Uncontrolled Duplicate Snapshot Detection across `(domain, source_url, content_hash)`
7. Downstream Silver/Gold Parquet Provenance Traceability (`bronze_key` resolution)

Also provides Option A non-destructive metadata backfill (`--backfill-metadata`) and live
2-pass idempotent re-crawl + `IfNoneMatch="*"` immutability probe (`--verify-recrawl`).
"""

from __future__ import annotations

import argparse
import hashlib
import html as html_lib
import io
import json
import re
import sys
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any, Literal
from urllib.parse import urlparse

import httpx
import pyarrow.parquet as pq
from botocore.exceptions import ClientError

from acdp.config import settings
from acdp.v2.bronze_crawl import (
    BRONZE_HTML_KEY_RE,
    REQUIRED_PROVENANCE_KEYS,
    compute_content_sha256,
    find_latest_bronze_snapshot,
    sanitize_s3_meta_value,
    upload_to_bronze_with_result,
)

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BRONZE_LEGACY_KEY_RE = re.compile(
    r"^bronze/([^/]+)/year=(\d{4})/month=(\d{2})/day=(\d{2})/(\d+)$"
)
PAGE_BOUNDARY_URL_RE = re.compile(r'<!--\s*ACDP_PAGE_BOUNDARY\s+url="([^"]*)"\s*-->')
HEX64_RE = re.compile(r"^[0-9a-f]{64}$")


@dataclass
class BronzeObjectAudit:
    """Audit result for a single Bronze object on Cloudflare R2."""

    key: str
    tier: Literal["v2_html", "v1_legacy", "system"]
    domain: str
    size_bytes: int
    etag: str | None = None
    last_modified: str | None = None
    content_type: str | None = None
    key_taxonomy_valid: bool = True
    non_empty: bool = True
    utf8_valid: bool = True
    page_boundary_count: int = 0
    extracted_boundary_url: str | None = None
    computed_sha256: str | None = None
    metadata_content_hash: str | None = None
    hash_matches: bool | None = None
    source_url: str | None = None
    crawled_at: str | None = None
    http_status: str | None = None
    metadata_complete: bool = True
    missing_metadata_keys: list[str] = field(default_factory=list)
    issues: list[str] = field(default_factory=list)


@dataclass
class DownstreamTraceabilityAudit:
    """Lineage verification from Silver/Gold/Qdrant back to Bronze object keys."""

    silver_rows: int = 0
    silver_with_bronze_key: int = 0
    silver_resolved_in_bronze: int = 0
    silver_dangling_keys: list[str] = field(default_factory=list)
    gold_rows: int = 0
    gold_linked_to_silver: int = 0
    qdrant_checked: bool = False
    qdrant_points_total: int = 0
    qdrant_sample_checked: int = 0
    qdrant_sample_with_bronze_key: int = 0
    issues: list[str] = field(default_factory=list)


@dataclass
class BronzeValidationReport:
    """Aggregate Bronze DQ validation report across all v2 HTML, legacy, and system objects."""

    bucket: str
    audited_at_utc: str
    total_objects: int
    v2_html_count: int
    v1_legacy_count: int
    system_count: int
    v2_total_bytes: int
    v2_unique_domains: int
    taxonomy_pass_count: int
    non_empty_pass_count: int
    utf8_pass_count: int
    boundary_pass_count: int
    provenance_pass_count: int
    hash_integrity_pass_count: int
    provenance_pass_rate: float
    utf8_pass_rate: float
    hash_integrity_pass_rate: float
    boundary_pass_rate: float
    taxonomy_pass_rate: float
    non_empty_pass_rate: float
    duplicate_content_groups: dict[str, list[str]]
    downstream: DownstreamTraceabilityAudit
    overall_status: Literal["PASS", "FAIL"]
    objects: list[BronzeObjectAudit] = field(default_factory=list)


def _list_all_bronze_objects(s3_client: Any, bucket_name: str) -> list[dict[str, Any]]:
    objs: list[dict[str, Any]] = []
    continuation_token: str | None = None
    while True:
        kwargs: dict[str, Any] = {"Bucket": bucket_name, "Prefix": "bronze/"}
        if continuation_token:
            kwargs["ContinuationToken"] = continuation_token
        resp = s3_client.list_objects_v2(**kwargs)
        if not isinstance(resp, dict):
            break
        contents = resp.get("Contents")
        if isinstance(contents, list):
            objs.extend(item for item in contents if isinstance(item, dict) and item.get("Key"))
        if not resp.get("IsTruncated"):
            break
        continuation_token = resp.get("NextContinuationToken")
        if not continuation_token:
            break
    return objs


def _classify_bronze_key(key: str) -> tuple[Literal["v2_html", "v1_legacy", "system"], str]:
    if key.startswith("bronze/_"):
        return "system", "_system"
    parts = key.split("/")
    domain = parts[1] if len(parts) > 1 else ""
    if key.endswith(".html"):
        return "v2_html", domain
    return "v1_legacy", domain


def _validate_taxonomy(key: str, tier: Literal["v2_html", "v1_legacy", "system"]) -> tuple[bool, int | None]:
    if tier == "system":
        return True, None
    pattern = BRONZE_HTML_KEY_RE if tier == "v2_html" else BRONZE_LEGACY_KEY_RE
    match = pattern.match(key)
    if not match:
        return False, None
    year, month, day, ts_str = int(match.group(2)), int(match.group(3)), int(match.group(4)), match.group(5)
    try:
        datetime(year, month, day, tzinfo=UTC)
    except ValueError:
        return False, None
    ts = int(ts_str)
    return ts > 0, ts


def _is_valid_iso8601(value: str) -> bool:
    if not value:
        return False
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
        return True
    except ValueError:
        return False


def _validate_v2_metadata(meta: dict[str, str], body_len: int | None) -> tuple[bool, list[str], list[str]]:
    missing: list[str] = []
    issues: list[str] = []
    for k in REQUIRED_PROVENANCE_KEYS:
        val = str(meta.get(k) or "").strip()
        if not val:
            missing.append(k)

    content_hash = str(meta.get("content_hash") or "").strip().lower()
    if content_hash and not HEX64_RE.match(content_hash):
        issues.append(f"invalid_content_hash_format:{content_hash[:20]}")

    source_url = str(meta.get("source_url") or "").strip()
    if source_url and not (source_url.startswith("http://") or source_url.startswith("https://")):
        issues.append(f"invalid_source_url:{source_url[:60]}")

    crawled_at = str(meta.get("crawled_at") or "").strip()
    if crawled_at and not _is_valid_iso8601(crawled_at):
        issues.append(f"invalid_crawled_at:{crawled_at}")

    if meta.get("layer") and meta.get("layer") != "bronze":
        issues.append(f"unexpected_layer:{meta.get('layer')}")
    if meta.get("format") and meta.get("format") != "raw_html":
        issues.append(f"unexpected_format:{meta.get('format')}")

    page_count_str = str(meta.get("page_count") or "").strip()
    if page_count_str and (not page_count_str.isdigit() or int(page_count_str) < 1):
        issues.append(f"invalid_page_count:{page_count_str}")

    content_bytes_str = str(meta.get("content_bytes") or "").strip()
    if content_bytes_str:
        if not content_bytes_str.isdigit() or int(content_bytes_str) <= 0:
            issues.append(f"invalid_content_bytes:{content_bytes_str}")
        elif body_len is not None and int(content_bytes_str) != body_len:
            issues.append(f"content_bytes_mismatch:{content_bytes_str}!={body_len}")

    return (len(missing) == 0 and len(issues) == 0), missing, issues


def _audit_downstream_traceability(
    s3_client: Any,
    bucket_name: str,
    bronze_keys: set[str],
    *,
    check_qdrant: bool = False,
) -> DownstreamTraceabilityAudit:
    audit = DownstreamTraceabilityAudit()
    silver_comp_keys: set[str] = set()

    try:
        silver_raw = s3_client.get_object(Bucket=bucket_name, Key="silver/competitions.parquet")["Body"].read()
        silver_tbl = pq.read_table(io.BytesIO(silver_raw))
        silver_rows = silver_tbl.to_pylist()
        audit.silver_rows = len(silver_rows)
        for row in silver_rows:
            comp_key = row.get("competition_key")
            if comp_key:
                silver_comp_keys.add(str(comp_key))
            bk = row.get("bronze_key")
            if bk:
                audit.silver_with_bronze_key += 1
                if str(bk) in bronze_keys:
                    audit.silver_resolved_in_bronze += 1
                else:
                    audit.silver_dangling_keys.append(str(bk))
            else:
                audit.issues.append(f"silver_missing_bronze_key:{row.get('name', 'unknown')}")
        if audit.silver_dangling_keys:
            audit.issues.append(f"silver_dangling_bronze_keys:{len(audit.silver_dangling_keys)}")
    except ClientError as exc:
        code = str(exc.response.get("Error", {}).get("Code", ""))
        if code not in {"NoSuchKey", "404", "NotFound"}:
            audit.issues.append(f"silver_read_error:{code or exc}")
    except Exception as exc:  # noqa: BLE001
        audit.issues.append(f"silver_read_error:{exc}")

    try:
        gold_raw = s3_client.get_object(Bucket=bucket_name, Key="gold/dim_competition.parquet")["Body"].read()
        gold_tbl = pq.read_table(io.BytesIO(gold_raw))
        gold_rows = gold_tbl.to_pylist()
        audit.gold_rows = len(gold_rows)
        for row in gold_rows:
            ck = str(row.get("competition_key") or "")
            if ck and (not silver_comp_keys or ck in silver_comp_keys):
                audit.gold_linked_to_silver += 1
            else:
                audit.issues.append(f"gold_unlinked_competition_key:{ck}")
    except ClientError as exc:
        code = str(exc.response.get("Error", {}).get("Code", ""))
        if code not in {"NoSuchKey", "404", "NotFound"}:
            audit.issues.append(f"gold_read_error:{code or exc}")
    except Exception as exc:  # noqa: BLE001
        audit.issues.append(f"gold_read_error:{exc}")

    if check_qdrant:
        try:
            from qdrant_client import QdrantClient

            qc = QdrantClient(url=settings.get_qdrant_url(), api_key=settings.get_qdrant_api_key(), timeout=15)
            col = settings.get_qdrant_collection()
            info = qc.get_collection(col)
            pts, _ = qc.scroll(collection_name=col, limit=50, with_payload=True, with_vectors=False)
            audit.qdrant_checked = True
            audit.qdrant_points_total = int(getattr(info, "points_count", 0) or 0)
            audit.qdrant_sample_checked = len(pts)
            for pt in pts:
                meta = (pt.payload or {}).get("metadata") or {}
                if meta.get("bronze_key") or meta.get("source_key"):
                    audit.qdrant_sample_with_bronze_key += 1
        except Exception as exc:  # noqa: BLE001
            audit.issues.append(f"qdrant_check_error:{exc}")

    return audit


def audit_bronze_bucket(
    s3_client: Any | None = None,
    bucket_name: str | None = None,
    *,
    verify_hashes: bool = True,
    check_downstream: bool = True,
    check_qdrant: bool = False,
) -> BronzeValidationReport:
    """Audit all Bronze objects on Cloudflare R2 for completeness, immutability, provenance, and lineage."""
    client = s3_client or settings.create_r2_client()
    bucket = bucket_name or settings.bucket_name
    raw_objects = _list_all_bronze_objects(client, bucket)

    audits: list[BronzeObjectAudit] = []
    v2_objects: list[BronzeObjectAudit] = []
    v1_count = 0
    sys_count = 0
    dup_buckets: dict[tuple[str, str, str], list[str]] = defaultdict(list)

    for obj in raw_objects:
        key = str(obj["Key"])
        tier, domain = _classify_bronze_key(key)
        size_bytes = int(obj.get("Size", 0))
        etag = obj.get("ETag")
        last_mod = obj.get("LastModified")
        last_mod_str = last_mod.isoformat() if hasattr(last_mod, "isoformat") else (str(last_mod) if last_mod else None)

        if tier == "v1_legacy":
            v1_count += 1
            audits.append(
                BronzeObjectAudit(
                    key=key,
                    tier=tier,
                    domain=domain,
                    size_bytes=size_bytes,
                    etag=etag,
                    last_modified=last_mod_str,
                )
            )
            continue

        if tier == "system":
            sys_count += 1
            audits.append(
                BronzeObjectAudit(
                    key=key,
                    tier=tier,
                    domain=domain,
                    size_bytes=size_bytes,
                    etag=etag,
                    last_modified=last_mod_str,
                )
            )
            continue

        head = client.head_object(Bucket=bucket, Key=key)
        meta = {str(k).lower(): str(v) for k, v in ((head.get("Metadata") or {}) if isinstance(head, dict) else {}).items()}
        content_type = str(head.get("ContentType") or "") if isinstance(head, dict) else ""

        taxonomy_ok, _ = _validate_taxonomy(key, tier)
        non_empty = size_bytes > 0
        issues: list[str] = []
        if not taxonomy_ok:
            issues.append("invalid_bronze_key_taxonomy")
        if not non_empty:
            issues.append("zero_byte_payload")
        if "text/html" not in content_type.lower() or "utf-8" not in content_type.lower():
            issues.append(f"unexpected_content_type:{content_type}")

        computed_sha256: str | None = None
        utf8_valid = True
        boundary_count = 0
        extracted_boundary_url: str | None = None
        body_len: int | None = None

        if verify_hashes:
            body = client.get_object(Bucket=bucket, Key=key)["Body"].read()
            body_len = len(body)
            non_empty = body_len > 0 and len(body.strip()) > 0
            if not non_empty and "zero_byte_payload" not in issues:
                issues.append("whitespace_or_empty_payload")
            computed_sha256 = hashlib.sha256(body).hexdigest()
            try:
                text = body.decode("utf-8", errors="strict")
                matches = PAGE_BOUNDARY_URL_RE.findall(text)
                boundary_count = len(matches)
                if matches:
                    extracted_boundary_url = html_lib.unescape(matches[0]).strip()
                else:
                    issues.append("missing_page_boundary_marker")
            except UnicodeDecodeError as exc:
                utf8_valid = False
                issues.append(f"invalid_utf8:{exc}")

        meta_complete, missing_keys, meta_issues = _validate_v2_metadata(meta, body_len)
        issues.extend(meta_issues)
        if missing_keys:
            issues.append(f"missing_metadata:{','.join(missing_keys)}")

        meta_hash = meta.get("content_hash")
        hash_matches: bool | None = None
        if computed_sha256 is not None:
            hash_matches = bool(meta_hash and computed_sha256 == meta_hash.lower())
            if meta_hash and not hash_matches:
                issues.append("sha256_integrity_mismatch")

        source_url = meta.get("source_url") or extracted_boundary_url or f"https://{domain}/"
        if computed_sha256:
            dup_buckets[(domain, source_url.strip().rstrip("/").lower(), computed_sha256)].append(key)

        record = BronzeObjectAudit(
            key=key,
            tier=tier,
            domain=domain,
            size_bytes=body_len if body_len is not None else size_bytes,
            etag=etag,
            last_modified=last_mod_str,
            content_type=content_type,
            key_taxonomy_valid=taxonomy_ok,
            non_empty=non_empty,
            utf8_valid=utf8_valid,
            page_boundary_count=boundary_count,
            extracted_boundary_url=extracted_boundary_url,
            computed_sha256=computed_sha256,
            metadata_content_hash=meta_hash,
            hash_matches=hash_matches,
            source_url=meta.get("source_url"),
            crawled_at=meta.get("crawled_at"),
            http_status=meta.get("http_status"),
            metadata_complete=meta_complete,
            missing_metadata_keys=missing_keys,
            issues=issues,
        )
        audits.append(record)
        v2_objects.append(record)

    dup_groups: dict[str, list[str]] = {}
    dup_key_set: set[str] = set()
    for (domain, _url, digest), keys in dup_buckets.items():
        if len(keys) > 1:
            sorted_keys = sorted(keys)
            dup_groups[f"{domain}:{digest[:12]}"] = sorted_keys
            dup_key_set.update(sorted_keys[1:])
    for obj in v2_objects:
        if obj.key in dup_key_set:
            obj.issues.append("uncontrolled_duplicate_snapshot")

    bronze_keys = {o.key for o in audits if o.tier in {"v2_html", "v1_legacy"}}
    downstream = (
        _audit_downstream_traceability(client, bucket, bronze_keys, check_qdrant=check_qdrant)
        if check_downstream
        else DownstreamTraceabilityAudit()
    )

    n_v2 = len(v2_objects)
    taxonomy_ok_cnt = sum(1 for o in v2_objects if o.key_taxonomy_valid)
    non_empty_cnt = sum(1 for o in v2_objects if o.non_empty)
    utf8_cnt = sum(1 for o in v2_objects if o.utf8_valid)
    boundary_cnt = sum(1 for o in v2_objects if ((o.page_boundary_count >= 1) if verify_hashes else True))
    provenance_cnt = sum(1 for o in v2_objects if o.metadata_complete)
    hash_ok_cnt = sum(1 for o in v2_objects if o.hash_matches is True)

    def _rate(num: int, den: int) -> float:
        return round((num / den) * 100.0, 2) if den > 0 else 100.0

    has_any_failure = (
        n_v2 == 0
        or any(bool(o.issues) for o in v2_objects)
        or bool(dup_groups)
        or bool(downstream.issues)
    )

    return BronzeValidationReport(
        bucket=bucket,
        audited_at_utc=datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        total_objects=len(audits),
        v2_html_count=n_v2,
        v1_legacy_count=v1_count,
        system_count=sys_count,
        v2_total_bytes=sum(o.size_bytes for o in v2_objects),
        v2_unique_domains=len({o.domain for o in v2_objects}),
        taxonomy_pass_count=taxonomy_ok_cnt,
        non_empty_pass_count=non_empty_cnt,
        utf8_pass_count=utf8_cnt,
        boundary_pass_count=boundary_cnt,
        provenance_pass_count=provenance_cnt,
        hash_integrity_pass_count=hash_ok_cnt,
        provenance_pass_rate=_rate(provenance_cnt, n_v2),
        utf8_pass_rate=_rate(utf8_cnt, n_v2),
        hash_integrity_pass_rate=_rate(hash_ok_cnt, n_v2),
        boundary_pass_rate=_rate(boundary_cnt, n_v2),
        taxonomy_pass_rate=_rate(taxonomy_ok_cnt, n_v2),
        non_empty_pass_rate=_rate(non_empty_cnt, n_v2),
        duplicate_content_groups=dup_groups,
        downstream=downstream,
        overall_status="FAIL" if has_any_failure else "PASS",
        objects=audits,
    )


def backfill_v2_bronze_metadata(
    s3_client: Any | None = None,
    bucket_name: str | None = None,
    *,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Option A non-destructive metadata backfill for existing v2 `.html` Bronze objects.

    Uses S3 `copy_object(..., MetadataDirective="REPLACE")` and verifies byte-for-byte
    SHA-256 parity before and after every update. Never modifies legacy v1 `.md` files.
    """
    client = s3_client or settings.create_r2_client()
    bucket = bucket_name or settings.bucket_name
    raw_objects = _list_all_bronze_objects(client, bucket)

    total_v2 = 0
    already_compliant = 0
    backfilled = 0
    byte_verified_ok = 0
    errors: list[str] = []
    updated_keys: list[str] = []

    for obj in raw_objects:
        key = str(obj["Key"])
        tier, domain = _classify_bronze_key(key)
        if tier != "v2_html":
            continue
        total_v2 += 1

        head = client.head_object(Bucket=bucket, Key=key)
        existing_meta = {
            str(k).lower(): str(v)
            for k, v in ((head.get("Metadata") or {}) if isinstance(head, dict) else {}).items()
        }
        body_before = client.get_object(Bucket=bucket, Key=key)["Body"].read()
        sha_before = hashlib.sha256(body_before).hexdigest()

        meta_ok, _missing, _issues = _validate_v2_metadata(existing_meta, len(body_before))
        if meta_ok and existing_meta.get("content_hash") == sha_before:
            already_compliant += 1
            byte_verified_ok += 1
            continue

        try:
            text_before = body_before.decode("utf-8", errors="strict")
        except UnicodeDecodeError as exc:
            errors.append(f"{key}: invalid UTF-8 ({exc})")
            continue

        boundary_matches = PAGE_BOUNDARY_URL_RE.findall(text_before)
        extracted_url = (
            html_lib.unescape(boundary_matches[0]).strip()
            if boundary_matches
            else f"https://{domain}/"
        )
        match = BRONZE_HTML_KEY_RE.match(key)
        if match:
            ts = int(match.group(5))
            crawled_at_iso = datetime.fromtimestamp(ts, tz=UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        else:
            crawled_at_iso = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

        page_count = existing_meta.get("page_count") or str(max(1, len(boundary_matches)))
        new_meta = {
            "source": sanitize_s3_meta_value(existing_meta.get("source") or domain),
            "source_url": sanitize_s3_meta_value(existing_meta.get("source_url") or extracted_url),
            "layer": "bronze",
            "format": "raw_html",
            "page_count": str(page_count),
            "content_hash": sha_before,
            "content_bytes": str(len(body_before)),
            "crawled_at": existing_meta.get("crawled_at") or crawled_at_iso,
            "http_status": existing_meta.get("http_status") or "inferred_200",
            "crawl_mode": existing_meta.get("crawl_mode") or "backfill",
            "metadata_backfilled": "true",
        }

        if dry_run:
            backfilled += 1
            byte_verified_ok += 1
            updated_keys.append(key)
            continue

        client.copy_object(
            Bucket=bucket,
            CopySource={"Bucket": bucket, "Key": key},
            Key=key,
            MetadataDirective="REPLACE",
            ContentType="text/html; charset=utf-8",
            Metadata=new_meta,
        )

        body_after = client.get_object(Bucket=bucket, Key=key)["Body"].read()
        sha_after = hashlib.sha256(body_after).hexdigest()
        head_after = client.head_object(Bucket=bucket, Key=key)
        after_meta = {
            str(k).lower(): str(v)
            for k, v in ((head_after.get("Metadata") or {}) if isinstance(head_after, dict) else {}).items()
        }
        after_ok, missing_after, issues_after = _validate_v2_metadata(after_meta, len(body_after))

        if sha_after != sha_before:
            errors.append(f"{key}: SHA-256 changed after backfill ({sha_before} != {sha_after})")
            continue
        if not after_ok:
            errors.append(f"{key}: metadata still invalid after backfill ({missing_after}, {issues_after})")
            continue

        backfilled += 1
        byte_verified_ok += 1
        updated_keys.append(key)

    return {
        "dry_run": dry_run,
        "bucket": bucket,
        "total_v2": total_v2,
        "already_compliant": already_compliant,
        "backfilled": backfilled,
        "byte_verified_ok": byte_verified_ok,
        "errors": errors,
        "updated_keys": updated_keys,
    }


def _count_domain_html_objects(s3_client: Any, bucket_name: str, domain: str) -> int:
    prefix = f"bronze/{domain}/"
    count = 0
    continuation_token: str | None = None
    while True:
        kwargs: dict[str, Any] = {"Bucket": bucket_name, "Prefix": prefix}
        if continuation_token:
            kwargs["ContinuationToken"] = continuation_token
        resp = s3_client.list_objects_v2(**kwargs)
        if not isinstance(resp, dict):
            break
        for obj in resp.get("Contents") or []:
            if BRONZE_HTML_KEY_RE.match(str(obj.get("Key", ""))):
                count += 1
        if not resp.get("IsTruncated"):
            break
        continuation_token = resp.get("NextContinuationToken")
        if not continuation_token:
            break
    return count


def verify_idempotent_recrawl(
    url: str,
    s3_client: Any | None = None,
    bucket_name: str | None = None,
) -> dict[str, Any]:
    """Run live 2-pass idempotent upload check and R2 `IfNoneMatch='*'` 412 immutability probe."""
    client = s3_client or settings.create_r2_client()
    bucket = bucket_name or settings.bucket_name
    domain = urlparse(url).netloc or url

    snap = find_latest_bronze_snapshot(client, bucket, domain, source_url=url)
    if snap:
        target_key = str(snap["key"])
        raw_bytes = client.get_object(Bucket=bucket, Key=target_key)["Body"].read()
        html_content = raw_bytes.decode("utf-8", errors="strict")
        source_mode = "existing_r2_snapshot"
    else:
        resp = httpx.get(url, follow_redirects=True, timeout=20.0)
        resp.raise_for_status()
        html_content = f'<!-- ACDP_PAGE_BOUNDARY url="{url}" -->\n{resp.text}'
        source_mode = "live_http_fetch"

    _, expected_sha256, _ = compute_content_sha256(html_content)
    count_before = _count_domain_html_objects(client, bucket, domain)

    pass1 = upload_to_bronze_with_result(
        html_content,
        url,
        http_status=200,
        crawl_mode="verify_recrawl",
        s3_client=client,
    )
    count_after_pass1 = _count_domain_html_objects(client, bucket, domain)

    pass2 = upload_to_bronze_with_result(
        html_content,
        url,
        http_status=200,
        crawl_mode="verify_recrawl",
        s3_client=client,
    )
    count_after_pass2 = _count_domain_html_objects(client, bucket, domain)

    probe_key = pass2.existing_key or pass1.bronze_key or pass1.existing_key
    probe_blocked = False
    probe_error_code = ""
    probe_http_status: int | None = None

    if probe_key:
        try:
            client.put_object(
                Bucket=bucket,
                Key=probe_key,
                Body=b"<!-- overwrite-probe -->",
                ContentType="text/html; charset=utf-8",
                IfNoneMatch="*",
            )
        except ClientError as exc:
            probe_blocked = True
            err = exc.response.get("Error", {}) if isinstance(exc.response, dict) else {}
            probe_error_code = str(err.get("Code", ""))
            probe_http_status = (
                exc.response.get("ResponseMetadata", {}).get("HTTPStatusCode")
                if isinstance(exc.response, dict)
                else None
            )

        after_probe_bytes = client.get_object(Bucket=bucket, Key=probe_key)["Body"].read()
        probe_intact = hashlib.sha256(after_probe_bytes).hexdigest() == expected_sha256
    else:
        probe_intact = False

    idempotent_ok = (
        pass2.status == "skipped_unchanged"
        and count_after_pass2 == count_after_pass1
        and probe_blocked
        and probe_intact
    )
    return {
        "url": url,
        "domain": domain,
        "source_mode": source_mode,
        "expected_sha256": expected_sha256,
        "count_before": count_before,
        "count_after_pass1": count_after_pass1,
        "count_after_pass2": count_after_pass2,
        "pass1_status": pass1.status,
        "pass1_key": pass1.bronze_key or pass1.existing_key,
        "pass2_status": pass2.status,
        "pass2_existing_key": pass2.existing_key,
        "delta_objects_pass2": count_after_pass2 - count_after_pass1,
        "if_none_match_probe_key": probe_key,
        "if_none_match_blocked": probe_blocked,
        "if_none_match_error_code": probe_error_code,
        "if_none_match_http_status": probe_http_status,
        "target_object_intact_after_probe": probe_intact,
        "overall_status": "PASS" if idempotent_ok else "FAIL",
    }


def _save_audit_report_to_r2(s3_client: Any, bucket_name: str, report: BronzeValidationReport) -> str:
    ts = int(datetime.now(UTC).timestamp())
    key = f"bronze/_validation/audit_{ts}.json"
    payload = asdict(report)
    s3_client.put_object(
        Bucket=bucket_name,
        Key=key,
        Body=json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8"),
        ContentType="application/json; charset=utf-8",
        Metadata={"layer": "bronze", "type": "validation_audit", "status": report.overall_status},
    )
    return key


def _print_audit_summary(report: BronzeValidationReport) -> None:
    print("================ BRONZE LAYER VALIDATION AUDIT ================")
    print(f"Bucket          : s3://{report.bucket}/bronze/")
    print(f"Audited At (UTC): {report.audited_at_utc}")
    print(
        f"Objects         : {report.total_objects} total "
        f"(v2_html={report.v2_html_count} across {report.v2_unique_domains} domains, "
        f"v1_legacy={report.v1_legacy_count}, system={report.system_count})"
    )
    print(f"v2 Payload Size : {report.v2_total_bytes:,} B ({report.v2_total_bytes / (1024 * 1024):.3f} MB)")
    print(f"Key Taxonomy    : {report.taxonomy_pass_count}/{report.v2_html_count} ({report.taxonomy_pass_rate}%)")
    print(f"Non-Empty       : {report.non_empty_pass_count}/{report.v2_html_count} ({report.non_empty_pass_rate}%)")
    print(f"UTF-8 Strict    : {report.utf8_pass_count}/{report.v2_html_count} ({report.utf8_pass_rate}%)")
    print(f"Page Boundary   : {report.boundary_pass_count}/{report.v2_html_count} ({report.boundary_pass_rate}%)")
    print(f"Provenance Meta : {report.provenance_pass_count}/{report.v2_html_count} ({report.provenance_pass_rate}%)")
    print(f"SHA-256 Match   : {report.hash_integrity_pass_count}/{report.v2_html_count} ({report.hash_integrity_pass_rate}%)")
    print(f"Duplicate Groups: {len(report.duplicate_content_groups)}")
    print(
        f"Downstream Link : Silver {report.downstream.silver_resolved_in_bronze}/{report.downstream.silver_rows} -> Bronze | "
        f"Gold {report.downstream.gold_linked_to_silver}/{report.downstream.gold_rows} -> Silver"
    )
    print(f"Overall Status  : {report.overall_status}")
    if report.overall_status == "FAIL":
        for obj in report.objects:
            if obj.tier == "v2_html" and obj.issues:
                print(f"  [ISSUE] {obj.key}: {', '.join(obj.issues)}")
        for issue in report.downstream.issues:
            print(f"  [DOWNSTREAM ISSUE] {issue}")
    print("===============================================================")


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="ACDP v2 Bronze Layer Validation & Backfill CLI (TASK-DQ-01)")
    parser.add_argument("--audit", action="store_true", help="Audit all Bronze objects on Cloudflare R2.")
    parser.add_argument("--save-report", action="store_true", help="Upload audit JSON report to bronze/_validation/.")
    parser.add_argument("--no-downstream", action="store_true", help="Skip Silver/Gold Parquet traceability check.")
    parser.add_argument("--check-qdrant", action="store_true", help="Also inspect Qdrant sample lineage.")
    parser.add_argument("--backfill-metadata", action="store_true", help="Run Option A non-destructive metadata backfill.")
    parser.add_argument("--dry-run", action="store_true", help="Preview backfill changes without modifying R2.")
    parser.add_argument("--verify-recrawl", action="store_true", help="Run live 2-pass idempotency & IfNoneMatch probe.")
    parser.add_argument("--url", type=str, default="https://codetour.org/", help="Target URL for --verify-recrawl.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    if not (args.audit or args.backfill_metadata or args.verify_recrawl):
        args.audit = True

    s3_client = settings.create_r2_client()
    bucket = settings.bucket_name
    exit_code = 0

    if args.backfill_metadata:
        bf = backfill_v2_bronze_metadata(s3_client=s3_client, bucket_name=bucket, dry_run=args.dry_run)
        print("================ BRONZE METADATA BACKFILL (OPTION A) ================")
        print(json.dumps(bf, ensure_ascii=False, indent=2))
        if bf["errors"]:
            exit_code = 1

    if args.audit:
        report = audit_bronze_bucket(
            s3_client=s3_client,
            bucket_name=bucket,
            verify_hashes=True,
            check_downstream=not args.no_downstream,
            check_qdrant=args.check_qdrant,
        )
        _print_audit_summary(report)
        if args.save_report:
            report_key = _save_audit_report_to_r2(s3_client, bucket, report)
            print(f"Saved validation audit report -> s3://{bucket}/{report_key}")
        if report.overall_status != "PASS":
            exit_code = 1

    if args.verify_recrawl:
        res = verify_idempotent_recrawl(args.url, s3_client=s3_client, bucket_name=bucket)
        print("================ LIVE IDEMPOTENT RE-CRAWL & 412 PROBE ================")
        print(json.dumps(res, ensure_ascii=False, indent=2))
        if res["overall_status"] != "PASS":
            exit_code = 1

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
