"""Module 4: Gold Layer Kimball Star Schema & DuckDB Materialization Engine.

Conforms to SPEC-0003 (docs/specs/0003-gold-dimensional-modeling-spec.md):
1. Deduplicates Silver JSON extractions (newest batch preferred, SHA-256 canonical URL key).
2. Builds Kimball Star Schema in DuckDB via atomic swap (.tmp -> acdp.duckdb):
   - 4 Dimensions: dim_competition, dim_date, dim_domain, dim_organizer
   - 3 Facts: fact_competitions, fact_prize_tiers, fact_timeline_stages
   - 2 Bridges: bridge_competition_domain (weighted), bridge_competition_organizer
   - 6 Analytical Data Marts (mart_*) + 6 backward-compatible views (gold_*)
3. Exports Parquet files to data/lakehouse/gold/ and optionally syncs to Cloudflare R2.

Usage:
    uv run python -m src.acdp.4_analytics_gold --build --verify
"""

from __future__ import annotations

import argparse
import hashlib
import os
import re
import unicodedata
from datetime import date, datetime
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

import duckdb
import pyarrow as pa
import pyarrow.parquet as pq

from acdp.config import settings
from acdp.schemas import Competition

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

CANONICAL_DOMAINS: list[tuple[int, str, str, int]] = [
    (1, "ai-data-science", "AI & Data Science", 1),
    (2, "web3-blockchain-fintech", "Web3, Blockchain & FinTech", 2),
    (3, "software-web-mobile", "Software, Web & Mobile", 3),
    (4, "security-iot-embedded", "Security, IoT & Embedded", 4),
    (5, "startup-design-interdisciplinary", "Startup, Design & Interdisciplinary", 5),
    (-1, "unclassified", "Chưa phân loại", 99),
]

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
            "distributed systems",
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


def slugify(text: str) -> str:
    """Convert arbitrary Unicode/Vietnamese text to lowercase URL-safe ASCII slug."""
    normalized = unicodedata.normalize("NFKD", text.replace("đ", "d").replace("Đ", "D"))
    ascii_only = normalized.encode("ascii", "ignore").decode("ascii").lower()
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_only).strip("-")
    return slug or "unknown"


def normalize_canonical_url(url: str | None, fallback_name: str = "") -> str:
    """Normalize URL by enforcing https, lowercase host, no tracking query or trailing slash."""
    if not url or not url.strip():
        return f"urn:acdp:name:{slugify(fallback_name)}"

    raw = url.strip()
    if "://" not in raw:
        raw = f"https://{raw}"

    parsed = urlparse(raw)
    if not parsed.netloc:
        return f"urn:acdp:name:{slugify(fallback_name)}"

    scheme = "https"
    netloc = parsed.netloc.lower()
    path = parsed.path.rstrip("/") or ""

    filtered_query = [
        (k, v)
        for k, v in parse_qsl(parsed.query, keep_blank_values=True)
        if not k.lower().startswith("utm_") and k.lower() != "fbclid"
    ]
    query_str = urlencode(filtered_query)
    return urlunparse((scheme, netloc, path, "", query_str, ""))


def compute_competition_key(canonical_url: str) -> str:
    """Compute immutable 64-char SHA-256 natural key from canonical URL."""
    return hashlib.sha256(canonical_url.encode("utf-8")).hexdigest()


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

    # Strip percentages (e.g. 'Học bổng 60%') so they are never misparsed as 60 VND
    text = re.sub(r"\d+(?:[.,]\d+)?\s*%", " ", val_str.strip())
    lower = text.lower()
    rate = usd_to_vnd_rate if usd_to_vnd_rate is not None else settings.usd_to_vnd_rate

    # 1. Explicit Vietnamese billion / million words ('tỷ', 'triệu')
    ty_matches = re.findall(r"(\d[\d.,]*)\s*(?:tỷ|ty)\b", lower)
    if ty_matches:
        return round(max(_parse_number_token(m) for m in ty_matches) * 1_000_000_000)

    trieu_matches = re.findall(r"(\d[\d.,]*)\s*(?:triệu|trieu)\b", lower)
    if trieu_matches:
        return round(max(_parse_number_token(m) for m in trieu_matches) * 1_000_000)

    # 2. Check whether USD is the primary currency (and not a parenthetical note under VND)
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

    # 3. Shorthand M / tr suffixes for VND (e.g. '100M VND', '250M+', 'Up to VND 100M')
    m_matches = re.findall(r"(\d[\d.,]*)\s*(?:m(?:\b|\+)|tr\b)", lower)
    if m_matches:
        return round(max(_parse_number_token(m) for m in m_matches) * 1_000_000)

    # 4. Plain VND digit tokens (require >= 10,000 VND to ignore years, top ranks, or hours)
    if any(tok in lower for tok in ("vnd", "vnđ", "đ", "ngàn", "nghìn")):
        num_tokens = re.findall(r"\d[\d.,]*", text)
        if num_tokens:
            val = round(max(_parse_number_token(n) for n in num_tokens))
            return val if val >= 10_000 else 0

    return 0


def parse_date_value(raw: str | None) -> date | None:
    """Parse ISO, Vietnamese DD/MM/YYYY, and MM/YYYY strings into Python date."""
    if not raw or not raw.strip():
        return None

    s = raw.strip()
    lower = s.lower()
    if any(tok in lower for tok in ("tbd", "rolling", "liên tục", "hàng tháng", "unknown", "n/a")):
        return None

    # ISO YYYY-MM-DD (optionally with time component)
    iso_match = re.match(r"^(\d{4})-(\d{1,2})-(\d{1,2})(?:[T\s].*)?$", s)
    if iso_match:
        try:
            return date(int(iso_match.group(1)), int(iso_match.group(2)), int(iso_match.group(3)))
        except ValueError:
            return None

    # Vietnamese DD/MM/YYYY or DD-MM-YYYY
    vn_match = re.match(r"^(\d{1,2})[/\-](\d{1,2})[/\-](\d{4})$", s)
    if vn_match:
        try:
            return date(int(vn_match.group(3)), int(vn_match.group(2)), int(vn_match.group(1)))
        except ValueError:
            return None

    # Month-Year: MM/YYYY, YYYY-MM, 'Tháng MM/YYYY'
    my_match = re.match(r"^(?:tháng\s*)?(\d{1,2})[/\-](\d{4})$", lower)
    if my_match:
        try:
            return date(int(my_match.group(2)), int(my_match.group(1)), 1)
        except ValueError:
            return None

    ym_match = re.match(r"^(\d{4})[/\-](\d{1,2})$", s)
    if ym_match:
        try:
            return date(int(ym_match.group(1)), int(ym_match.group(2)), 1)
        except ValueError:
            return None

    return None


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

        # Exact word match for 'ai' short token before substring rules
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
    mapping = {
        "online": "Online",
        "offline": "Offline",
        "hybrid": "Hybrid",
    }
    return mapping.get((mode or "").strip().lower(), "Unknown")


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
            "corp",
            "company",
            "group",
            "bank",
            "vietnam",
            "fpt",
            "vng",
            "naver",
            "zalo",
            "meta",
            "aws",
            "openai",
            "netcompany",
            "tinyfish",
            "sotatek",
            "axon",
            "cloudgo",
            "kyanon",
            "onyx",
            "shb",
            "bitmart",
            "tether",
            "fonOS".lower(),
            "zalopay",
            "mindx",
            "masan",
        )
    ):
        return "Enterprise"
    if any(tok in lower for tok in ("club", "clb", "team", "community", "liên chi", "hội", "gdg", "vbi")):
        return "Community"
    return "Unknown"


def _extract_batch_sort_key(path: Path) -> tuple[int, str]:
    """Extract numeric timestamp suffix from batch file name for deterministic sorting."""
    match = re.search(r"_(\d+)\.json$", path.name)
    ts = int(match.group(1)) if match else int(path.stat().st_mtime)
    return (ts, path.name)


def _competition_richness_score(c: Competition) -> tuple[int, int, int]:
    """Score record completeness for deterministic deduplication tie-breaking."""
    return (len(c.prizes), len(c.timeline_stages), len(c.summary or ""))


def load_silver_competitions_with_source(extractions_dir: Path | None = None) -> tuple[list[Competition], str]:
    """Load and deduplicate Silver extracted competitions without double-counting batch vs single files."""
    target_dir = extractions_dir or Path("data/extractions")
    if not target_dir.exists():
        raise RuntimeError(f"Silver extractions directory does not exist: '{target_dir.resolve()}'.")

    batch_files = sorted(target_dir.glob("extractions_*.json"), key=_extract_batch_sort_key)
    if batch_files:
        selected_files = [batch_files[-1]]
        source_label = batch_files[-1].name
    else:
        selected_files = sorted(
            jf for jf in target_dir.glob("*.json") if not jf.name.startswith("extractions_")
        )
        source_label = "single_domain_json_files" if selected_files else "empty"

    dedup_by_key: dict[str, Competition] = {}
    for jf in selected_files:
        try:
            import json

            with open(jf, encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, dict):
                continue

            raw_items: list[dict[str, Any]] = []
            if "results" in data:
                for item in data["results"]:
                    raw_items.extend(item.get("competitions", []))
            elif "competitions" in data:
                raw_items.extend(data.get("competitions", []))

            for raw_comp in raw_items:
                comp = Competition.model_validate(raw_comp)
                key = compute_competition_key(normalize_canonical_url(comp.url, comp.name))
                existing = dedup_by_key.get(key)
                if existing is None or _competition_richness_score(comp) > _competition_richness_score(existing):
                    dedup_by_key[key] = comp
        except (OSError, ValueError) as exc:
            print(f"[WARN] Failed to parse {jf.name}: {exc}")

    competitions = list(dedup_by_key.values())
    if not competitions:
        raise RuntimeError(
            f"No valid Silver extracted competition records found in '{target_dir.resolve()}'. "
            "Ensure Silver extraction (src/acdp/2_instruction.py) completed successfully."
        )

    return competitions, source_label


def load_silver_competitions(extractions_dir: Path | None = None) -> list[Competition]:
    """Load deduplicated Silver competitions."""
    competitions, _ = load_silver_competitions_with_source(extractions_dir)
    return competitions


def _compute_competition_total_prize_vnd(c: Competition) -> int:
    """Compute canonical total prize VND honoring total_prize_pool first then prizes sum fallback."""
    pool_vnd = parse_vnd_currency(c.total_prize_pool)
    if pool_vnd > 0:
        return pool_vnd

    tier_sum = 0
    for prize in c.prizes:
        val = round(prize.estimated_value_vnd) if prize.estimated_value_vnd else parse_vnd_currency(prize.reward)
        tier_sum += max(val, 0)
    return tier_sum


def export_silver_parquet(competitions: list[Competition], output_dir: Path) -> tuple[Path, Path]:
    """Export deduplicated Silver competitions and prizes to Parquet files."""
    output_dir.mkdir(parents=True, exist_ok=True)
    comp_parquet_path = output_dir / "competitions.parquet"
    prizes_parquet_path = output_dir / "prizes.parquet"

    comp_rows: list[dict[str, Any]] = []
    prize_rows: list[dict[str, Any]] = []

    for c in competitions:
        canonical_url = normalize_canonical_url(c.url, c.name)
        comp_key = compute_competition_key(canonical_url)
        calculated_prize_vnd = _compute_competition_total_prize_vnd(c)

        comp_rows.append(
            {
                "competition_key": comp_key,
                "name": c.name,
                "tagline": c.tagline or "",
                "url": canonical_url,
                "summary": c.summary,
                "organizers": c.organizers,
                "partners_and_sponsors": c.partners_and_sponsors,
                "category": c.category,
                "target_audience": str(c.target_audience or ""),
                "team_size_min": c.team_size_min,
                "team_size_max": c.team_size_max,
                "is_team_required": bool(c.team_size_min and c.team_size_min > 1),
                "team_description": c.team_description or "",
                "mode": c.mode,
                "location": c.location or "",
                "participation_fee": c.participation_fee or "",
                "total_prize_pool": c.total_prize_pool or "",
                "total_prize_vnd": calculated_prize_vnd,
                "registration_start": c.registration_start or "",
                "registration_deadline": c.registration_deadline or "",
                "registration_status": c.registration_status,
                "event_start": c.event_start or "",
                "event_end": c.event_end or "",
                "challenge_overview": c.challenge_overview or "",
                "submission_platform": c.submission_platform or "",
            }
        )

        for tier_idx, p in enumerate(c.prizes, start=1):
            val = round(p.estimated_value_vnd) if p.estimated_value_vnd else parse_vnd_currency(p.reward)
            prize_rows.append(
                {
                    "competition_key": comp_key,
                    "competition_name": c.name,
                    "tier_rank": tier_idx,
                    "tier": p.tier,
                    "reward": p.reward,
                    "estimated_value_vnd": max(val, 0),
                    "is_scholarship": p.is_scholarship,
                }
            )

    pq.write_table(pa.Table.from_pylist(comp_rows), comp_parquet_path)
    print(f">> [PARQUET EXPORTED] {len(comp_rows)} competitions -> {comp_parquet_path}")

    if prize_rows:
        pq.write_table(pa.Table.from_pylist(prize_rows), prizes_parquet_path)
        print(f">> [PARQUET EXPORTED] {len(prize_rows)} prize tiers -> {prizes_parquet_path}")

    return comp_parquet_path, prizes_parquet_path


def _create_star_schema_ddl(con: duckdb.DuckDBPyConnection) -> None:
    """Create Kimball Star Schema tables (4 dim, 3 fact, 2 bridge)."""
    con.execute("""
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
            challenge_overview VARCHAR,
            raw_categories VARCHAR[],
            organizers VARCHAR[],
            partners_and_sponsors VARCHAR[],
            registration_start_raw VARCHAR,
            registration_deadline_raw VARCHAR,
            event_start_raw VARCHAR,
            event_end_raw VARCHAR,
            source_batch_file VARCHAR NOT NULL,
            loaded_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
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
            team_size_min SMALLINT,
            team_size_max SMALLINT,
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


def _create_data_marts_and_aliases(con: duckdb.DuckDBPyConnection) -> None:
    """Create 6 mart_* analytical views and 6 backward-compatible gold_* aliases."""
    con.execute("""
        CREATE OR REPLACE VIEW mart_kpi_overview AS
        SELECT
            COUNT(*) AS total_competitions,
            COUNT(*) FILTER (WHERE LOWER(COALESCE(d.registration_status, '')) = 'open') AS open_competitions,
            CAST(COALESCE(SUM(f.total_prize_vnd), 0) AS BIGINT) AS total_prize_pool_vnd,
            ROUND(COALESCE(AVG(CASE WHEN d.is_free THEN 100.0 ELSE 0.0 END), 0.0), 1) AS free_participation_pct,
            COUNT(*) FILTER (WHERE f.has_scholarship) AS scholarship_competitions,
            ROUND(COALESCE(AVG(f.team_size_max), 0.0), 1) AS avg_team_size_max,
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
            f.team_size_min,
            f.team_size_max,
            dc.team_profile,
            dc.team_description,
            dc.registration_status,
            dc.registration_start_raw,
            dc.registration_deadline_raw,
            dc.event_start_raw,
            dc.event_end_raw,
            dc.submission_platform,
            dc.challenge_overview,
            COALESCE(da.domain_groups, ['Chưa phân loại']) AS domain_groups,
            COALESCE(da.domain_slugs, ['unclassified']) AS domain_slugs,
            dc.organizers,
            dc.partners_and_sponsors,
            dc.source_batch_file
        FROM dim_competition AS dc
        JOIN fact_competitions AS f ON dc.competition_sk = f.competition_sk
        LEFT JOIN domain_agg AS da ON dc.competition_sk = da.competition_sk
        ORDER BY f.total_prize_vnd DESC, dc.name ASC;

        -- Backward-compatible Gold views (SPEC-0003 Section 2.4)
        CREATE OR REPLACE VIEW gold_competitions AS
        SELECT
            competition_key,
            name,
            tagline,
            canonical_url AS url,
            summary,
            organizers,
            partners_and_sponsors,
            domain_groups AS category,
            target_audience,
            team_size_min,
            team_size_max,
            team_description,
            mode_canonical AS mode,
            location,
            participation_fee_raw AS participation_fee,
            is_free,
            total_prize_pool_raw AS total_prize_pool,
            total_prize_vnd,
            registration_start_raw AS registration_start,
            registration_deadline_raw AS registration_deadline,
            registration_status,
            event_start_raw AS event_start,
            event_end_raw AS event_end,
            challenge_overview,
            submission_platform
        FROM mart_competition_explorer;

        CREATE OR REPLACE VIEW gold_prizes AS
        SELECT
            dc.competition_key,
            dc.name AS competition_name,
            pt.tier_rank,
            pt.tier_name AS tier,
            pt.reward_description AS reward,
            pt.estimated_value_vnd,
            pt.is_scholarship
        FROM fact_prize_tiers AS pt
        JOIN dim_competition AS dc ON pt.competition_sk = dc.competition_sk;

        CREATE OR REPLACE VIEW gold_category_summary AS
        SELECT
            domain_group AS category,
            domain_group AS domain_category,
            competition_count AS count,
            competition_count AS total_competitions,
            allocated_prize_vnd AS total_prize_vnd,
            allocated_prize_vnd AS total_prize_pool_vnd,
            avg_prize_vnd
        FROM mart_domain_analytics;

        CREATE OR REPLACE VIEW gold_mode_distribution AS
        SELECT
            mode_canonical AS mode,
            SUM(competition_count) AS count,
            ROUND(SUM(competition_count) * 100.0 / NULLIF(SUM(SUM(competition_count)) OVER (), 0), 1) AS percentage
        FROM mart_team_and_mode_matrix
        GROUP BY mode_canonical
        ORDER BY count DESC;

        CREATE OR REPLACE VIEW gold_seasonality AS
        SELECT
            CASE
                WHEN date_known THEN CONCAT(year, '-', LPAD(CAST(month AS VARCHAR), 2, '0'))
                ELSE 'Khác'
            END AS month_key,
            CASE
                WHEN date_known THEN CONCAT(year, '-', LPAD(CAST(month AS VARCHAR), 2, '0'))
                ELSE 'Khác'
            END AS deadline_month,
            academic_term,
            SUM(competition_count) AS count,
            SUM(competition_count) AS competition_count,
            STRING_AGG(competitions_csv, '; ') AS competitions
        FROM mart_seasonality_academic
        GROUP BY 1, 2, academic_term
        ORDER BY 1;

        CREATE OR REPLACE VIEW gold_top_prizes AS
        SELECT
            competition_key,
            name,
            total_prize_pool_raw AS total_prize_pool,
            total_prize_vnd,
            mode_canonical AS mode,
            registration_deadline_raw AS registration_deadline,
            registration_status,
            canonical_url AS url
        FROM mart_competition_explorer
        ORDER BY total_prize_vnd DESC;
    """)


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


def build_gold_star_schema(
    db_path: Path,
    competitions: list[Competition],
    source_batch_file: str = "manual_input",
    gold_dir: Path | None = None,
    sync_r2: bool = False,
) -> list[Path]:
    """Build full Kimball Star Schema into DuckDB via atomic swap and export Gold Parquet."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_db_path = db_path.with_name(f"{db_path.name}.tmp")
    if tmp_db_path.exists():
        tmp_db_path.unlink()

    con = duckdb.connect(":memory:")
    escaped_tmp_path = str(tmp_db_path).replace("'", "''")
    con.execute(f"ATTACH '{escaped_tmp_path}' AS gold_compat (STORAGE_VERSION 'v1.5.0')")
    con.execute("USE gold_compat")
    try:
        _create_star_schema_ddl(con)

        # 1. Seed dim_domain
        con.executemany(
            "INSERT INTO dim_domain (domain_sk, domain_slug, domain_group, display_order) VALUES (?, ?, ?, ?)",
            CANONICAL_DOMAINS,
        )

        # 2. Prepare Dimension, Fact, and Bridge buffers
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
        fact_comp_rows: list[tuple[Any, ...]] = []
        fact_prize_rows: list[tuple[Any, ...]] = []
        fact_stage_rows: list[tuple[Any, ...]] = []
        bridge_domain_rows: list[tuple[Any, ...]] = []
        bridge_org_rows: list[tuple[Any, ...]] = []

        prize_sk_seq = 1
        stage_sk_seq = 1

        for comp_sk, c in enumerate(competitions, start=1):
            canonical_url = normalize_canonical_url(c.url, c.name)
            comp_key = compute_competition_key(canonical_url)

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
                    c.challenge_overview,
                    c.category,
                    c.organizers,
                    c.partners_and_sponsors,
                    c.registration_start,
                    c.registration_deadline,
                    c.event_start,
                    c.event_end,
                    source_batch_file,
                    datetime.now(),
                )
            )

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
                    c.team_size_min,
                    c.team_size_max,
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
            "INSERT INTO dim_competition VALUES (" + ", ".join(["?"] * 29) + ")",
            dim_comp_rows,
        )
        con.executemany(
            "INSERT INTO fact_competitions VALUES (" + ", ".join(["?"] * 15) + ")",
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

        _create_data_marts_and_aliases(con)

        # Internal integrity assertion (SPEC-0003 EC-G1)
        check = con.execute("""
            SELECT
                (SELECT total_prize_pool_vnd FROM mart_kpi_overview) AS kpi_total,
                (SELECT COALESCE(SUM(allocated_prize_vnd), 0) FROM mart_domain_analytics) AS domain_sum
        """).fetchone()
        assert check is not None
        if abs(float(check[0]) - float(check[1])) > 1.0:
            raise RuntimeError(f"Prize allocation mismatch: kpi_total={check[0]}, domain_sum={check[1]}")

        exported_files: list[Path] = []
        if gold_dir is not None:
            exported_files = export_gold_parquet_and_sync_r2(con, gold_dir, sync_r2=sync_r2)
    finally:
        con.close()

    os.replace(tmp_db_path, db_path)
    print(f">> [STAR SCHEMA COMMITTED] Atomic swap complete -> {db_path}")
    return exported_files


def export_gold_parquet_and_sync_r2(
    con: duckdb.DuckDBPyConnection,
    gold_dir: Path,
    sync_r2: bool = False,
) -> list[Path]:
    """Export all Star Schema tables, Data Marts, and aliases to Parquet and optionally sync R2."""
    gold_dir.mkdir(parents=True, exist_ok=True)
    gold_entities = [
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
        "gold_competitions",
        "gold_prizes",
        "gold_category_summary",
        "gold_mode_distribution",
        "gold_seasonality",
        "gold_top_prizes",
    ]
    exported_files: list[Path] = []
    for entity in gold_entities:
        parquet_file = gold_dir / f"{entity}.parquet"
        escaped_file = str(parquet_file).replace("\\", "/")
        con.execute(f"COPY {entity} TO '{escaped_file}' (FORMAT PARQUET)")
        exported_files.append(parquet_file)
    print(f">> [GOLD PARQUET EXPORTED] {len(exported_files)} tables/views -> {gold_dir}")

    if (
        sync_r2
        and settings.bronze_storage_backend == "cloudflare_r2"
        and settings.bucket_name
        and settings.aws_endpoint_url
        and settings.aws_access_key_id
    ):
        print(f"\n>> [R2 SYNC] Synchronizing Silver & Gold Parquet to s3://{settings.bucket_name} ...")
        s3 = settings.create_r2_client()

        silver_dir = Path("data/lakehouse/silver")
        silver_files = list(silver_dir.glob("*.parquet"))
        for sp in silver_files:
            s3.upload_file(str(sp), settings.bucket_name, f"silver/{sp.name}")

        for gp in exported_files:
            s3.upload_file(str(gp), settings.bucket_name, f"gold/{gp.name}")

        print(f">> [R2 SYNC COMPLETE] {len(silver_files)} Silver and {len(exported_files)} Gold Parquet files uploaded.")

    return exported_files


def verify_analytics(con: duckdb.DuckDBPyConnection) -> None:
    """Execute verification queries over the Gold Star Schema Data Marts."""
    print("\n" + "=" * 72)
    print("ACDP GOLD LAYER STAR SCHEMA REPORT (DuckDB Read-Only OLAP)")
    print("=" * 72)

    print("\n[1] KPI Overview (mart_kpi_overview):")
    con.sql("SELECT * FROM mart_kpi_overview").show()

    print("\n[2] Weighted Domain Analytics (mart_domain_analytics):")
    con.sql(
        "SELECT domain_group, competition_count, allocated_prize_vnd, free_count FROM mart_domain_analytics"
    ).show()

    print("\n[3] Academic Seasonality (mart_seasonality_academic):")
    con.sql(
        "SELECT year, month, academic_year, academic_term, competition_count FROM mart_seasonality_academic"
    ).show()

    print("\n[4] Mode x Team Matrix (mart_team_and_mode_matrix):")
    con.sql("SELECT * FROM mart_team_and_mode_matrix").show()

    print("\n[5] Top Sponsors & Organizers (mart_organizer_ecosystem LIMIT 8):")
    con.sql(
        "SELECT organizer_name, organizer_tier, role_type, competition_count FROM mart_organizer_ecosystem LIMIT 8"
    ).show()
    print("=" * 72)


def run_gold_pipeline() -> None:
    """Execute end-to-end Silver-to-Gold Star Schema pipeline."""
    extractions_dir = Path("data/extractions")
    silver_dir = Path("data/lakehouse/silver")
    gold_dir = Path("data/lakehouse/gold")
    duckdb_file = Path(settings.duckdb_database_path)

    competitions, source_batch = load_silver_competitions_with_source(extractions_dir)
    export_silver_parquet(competitions, silver_dir)
    build_gold_star_schema(duckdb_file, competitions, source_batch_file=source_batch, gold_dir=gold_dir, sync_r2=True)

    con = duckdb.connect(str(duckdb_file), read_only=True)
    try:
        verify_analytics(con)
    finally:
        con.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ACDP Gold Layer Star Schema & DuckDB Materialization Engine")
    parser.add_argument("--build", action="store_true", help="Build Silver Parquet and DuckDB Gold Star Schema")
    parser.add_argument("--verify", action="store_true", help="Print verification queries from DuckDB")
    args = parser.parse_args()

    if args.build or not args.verify:
        run_gold_pipeline()
    elif args.verify:
        con = duckdb.connect(str(settings.duckdb_database_path), read_only=True)
        try:
            verify_analytics(con)
        finally:
            con.close()
