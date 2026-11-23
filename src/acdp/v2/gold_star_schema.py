"""TASK-SLV-04: Silver Explicit PyArrow Parquet Exporter & Loader (ACDP v2).

Implements TASK-SLV-02 / G1–G8 recommendations for Silver storage:
1. Loads Silver JSON extractions (`silver/extractions/`) from Cloudflare R2 (or local dir in tests),
   preserving backward compatibility with v1 JSON payloads and enriching lineage from `_metadata`.
2. Enforces explicit `pa.schema` definitions (`SILVER_COMPETITIONS_ARROW_SCHEMA`,
   `SILVER_PRIZES_ARROW_SCHEMA`, `SILVER_TIMELINE_STAGES_ARROW_SCHEMA`) with `pa.date32()`,
   `pa.int32()`, `pa.int64()`, `pa.timestamp("us", tz="UTC")`, and true `None` nulls.
3. Exports ZSTD-compressed Parquet files (`competitions.parquet`, `prizes.parquet`,
   `timeline_stages.parquet`) to Cloudflare R2 `silver/` (or local `output_dir`).

Usage:
    uv run python -m acdp.v2.gold_star_schema --export-silver-r2 --verify
"""

from __future__ import annotations

import argparse
import io
import json
import re
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq

from acdp.config import settings
from acdp.v2.schemas import (
    Competition,
    compute_competition_key,
    normalize_canonical_url,
    parse_date_value,
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


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="ACDP v2 Silver Schema & Explicit PyArrow Parquet Exporter")
    parser.add_argument("--export-silver-r2", action="store_true", help="Load Silver JSON from R2 and export ZSTD Parquet")
    parser.add_argument("--verify", action="store_true", help="Verify exported Silver Parquet files on Cloudflare R2")
    parser.add_argument("--date", type=str, default=None, help="Optional Silver extraction date (YYYY-MM-DD)")
    args = parser.parse_args(argv)

    if args.export_silver_r2 or not args.verify:
        competitions, _ = load_silver_competitions_from_r2(target_date=args.date)
        export_silver_parquet(competitions, output_dir=None)
    if args.verify:
        verify_silver_parquet_on_r2()


if __name__ == "__main__":
    main()
