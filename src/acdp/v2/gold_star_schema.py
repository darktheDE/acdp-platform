"""TASK-SLV-04 & TASK-GLD-02: Silver Parquet & Two-Tier Gold Star Schema (ACDP v2).

Implements:
- TASK-SLV-04 (G1–G8): Explicit PyArrow Silver Parquet exporter (`competitions.parquet`,
  `prizes.parquet`, `timeline_stages.parquet`) to Cloudflare R2 `silver/`.
- TASK-GLD-02 (A1–A4 from TASK-GLD-01): Two-Tier Gold Star Schema on Cloudflare R2 `gold/`:
  * A1: Removes duplicate `team_size_min` / `team_size_max` from `fact_competitions`
    (kept exclusively on `dim_competition` and surfaced in `mart_competition_explorer`).
  * A2: Slims `dim_competition` to 1NF filterable attributes (removes nested `VARCHAR[]`
    arrays and `challenge_overview`, moving them to OBT `mart_competition_explorer` via
    normalized `bridge_competition_organizer` + `dim_organizer` and staging text).
  * A4: Materializes strictly 15 Gold Parquet files on R2 (`9` Core + `6` Marts), removing
    the 6 legacy `gold_*.parquet` files (which remain available as virtual SQL views in
    `build_metabase_r2_init_sql()`).

Usage:
    uv run python -m acdp.v2.gold_star_schema --export-silver-r2 --build-gold-r2 --verify
"""

from __future__ import annotations

import argparse
import io
import json
import os
import re
from collections import defaultdict
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

import duckdb
import pyarrow as pa
import pyarrow.parquet as pq

from acdp.config import settings
from acdp.v2.data_contracts import (
    DEFAULT_REFERENCE_YEAR,
    DataContractViolationError,
    QualityGateReport,
    _build_gate_report,
    run_silver_quality_gate,
    validate_silver_records_pydantic,
    validate_silver_to_gold_gate,
)
from acdp.v2.schemas import (
    Competition,
    compute_competition_key,
    normalize_canonical_url,
    parse_date_value,
    slugify,
)

SILVER_KEY_PATTERN = re.compile(
    r"^silver/extractions/([^/]+)/year=(\d{4})/month=(\d{2})/day=(\d{2})/(\d+)\.json$"
)

SILVER_COMPETITIONS_ARROW_SCHEMA = pa.schema(
    [
        pa.field("competition_key", pa.string(), nullable=False),
        pa.field("name", pa.string(), nullable=False),
        pa.field("tagline", pa.string(), nullable=True),
        pa.field("url", pa.string(), nullable=False),
        pa.field("summary", pa.string(), nullable=False),
        pa.field("organizers", pa.list_(pa.string()), nullable=False),
        pa.field("partners_and_sponsors", pa.list_(pa.string()), nullable=False),
        pa.field("category", pa.list_(pa.string()), nullable=False),
        pa.field("target_audience", pa.string(), nullable=True),
        pa.field("team_size_min", pa.int32(), nullable=True),
        pa.field("team_size_max", pa.int32(), nullable=True),
        pa.field("is_team_required", pa.bool_(), nullable=False),
        pa.field("team_description", pa.string(), nullable=True),
        pa.field("is_individual_allowed", pa.bool_(), nullable=True),
        pa.field("eligibility_level", pa.string(), nullable=False),
        pa.field("allowed_majors", pa.list_(pa.string()), nullable=False),
        pa.field("required_skills", pa.list_(pa.string()), nullable=False),
        pa.field("mode", pa.string(), nullable=False),
        pa.field("location", pa.string(), nullable=True),
        pa.field("participation_fee", pa.string(), nullable=True),
        pa.field("total_prize_pool", pa.string(), nullable=True),
        pa.field("total_prize_vnd", pa.int64(), nullable=False),
        pa.field("registration_start", pa.string(), nullable=True),
        pa.field("registration_deadline", pa.string(), nullable=True),
        pa.field("registration_status", pa.string(), nullable=False),
        pa.field("event_start", pa.string(), nullable=True),
        pa.field("event_end", pa.string(), nullable=True),
        pa.field("team_registration_deadline", pa.string(), nullable=True),
        pa.field("registration_start_date", pa.date32(), nullable=True),
        pa.field("registration_deadline_date", pa.date32(), nullable=True),
        pa.field("event_start_date", pa.date32(), nullable=True),
        pa.field("event_end_date", pa.date32(), nullable=True),
        pa.field("team_registration_deadline_date", pa.date32(), nullable=True),
        pa.field("challenge_overview", pa.string(), nullable=True),
        pa.field("submission_platform", pa.string(), nullable=True),
        pa.field("official_rules_url", pa.string(), nullable=True),
        pa.field("organizer_contact", pa.string(), nullable=True),
        pa.field("requires_advisor", pa.bool_(), nullable=True),
        pa.field("source_url", pa.string(), nullable=True),
        pa.field("bronze_key", pa.string(), nullable=True),
        pa.field("extracted_at", pa.timestamp("us", tz="UTC"), nullable=True),
        pa.field("extractor_model", pa.string(), nullable=True),
        pa.field("schema_version", pa.string(), nullable=False),
    ]
)

SILVER_PRIZES_ARROW_SCHEMA = pa.schema(
    [
        pa.field("competition_key", pa.string(), nullable=False),
        pa.field("competition_name", pa.string(), nullable=False),
        pa.field("tier_rank", pa.int32(), nullable=False),
        pa.field("tier", pa.string(), nullable=False),
        pa.field("reward", pa.string(), nullable=False),
        pa.field("quantity", pa.int32(), nullable=False),
        pa.field("currency", pa.string(), nullable=False),
        pa.field("prize_type", pa.string(), nullable=False),
        pa.field("estimated_value_vnd", pa.int64(), nullable=False),
        pa.field("is_scholarship", pa.bool_(), nullable=False),
    ]
)

SILVER_TIMELINE_STAGES_ARROW_SCHEMA = pa.schema(
    [
        pa.field("competition_key", pa.string(), nullable=False),
        pa.field("competition_name", pa.string(), nullable=False),
        pa.field("stage_order", pa.int32(), nullable=False),
        pa.field("stage_name", pa.string(), nullable=False),
        pa.field("start_date", pa.string(), nullable=True),
        pa.field("end_date", pa.string(), nullable=True),
        pa.field("start_date_iso", pa.date32(), nullable=True),
        pa.field("end_date_iso", pa.date32(), nullable=True),
        pa.field("description", pa.string(), nullable=True),
    ]
)


def _parse_number_token(token: str) -> float:
    """Parse number string respecting thousand vs decimal dot/comma conventions."""
    clean = token.strip()
    if not clean:
        return 0.0

    if "." in clean and "," in clean:
        last_dot = clean.rfind(".")
        last_comma = clean.rfind(",")
        if last_dot > last_comma:
            dec_part = clean[last_dot + 1 :]
            if len(dec_part) == 3:
                return float(clean.replace(".", "").replace(",", ""))
            return float(clean.replace(",", ""))
        dec_part = clean[last_comma + 1 :]
        if len(dec_part) == 3:
            return float(clean.replace(".", "").replace(",", ""))
        return float(clean.replace(".", "").replace(",", "."))

    sep = "." if "." in clean else ("," if "," in clean else "")
    if sep:
        parts = clean.split(sep)
        if len(parts) > 2 or len(parts[-1]) == 3:
            return float(clean.replace(sep, ""))
        return float(clean.replace(sep, "."))

    return float(clean)


def parse_vnd_currency(val_str: str | None, usd_to_vnd_rate: int | None = None) -> int:
    """Parse Vietnamese and USD prize strings into integer VND."""
    if not val_str or not val_str.strip():
        return 0

    text = re.sub(r"\d+(?:[.,]\d+)?\s*%", " ", val_str.strip())
    lower = text.lower()
    rate = usd_to_vnd_rate if usd_to_vnd_rate is not None else settings.usd_to_vnd_rate

    ty_matches = re.findall(r"(\d[\d.,]*)\s*(?:tỷ|ty)\b", lower)
    if ty_matches:
        return round(max(_parse_number_token(m) for m in ty_matches) * 1_000_000_000)

    trieu_matches = re.findall(r"(\d[\d.,]*)\s*(?:triệu|trieu)\b", lower)
    if trieu_matches:
        return round(max(_parse_number_token(m) for m in trieu_matches) * 1_000_000)

    vnd_before_usd = False
    usd_pos = re.search(r"(\$|usd[tc]?)", lower)
    vnd_pos = re.search(r"(?:\d[\d.,]*\+*\s*(?:vnđ|vnd|đ|\bm\b|tr\b)|\b(?:vnđ|vnd)\s*\d)", lower)
    if vnd_pos and usd_pos and vnd_pos.start() < usd_pos.start():
        vnd_before_usd = True

    if usd_pos and not vnd_before_usd:
        usd_unit_mult = {"k": 1_000, "m": 1_000_000, "million": 1_000_000, "b": 1_000_000_000, "billion": 1_000_000_000}
        usd_matches = re.findall(
            r"(?:usdt?|usdc|\$)\s*(\d[\d.,]*)\s*(k|million|billion|m|b)?\b"
            r"|(\d[\d.,]*)\s*(k|million|billion|m|b)?\s*(?:usdt?|usdc|\$)",
            lower,
        )
        amounts_usd: list[float] = []
        for g1, u1, g2, u2 in usd_matches:
            num_tok = g1 or g2
            unit_tok = (u1 or u2 or "").lower()
            amounts_usd.append(_parse_number_token(num_tok) * usd_unit_mult.get(unit_tok, 1))

        if not amounts_usd or ("-" in lower or "to" in lower):
            raw_nums = re.findall(r"\d[\d.,]*", text)
            if raw_nums:
                amounts_usd.append(max(_parse_number_token(n) for n in raw_nums))

        if amounts_usd:
            return round(max(amounts_usd) * rate)

    m_matches = re.findall(r"(\d[\d.,]*)\s*(?:m(?:\b|\+)|tr\b)", lower)
    if m_matches:
        return round(max(_parse_number_token(m) for m in m_matches) * 1_000_000)

    if any(tok in lower for tok in ("vnd", "vnđ", "đ", "ngàn", "nghìn")):
        num_tokens = re.findall(r"\d[\d.,]*", text)
        if num_tokens:
            val = round(max(_parse_number_token(n) for n in num_tokens))
            return val if val >= 10_000 else 0

    return 0


def _compute_competition_total_prize_vnd(c: Competition) -> int:
    """Compute canonical total prize VND honoring total_prize_pool first then quantity-weighted prizes."""
    pool_vnd = parse_vnd_currency(c.total_prize_pool)
    if pool_vnd > 0:
        return pool_vnd

    tier_sum = 0
    for prize in c.prizes:
        unit_val = round(prize.estimated_value_vnd) if prize.estimated_value_vnd else parse_vnd_currency(prize.reward)
        tier_sum += max(unit_val, 0) * max(prize.quantity, 1)
    return tier_sum


def _competition_richness_score(c: Competition) -> tuple[int, int, int]:
    """Score record completeness for deterministic deduplication tie-breaking."""
    return (len(c.prizes), len(c.timeline_stages), len(c.summary or ""))


def parse_silver_key(fkey: str) -> dict[str, Any] | None:
    """Parse silver/extractions/<domain>/year=<Y>/month=<M>/day=<D>/<ts>.json."""
    match = SILVER_KEY_PATTERN.match(fkey)
    if not match:
        return None
    domain, year, month, day, ts = match.groups()
    return {
        "key": fkey,
        "domain": domain,
        "date": f"{year}-{month}-{day}",
        "timestamp": int(ts),
    }


def _parse_extracted_at(raw_ts: Any) -> datetime | None:
    if isinstance(raw_ts, datetime):
        return raw_ts.astimezone(UTC) if raw_ts.tzinfo else raw_ts.replace(tzinfo=UTC)
    if isinstance(raw_ts, str) and raw_ts.strip():
        try:
            dt = datetime.fromisoformat(raw_ts.strip().replace("Z", "+00:00"))
            return dt.astimezone(UTC) if dt.tzinfo else dt.replace(tzinfo=UTC)
        except ValueError:
            return None
    return None


def _deduplicate_competition_payloads(payloads: list[tuple[str, dict[str, Any]]]) -> list[Competition]:
    """Validate and deduplicate extracted competition records (v1 & v2) by canonical URL key."""
    dedup_by_key: dict[str, Competition] = {}
    for label, data in payloads:
        try:
            if not isinstance(data, dict):
                continue

            meta = data.get("_metadata") if isinstance(data.get("_metadata"), dict) else {}
            det = data.get("_deterministic") if isinstance(data.get("_deterministic"), dict) else {}

            raw_items: list[dict[str, Any]] = []
            if "results" in data:
                for item in data["results"]:
                    item_meta = item.get("_metadata") if isinstance(item.get("_metadata"), dict) else meta
                    item_det = item.get("_deterministic") if isinstance(item.get("_deterministic"), dict) else det
                    for comp_dict in item.get("competitions", []):
                        raw_items.append({"comp": comp_dict, "meta": item_meta, "det": item_det})
            elif "competitions" in data:
                for comp_dict in data.get("competitions", []):
                    raw_items.append({"comp": comp_dict, "meta": meta, "det": det})

            for entry in raw_items:
                raw_comp = dict(entry["comp"])
                m = entry["meta"]
                d = entry["det"]

                # Enrich lineage & deterministic fields if missing (backward compatible with v1 JSONs)
                if not raw_comp.get("source_url") and m.get("source_url"):
                    raw_comp["source_url"] = m["source_url"]
                if not raw_comp.get("bronze_key") and (m.get("source_key") or m.get("bronze_key")):
                    raw_comp["bronze_key"] = m.get("bronze_key") or m.get("source_key")
                if not raw_comp.get("extracted_at") and m.get("extracted_at"):
                    raw_comp["extracted_at"] = m["extracted_at"]
                if not raw_comp.get("official_rules_url"):
                    rules = d.get("official_rules_urls") or []
                    if isinstance(rules, list) and rules:
                        raw_comp["official_rules_url"] = rules[0]

                comp = Competition.model_validate(raw_comp)
                key = comp.competition_key or compute_competition_key(normalize_canonical_url(comp.url, comp.name))
                existing = dedup_by_key.get(key)
                if existing is None or _competition_richness_score(comp) > _competition_richness_score(existing):
                    dedup_by_key[key] = comp
        except (OSError, ValueError) as exc:
            print(f"[WARN] Failed to parse {label}: {exc}")

    return list(dedup_by_key.values())


def _extract_batch_sort_key(path: Path) -> tuple[int, str]:
    match = re.search(r"_(\d+)\.json$", path.name)
    ts = int(match.group(1)) if match else int(path.stat().st_mtime)
    return (ts, path.name)


def load_silver_competitions_from_r2(target_date: str | None = None) -> tuple[list[Competition], str]:
    """Load latest Silver JSON extraction per domain directly from Cloudflare R2."""
    if not settings.bucket_name:
        raise RuntimeError("BUCKET_NAME is required in .env to load Silver layer from Cloudflare R2.")

    s3 = settings.create_r2_client()
    paginator = s3.get_paginator("list_objects_v2")
    parsed_items: list[dict[str, Any]] = []

    for page in paginator.paginate(Bucket=settings.bucket_name, Prefix="silver/extractions/"):
        for obj in page.get("Contents", []):
            if obj.get("Size", 0) == 0:
                continue
            parsed = parse_silver_key(obj["Key"])
            if parsed is not None:
                parsed_items.append(parsed)

    if not parsed_items:
        raise RuntimeError(
            f"No Silver JSON extractions found in s3://{settings.bucket_name}/silver/extractions/."
        )

    if target_date:
        filtered = [it for it in parsed_items if it["date"] == target_date]
        if not filtered:
            available = sorted({it["date"] for it in parsed_items})
            raise RuntimeError(
                f"No Silver extractions found on R2 for date '{target_date}'. Available dates: {available}"
            )
        selected_pool = filtered
        scope_label = f"r2:silver/extractions@{target_date}"
    else:
        selected_pool = parsed_items
        latest_date = max(it["date"] for it in parsed_items)
        scope_label = f"r2:silver/extractions@latest({latest_date})"

    by_domain: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for it in selected_pool:
        by_domain[it["domain"]].append(it)

    latest_per_domain = [max(group, key=lambda x: x["timestamp"]) for group in by_domain.values()]
    payloads: list[tuple[str, dict[str, Any]]] = []
    for snap in sorted(latest_per_domain, key=lambda x: x["domain"]):
        body = s3.get_object(Bucket=settings.bucket_name, Key=snap["key"])["Body"]
        raw_text = body.read().decode("utf-8", errors="replace")
        try:
            payloads.append((snap["key"], json.loads(raw_text)))
        except json.JSONDecodeError as exc:
            print(f"[WARN] Failed to decode JSON {snap['key']}: {exc}")

    competitions = _deduplicate_competition_payloads(payloads)
    if not competitions:
        raise RuntimeError(
            f"No valid Silver extracted competition records found in s3://{settings.bucket_name}/silver/extractions/."
        )

    print(
        f">> [R2 SILVER LOADED] {len(competitions)} competitions from {len(latest_per_domain)} domains ({scope_label})"
    )
    return competitions, scope_label


def load_silver_competitions_with_source(
    extractions_dir: Path | None = None,
    target_date: str | None = None,
) -> tuple[list[Competition], str]:
    """Load Silver competitions from R2 by default, or from an explicit local directory in tests."""
    if extractions_dir is None:
        return load_silver_competitions_from_r2(target_date=target_date)

    if not extractions_dir.exists():
        raise RuntimeError(f"Silver extractions directory does not exist: '{extractions_dir.resolve()}'.")

    batch_files = sorted(extractions_dir.glob("extractions_*.json"), key=_extract_batch_sort_key)
    if batch_files:
        selected_files = [batch_files[-1]]
        source_label = batch_files[-1].name
    else:
        selected_files = sorted(
            jf for jf in extractions_dir.glob("*.json") if not jf.name.startswith("extractions_")
        )
        source_label = "single_domain_json_files" if selected_files else "empty"

    payloads: list[tuple[str, dict[str, Any]]] = []
    for jf in selected_files:
        try:
            with open(jf, encoding="utf-8") as f:
                payloads.append((jf.name, json.load(f)))
        except (OSError, ValueError) as exc:
            print(f"[WARN] Failed to parse {jf.name}: {exc}")

    competitions = _deduplicate_competition_payloads(payloads)
    if not competitions:
        raise RuntimeError(
            f"No valid Silver extracted competition records found in '{extractions_dir.resolve()}'."
        )
    return competitions, source_label


def export_silver_parquet(
    competitions: list[Competition],
    output_dir: Path | None = None,
    *,
    enforce_contract: bool = True,
    reference_year: int = DEFAULT_REFERENCE_YEAR,
    gate_report_path: Path | None = None,
) -> list[str | Path]:
    """Export Silver v2 competitions, prizes, and timeline_stages to ZSTD Parquet with explicit pa.schema."""
    comp_rows: list[dict[str, Any]] = []
    prize_rows: list[dict[str, Any]] = []
    stage_rows: list[dict[str, Any]] = []

    for c in competitions:
        canonical_url = normalize_canonical_url(c.url, c.name)
        comp_key = c.competition_key or compute_competition_key(canonical_url)
        calculated_prize_vnd = _compute_competition_total_prize_vnd(c)
        extracted_dt = _parse_extracted_at(c.extracted_at)

        comp_rows.append(
            {
                "competition_key": comp_key,
                "name": c.name,
                "tagline": c.tagline,
                "url": canonical_url,
                "summary": c.summary,
                "organizers": c.organizers,
                "partners_and_sponsors": c.partners_and_sponsors,
                "category": c.category,
                "target_audience": str(c.target_audience) if c.target_audience is not None else None,
                "team_size_min": c.team_size_min,
                "team_size_max": c.team_size_max,
                "is_team_required": bool(c.team_size_min and c.team_size_min > 1),
                "team_description": c.team_description,
                "is_individual_allowed": c.is_individual_allowed,
                "eligibility_level": c.eligibility_level,
                "allowed_majors": c.allowed_majors,
                "required_skills": c.required_skills,
                "mode": c.mode,
                "location": c.location,
                "participation_fee": c.participation_fee,
                "total_prize_pool": c.total_prize_pool,
                "total_prize_vnd": calculated_prize_vnd,
                "registration_start": c.registration_start,
                "registration_deadline": c.registration_deadline,
                "registration_status": c.registration_status,
                "event_start": c.event_start,
                "event_end": c.event_end,
                "team_registration_deadline": c.team_registration_deadline,
                "registration_start_date": c.registration_start_date or parse_date_value(c.registration_start),
                "registration_deadline_date": c.registration_deadline_date or parse_date_value(c.registration_deadline),
                "event_start_date": c.event_start_date or parse_date_value(c.event_start),
                "event_end_date": c.event_end_date or parse_date_value(c.event_end),
                "team_registration_deadline_date": (
                    c.team_registration_deadline_date or parse_date_value(c.team_registration_deadline)
                ),
                "challenge_overview": c.challenge_overview,
                "submission_platform": c.submission_platform,
                "official_rules_url": c.official_rules_url,
                "organizer_contact": c.organizer_contact,
                "requires_advisor": c.requires_advisor,
                "source_url": c.source_url,
                "bronze_key": c.bronze_key,
                "extracted_at": extracted_dt,
                "extractor_model": c.extractor_model,
                "schema_version": c.schema_version,
            }
        )

        for tier_idx, p in enumerate(c.prizes, start=1):
            val = round(p.estimated_value_vnd) if p.estimated_value_vnd is not None else parse_vnd_currency(p.reward)
            prize_rows.append(
                {
                    "competition_key": comp_key,
                    "competition_name": c.name,
                    "tier_rank": p.tier_rank or tier_idx,
                    "tier": p.tier,
                    "reward": p.reward,
                    "quantity": max(p.quantity, 1),
                    "currency": p.currency,
                    "prize_type": p.prize_type,
                    "estimated_value_vnd": max(val, 0),
                    "is_scholarship": p.is_scholarship,
                }
            )

        for stage_idx, st in enumerate(c.timeline_stages, start=1):
            stage_rows.append(
                {
                    "competition_key": comp_key,
                    "competition_name": c.name,
                    "stage_order": stage_idx,
                    "stage_name": st.stage_name,
                    "start_date": st.start_date,
                    "end_date": st.end_date,
                    "start_date_iso": st.start_date_iso or parse_date_value(st.start_date),
                    "end_date_iso": st.end_date_iso or parse_date_value(st.end_date),
                    "description": st.description,
                }
            )

    comp_table = pa.Table.from_pylist(comp_rows, schema=SILVER_COMPETITIONS_ARROW_SCHEMA)
    prize_table = pa.Table.from_pylist(prize_rows, schema=SILVER_PRIZES_ARROW_SCHEMA)
    stage_table = pa.Table.from_pylist(stage_rows, schema=SILVER_TIMELINE_STAGES_ARROW_SCHEMA)

    if enforce_contract:
        gate_report = run_silver_quality_gate(
            competitions,
            comp_table,
            prize_table,
            stage_table,
            gate_name="Silver Pre-Publish WAP Quality Gate",
            source_label="export_silver_parquet",
            reference_year=reference_year,
            min_records=1,
            fail_fast=False,
        )
        if gate_report_path is not None:
            gate_report_path.parent.mkdir(parents=True, exist_ok=True)
            gate_report_path.write_text(gate_report.model_dump_json(indent=2), encoding="utf-8")
        if gate_report.circuit_breaker_tripped:
            raise DataContractViolationError(gate_report)

    tables = (
        ("competitions.parquet", comp_table),
        ("prizes.parquet", prize_table),
        ("timeline_stages.parquet", stage_table),
    )

    if output_dir is not None:
        output_dir.mkdir(parents=True, exist_ok=True)
        exported: list[str | Path] = []
        for filename, table in tables:
            parquet_path = output_dir / filename
            pq.write_table(table, parquet_path, compression="zstd")
            print(f">> [SILVER PARQUET ZSTD] {len(table)} rows -> {parquet_path}")
            exported.append(parquet_path)
        return exported

    if not settings.bucket_name:
        raise RuntimeError("BUCKET_NAME is required to upload Silver Parquet to Cloudflare R2.")

    s3 = settings.create_r2_client()
    uploaded: list[str | Path] = []
    for filename, table in tables:
        buf = io.BytesIO()
        pq.write_table(table, buf, compression="zstd")
        key = f"silver/{filename}"
        s3.put_object(
            Bucket=settings.bucket_name,
            Key=key,
            Body=buf.getvalue(),
            ContentType="application/vnd.apache.parquet",
            Metadata={"layer": "silver", "schema_version": "2.0", "compression": "zstd"},
        )
        uri = f"s3://{settings.bucket_name}/{key}"
        uploaded.append(uri)
        print(f">> [R2 SILVER PARQUET ZSTD] {len(table)} rows ({len(buf.getvalue()):,} bytes) -> {uri}")

    return uploaded


def verify_silver_parquet_on_r2() -> dict[str, Any]:
    """Read back silver/*.parquet from Cloudflare R2 to verify schema, compression, and row counts."""
    if not settings.bucket_name:
        raise RuntimeError("BUCKET_NAME is required to verify Silver Parquet on R2.")
    s3 = settings.create_r2_client()
    report: dict[str, Any] = {}
    for filename in ("competitions.parquet", "prizes.parquet", "timeline_stages.parquet"):
        key = f"silver/{filename}"
        raw = s3.get_object(Bucket=settings.bucket_name, Key=key)["Body"].read()
        pf = pq.ParquetFile(io.BytesIO(raw))
        meta = pf.metadata
        codecs = sorted(
            {
                meta.row_group(rg).column(col).compression
                for rg in range(meta.num_row_groups)
                for col in range(meta.num_columns)
            }
        )
        report[filename] = {
            "key": key,
            "rows": meta.num_rows,
            "columns": meta.num_columns,
            "bytes": len(raw),
            "compressions": codecs,
        }
        print(
            f">> [VERIFY R2] {key}: rows={meta.num_rows}, cols={meta.num_columns}, "
            f"bytes={len(raw):,}, codecs={codecs}"
        )
    return report


# ---------------------------------------------------------------------------
# TASK-GLD-02: Two-Tier Gold Star Schema (9 Core + 6 OBT Marts = 15 Parquets)
# ---------------------------------------------------------------------------

CANONICAL_DOMAINS: tuple[tuple[int, str, str, int], ...] = (
    (1, "ai-data-science", "AI & Data Science", 1),
    (2, "web3-blockchain-fintech", "Web3, Blockchain & FinTech", 2),
    (3, "software-web-mobile", "Software, Web & Mobile", 3),
    (4, "security-iot-embedded", "Security, IoT & Embedded", 4),
    (5, "startup-design-interdisciplinary", "Startup, Design & Interdisciplinary", 5),
    (-1, "unclassified", "Chưa phân loại", 99),
)

MONTH_NAMES_VI: dict[int, str] = {
    1: "Tháng 1",
    2: "Tháng 2",
    3: "Tháng 3",
    4: "Tháng 4",
    5: "Tháng 5",
    6: "Tháng 6",
    7: "Tháng 7",
    8: "Tháng 8",
    9: "Tháng 9",
    10: "Tháng 10",
    11: "Tháng 11",
    12: "Tháng 12",
}

_DOMAIN_KEYWORD_RULES: list[tuple[int, tuple[str, ...]]] = [
    (
        2,
        (
            "web3",
            "blockchain",
            "defi",
            "crypto",
            "fintech",
            "smart contract",
            "ethereum",
            "solana",
            "aptos",
            "sui",
        ),
    ),
    (
        4,
        (
            "cybersecurity",
            "security",
            "ctf",
            "iot",
            "embedded",
            "hardware",
        ),
    ),
    (
        1,
        (
            "artificial intelligence",
            "machine learning",
            "data science",
            "data analytics",
            "business analytics",
            "business intelligence",
            "healthcare analytics",
            "natural language",
            "nlp",
            "llm",
            "language model",
            "generative ai",
            "agentic ai",
            "multimodal",
            "computer vision",
            "quantum",
            "deeptech",
            "deep tech",
            "robotics",
            "data driven",
        ),
    ),
    (
        3,
        (
            "software",
            "competitive programming",
            "algorithm",
            "full-stack",
            "fullstack",
            "mobile",
            "cloud",
            "devops",
            "gaming",
            "information systems",
            "web",
        ),
    ),
    (
        5,
        (
            "startup",
            "entrepreneurship",
            "ui/ux",
            "design",
            "business",
            "case study",
            "marketing",
            "innovation",
            "e-commerce",
            "ecommerce",
            "economics",
            "finance",
            "it consulting",
            "enterprise",
            "edtech",
            "digital transformation",
        ),
    ),
]

GOLD_ENTITIES: tuple[str, ...] = (
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


def resolve_date_sk(raw: str | None) -> int:
    """Convert raw date string to YYYYMMDD integer surrogate key, or -1 if unknown."""
    parsed = parse_date_value(raw)
    if parsed is None:
        return -1
    return parsed.year * 10000 + parsed.month * 100 + parsed.day


def map_academic_term(d: date) -> tuple[str, str]:
    """Map calendar date to HCM-UTE academic year and term ('HK1', 'HK2', 'Hè')."""
    if d.month >= 9:
        return f"{d.year}-{d.year + 1}", "HK1"
    if d.month <= 5:
        return f"{d.year - 1}-{d.year}", "HK2"
    return f"{d.year - 1}-{d.year}", "Hè"


def classify_competition_domains(categories: list[str]) -> list[int]:
    """Map raw category tags to deduplicated canonical domain_sk IDs (1..5 or -1)."""
    if not categories:
        return [-1]

    matched: set[int] = set()
    saw_hackathon = False
    saw_ideathon = False

    for raw_tag in categories:
        tag = raw_tag.strip().lower()
        if not tag:
            continue
        if tag == "hackathon":
            saw_hackathon = True
            continue
        if tag == "ideathon":
            saw_ideathon = True
            continue

        if re.search(r"\bai\b", tag):
            matched.add(1)

        for domain_sk, keywords in _DOMAIN_KEYWORD_RULES:
            if any(kw in tag for kw in keywords):
                matched.add(domain_sk)
                break

    if not matched:
        if saw_ideathon:
            matched.add(5)
        elif saw_hackathon:
            matched.add(3)
        else:
            return [-1]

    return sorted(matched)


def normalize_mode(mode: str | None) -> str:
    """Normalize competition mode to canonical UI labels."""
    return {"online": "Online", "offline": "Offline", "hybrid": "Hybrid"}.get(
        (mode or "").strip().lower(), "Unknown"
    )


def classify_team_profile(team_min: int | None, team_max: int | None) -> str:
    """Categorize team size rules into canonical dashboard profiles."""
    if team_min is None and team_max is None:
        return "Unspecified"
    effective_max = team_max if team_max is not None else team_min
    assert effective_max is not None
    if effective_max <= 1:
        return "Individual (1)"
    if effective_max <= 4:
        return "Small Team (2-4)"
    return "Large Team (5+)"


def is_participation_free(fee_raw: str | None) -> bool:
    """Determine if participation is free according to EC-G5."""
    if not fee_raw or not fee_raw.strip():
        return False
    lower = fee_raw.strip().lower()
    if any(tok in lower for tok in ("miễn phí", "free", "no fee", "không thu phí")):
        return True
    digits = re.sub(r"[^\d]", "", lower)
    return bool(digits and int(digits) == 0)


def classify_organizer_tier(name: str) -> str:
    """Classify organizer or sponsor name into ecosystem tier."""
    lower = name.lower()
    if any(
        tok in lower
        for tok in ("đại học", "university", "học viện", "khoa ", "rmit", "vinuni", "fulbright", "uit", "hcmute")
    ):
        return "University"
    if any(
        tok in lower
        for tok in ("bộ ", "sở ", "trung tâm", "hiệp hội", "đoàn", "people's committee", "vtv", "nic")
    ):
        return "Government/Agency"
    if any(
        tok in lower
        for tok in (
            "corp", "company", "group", "bank", "vietnam", "fpt", "vng", "naver", "zalo", "meta",
            "aws", "openai", "netcompany", "tinyfish", "sotatek", "axon", "cloudgo", "kyanon",
            "onyx", "shb", "bitmart", "tether", "fonos", "zalopay", "mindx", "masan",
        )
    ):
        return "Enterprise"
    if any(tok in lower for tok in ("club", "clb", "team", "community", "liên chi", "hội", "gdg", "vbi")):
        return "Community"
    return "Unknown"


def resolve_effective_registration_status(
    raw_status: str | None,
    registration_deadline: str | None,
    reference_date: date | None = None,
) -> str:
    """Normalize registration_status and auto-close 'open' contests past their deadline."""
    normalized = (raw_status or "unknown").strip().lower() or "unknown"
    if normalized == "open":
        deadline_dt = parse_date_value(registration_deadline)
        today_dt = reference_date or date.today()
        if deadline_dt is not None and deadline_dt < today_dt:
            return "closed"
    return normalized


def _create_star_schema_ddl(con: duckdb.DuckDBPyConnection) -> None:
    """Create Two-Tier Gold Kimball Star Schema (A1, A2 compliant) + internal staging text."""
    con.execute("""
        -- A2: Slim 1NF dim_competition (no nested VARCHAR[] arrays, no challenge_overview)
        CREATE OR REPLACE TABLE dim_competition (
            competition_sk BIGINT PRIMARY KEY,
            competition_key VARCHAR NOT NULL UNIQUE,
            name VARCHAR NOT NULL,
            tagline VARCHAR,
            canonical_url VARCHAR NOT NULL,
            summary VARCHAR,
            target_audience VARCHAR,
            team_size_min SMALLINT,
            team_size_max SMALLINT,
            team_description VARCHAR,
            team_profile VARCHAR NOT NULL,
            mode_raw VARCHAR,
            mode_canonical VARCHAR NOT NULL,
            location VARCHAR,
            participation_fee_raw VARCHAR,
            is_free BOOLEAN NOT NULL DEFAULT FALSE,
            total_prize_pool_raw VARCHAR,
            registration_status VARCHAR,
            submission_platform VARCHAR,
            registration_start_raw VARCHAR,
            registration_deadline_raw VARCHAR,
            event_start_raw VARCHAR,
            event_end_raw VARCHAR,
            source_batch_file VARCHAR NOT NULL,
            loaded_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        -- Internal staging table for long display text fed into OBT mart_competition_explorer (not exported to R2)
        CREATE OR REPLACE TABLE _stg_competition_text (
            competition_sk BIGINT PRIMARY KEY REFERENCES dim_competition(competition_sk),
            challenge_overview VARCHAR
        );

        CREATE OR REPLACE TABLE dim_date (
            date_sk INTEGER PRIMARY KEY,
            full_date DATE,
            year SMALLINT,
            quarter TINYINT,
            month TINYINT,
            month_name_vi VARCHAR,
            day_of_month TINYINT,
            academic_year VARCHAR NOT NULL,
            academic_term VARCHAR NOT NULL,
            date_known BOOLEAN NOT NULL
        );

        CREATE OR REPLACE TABLE dim_domain (
            domain_sk INTEGER PRIMARY KEY,
            domain_slug VARCHAR NOT NULL UNIQUE,
            domain_group VARCHAR NOT NULL,
            display_order TINYINT NOT NULL
        );

        CREATE OR REPLACE TABLE dim_organizer (
            organizer_sk INTEGER PRIMARY KEY,
            organizer_slug VARCHAR NOT NULL UNIQUE,
            organizer_name VARCHAR NOT NULL,
            organizer_tier VARCHAR NOT NULL
        );

        -- A1: fact_competitions contains additive/semi-additive measures only (no team_size_min/max)
        CREATE OR REPLACE TABLE fact_competitions (
            competition_sk BIGINT PRIMARY KEY REFERENCES dim_competition(competition_sk),
            reg_start_date_sk INTEGER NOT NULL REFERENCES dim_date(date_sk),
            reg_deadline_date_sk INTEGER NOT NULL REFERENCES dim_date(date_sk),
            event_start_date_sk INTEGER NOT NULL REFERENCES dim_date(date_sk),
            event_end_date_sk INTEGER NOT NULL REFERENCES dim_date(date_sk),
            total_prize_vnd BIGINT NOT NULL DEFAULT 0,
            prize_tier_count SMALLINT NOT NULL DEFAULT 0,
            stage_count SMALLINT NOT NULL DEFAULT 0,
            organizer_count SMALLINT NOT NULL DEFAULT 0,
            sponsor_count SMALLINT NOT NULL DEFAULT 0,
            domain_count SMALLINT NOT NULL DEFAULT 0,
            duration_days INTEGER,
            has_scholarship BOOLEAN NOT NULL DEFAULT FALSE
        );

        CREATE OR REPLACE TABLE fact_prize_tiers (
            prize_tier_sk BIGINT PRIMARY KEY,
            competition_sk BIGINT NOT NULL REFERENCES dim_competition(competition_sk),
            tier_rank SMALLINT NOT NULL,
            tier_name VARCHAR NOT NULL,
            reward_description VARCHAR NOT NULL,
            estimated_value_vnd BIGINT NOT NULL DEFAULT 0,
            is_scholarship BOOLEAN NOT NULL DEFAULT FALSE
        );

        CREATE OR REPLACE TABLE fact_timeline_stages (
            stage_sk BIGINT PRIMARY KEY,
            competition_sk BIGINT NOT NULL REFERENCES dim_competition(competition_sk),
            stage_order SMALLINT NOT NULL,
            stage_name VARCHAR NOT NULL,
            stage_start_date_sk INTEGER NOT NULL REFERENCES dim_date(date_sk),
            stage_end_date_sk INTEGER NOT NULL REFERENCES dim_date(date_sk),
            start_date_raw VARCHAR,
            end_date_raw VARCHAR,
            description VARCHAR
        );

        CREATE OR REPLACE TABLE bridge_competition_domain (
            competition_sk BIGINT NOT NULL REFERENCES dim_competition(competition_sk),
            domain_sk INTEGER NOT NULL REFERENCES dim_domain(domain_sk),
            allocation_weight DOUBLE NOT NULL CHECK (allocation_weight > 0.0 AND allocation_weight <= 1.0),
            PRIMARY KEY (competition_sk, domain_sk)
        );

        CREATE OR REPLACE TABLE bridge_competition_organizer (
            competition_sk BIGINT NOT NULL REFERENCES dim_competition(competition_sk),
            organizer_sk INTEGER NOT NULL REFERENCES dim_organizer(organizer_sk),
            role_type VARCHAR NOT NULL CHECK (role_type IN ('organizer', 'partner_sponsor')),
            allocation_weight DOUBLE NOT NULL CHECK (allocation_weight > 0.0 AND allocation_weight <= 1.0),
            PRIMARY KEY (competition_sk, organizer_sk, role_type)
        );
    """)


def _create_data_marts(con: duckdb.DuckDBPyConnection) -> None:
    """Create the 6 OBT/Analytical Data Marts (mart_*) materialized to R2."""
    con.execute("""
        CREATE OR REPLACE VIEW mart_kpi_overview AS
        SELECT
            COUNT(*) AS total_competitions,
            COUNT(*) FILTER (WHERE LOWER(COALESCE(d.registration_status, '')) = 'open') AS open_competitions,
            CAST(COALESCE(SUM(f.total_prize_vnd), 0) AS BIGINT) AS total_prize_pool_vnd,
            ROUND(COALESCE(AVG(CASE WHEN d.is_free THEN 100.0 ELSE 0.0 END), 0.0), 1) AS free_participation_pct,
            COUNT(*) FILTER (WHERE f.has_scholarship) AS scholarship_competitions,
            ROUND(COALESCE(AVG(d.team_size_max), 0.0), 1) AS avg_team_size_max,
            (SELECT COUNT(DISTINCT domain_sk) FROM bridge_competition_domain WHERE domain_sk > 0) AS unique_domains,
            (SELECT COUNT(DISTINCT organizer_sk) FROM bridge_competition_organizer) AS unique_organizers
        FROM fact_competitions AS f
        JOIN dim_competition AS d ON f.competition_sk = d.competition_sk;

        CREATE OR REPLACE VIEW mart_domain_analytics AS
        SELECT
            dm.domain_sk,
            dm.domain_slug,
            dm.domain_group,
            dm.display_order,
            COUNT(DISTINCT b.competition_sk) AS competition_count,
            ROUND(COALESCE(SUM(f.total_prize_vnd * b.allocation_weight), 0.0), 2) AS allocated_prize_vnd,
            ROUND(COALESCE(AVG(f.total_prize_vnd), 0.0), 0) AS avg_prize_vnd,
            COUNT(DISTINCT b.competition_sk) FILTER (WHERE dc.is_free) AS free_count
        FROM dim_domain AS dm
        LEFT JOIN bridge_competition_domain AS b ON dm.domain_sk = b.domain_sk
        LEFT JOIN fact_competitions AS f ON b.competition_sk = f.competition_sk
        LEFT JOIN dim_competition AS dc ON f.competition_sk = dc.competition_sk
        GROUP BY dm.domain_sk, dm.domain_slug, dm.domain_group, dm.display_order
        HAVING COUNT(DISTINCT b.competition_sk) > 0
        ORDER BY allocated_prize_vnd DESC, competition_count DESC, dm.display_order ASC;

        CREATE OR REPLACE VIEW mart_seasonality_academic AS
        WITH anchored AS (
            SELECT
                f.competition_sk,
                dc.name,
                f.total_prize_vnd,
                COALESCE(
                    NULLIF(f.event_start_date_sk, -1),
                    NULLIF(f.reg_deadline_date_sk, -1),
                    NULLIF(f.event_end_date_sk, -1),
                    -1
                ) AS primary_date_sk
            FROM fact_competitions AS f
            JOIN dim_competition AS dc ON f.competition_sk = dc.competition_sk
        )
        SELECT
            dd.year,
            dd.month,
            dd.academic_year,
            dd.academic_term,
            dd.date_known,
            COUNT(*) AS competition_count,
            CAST(COALESCE(SUM(a.total_prize_vnd), 0) AS BIGINT) AS total_prize_vnd,
            STRING_AGG(a.name, '; ' ORDER BY a.name) AS competitions_csv
        FROM anchored AS a
        JOIN dim_date AS dd ON a.primary_date_sk = dd.date_sk
        GROUP BY dd.year, dd.month, dd.academic_year, dd.academic_term, dd.date_known
        ORDER BY dd.year ASC NULLS LAST, dd.month ASC NULLS LAST;

        CREATE OR REPLACE VIEW mart_organizer_ecosystem AS
        SELECT
            org.organizer_sk,
            org.organizer_slug,
            org.organizer_name,
            org.organizer_tier,
            b.role_type,
            COUNT(DISTINCT b.competition_sk) AS competition_count,
            ROUND(COALESCE(SUM(f.total_prize_vnd * b.allocation_weight), 0.0), 2) AS allocated_prize_vnd
        FROM bridge_competition_organizer AS b
        JOIN dim_organizer AS org ON b.organizer_sk = org.organizer_sk
        JOIN fact_competitions AS f ON b.competition_sk = f.competition_sk
        GROUP BY org.organizer_sk, org.organizer_slug, org.organizer_name, org.organizer_tier, b.role_type
        ORDER BY competition_count DESC, allocated_prize_vnd DESC, org.organizer_name ASC;

        CREATE OR REPLACE VIEW mart_team_and_mode_matrix AS
        SELECT
            dc.mode_canonical,
            dc.team_profile,
            COUNT(*) AS competition_count,
            CAST(COALESCE(SUM(f.total_prize_vnd), 0) AS BIGINT) AS total_prize_vnd
        FROM fact_competitions AS f
        JOIN dim_competition AS dc ON f.competition_sk = dc.competition_sk
        GROUP BY dc.mode_canonical, dc.team_profile
        ORDER BY competition_count DESC, total_prize_vnd DESC;

        CREATE OR REPLACE VIEW mart_competition_explorer AS
        WITH domain_agg AS (
            SELECT
                b.competition_sk,
                LIST(dm.domain_group ORDER BY dm.display_order) AS domain_groups,
                LIST(dm.domain_slug ORDER BY dm.display_order) AS domain_slugs
            FROM bridge_competition_domain AS b
            JOIN dim_domain AS dm ON b.domain_sk = dm.domain_sk
            GROUP BY b.competition_sk
        ),
        org_agg AS (
            SELECT
                b.competition_sk,
                COALESCE(
                    LIST(org.organizer_name ORDER BY org.organizer_sk) FILTER (WHERE b.role_type = 'organizer'),
                    []
                ) AS organizers,
                COALESCE(
                    LIST(org.organizer_name ORDER BY org.organizer_sk) FILTER (WHERE b.role_type = 'partner_sponsor'),
                    []
                ) AS partners_and_sponsors
            FROM bridge_competition_organizer AS b
            JOIN dim_organizer AS org ON b.organizer_sk = org.organizer_sk
            GROUP BY b.competition_sk
        )
        SELECT
            dc.competition_sk,
            dc.competition_key,
            dc.name,
            dc.tagline,
            dc.canonical_url,
            dc.summary,
            dc.target_audience,
            dc.mode_canonical,
            dc.location,
            dc.participation_fee_raw,
            dc.is_free,
            dc.total_prize_pool_raw,
            f.total_prize_vnd,
            f.prize_tier_count,
            f.stage_count,
            f.has_scholarship,
            dc.team_size_min,
            dc.team_size_max,
            dc.team_profile,
            dc.team_description,
            dc.registration_status,
            dc.registration_start_raw,
            dc.registration_deadline_raw,
            dc.event_start_raw,
            dc.event_end_raw,
            dc.submission_platform,
            st.challenge_overview,
            COALESCE(da.domain_groups, ['Chưa phân loại']) AS domain_groups,
            COALESCE(da.domain_slugs, ['unclassified']) AS domain_slugs,
            COALESCE(oa.organizers, []) AS organizers,
            COALESCE(oa.partners_and_sponsors, []) AS partners_and_sponsors,
            dc.source_batch_file
        FROM dim_competition AS dc
        JOIN fact_competitions AS f ON dc.competition_sk = f.competition_sk
        LEFT JOIN _stg_competition_text AS st ON dc.competition_sk = st.competition_sk
        LEFT JOIN domain_agg AS da ON dc.competition_sk = da.competition_sk
        LEFT JOIN org_agg AS oa ON dc.competition_sk = oa.competition_sk
        ORDER BY f.total_prize_vnd DESC, dc.name ASC;
    """)


def export_gold_parquet_and_sync_r2(
    con: duckdb.DuckDBPyConnection,
    gold_dir: Path | None = None,
    sync_r2: bool = False,
) -> list[str | Path]:
    """Export strictly 15 Gold Parquet entities (9 Core + 6 Marts) to R2 (or local gold_dir)."""
    exported: list[str | Path] = []
    if gold_dir is not None:
        gold_dir.mkdir(parents=True, exist_ok=True)
        for entity in GOLD_ENTITIES:
            parquet_file = gold_dir / f"{entity}.parquet"
            escaped_file = str(parquet_file).replace("\\", "/")
            con.execute(f"COPY {entity} TO '{escaped_file}' (FORMAT PARQUET, COMPRESSION ZSTD)")
            exported.append(parquet_file)
        print(f">> [GOLD PARQUET EXPORTED] {len(exported)} tables/marts -> {gold_dir}")

    if sync_r2:
        if not settings.bucket_name:
            raise RuntimeError("BUCKET_NAME is required to upload Gold Parquet to Cloudflare R2.")
        print(
            f"\n>> [R2 GOLD SYNC] Uploading {len(GOLD_ENTITIES)} Gold Parquet files (ZSTD) "
            f"to s3://{settings.bucket_name}/gold/ ..."
        )
        s3 = settings.create_r2_client()
        uploaded: list[str | Path] = []
        cur = con.cursor()
        try:
            for entity in GOLD_ENTITIES:
                arrow_table = cur.sql(f"SELECT * FROM {entity}").to_arrow_table()
                buf = io.BytesIO()
                pq.write_table(arrow_table, buf, compression="zstd")
                key = f"gold/{entity}.parquet"
                s3.put_object(
                    Bucket=settings.bucket_name,
                    Key=key,
                    Body=buf.getvalue(),
                    ContentType="application/vnd.apache.parquet",
                    Metadata={"layer": "gold", "schema_version": "2.0", "compression": "zstd"},
                )
                uploaded.append(f"s3://{settings.bucket_name}/{key}")

            # A4 cleanup: remove any legacy gold/gold_*.parquet or stale objects not in GOLD_ENTITIES
            expected_keys = {f"gold/{entity}.parquet" for entity in GOLD_ENTITIES}
            paginator = s3.get_paginator("list_objects_v2")
            stale_keys: list[str] = []
            for page in paginator.paginate(Bucket=settings.bucket_name, Prefix="gold/"):
                for obj in page.get("Contents", []):
                    obj_key = obj["Key"]
                    if obj_key.endswith(".parquet") and obj_key not in expected_keys:
                        stale_keys.append(obj_key)
            for stale_key in stale_keys:
                s3.delete_object(Bucket=settings.bucket_name, Key=stale_key)
                print(f">> [R2 GOLD CLEANUP] Deleted stale object: {stale_key}")
        finally:
            cur.close()
        print(f">> [R2 SYNC COMPLETE] {len(uploaded)} Gold Parquet objects active on R2.")
        return uploaded if gold_dir is None else exported

    return exported


def build_gold_star_schema(
    db_path: Path | None,
    competitions: list[Competition],
    source_batch_file: str = "manual_input",
    gold_dir: Path | None = None,
    sync_r2: bool = False,
    *,
    enforce_contract: bool = True,
    reference_year: int = DEFAULT_REFERENCE_YEAR,
    gate_report_path: Path | None = None,
) -> list[str | Path]:
    """Build Two-Tier Gold Star Schema in DuckDB (:memory: for R2-only, or atomic swap if db_path given)."""
    if enforce_contract:
        pre_rules = validate_silver_records_pydantic(competitions, reference_year=reference_year)
        if not competitions or any(r.status == "FAIL" for r in pre_rules):
            pre_report: QualityGateReport = _build_gate_report(
                gate_name="Silver-to-Gold Input Quality Gate",
                source_label=source_batch_file,
                reference_year=reference_year,
                record_counts={"competitions": len(competitions)},
                rules=pre_rules,
                elapsed_ms=sum(r.duration_ms for r in pre_rules),
            )
            if gate_report_path is not None:
                gate_report_path.parent.mkdir(parents=True, exist_ok=True)
                gate_report_path.write_text(pre_report.model_dump_json(indent=2), encoding="utf-8")
            if not competitions or pre_report.circuit_breaker_tripped:
                raise DataContractViolationError(pre_report)

    tmp_db_path: Path | None = None
    con = duckdb.connect(":memory:")
    if db_path is not None:
        db_path.parent.mkdir(parents=True, exist_ok=True)
        tmp_db_path = db_path.with_name(f"{db_path.name}.tmp")
        if tmp_db_path.exists():
            tmp_db_path.unlink()
        escaped_tmp_path = str(tmp_db_path).replace("'", "''")
        con.execute(f"ATTACH '{escaped_tmp_path}' AS gold_compat (STORAGE_VERSION 'v1.5.0')")
        con.execute("USE gold_compat")
    try:
        _create_star_schema_ddl(con)
        con.executemany(
            "INSERT INTO dim_domain (domain_sk, domain_slug, domain_group, display_order) VALUES (?, ?, ?, ?)",
            CANONICAL_DOMAINS,
        )

        dim_dates: dict[int, tuple[Any, ...]] = {
            -1: (-1, None, None, None, None, "Không xác định", None, "Không xác định", "Không xác định", False)
        }
        organizers_by_slug: dict[str, tuple[int, str, str, str]] = {}

        def _register_date(raw: str | None) -> int:
            parsed = parse_date_value(raw)
            if parsed is None:
                return -1
            sk = parsed.year * 10000 + parsed.month * 100 + parsed.day
            if sk not in dim_dates:
                acad_year, acad_term = map_academic_term(parsed)
                quarter = (parsed.month - 1) // 3 + 1
                dim_dates[sk] = (
                    sk,
                    parsed,
                    parsed.year,
                    quarter,
                    parsed.month,
                    MONTH_NAMES_VI[parsed.month],
                    parsed.day,
                    acad_year,
                    acad_term,
                    True,
                )
            return sk

        def _register_organizer(org_name: str) -> int:
            org_slug = slugify(org_name)
            if org_slug not in organizers_by_slug:
                next_sk = len(organizers_by_slug) + 1
                organizers_by_slug[org_slug] = (next_sk, org_slug, org_name.strip(), classify_organizer_tier(org_name))
            return organizers_by_slug[org_slug][0]

        dim_comp_rows: list[tuple[Any, ...]] = []
        stg_text_rows: list[tuple[Any, ...]] = []
        fact_comp_rows: list[tuple[Any, ...]] = []
        fact_prize_rows: list[tuple[Any, ...]] = []
        fact_stage_rows: list[tuple[Any, ...]] = []
        bridge_domain_rows: list[tuple[Any, ...]] = []
        bridge_org_rows: list[tuple[Any, ...]] = []

        prize_sk_seq = 1
        stage_sk_seq = 1

        for comp_sk, c in enumerate(competitions, start=1):
            canonical_url = normalize_canonical_url(c.url, c.name)
            comp_key = c.competition_key or compute_competition_key(canonical_url)

            reg_start_sk = _register_date(c.registration_start)
            reg_deadline_sk = _register_date(c.registration_deadline)
            event_start_sk = _register_date(c.event_start)
            event_end_sk = _register_date(c.event_end)

            d_start = parse_date_value(c.event_start)
            d_end = parse_date_value(c.event_end)
            duration_days = (d_end - d_start).days + 1 if d_start and d_end and d_end >= d_start else None

            domain_sks = classify_competition_domains(c.category)
            domain_weight = 1.0 / len(domain_sks)
            for d_sk in domain_sks:
                bridge_domain_rows.append((comp_sk, d_sk, domain_weight))

            unique_org_pairs: dict[tuple[int, str], None] = {}
            for org_name in c.organizers:
                if org_name.strip():
                    o_sk = _register_organizer(org_name)
                    unique_org_pairs[(o_sk, "organizer")] = None
            for sp_name in c.partners_and_sponsors:
                if sp_name.strip():
                    s_sk = _register_organizer(sp_name)
                    unique_org_pairs[(s_sk, "partner_sponsor")] = None

            org_keys = [k for k in unique_org_pairs if k[1] == "organizer"]
            sp_keys = [k for k in unique_org_pairs if k[1] == "partner_sponsor"]
            total_org_links = len(unique_org_pairs)
            if total_org_links > 0:
                org_weight = 1.0 / total_org_links
                for o_sk, role_type in unique_org_pairs:
                    bridge_org_rows.append((comp_sk, o_sk, role_type, org_weight))

            has_scholarship = False
            for tier_rank, prize in enumerate(c.prizes, start=1):
                est_vnd = (
                    round(prize.estimated_value_vnd)
                    if prize.estimated_value_vnd is not None
                    else parse_vnd_currency(prize.reward)
                )
                if prize.is_scholarship:
                    has_scholarship = True
                fact_prize_rows.append(
                    (
                        prize_sk_seq,
                        comp_sk,
                        tier_rank,
                        prize.tier or f"Tier {tier_rank}",
                        prize.reward or "",
                        max(est_vnd, 0),
                        prize.is_scholarship,
                    )
                )
                prize_sk_seq += 1

            if "học bổng" in (c.total_prize_pool or "").lower():
                has_scholarship = True

            for stage_order, stage in enumerate(c.timeline_stages, start=1):
                st_start_sk = _register_date(stage.start_date)
                st_end_sk = _register_date(stage.end_date)
                fact_stage_rows.append(
                    (
                        stage_sk_seq,
                        comp_sk,
                        stage_order,
                        stage.stage_name,
                        st_start_sk,
                        st_end_sk,
                        stage.start_date,
                        stage.end_date,
                        stage.description,
                    )
                )
                stage_sk_seq += 1

            total_prize_vnd = _compute_competition_total_prize_vnd(c)
            is_free = is_participation_free(c.participation_fee)
            mode_canonical = normalize_mode(c.mode)
            team_profile = classify_team_profile(c.team_size_min, c.team_size_max)
            effective_status = resolve_effective_registration_status(c.registration_status, c.registration_deadline)

            dim_comp_rows.append(
                (
                    comp_sk,
                    comp_key,
                    c.name,
                    c.tagline,
                    canonical_url,
                    c.summary,
                    str(c.target_audience) if c.target_audience is not None else None,
                    c.team_size_min,
                    c.team_size_max,
                    c.team_description,
                    team_profile,
                    c.mode,
                    mode_canonical,
                    c.location,
                    c.participation_fee,
                    is_free,
                    c.total_prize_pool,
                    effective_status,
                    c.submission_platform,
                    c.registration_start,
                    c.registration_deadline,
                    c.event_start,
                    c.event_end,
                    source_batch_file,
                    datetime.now(),
                )
            )
            stg_text_rows.append((comp_sk, c.challenge_overview))

            fact_comp_rows.append(
                (
                    comp_sk,
                    reg_start_sk,
                    reg_deadline_sk,
                    event_start_sk,
                    event_end_sk,
                    total_prize_vnd,
                    len(c.prizes),
                    len(c.timeline_stages),
                    len(org_keys),
                    len(sp_keys),
                    len(domain_sks),
                    duration_days,
                    has_scholarship,
                )
            )

        con.executemany(
            "INSERT INTO dim_date VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            list(dim_dates.values()),
        )
        if organizers_by_slug:
            con.executemany(
                "INSERT INTO dim_organizer VALUES (?, ?, ?, ?)",
                list(organizers_by_slug.values()),
            )
        con.executemany(
            "INSERT INTO dim_competition VALUES (" + ", ".join(["?"] * 25) + ")",
            dim_comp_rows,
        )
        con.executemany("INSERT INTO _stg_competition_text VALUES (?, ?)", stg_text_rows)
        con.executemany(
            "INSERT INTO fact_competitions VALUES (" + ", ".join(["?"] * 13) + ")",
            fact_comp_rows,
        )
        if fact_prize_rows:
            con.executemany("INSERT INTO fact_prize_tiers VALUES (?, ?, ?, ?, ?, ?, ?)", fact_prize_rows)
        if fact_stage_rows:
            con.executemany("INSERT INTO fact_timeline_stages VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", fact_stage_rows)
        if bridge_domain_rows:
            con.executemany("INSERT INTO bridge_competition_domain VALUES (?, ?, ?)", bridge_domain_rows)
        if bridge_org_rows:
            con.executemany("INSERT INTO bridge_competition_organizer VALUES (?, ?, ?, ?)", bridge_org_rows)

        _create_data_marts(con)

        # Internal integrity assertion (SPEC-0003 EC-G1: 0.0 VND bridge error)
        check_rows = con.execute("""
            SELECT
                (SELECT total_prize_pool_vnd FROM mart_kpi_overview) AS kpi_total,
                (SELECT COALESCE(SUM(allocated_prize_vnd), 0) FROM mart_domain_analytics) AS domain_sum
        """).fetchall()
        assert check_rows
        check = check_rows[0]
        if abs(float(check[0]) - float(check[1])) > 1.0:
            raise RuntimeError(f"Prize allocation mismatch: kpi_total={check[0]}, domain_sum={check[1]}")

        if enforce_contract:
            gold_rules = validate_silver_to_gold_gate(con, expected_silver_count=len(competitions))
            gold_report = _build_gate_report(
                gate_name="Gold Pre-Publish WAP Quality Gate",
                source_label=source_batch_file,
                reference_year=reference_year,
                record_counts={"competitions": len(competitions)},
                rules=gold_rules,
                elapsed_ms=sum(r.duration_ms for r in gold_rules),
            )
            if gate_report_path is not None:
                gate_report_path.parent.mkdir(parents=True, exist_ok=True)
                gate_report_path.write_text(gold_report.model_dump_json(indent=2), encoding="utf-8")
            if gold_report.circuit_breaker_tripped:
                raise DataContractViolationError(gold_report)

        exported_files: list[str | Path] = []
        if gold_dir is not None or sync_r2:
            exported_files = export_gold_parquet_and_sync_r2(con, gold_dir=gold_dir, sync_r2=sync_r2)
    finally:
        con.close()

    if db_path is not None and tmp_db_path is not None:
        os.replace(tmp_db_path, db_path)
        print(f">> [STAR SCHEMA COMMITTED] Atomic swap complete -> {db_path}")
    else:
        print(f">> [STAR SCHEMA COMMITTED] In-memory build synced ({len(exported_files)} Parquet objects).")
    return exported_files


def build_metabase_r2_init_sql() -> str:
    """Generate DuckDB SQL snippet to register Cloudflare R2 httpfs secret, 15 Gold views & 4 virtual legacy views."""
    endpoint = settings.get_r2_endpoint_host() or "<ACCOUNT_ID>.r2.cloudflarestorage.com"
    bucket = (settings.bucket_name or "acdp-lakehouse").strip().strip("/")
    view_lines = [
        f"CREATE OR REPLACE VIEW {entity} AS SELECT * FROM read_parquet('s3://{bucket}/gold/{entity}.parquet');"
        for entity in GOLD_ENTITIES
    ]
    legacy_views = [
        "CREATE OR REPLACE VIEW gold_category_summary AS "
        "SELECT domain_group AS category, competition_count AS count, allocated_prize_vnd AS total_prize_vnd "
        "FROM mart_domain_analytics;",
        "CREATE OR REPLACE VIEW gold_mode_distribution AS "
        "SELECT mode_canonical AS mode, SUM(competition_count) AS count FROM mart_team_and_mode_matrix "
        "GROUP BY mode_canonical;",
        "CREATE OR REPLACE VIEW gold_seasonality AS "
        "SELECT CONCAT(year, '-', LPAD(CAST(month AS VARCHAR), 2, '0')) AS month_key, "
        "academic_term, SUM(competition_count) AS count "
        "FROM mart_seasonality_academic WHERE date_known = TRUE GROUP BY year, month, academic_term;",
        "CREATE OR REPLACE VIEW gold_top_prizes AS "
        "SELECT competition_key, name, total_prize_vnd, mode_canonical AS mode "
        "FROM mart_competition_explorer ORDER BY total_prize_vnd DESC;",
    ]
    return "\n".join(
        [
            "INSTALL httpfs;",
            "LOAD httpfs;",
            "CREATE OR REPLACE PERSISTENT SECRET r2_secret (",
            "    TYPE S3,",
            "    KEY_ID '<R2_ACCESS_KEY_ID>',",
            "    SECRET '<R2_SECRET_ACCESS_KEY>',",
            "    REGION 'auto',",
            f"    ENDPOINT '{endpoint}',",
            "    URL_STYLE 'path'",
            ");",
            *view_lines,
            *legacy_views,
        ]
    )


def build_motherduck_r2_init_sql(include_credentials: bool = False) -> str:
    """Generate MotherDuck Lite SQL script with IN MOTHERDUCK R2 secret, 19 Gold views & 3 Data Quality queries."""
    endpoint = settings.get_r2_endpoint_host() or "<ACCOUNT_ID>.r2.cloudflarestorage.com"
    bucket = (settings.bucket_name or "acdp-lakehouse").strip().strip("/")
    db_name = (settings.motherduck_database or "acdp_gold").strip() or "acdp_gold"
    if include_credentials and settings.aws_access_key_id and settings.aws_secret_access_key:
        key_id = settings.aws_access_key_id.replace("'", "''")
        secret = settings.aws_secret_access_key.replace("'", "''")
    else:
        key_id = "<R2_ACCESS_KEY_ID>"
        secret = "<R2_SECRET_ACCESS_KEY>"

    view_lines = [
        f"CREATE OR REPLACE VIEW {entity} AS SELECT * FROM read_parquet('s3://{bucket}/gold/{entity}.parquet');"
        for entity in GOLD_ENTITIES
    ]
    legacy_views = [
        "CREATE OR REPLACE VIEW gold_category_summary AS "
        "SELECT domain_group AS category, competition_count AS count, allocated_prize_vnd AS total_prize_vnd "
        "FROM mart_domain_analytics;",
        "CREATE OR REPLACE VIEW gold_mode_distribution AS "
        "SELECT mode_canonical AS mode, SUM(competition_count) AS count FROM mart_team_and_mode_matrix "
        "GROUP BY mode_canonical;",
        "CREATE OR REPLACE VIEW gold_seasonality AS "
        "SELECT CONCAT(year, '-', LPAD(CAST(month AS VARCHAR), 2, '0')) AS month_key, "
        "academic_term, SUM(competition_count) AS count "
        "FROM mart_seasonality_academic WHERE date_known = TRUE GROUP BY year, month, academic_term;",
        "CREATE OR REPLACE VIEW gold_top_prizes AS "
        "SELECT competition_key, name, total_prize_vnd, mode_canonical AS mode "
        "FROM mart_competition_explorer ORDER BY total_prize_vnd DESC;",
    ]
    quality_queries = [
        "-- 1. Data Quality Scorecard: Unknown Member (-1) & NULL checks across Fact/Dim",
        "SELECT",
        "    COUNT(*) AS total_competitions,",
        "    SUM(CASE WHEN f.reg_deadline_date_sk = -1 THEN 1 ELSE 0 END) AS missing_deadline_count,",
        "    SUM(CASE WHEN d.team_size_max IS NULL THEN 1 ELSE 0 END) AS missing_team_size_count,",
        "    SUM(CASE WHEN f.prize_tier_count = 0 THEN 1 ELSE 0 END) AS missing_prize_tiers_count",
        "FROM fact_competitions f",
        "JOIN dim_competition d USING (competition_sk);",
        "",
        "-- 2. Bridge Weighting Factor Prize Conservation Invariant (Expected drift_vnd = 0)",
        "WITH kpi_sum AS (",
        "    SELECT COALESCE(SUM(total_prize_vnd), 0) AS fact_total_vnd FROM fact_competitions",
        "),",
        "domain_sum AS (",
        "    SELECT COALESCE(SUM(allocated_prize_vnd), 0) AS bridge_total_vnd FROM mart_domain_analytics",
        ")",
        "SELECT fact_total_vnd, bridge_total_vnd, ABS(fact_total_vnd - bridge_total_vnd) AS drift_vnd",
        "FROM kpi_sum, domain_sum;",
        "",
        "-- 3. Batch Lineage & Freshness Audit",
        "SELECT",
        "    source_batch_file,",
        "    COUNT(*) AS record_count,",
        "    MAX(loaded_at) AS latest_loaded_at",
        "FROM dim_competition",
        "GROUP BY source_batch_file",
        "ORDER BY latest_loaded_at DESC;",
    ]
    return "\n".join(
        [
            f"CREATE DATABASE IF NOT EXISTS {db_name};",
            f"USE {db_name};",
            "CREATE OR REPLACE SECRET r2_secret IN MOTHERDUCK (",
            "    TYPE S3,",
            f"    KEY_ID '{key_id}',",
            f"    SECRET '{secret}',",
            "    REGION 'auto',",
            f"    ENDPOINT '{endpoint}',",
            "    URL_STYLE 'path'",
            ");",
            *view_lines,
            *legacy_views,
            "",
            *quality_queries,
        ]
    )


def verify_analytics(con: duckdb.DuckDBPyConnection) -> dict[str, Any]:
    """Run integrity and analytical verification queries on Gold Star Schema."""
    kpi = con.execute("SELECT * FROM mart_kpi_overview").fetchone()
    domain_sum_row = con.execute("SELECT COALESCE(SUM(allocated_prize_vnd), 0) FROM mart_domain_analytics").fetchone()
    domain_sum = float(domain_sum_row[0]) if domain_sum_row else 0.0
    bridge_diff = abs(float(kpi[2]) - domain_sum) if kpi else 0.0
    print("\n=== GOLD KPI OVERVIEW (R2 TWO-TIER GOLD) ===")
    print(f"KPI: {kpi} | Bridge Diff: {bridge_diff:.2f} VND")

    print("\n=== DOMAIN ANALYTICS (WEIGHTED BRIDGE) ===")
    for r in con.execute(
        "SELECT domain_group, competition_count, allocated_prize_vnd FROM mart_domain_analytics"
    ).fetchall():
        print(f"  - {r[0]}: {r[1]} contests | {r[2]:,.0f} VND")

    return {
        "total_competitions": int(kpi[0]) if kpi else 0,
        "open_competitions": int(kpi[1]) if kpi else 0,
        "total_prize_pool_vnd": int(kpi[2]) if kpi else 0,
        "free_participation_pct": float(kpi[3]) if kpi else 0.0,
        "scholarship_competitions": int(kpi[4]) if kpi else 0,
        "avg_team_size_max": float(kpi[5]) if kpi else 0.0,
        "bridge_diff_vnd": bridge_diff,
    }


def verify_analytics_from_r2() -> dict[str, Any]:
    """Read the 15 Gold Parquet objects directly from Cloudflare R2 via DuckDB httpfs and verify KPIs."""
    if not settings.bucket_name:
        raise RuntimeError("BUCKET_NAME is required in .env to verify Gold Parquet on R2.")
    con = duckdb.connect(":memory:")
    try:
        settings.configure_duckdb_r2(con)
        bucket = settings.bucket_name.strip().strip("/")
        for entity in GOLD_ENTITIES:
            s3_uri = f"s3://{bucket}/gold/{entity}.parquet"
            con.execute(f"CREATE OR REPLACE VIEW {entity} AS SELECT * FROM read_parquet('{s3_uri}')")
        return verify_analytics(con)
    finally:
        con.close()


def verify_motherduck_views_from_r2() -> dict[str, Any]:
    """Verify all 19 Gold Views & 3 Data Quality Scorecard queries on MotherDuck Cloud or direct R2 httpfs."""
    if not settings.bucket_name:
        raise RuntimeError("BUCKET_NAME is required in .env to verify Gold Views on Cloudflare R2.")

    bucket = settings.bucket_name.strip().strip("/")
    has_md_token = bool(settings.motherduck_token.strip())
    if has_md_token:
        con = duckdb.connect(f"md:?motherduck_token={settings.motherduck_token.strip()}")
        mode = "motherduck_cloud"
        endpoint = settings.get_r2_endpoint_host()
        if not endpoint or not settings.aws_access_key_id or not settings.aws_secret_access_key:
            raise RuntimeError("Cloudflare R2 credentials are required to configure IN MOTHERDUCK secret.")
        key_id = settings.aws_access_key_id.replace("'", "''")
        secret = settings.aws_secret_access_key.replace("'", "''")
        db_name = (settings.motherduck_database or "acdp_gold").strip() or "acdp_gold"
        con.execute(f"CREATE DATABASE IF NOT EXISTS {db_name}")
        con.execute(f"USE {db_name}")
        con.execute(
            f"""
            CREATE OR REPLACE SECRET r2_secret IN MOTHERDUCK (
                TYPE S3,
                KEY_ID '{key_id}',
                SECRET '{secret}',
                REGION 'auto',
                ENDPOINT '{endpoint.replace("'", "''")}',
                URL_STYLE 'path'
            )
            """
        )
    else:
        con = duckdb.connect(":memory:")
        mode = "r2_direct_httpfs_verified"
        settings.configure_duckdb_r2(con)

    try:
        for entity in GOLD_ENTITIES:
            s3_uri = f"s3://{bucket}/gold/{entity}.parquet"
            con.execute(f"CREATE OR REPLACE VIEW {entity} AS SELECT * FROM read_parquet('{s3_uri}')")

        legacy_defs = (
            "CREATE OR REPLACE VIEW gold_category_summary AS "
            "SELECT domain_group AS category, competition_count AS count, allocated_prize_vnd AS total_prize_vnd "
            "FROM mart_domain_analytics",
            "CREATE OR REPLACE VIEW gold_mode_distribution AS "
            "SELECT mode_canonical AS mode, SUM(competition_count) AS count FROM mart_team_and_mode_matrix "
            "GROUP BY mode_canonical",
            "CREATE OR REPLACE VIEW gold_seasonality AS "
            "SELECT CONCAT(year, '-', LPAD(CAST(month AS VARCHAR), 2, '0')) AS month_key, "
            "academic_term, SUM(competition_count) AS count "
            "FROM mart_seasonality_academic WHERE date_known = TRUE GROUP BY year, month, academic_term",
            "CREATE OR REPLACE VIEW gold_top_prizes AS "
            "SELECT competition_key, name, total_prize_vnd, mode_canonical AS mode "
            "FROM mart_competition_explorer ORDER BY total_prize_vnd DESC",
        )
        for stmt in legacy_defs:
            con.execute(stmt)

        all_views = [*GOLD_ENTITIES, "gold_category_summary", "gold_mode_distribution", "gold_seasonality", "gold_top_prizes"]
        view_counts: dict[str, int] = {}
        for view_name in all_views:
            row = con.execute(f"SELECT COUNT(*) FROM {view_name}").fetchone()
            view_counts[view_name] = int(row[0]) if row else 0

        sc_row = con.execute(
            """
            SELECT
                COUNT(*) AS total_competitions,
                SUM(CASE WHEN f.reg_deadline_date_sk = -1 THEN 1 ELSE 0 END) AS missing_deadline_count,
                SUM(CASE WHEN d.team_size_max IS NULL THEN 1 ELSE 0 END) AS missing_team_size_count,
                SUM(CASE WHEN f.prize_tier_count = 0 THEN 1 ELSE 0 END) AS missing_prize_tiers_count
            FROM fact_competitions f
            JOIN dim_competition d USING (competition_sk)
            """
        ).fetchone()
        scorecard = {
            "total_competitions": int(sc_row[0]) if sc_row else 0,
            "missing_deadline_count": int(sc_row[1] or 0) if sc_row else 0,
            "missing_team_size_count": int(sc_row[2] or 0) if sc_row else 0,
            "missing_prize_tiers_count": int(sc_row[3] or 0) if sc_row else 0,
        }

        inv_row = con.execute(
            """
            WITH kpi_sum AS (
                SELECT COALESCE(SUM(total_prize_vnd), 0) AS fact_total_vnd FROM fact_competitions
            ),
            domain_sum AS (
                SELECT COALESCE(SUM(allocated_prize_vnd), 0) AS bridge_total_vnd FROM mart_domain_analytics
            )
            SELECT fact_total_vnd, bridge_total_vnd, ABS(fact_total_vnd - bridge_total_vnd) AS drift_vnd
            FROM kpi_sum, domain_sum
            """
        ).fetchone()
        bridge_invariant = {
            "fact_total_vnd": int(inv_row[0]) if inv_row else 0,
            "bridge_total_vnd": int(inv_row[1]) if inv_row else 0,
            "drift_vnd": float(inv_row[2]) if inv_row else 0.0,
        }

        print(f"\n=== MOTHERDUCK / R2 GOLD VIEWS VERIFICATION ({mode}) ===")
        print(f"Verified {len(view_counts)} views (15 Two-Tier Gold + 4 Virtual Legacy Views):")
        for vname, cnt in view_counts.items():
            print(f"  - {vname}: {cnt} rows")
        print(f"Data Quality Scorecard: {scorecard}")
        print(f"Bridge Weighting Invariant: {bridge_invariant}")

        return {
            "mode": mode,
            "view_counts": view_counts,
            "scorecard": scorecard,
            "bridge_invariant": bridge_invariant,
        }
    finally:
        con.close()


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="ACDP v2 Silver Parquet & Two-Tier Gold Star Schema Builder")
    parser.add_argument("--export-silver-r2", action="store_true", help="Export Silver ZSTD Parquet to R2")
    parser.add_argument("--build-gold-r2", action="store_true", help="Build Two-Tier Gold (15 Parquets) on R2")
    parser.add_argument("--verify", action="store_true", help="Verify Silver and/or Gold Parquet on R2")
    parser.add_argument("--metabase-sql", action="store_true", help="Print DuckDB httpfs init SQL for Metabase")
    parser.add_argument("--motherduck-sql", action="store_true", help="Print MotherDuck Lite IN MOTHERDUCK R2 init SQL")
    parser.add_argument("--verify-motherduck", action="store_true", help="Verify 19 Gold Views & Data Quality Scorecard")
    parser.add_argument("--date", type=str, default=None, help="Optional Silver extraction date (YYYY-MM-DD)")
    parser.add_argument("--skip-quality-gate", action="store_true", help="Bypass Data Contract WAP circuit breaker")
    parser.add_argument("--gate-report", type=Path, default=None, help="Optional path to write Quality Gate JSON report")
    args = parser.parse_args(argv)

    if args.metabase_sql:
        print(build_metabase_r2_init_sql())
        return
    if args.motherduck_sql:
        print(build_motherduck_r2_init_sql(include_credentials=False))
        return
    if args.verify_motherduck:
        verify_motherduck_views_from_r2()
        return

    enforce_contract = not args.skip_quality_gate
    run_all = not (args.export_silver_r2 or args.build_gold_r2 or args.verify)
    if args.export_silver_r2 or args.build_gold_r2 or run_all:
        competitions, source_label = load_silver_competitions_from_r2(target_date=args.date)
        if args.export_silver_r2 or run_all:
            export_silver_parquet(
                competitions,
                output_dir=None,
                enforce_contract=enforce_contract,
                gate_report_path=args.gate_report,
            )
        if args.build_gold_r2 or run_all:
            build_gold_star_schema(
                db_path=None,
                competitions=competitions,
                source_batch_file=source_label,
                gold_dir=None,
                sync_r2=True,
                enforce_contract=enforce_contract,
                gate_report_path=args.gate_report,
            )

    if args.verify:
        if args.export_silver_r2 or run_all:
            verify_silver_parquet_on_r2()
        if args.build_gold_r2 or not args.export_silver_r2 or run_all:
            verify_analytics_from_r2()


if __name__ == "__main__":
    main()
