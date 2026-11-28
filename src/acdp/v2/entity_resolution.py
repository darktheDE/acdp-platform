"""TASK-DQ-04: Entity Resolution, Deduplication & Data Fusion for Silver Layer (ACDP v2).

Implements a 5-stage Entity Resolution (ER) pipeline grounded in:
- Christophides et al. (2020, ACM CSUR): Normalization -> Blocking -> Matching -> Clustering -> Fusion.
- Papadakis et al. (2020, ACM CSUR): Temporal blocking to prune O(n^2) comparisons.
- Fellegi & Sunter (1969, JASA): Three-zone match decisioning (AUTO_MERGE / CLERICAL_REVIEW / NON_MATCH).
- Li, Dong, Maurino & Srivastava (2011, PVLDB): Temporal record linkage preventing cross-season merges.
- Bleiholder & Naumann (2009, ACM CSUR): Authority-first Data Fusion and attribute survivorship.

Usage:
    uv run python -m acdp.v2.entity_resolution --audit-local tests/fixtures/dq04/multi_source_and_season_batch.json
    uv run python -m acdp.v2.entity_resolution --audit-r2
    uv run python -m acdp.v2.entity_resolution --benchmark
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, date, datetime
from enum import IntEnum
from pathlib import Path
from typing import Any, Literal
from urllib.parse import urlparse

import duckdb
from pydantic import BaseModel, Field

from acdp.config import settings
from acdp.v2.data_contracts import (
    AGGREGATOR_HOSTS,
    GENERIC_ROOT_ONLY_HOSTS,
    NOISY_HOST_PREFIXES,
    NOISY_PATH_MARKERS,
    SOCIAL_OR_FORM_HOSTS,
)
from acdp.v2.schemas import (
    Competition,
    build_natural_key,
    canonicalize_organizers,
    clean_placeholder,
    compute_competition_key,
    extract_edition_number,
    extract_season_month,
    extract_season_year,
    fold_vietnamese,
    normalize_canonical_url,
    normalize_competition_name,
)

SILVER_KEY_PATTERN = re.compile(
    r"^silver/extractions/([^/]+)/year=(\d{4})/month=(\d{2})/day=(\d{2})/(\d+)\.json$"
)

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

AUTO_MERGE_THRESHOLD = 0.82
CLERICAL_REVIEW_THRESHOLD = 0.65
DISTINCT_OFFICIAL_MIN_NAME_SIM = 0.90

MEDIA_PATH_MARKERS = (
    "/tin-tuc/",
    "/bai-viet/",
    "/thong-bao/",
    "/su-kien/",
    "/news/",
)


class SourceAuthority(IntEnum):
    """Authority ranking for URL/source survivorship (DIR-022)."""

    NOISY_OR_INVALID = 0
    AGGREGATOR_OR_MEDIA = 1
    INSTITUTIONAL_ANNOUNCEMENT = 2
    OFFICIAL = 3


def canonicalize_official_url(raw_url: str | None) -> str:
    """Normalize HTTP(S) URL per RFC 3986 §6, returning empty string for invalid/URN inputs."""
    if not raw_url or not isinstance(raw_url, str) or not raw_url.strip():
        return ""
    raw = raw_url.strip()
    if raw.lower().startswith("urn:"):
        return ""
    norm = normalize_canonical_url(raw)
    if norm.startswith("urn:"):
        return ""
    return norm


def _host_and_bare(url: str) -> tuple[str, str]:
    parsed = urlparse(url)
    host = parsed.netloc.lower().split(":")[0]
    bare = host[4:] if host.startswith("www.") else host
    return host, bare


def classify_url_authority(url: str | None, source_url: str | None = None) -> SourceAuthority:
    """Classify competition URL authority into 4 ordered tiers for DIR-022 survivorship."""
    canon = canonicalize_official_url(url)
    if not canon:
        return SourceAuthority.NOISY_OR_INVALID

    parsed = urlparse(canon)
    host, bare = _host_and_bare(canon)
    path_lower = (parsed.path or "").lower()

    if not bare or "." not in bare:
        return SourceAuthority.NOISY_OR_INVALID
    if any(bare.startswith(prefix) for prefix in NOISY_HOST_PREFIXES):
        return SourceAuthority.NOISY_OR_INVALID
    if any(marker in path_lower for marker in NOISY_PATH_MARKERS):
        return SourceAuthority.NOISY_OR_INVALID
    if bare in GENERIC_ROOT_ONLY_HOSTS and path_lower in {"", "/"}:
        return SourceAuthority.NOISY_OR_INVALID
    if bare in SOCIAL_OR_FORM_HOSTS or host in SOCIAL_OR_FORM_HOSTS:
        return SourceAuthority.NOISY_OR_INVALID

    if bare in AGGREGATOR_HOSTS or host in AGGREGATOR_HOSTS:
        return SourceAuthority.AGGREGATOR_OR_MEDIA
    if any(marker in path_lower for marker in MEDIA_PATH_MARKERS):
        if bare.endswith((".edu.vn", ".gov.vn")):
            return SourceAuthority.INSTITUTIONAL_ANNOUNCEMENT
        return SourceAuthority.AGGREGATOR_OR_MEDIA

    # Dedicated official site vs institutional sub-page
    if bare.endswith((".edu.vn", ".gov.vn")) and path_lower not in {"", "/"}:
        # Subdomain like ai-arena-vietnam.vnu.edu.vn/ is OFFICIAL; deep news path is INSTITUTIONAL
        if bare.count(".") >= 3 and any(m in path_lower for m in ("/content/", "/asset_publisher/", "/bai-viet/")):
            return SourceAuthority.INSTITUTIONAL_ANNOUNCEMENT
    return SourceAuthority.OFFICIAL


def extract_official_domain(url: str | None) -> str:
    """Return bare official domain if URL passes authority checks, else empty string."""
    auth = classify_url_authority(url)
    if auth < SourceAuthority.INSTITUTIONAL_ANNOUNCEMENT:
        return ""
    canon = canonicalize_official_url(url)
    _, bare = _host_and_bare(canon)
    return bare


def _jaro_winkler_similarity(s1: str, s2: str) -> float:
    """Compute Jaro-Winkler similarity in [0.0, 1.0] (pure stdlib fallback matching DuckDB)."""
    if s1 == s2:
        return 1.0
    if not s1 or not s2:
        return 0.0

    len1, len2 = len(s1), len(s2)
    match_dist = max(max(len1, len2) // 2 - 1, 0)
    s1_matches = [False] * len1
    s2_matches = [False] * len2

    matches = 0
    for i in range(len1):
        start = max(0, i - match_dist)
        end = min(i + match_dist + 1, len2)
        for j in range(start, end):
            if not s2_matches[j] and s1[i] == s2[j]:
                s1_matches[i] = True
                s2_matches[j] = True
                matches += 1
                break

    if matches == 0:
        return 0.0

    transpositions = 0
    k = 0
    for i in range(len1):
        if not s1_matches[i]:
            continue
        while not s2_matches[k]:
            k += 1
        if s1[i] != s2[k]:
            transpositions += 1
        k += 1

    jaro = (matches / len1 + matches / len2 + (matches - transpositions / 2.0) / matches) / 3.0
    prefix = 0
    for c1, c2 in zip(s1[:4], s2[:4], strict=False):
        if c1 == c2:
            prefix += 1
        else:
            break
    return jaro + 0.1 * prefix * (1.0 - jaro)


def _token_dice_sets(t1: frozenset[str], t2: frozenset[str]) -> float:
    """Compute token-set Dice coefficient in [0.0, 1.0] from precomputed token sets."""
    if not t1 or not t2:
        return 0.0
    if t1 == t2:
        return 1.0
    return (2.0 * len(t1 & t2)) / (len(t1) + len(t2))


def _token_dice_similarity(s1: str, s2: str) -> float:
    """Compute token-set Dice coefficient in [0.0, 1.0] resilient to word-order differences."""
    return _token_dice_sets(frozenset(fold_vietnamese(s1).split()), frozenset(fold_vietnamese(s2).split()))


# ---------------------------------------------------------------------------
# Pydantic Report Contracts
# ---------------------------------------------------------------------------


class EntityMatchDecision(BaseModel):
    """Pairwise match decision under the 3-zone Fellegi-Sunter framework."""

    left_index: int
    right_index: int
    left_name: str
    right_name: str
    decision: Literal["AUTO_MERGE", "CLERICAL_REVIEW", "NON_MATCH"]
    rule_id: str
    score: float = Field(ge=0.0, le=1.0)
    feature_scores: dict[str, float] = Field(default_factory=dict)
    reason: str


class EntityClusterSummary(BaseModel):
    """Audit summary for a resolved entity cluster."""

    cluster_id: int
    competition_key: str
    natural_key: str
    season_year: int | None = None
    survivor_name: str
    survivor_url: str
    member_count: int
    merged_names: list[str] = Field(default_factory=list)
    merged_source_urls: list[str] = Field(default_factory=list)
    match_rules: list[str] = Field(default_factory=list)
    fused_fields: list[str] = Field(default_factory=list)


class EntityResolutionReport(BaseModel):
    """Full audit report for a Silver Entity Resolution & Deduplication run."""

    source_label: str = "unknown"
    audited_at_utc: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    input_count: int = 0
    output_count: int = 0
    merged_duplicates_count: int = 0
    dropped_no_official_count: int = 0
    multi_season_groups: dict[str, list[int | None]] = Field(default_factory=dict)
    clerical_review_pairs: list[EntityMatchDecision] = Field(default_factory=list)
    clusters: list[EntityClusterSummary] = Field(default_factory=list)
    dropped_entities: list[dict[str, Any]] = Field(default_factory=list)
    blocking_comparisons: int = 0
    naive_comparisons: int = 0
    comparison_reduction_pct: float = 0.0
    elapsed_ms: float = 0.0

    def to_console_table(self) -> str:
        """Render concise deterministic terminal summary table."""
        lines = [
            "=" * 92,
            f"ENTITY RESOLUTION & DEDUPLICATION REPORT ({self.source_label})",
            f"Input: {self.input_count} -> Output: {self.output_count} | Merged Dups: {self.merged_duplicates_count} "
            f"| Dropped(No Official): {self.dropped_no_official_count} | Elapsed: {self.elapsed_ms:.2f} ms",
            f"Blocking Comparisons: {self.blocking_comparisons} / {self.naive_comparisons} naive "
            f"({self.comparison_reduction_pct:.1f}% reduction)",
            "-" * 92,
        ]
        merged_clusters = [c for c in self.clusters if c.member_count > 1]
        if merged_clusters:
            lines.append("MERGED MULTI-SOURCE CLUSTERS:")
            for cl in merged_clusters:
                lines.append(
                    f"  [Cluster #{cl.cluster_id}] {cl.survivor_name} (year={cl.season_year}, "
                    f"members={cl.member_count}, rules={cl.match_rules})"
                )
                lines.append(f"    -> Official URL : {cl.survivor_url}")
                lines.append(f"    -> Natural Key  : {cl.natural_key}")
                lines.append(f"    -> Merged Names : {cl.merged_names}")
                lines.append(f"    -> Source URLs  : {cl.merged_source_urls}")
                if cl.fused_fields:
                    lines.append(f"    -> Fused Fields : {cl.fused_fields}")
        else:
            lines.append("MERGED MULTI-SOURCE CLUSTERS: None (all input records already unique)")

        if self.multi_season_groups:
            lines.append("-" * 92)
            lines.append("MULTI-SEASON SEPARATIONS (PRESERVED DISTINCT):")
            for base_slug, years in sorted(self.multi_season_groups.items()):
                lines.append(f"  - {base_slug}: seasons={years}")

        if self.clerical_review_pairs:
            lines.append("-" * 92)
            lines.append(f"CLERICAL REVIEW QUEUE ({len(self.clerical_review_pairs)} pairs):")
            for pair in self.clerical_review_pairs:
                lines.append(
                    f"  - ({pair.score:.3f}) '{pair.left_name}' vs '{pair.right_name}' [{pair.rule_id}]: {pair.reason}"
                )

        lines.append("=" * 92)
        return "\n".join(lines)

    def to_markdown_table(self) -> str:
        """Render merged clusters and multi-season splits as Markdown."""
        rows = [
            "| Cluster | Survivor Name | Season | Members | Official URL | Natural Key | Rules |",
            "| :---: | :--- | :---: | :---: | :--- | :--- | :--- |",
        ]
        for cl in self.clusters:
            if cl.member_count > 1:
                rows.append(
                    f"| `#{cl.cluster_id}` | {cl.survivor_name} | `{cl.season_year}` | "
                    f"`{cl.member_count}` | `{cl.survivor_url}` | `{cl.natural_key}` | "
                    f"`{', '.join(cl.match_rules)}` |"
                )
        return "\n".join(rows)


# ---------------------------------------------------------------------------
# Stage 1: Profile Extraction & Normalization
# ---------------------------------------------------------------------------


@dataclass
class _EntityProfile:
    index: int
    comp: Competition
    canonical_url: str
    official_domain: str
    source_domain: str
    authority: SourceAuthority
    is_direct_official_source: bool
    full_norm_name: str
    core_name_slug: str
    core_name_text: str
    full_tokens: frozenset[str]
    core_tokens: frozenset[str]
    canonical_orgs: set[str]
    season_year: int | None
    season_month: int | None
    edition_number: int | None
    natural_key: str
    anchor_date: date | None
    completeness: tuple[int, int, int, int, float]


def _count_non_null_scalars(comp: Competition) -> int:
    scalar_fields = (
        comp.tagline,
        comp.location,
        comp.participation_fee,
        comp.total_prize_pool,
        comp.registration_start_date,
        comp.registration_deadline_date,
        comp.event_start_date,
        comp.event_end_date,
        comp.challenge_overview,
        comp.submission_platform,
        comp.official_rules_url,
        comp.organizer_contact,
        comp.requires_advisor,
        comp.team_description,
    )
    return sum(1 for val in scalar_fields if val is not None and str(val).strip() != "")


def _build_profile(index: int, comp: Competition) -> _EntityProfile:
    canon_url = canonicalize_official_url(comp.url)
    official_domain = extract_official_domain(comp.url)
    src_canon = canonicalize_official_url(comp.source_url)
    _, src_bare = _host_and_bare(src_canon) if src_canon else ("", "")
    authority = classify_url_authority(comp.url, comp.source_url)
    full_norm, core_slug = normalize_competition_name(comp.name)
    canon_orgs = set(canonicalize_organizers(comp.organizers))
    timeline_dates = [d for st in comp.timeline_stages for d in (st.start_date_iso, st.end_date_iso)]
    season_year = comp.season_year or extract_season_year(
        comp.name,
        comp.url,
        event_start_date=comp.event_start_date,
        registration_deadline_date=comp.registration_deadline_date,
        registration_start_date=comp.registration_start_date,
        event_end_date=comp.event_end_date,
        timeline_dates=timeline_dates,
        tagline=comp.tagline,
        summary=comp.summary,
    )
    season_month = extract_season_month(comp.name, comp.url)
    edition_number = extract_edition_number(comp.name)
    natural_key, _ = build_natural_key(
        comp.name,
        comp.organizers,
        comp.url,
        season_year,
        season_month=season_month,
        official_domain=official_domain or None,
    )
    anchor_date = (
        comp.event_start_date
        or comp.registration_deadline_date
        or comp.registration_start_date
        or comp.event_end_date
    )
    is_direct_official = bool(
        authority >= SourceAuthority.INSTITUTIONAL_ANNOUNCEMENT
        and official_domain
        and src_bare
        and (src_bare == official_domain or src_bare.endswith(f".{official_domain}"))
    )
    ext_ts = comp.extracted_at.timestamp() if comp.extracted_at else 0.0
    completeness = (
        _count_non_null_scalars(comp),
        len(comp.prizes),
        len(comp.timeline_stages),
        len(comp.summary or ""),
        ext_ts,
    )
    core_name_text = core_slug.replace("-", " ")
    return _EntityProfile(
        index=index,
        comp=comp,
        canonical_url=canon_url,
        official_domain=official_domain,
        source_domain=src_bare,
        authority=authority,
        is_direct_official_source=is_direct_official,
        full_norm_name=full_norm,
        core_name_slug=core_slug,
        core_name_text=core_name_text,
        full_tokens=frozenset(full_norm.split()),
        core_tokens=frozenset(core_name_text.split()),
        canonical_orgs=canon_orgs,
        season_year=season_year,
        season_month=season_month,
        edition_number=edition_number,
        natural_key=natural_key,
        anchor_date=anchor_date,
        completeness=completeness,
    )


# ---------------------------------------------------------------------------
# Stage 3: Pairwise Matching (Rules 0–4)
# ---------------------------------------------------------------------------


def _score_profiles(a: _EntityProfile, b: _EntityProfile) -> EntityMatchDecision:
    # Rule 0: Hard Temporal & Edition Separation (Li et al. 2011)
    if a.season_year is not None and b.season_year is not None and a.season_year != b.season_year:
        return EntityMatchDecision(
            left_index=a.index,
            right_index=b.index,
            left_name=a.comp.name,
            right_name=b.comp.name,
            decision="NON_MATCH",
            rule_id="R0_DIFF_SEASON",
            score=0.0,
            reason=f"Different season years ({a.season_year} vs {b.season_year})",
        )
    if a.season_month is not None and b.season_month is not None and a.season_month != b.season_month:
        return EntityMatchDecision(
            left_index=a.index,
            right_index=b.index,
            left_name=a.comp.name,
            right_name=b.comp.name,
            decision="NON_MATCH",
            rule_id="R0_DIFF_MONTH",
            score=0.0,
            reason=f"Different recurring months ({a.season_month} vs {b.season_month})",
        )
    if a.edition_number is not None and b.edition_number is not None and a.edition_number != b.edition_number:
        return EntityMatchDecision(
            left_index=a.index,
            right_index=b.index,
            left_name=a.comp.name,
            right_name=b.comp.name,
            decision="NON_MATCH",
            rule_id="R0_DIFF_EDITION",
            score=0.0,
            reason=f"Different edition numbers ({a.edition_number} vs {b.edition_number})",
        )

    both_dedicated_official = (
        a.authority >= SourceAuthority.INSTITUTIONAL_ANNOUNCEMENT
        and b.authority >= SourceAuthority.INSTITUTIONAL_ANNOUNCEMENT
        and bool(a.official_domain)
        and bool(b.official_domain)
        and a.official_domain != b.official_domain
    )

    # Rule 1: Exact Canonical Official URL Match within same/compatible season
    if (
        a.authority >= SourceAuthority.INSTITUTIONAL_ANNOUNCEMENT
        and b.authority >= SourceAuthority.INSTITUTIONAL_ANNOUNCEMENT
        and a.canonical_url
        and a.canonical_url == b.canonical_url
    ):
        return EntityMatchDecision(
            left_index=a.index,
            right_index=b.index,
            left_name=a.comp.name,
            right_name=b.comp.name,
            decision="AUTO_MERGE",
            rule_id="R1_EXACT_URL",
            score=1.0,
            feature_scores={"name": 1.0, "org": 1.0, "domain": 1.0, "date": 1.0},
            reason=f"Exact canonical official URL match ({a.canonical_url}) in season {a.season_year or b.season_year}",
        )

    # Rule 2: Aggregator/Media resolved to matching Official Domain (DIR-022)
    if (
        a.official_domain
        and b.official_domain
        and a.official_domain == b.official_domain
        and (a.authority != b.authority or a.canonical_url != b.canonical_url)
    ):
        # Verify same path when both are sub-paths on a multi-event host (e.g. event.navercorp.vn)
        path_a = urlparse(a.canonical_url).path.rstrip("/")
        path_b = urlparse(b.canonical_url).path.rstrip("/")
        if path_a == path_b or not path_a or not path_b:
            return EntityMatchDecision(
                left_index=a.index,
                right_index=b.index,
                left_name=a.comp.name,
                right_name=b.comp.name,
                decision="AUTO_MERGE",
                rule_id="R2_AGGREGATOR_TO_OFFICIAL",
                score=0.98,
                feature_scores={"name": 0.95, "org": 1.0, "domain": 1.0, "date": 1.0},
                reason=f"Matched official domain '{a.official_domain}' in season {a.season_year or b.season_year}",
            )

    # Compute feature similarities for Rule 3 & Rule 4 using precomputed token sets first
    dice_full = _token_dice_sets(a.full_tokens, b.full_tokens)
    dice_core = _token_dice_sets(a.core_tokens, b.core_tokens)
    if max(dice_full, dice_core) >= 0.25:
        jw_full = _jaro_winkler_similarity(a.full_norm_name, b.full_norm_name)
        jw_core = _jaro_winkler_similarity(a.core_name_text, b.core_name_text)
    else:
        jw_full = dice_full
        jw_core = dice_core

    if both_dedicated_official:
        # Guard against Jaro-Winkler prefix inflation (e.g. "RMIT Hackathon" vs "RMIT Hack-A-Venture")
        s_name = round(0.4 * jw_full + 0.6 * dice_full, 4)
    else:
        s_name = max(jw_full, dice_full, jw_core, dice_core)

    if a.canonical_orgs and b.canonical_orgs:
        if a.canonical_orgs & b.canonical_orgs:
            s_org = 1.0
        else:
            s_org = max(
                _token_dice_similarity(oa, ob)
                for oa in a.canonical_orgs
                for ob in b.canonical_orgs
            )
            s_org = 0.85 if s_org >= 0.75 else 0.0
    else:
        s_org = 0.0

    if a.official_domain and b.official_domain and a.official_domain == b.official_domain:
        s_domain = 1.0
    elif both_dedicated_official:
        s_domain = 0.0
    else:
        # One side is aggregator/noisy/unverified
        s_domain = 0.5

    if a.anchor_date and b.anchor_date:
        delta_days = abs((a.anchor_date - b.anchor_date).days)
        if delta_days <= 14:
            s_date = 1.0
        elif delta_days <= 60:
            s_date = 0.5
        else:
            s_date = 0.0
    else:
        s_date = 0.25

    # Rule 3: Exact Composite Core Name + Overlapping Canonical Organizer in same season
    # (Catches polluted aggregator records like Live R2 #17 vs #24 VinUni Datathon 2026)
    if (
        not both_dedicated_official
        and a.core_name_slug
        and a.core_name_slug != "unknown"
        and a.core_name_slug == b.core_name_slug
        and s_org >= 0.85
    ):
        return EntityMatchDecision(
            left_index=a.index,
            right_index=b.index,
            left_name=a.comp.name,
            right_name=b.comp.name,
            decision="AUTO_MERGE",
            rule_id="R3_NATURAL_KEY",
            score=0.95,
            feature_scores={"name": round(s_name, 4), "org": round(s_org, 4), "domain": s_domain, "date": s_date},
            reason=f"Exact core name '{a.core_name_slug}' + organizer overlap ({sorted(a.canonical_orgs & b.canonical_orgs)}) in season {a.season_year or b.season_year}",
        )

    # Rule 4: Fellegi-Sunter Weighted Composite Similarity
    weighted_score = round(0.45 * s_name + 0.25 * s_org + 0.20 * s_domain + 0.10 * s_date, 4)
    features = {
        "name": round(s_name, 4),
        "org": round(s_org, 4),
        "domain": round(s_domain, 4),
        "date": round(s_date, 4),
    }

    if both_dedicated_official:
        if s_name >= DISTINCT_OFFICIAL_MIN_NAME_SIM and dice_core >= 0.80 and s_org >= 0.5 and s_date >= 0.5:
            return EntityMatchDecision(
                left_index=a.index,
                right_index=b.index,
                left_name=a.comp.name,
                right_name=b.comp.name,
                decision="AUTO_MERGE",
                rule_id="R4_WEIGHTED_SIMILARITY",
                score=weighted_score,
                feature_scores=features,
                reason="Very high full-name, organizer, and date similarity across official mirrors",
            )
        return EntityMatchDecision(
            left_index=a.index,
            right_index=b.index,
            left_name=a.comp.name,
            right_name=b.comp.name,
            decision="NON_MATCH",
            rule_id="R4_DISTINCT_OFFICIAL_GUARD",
            score=weighted_score,
            feature_scores=features,
            reason=f"Distinct official domains ({a.official_domain} vs {b.official_domain}) with name_sim={s_name:.3f}, dice_core={dice_core:.3f}",
        )

    if weighted_score >= AUTO_MERGE_THRESHOLD and (s_name >= 0.72 or a.core_name_slug == b.core_name_slug):
        return EntityMatchDecision(
            left_index=a.index,
            right_index=b.index,
            left_name=a.comp.name,
            right_name=b.comp.name,
            decision="AUTO_MERGE",
            rule_id="R4_WEIGHTED_SIMILARITY",
            score=weighted_score,
            feature_scores=features,
            reason=f"Weighted similarity {weighted_score:.3f} >= {AUTO_MERGE_THRESHOLD}",
        )

    if weighted_score >= CLERICAL_REVIEW_THRESHOLD:
        return EntityMatchDecision(
            left_index=a.index,
            right_index=b.index,
            left_name=a.comp.name,
            right_name=b.comp.name,
            decision="CLERICAL_REVIEW",
            rule_id="R4_WEIGHTED_SIMILARITY",
            score=weighted_score,
            feature_scores=features,
            reason=f"Borderline similarity {weighted_score:.3f} in [{CLERICAL_REVIEW_THRESHOLD}, {AUTO_MERGE_THRESHOLD})",
        )

    return EntityMatchDecision(
        left_index=a.index,
        right_index=b.index,
        left_name=a.comp.name,
        right_name=b.comp.name,
        decision="NON_MATCH",
        rule_id="R4_WEIGHTED_SIMILARITY",
        score=weighted_score,
        feature_scores=features,
        reason=f"Below clerical threshold ({weighted_score:.3f} < {CLERICAL_REVIEW_THRESHOLD})",
    )


def score_competition_pair(a: Competition, b: Competition) -> EntityMatchDecision:
    """Public helper scoring two Competition records using the 5-rule ER matcher."""
    return _score_profiles(_build_profile(0, a), _build_profile(1, b))


# ---------------------------------------------------------------------------
# Stage 4: Season-Consistent Union-Find Clustering
# ---------------------------------------------------------------------------


class _SeasonConsistentUnionFind:
    """Disjoint-set structure that forbids transitive merges across conflicting seasons/editions."""

    def __init__(self, profiles: list[_EntityProfile]) -> None:
        n = len(profiles)
        self.parent = list(range(n))
        self.years: list[set[int]] = [{p.season_year} if p.season_year is not None else set() for p in profiles]
        self.months: list[set[int]] = [{p.season_month} if p.season_month is not None else set() for p in profiles]
        self.editions: list[set[int]] = [{p.edition_number} if p.edition_number is not None else set() for p in profiles]

    def find(self, x: int) -> int:
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, a: int, b: int) -> bool:
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return False
        combined_years = self.years[ra] | self.years[rb]
        combined_months = self.months[ra] | self.months[rb]
        combined_editions = self.editions[ra] | self.editions[rb]
        if len(combined_years) > 1 or len(combined_months) > 1 or len(combined_editions) > 1:
            return False
        if ra > rb:
            ra, rb = rb, ra
        self.parent[rb] = ra
        self.years[ra] = combined_years
        self.months[ra] = combined_months
        self.editions[ra] = combined_editions
        return True


# ---------------------------------------------------------------------------
# Stage 5: Authority-First Data Fusion (Bleiholder & Naumann 2009)
# ---------------------------------------------------------------------------


def _union_preserve_order(lists: list[list[str]]) -> list[str]:
    merged: list[str] = []
    seen_folded: set[str] = set()
    for lst in lists:
        for item in lst:
            cleaned = clean_placeholder(item)
            if not cleaned or not isinstance(cleaned, str):
                continue
            key = fold_vietnamese(cleaned) or cleaned.lower()
            if key not in seen_folded:
                seen_folded.add(key)
                merged.append(cleaned)
    return merged


def fuse_competition_cluster(
    profiles: list[_EntityProfile],
) -> tuple[Competition, list[str]]:
    """Fuse duplicate Competition profiles into one Golden Survivor record with lineage."""
    ranked = sorted(
        profiles,
        key=lambda p: (
            int(p.authority),
            1 if p.is_direct_official_source else 0,
            p.completeness,
        ),
        reverse=True,
    )
    survivor_prof = ranked[0]
    survivor = survivor_prof.comp
    fused_fields: list[str] = []

    if len(ranked) == 1:
        canonical_u = canonicalize_official_url(survivor.url) or normalize_canonical_url(survivor.url, survivor.name)
        s_year = survivor_prof.season_year
        comp_key = compute_competition_key(canonical_u, season_year=s_year)
        nat_key = survivor_prof.natural_key
        merged_urls = list(
            dict.fromkeys(
                u
                for u in (*survivor.merged_source_urls, survivor.source_url, survivor.url)
                if u and u.strip()
            )
        )
        return (
            survivor.model_copy(
                update={
                    "season_year": s_year,
                    "natural_key": nat_key,
                    "competition_key": comp_key,
                    "merged_source_urls": merged_urls,
                }
            ),
            fused_fields,
        )

    updates: dict[str, Any] = {}
    coalesce_scalar_fields = (
        "tagline",
        "target_audience",
        "team_size_min",
        "team_size_max",
        "team_description",
        "is_individual_allowed",
        "location",
        "participation_fee",
        "total_prize_pool",
        "registration_start",
        "registration_deadline",
        "event_start",
        "event_end",
        "registration_start_date",
        "registration_deadline_date",
        "event_start_date",
        "event_end_date",
        "challenge_overview",
        "submission_platform",
        "official_rules_url",
        "organizer_contact",
        "requires_advisor",
        "team_registration_deadline",
        "team_registration_deadline_date",
        "source_url",
        "bronze_key",
        "extracted_at",
        "extractor_model",
    )
    for fname in coalesce_scalar_fields:
        curr_val = getattr(survivor, fname)
        if curr_val is None or (isinstance(curr_val, str) and not curr_val.strip()):
            for other in ranked[1:]:
                cand_val = getattr(other.comp, fname)
                if cand_val is not None and (not isinstance(cand_val, str) or cand_val.strip()):
                    updates[fname] = cand_val
                    fused_fields.append(fname)
                    break

    for enum_field in ("mode", "registration_status", "eligibility_level"):
        if getattr(survivor, enum_field) == "unknown":
            for other in ranked[1:]:
                cand_enum = getattr(other.comp, enum_field)
                if cand_enum != "unknown":
                    updates[enum_field] = cand_enum
                    fused_fields.append(enum_field)
                    break

    for list_field in (
        "organizers",
        "partners_and_sponsors",
        "category",
        "allowed_majors",
        "required_skills",
    ):
        base_list = getattr(survivor, list_field)
        merged_list = _union_preserve_order([getattr(p.comp, list_field) for p in ranked])
        if len(merged_list) > len(base_list):
            updates[list_field] = merged_list
            fused_fields.append(list_field)

    if not survivor.prizes:
        richest_prizes = max((p.comp.prizes for p in ranked[1:]), key=len, default=[])
        if richest_prizes:
            updates["prizes"] = richest_prizes
            fused_fields.append("prizes")

    if not survivor.timeline_stages:
        richest_stages = max((p.comp.timeline_stages for p in ranked[1:]), key=len, default=[])
        if richest_stages:
            updates["timeline_stages"] = richest_stages
            fused_fields.append("timeline_stages")

    # Collect full lineage of merged source URLs (preserve crawl sources; exclude noisy ad URLs)
    all_urls: list[str] = []
    seen_url_canon: set[str] = set()
    for p in ranked:
        candidates = list(p.comp.merged_source_urls)
        if p.comp.source_url and p.comp.source_url.strip():
            candidates.append(p.comp.source_url.strip())
        for candidate_u in candidates:
            u_str = candidate_u.strip()
            if not u_str:
                continue
            # Skip polluted/noisy target URLs if crawl source_url is already tracked
            if u_str == (p.comp.url or "").strip() and p.authority == SourceAuthority.NOISY_OR_INVALID:
                continue
            if u_str not in all_urls:
                all_urls.append(u_str)
                seen_url_canon.add(normalize_canonical_url(u_str))
        if p.comp.url and p.authority >= SourceAuthority.AGGREGATOR_OR_MEDIA:
            u_clean = p.comp.url.strip()
            u_canon = normalize_canonical_url(u_clean)
            if u_clean and u_clean not in all_urls and u_canon not in seen_url_canon:
                all_urls.append(u_clean)
                seen_url_canon.add(u_canon)
    updates["merged_source_urls"] = all_urls

    # Recompute canonical natural_key, season_year, and competition_key on survivor
    s_year = survivor_prof.season_year or next((p.season_year for p in ranked[1:] if p.season_year is not None), None)
    s_month = survivor_prof.season_month or next((p.season_month for p in ranked[1:] if p.season_month is not None), None)
    canonical_u = canonicalize_official_url(survivor.url) or normalize_canonical_url(survivor.url, survivor.name)
    nat_key, _ = build_natural_key(
        survivor.name,
        updates.get("organizers", survivor.organizers),
        survivor.url,
        s_year,
        season_month=s_month,
        official_domain=survivor_prof.official_domain or None,
    )
    updates["season_year"] = s_year
    updates["natural_key"] = nat_key
    updates["competition_key"] = compute_competition_key(canonical_u, season_year=s_year)

    fused = survivor.model_copy(update=updates)
    return fused, fused_fields


# ---------------------------------------------------------------------------
# Public Orchestrator: 5-Stage Entity Resolution Pipeline
# ---------------------------------------------------------------------------


def resolve_competition_entities(
    competitions: list[Competition],
    *,
    source_label: str = "silver_batch",
    drop_without_official_site: bool = False,
    use_blocking: bool = True,
) -> tuple[list[Competition], EntityResolutionReport]:
    """Execute 5-stage ER (Normalization -> Blocking -> Matching -> Clustering -> Fusion)."""
    t0 = time.perf_counter()
    n = len(competitions)
    naive_comparisons = n * (n - 1) // 2

    if n == 0:
        return [], EntityResolutionReport(source_label=source_label)

    profiles = [_build_profile(idx, c) for idx, c in enumerate(competitions)]

    # Stage 2: Temporal Blocking (partition by season_year; unknown year joins all blocks)
    candidate_pairs: set[tuple[int, int]] = set()
    if use_blocking:
        blocks: dict[int, list[int]] = defaultdict(list)
        unknown_indices: list[int] = []
        for p in profiles:
            if p.season_year is None:
                unknown_indices.append(p.index)
            else:
                blocks[p.season_year].append(p.index)

        for idxs in blocks.values():
            for i in range(len(idxs)):
                for j in range(i + 1, len(idxs)):
                    a_idx, b_idx = idxs[i], idxs[j]
                    candidate_pairs.add((min(a_idx, b_idx), max(a_idx, b_idx)))

        for u_idx in unknown_indices:
            for other in profiles:
                if other.index != u_idx:
                    candidate_pairs.add((min(u_idx, other.index), max(u_idx, other.index)))
    else:
        for i in range(n):
            for j in range(i + 1, n):
                candidate_pairs.add((i, j))

    # Stage 3: Pairwise Matching
    auto_merge_edges: list[EntityMatchDecision] = []
    clerical_pairs: list[EntityMatchDecision] = []
    for i, j in sorted(candidate_pairs):
        dec = _score_profiles(profiles[i], profiles[j])
        if dec.decision == "AUTO_MERGE":
            auto_merge_edges.append(dec)
        elif dec.decision == "CLERICAL_REVIEW":
            clerical_pairs.append(dec)

    # Stage 4: Season-Consistent Union-Find Clustering (highest confidence edges first)
    uf = _SeasonConsistentUnionFind(profiles)
    cluster_rules: dict[tuple[int, int], str] = {}
    for edge in sorted(auto_merge_edges, key=lambda e: e.score, reverse=True):
        if uf.union(edge.left_index, edge.right_index):
            cluster_rules[(edge.left_index, edge.right_index)] = edge.rule_id

    groups: dict[int, list[_EntityProfile]] = defaultdict(list)
    for p in profiles:
        groups[uf.find(p.index)].append(p)

    # Stage 5: Data Fusion & DIR-022 Official Website Filtering
    resolved: list[Competition] = []
    cluster_summaries: list[EntityClusterSummary] = []
    dropped_entities: list[dict[str, Any]] = []

    for cluster_idx, (_, member_profiles) in enumerate(
        sorted(groups.items(), key=lambda kv: min(m.index for m in kv[1])),
        start=1,
    ):
        fused_comp, fused_fields = fuse_competition_cluster(member_profiles)
        member_indices = {m.index for m in member_profiles}
        used_rules = sorted(
            {
                rule_id
                for (li, ri), rule_id in cluster_rules.items()
                if li in member_indices and ri in member_indices
            }
        )
        max_auth = max(m.authority for m in member_profiles)
        if drop_without_official_site and max_auth < SourceAuthority.INSTITUTIONAL_ANNOUNCEMENT:
            dropped_entities.append(
                {
                    "name": fused_comp.name,
                    "url": fused_comp.url,
                    "source_url": fused_comp.source_url,
                    "reason": "no_official_website_after_er",
                }
            )
            continue

        resolved.append(fused_comp)
        cluster_summaries.append(
            EntityClusterSummary(
                cluster_id=cluster_idx,
                competition_key=fused_comp.competition_key or "",
                natural_key=fused_comp.natural_key or "",
                season_year=fused_comp.season_year,
                survivor_name=fused_comp.name,
                survivor_url=canonicalize_official_url(fused_comp.url) or str(fused_comp.url or ""),
                member_count=len(member_profiles),
                merged_names=[m.comp.name for m in member_profiles],
                merged_source_urls=fused_comp.merged_source_urls,
                match_rules=used_rules or ["SINGLETON"],
                fused_fields=fused_fields,
            )
        )

    # Track multi-season groups preserved distinctly (same domain or core_name across >=2 years)
    seasons_by_base: dict[str, set[int | None]] = defaultdict(set)
    for comp in resolved:
        domain = extract_official_domain(comp.url)
        _, core_slug = normalize_competition_name(comp.name)
        base_id = domain or core_slug
        seasons_by_base[base_id].add(comp.season_year)
    multi_season_groups = {
        base_id: sorted(yrs, key=lambda y: (y is None, y or 0))
        for base_id, yrs in seasons_by_base.items()
        if len(yrs) > 1
    }

    blocking_comps = len(candidate_pairs)
    reduction_pct = (
        round(((naive_comparisons - blocking_comps) / naive_comparisons) * 100.0, 2)
        if naive_comparisons > 0
        else 0.0
    )
    elapsed_ms = round((time.perf_counter() - t0) * 1000.0, 3)

    report = EntityResolutionReport(
        source_label=source_label,
        input_count=n,
        output_count=len(resolved),
        merged_duplicates_count=n - len(groups),
        dropped_no_official_count=len(dropped_entities),
        multi_season_groups=multi_season_groups,
        clerical_review_pairs=clerical_pairs,
        clusters=cluster_summaries,
        dropped_entities=dropped_entities,
        blocking_comparisons=blocking_comps,
        naive_comparisons=naive_comparisons,
        comparison_reduction_pct=reduction_pct,
        elapsed_ms=elapsed_ms,
    )
    return resolved, report


# ---------------------------------------------------------------------------
# DuckDB Native Text Similarity Audit (jaro_winkler_similarity / jaccard)
# ---------------------------------------------------------------------------


def audit_near_duplicates_duckdb(
    competitions: list[Competition],
    threshold: float = 0.78,
) -> list[dict[str, Any]]:
    """Audit potential near-duplicates using DuckDB native vectorized text similarity functions."""
    if len(competitions) < 2:
        return []

    rows: list[tuple[int, str, str, str, int, str]] = []
    for idx, comp in enumerate(competitions):
        prof = _build_profile(idx, comp)
        rows.append(
            (
                idx,
                comp.name,
                prof.core_name_slug.replace("-", " "),
                ",".join(sorted(prof.canonical_orgs)),
                prof.season_year or -1,
                prof.official_domain or prof.source_domain,
            )
        )

    con = duckdb.connect(":memory:")
    try:
        con.execute(
            """
            CREATE TABLE er_candidates (
                idx INTEGER,
                raw_name VARCHAR,
                core_name VARCHAR,
                org_tokens VARCHAR,
                season_year INTEGER,
                domain VARCHAR
            )
            """
        )
        con.executemany("INSERT INTO er_candidates VALUES (?, ?, ?, ?, ?, ?)", rows)
        matches = con.execute(
            """
            SELECT
                a.idx AS left_idx,
                b.idx AS right_idx,
                a.raw_name AS left_name,
                b.raw_name AS right_name,
                a.season_year AS left_year,
                b.season_year AS right_year,
                a.domain AS left_domain,
                b.domain AS right_domain,
                ROUND(jaro_winkler_similarity(a.core_name, b.core_name), 4) AS jw_core,
                ROUND(jaccard(a.core_name, b.core_name), 4) AS jaccard_core
            FROM er_candidates a
            JOIN er_candidates b
              ON a.idx < b.idx
             AND (a.season_year = b.season_year OR a.season_year = -1 OR b.season_year = -1)
            WHERE jaro_winkler_similarity(a.core_name, b.core_name) >= ?
            ORDER BY jw_core DESC
            """,
            [threshold],
        ).fetchall()

        return [
            {
                "left_index": r[0],
                "right_index": r[1],
                "left_name": r[2],
                "right_name": r[3],
                "left_year": None if r[4] == -1 else r[4],
                "right_year": None if r[5] == -1 else r[5],
                "left_domain": r[6],
                "right_domain": r[7],
                "jaro_winkler_core": float(r[8]),
                "jaccard_core": float(r[9]),
            }
            for r in matches
        ]
    finally:
        con.close()


# ---------------------------------------------------------------------------
# Local / R2 Raw Loaders & Benchmarks (Read-Only)
# ---------------------------------------------------------------------------


def _extract_competitions_from_json_payload(payload: Any) -> list[Competition]:
    items: list[dict[str, Any]] = []
    if isinstance(payload, list):
        items = [x for x in payload if isinstance(x, dict)]
    elif isinstance(payload, dict):
        meta = payload.get("_metadata") if isinstance(payload.get("_metadata"), dict) else {}
        det = payload.get("_deterministic") if isinstance(payload.get("_deterministic"), dict) else {}
        if "results" in payload and isinstance(payload["results"], list):
            for res in payload["results"]:
                if not isinstance(res, dict):
                    continue
                r_meta = res.get("_metadata") if isinstance(res.get("_metadata"), dict) else meta
                r_det = res.get("_deterministic") if isinstance(res.get("_deterministic"), dict) else det
                for c in res.get("competitions") or []:
                    if isinstance(c, dict):
                        items.append({**c, "_m": r_meta, "_d": r_det})
        elif "competitions" in payload and isinstance(payload["competitions"], list):
            for c in payload["competitions"]:
                if isinstance(c, dict):
                    items.append({**c, "_m": meta, "_d": det})

    comps: list[Competition] = []
    for raw in items:
        rec = dict(raw)
        m = rec.pop("_m", {}) or {}
        d = rec.pop("_d", {}) or {}
        if not rec.get("source_url") and m.get("source_url"):
            rec["source_url"] = m["source_url"]
        if not rec.get("bronze_key") and (m.get("source_key") or m.get("bronze_key")):
            rec["bronze_key"] = m.get("bronze_key") or m.get("source_key")
        if not rec.get("extracted_at") and m.get("extracted_at"):
            rec["extracted_at"] = m["extracted_at"]
        if not rec.get("official_rules_url"):
            rules = d.get("official_rules_urls") or []
            if isinstance(rules, list) and rules:
                rec["official_rules_url"] = rules[0]
        comps.append(Competition.model_validate(rec))
    return comps


def load_raw_silver_from_r2_readonly(target_date: str | None = None) -> tuple[list[Competition], str]:
    """Read-only loader fetching pre-ER Silver JSON extractions per domain from Cloudflare R2."""
    if not settings.bucket_name:
        raise RuntimeError("BUCKET_NAME is required in .env for read-only Cloudflare R2 audit.")
    s3 = settings.create_r2_client()
    paginator = s3.get_paginator("list_objects_v2")
    parsed_items: list[dict[str, Any]] = []
    for page in paginator.paginate(Bucket=settings.bucket_name, Prefix="silver/extractions/"):
        for obj in page.get("Contents", []):
            if obj.get("Size", 0) == 0:
                continue
            m = SILVER_KEY_PATTERN.match(obj["Key"])
            if m:
                domain, year, month, day, ts = m.groups()
                parsed_items.append(
                    {
                        "key": obj["Key"],
                        "domain": domain,
                        "date": f"{year}-{month}-{day}",
                        "timestamp": int(ts),
                    }
                )
    if not parsed_items:
        raise RuntimeError(f"No Silver extractions found on s3://{settings.bucket_name}/silver/extractions/")

    pool = [it for it in parsed_items if it["date"] == target_date] if target_date else parsed_items
    latest_date = target_date or max(it["date"] for it in parsed_items)
    by_domain: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for it in pool:
        by_domain[it["domain"]].append(it)
    latest_per_domain = [max(group, key=lambda x: x["timestamp"]) for group in by_domain.values()]

    raw_comps: list[Competition] = []
    for snap in sorted(latest_per_domain, key=lambda x: x["domain"]):
        body = s3.get_object(Bucket=settings.bucket_name, Key=snap["key"])["Body"].read().decode("utf-8", errors="replace")
        raw_comps.extend(_extract_competitions_from_json_payload(json.loads(body)))

    return raw_comps, f"r2:silver/extractions@{latest_date} (read-only raw)"


def run_er_benchmark(sizes: tuple[int, ...] = (10, 24, 100, 500)) -> dict[str, Any]:
    """Measure ER runtime and comparison pruning across TLCN (10-24) and KLTN (100-500) scales."""
    measurements: list[dict[str, Any]] = []
    for size in sizes:
        synthetic: list[Competition] = []
        for idx in range(size):
            base_idx = idx // 2  # inject ~50% multi-source duplicates sharing the same season
            season = 2025 + (base_idx % 3)  # 2025, 2026, 2027 across different contests
            if idx % 2 == 0:
                synthetic.append(
                    Competition(
                        name=f"AI Hackathon #{base_idx} {season}",
                        url=f"https://contest-{base_idx}.edu.vn",
                        summary=f"Cuộc thi Trí tuệ Nhân tạo sinh viên mùa {season} quy mô toàn quốc.",
                        organizers=[f"University {base_idx % 8}"],
                        category=["Artificial Intelligence"],
                        event_start=f"{season}-10-01",
                        event_end=f"{season}-10-15",
                    )
                )
            else:
                synthetic.append(
                    Competition(
                        name=f"Cuộc thi AI Hackathon #{base_idx} năm {season}",
                        url=f"https://www.contest-{base_idx}.edu.vn/trang-chu?utm_source=ybox",
                        summary=f"Thông báo cuộc thi AI sinh viên #{base_idx} năm {season}.",
                        organizers=[f"University {base_idx % 8}"],
                        category=["Artificial Intelligence"],
                        source_url=f"https://ybox.vn/cuoc-thi/ai-hackathon-{base_idx}-{season}",
                        official_rules_url=f"https://contest-{base_idx}.edu.vn/rules.pdf",
                        event_start=f"{season}-10-01",
                    )
                )

        _, rep_blocked = resolve_competition_entities(
            synthetic, source_label=f"bench_blocked_{size}", use_blocking=True
        )
        _, rep_naive = resolve_competition_entities(
            synthetic, source_label=f"bench_naive_{size}", use_blocking=False
        )
        t_duck = time.perf_counter()
        duck_hits = audit_near_duplicates_duckdb(synthetic, threshold=0.85)
        duck_ms = round((time.perf_counter() - t_duck) * 1000.0, 3)

        measurements.append(
            {
                "input_records": size,
                "resolved_entities": rep_blocked.output_count,
                "merged_duplicates": rep_blocked.merged_duplicates_count,
                "blocked_ms": rep_blocked.elapsed_ms,
                "naive_ms": rep_naive.elapsed_ms,
                "duckdb_similarity_ms": duck_ms,
                "duckdb_candidate_pairs": len(duck_hits),
                "blocking_comparisons": rep_blocked.blocking_comparisons,
                "naive_comparisons": rep_blocked.naive_comparisons,
                "comparison_reduction_pct": rep_blocked.comparison_reduction_pct,
            }
        )

    return {
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "measurements": measurements,
    }


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="ACDP v2 Entity Resolution & Deduplication (TASK-DQ-04)")
    parser.add_argument("--audit-local", type=Path, default=None, help="Audit a local Silver JSON fixture/batch")
    parser.add_argument("--audit-r2", action="store_true", help="Read-only ER audit on live Cloudflare R2 Silver JSONs")
    parser.add_argument("--drop-no-official", action="store_true", help="Drop clusters lacking an official website")
    parser.add_argument("--benchmark", action="store_true", help="Run 10/24/100/500 scaling benchmark")
    parser.add_argument("--out", type=Path, default=None, help="Optional JSON output path")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)

    if args.benchmark:
        bench = run_er_benchmark()
        print("=" * 92)
        print("ENTITY RESOLUTION SCALING BENCHMARK (Temporal Blocking vs Naive vs DuckDB SQL)")
        print("-" * 92)
        print(
            f"{'Scale':>6} | {'Resolved':>8} | {'Blocked(ms)':>11} | {'Naive(ms)':>9} | "
            f"{'DuckDB(ms)':>10} | {'Comps (Blk/Naive)':>19} | {'Pruned %':>8}"
        )
        print("-" * 92)
        for row in bench["measurements"]:
            pair_ratio = f"{row['blocking_comparisons']}/{row['naive_comparisons']}"
            print(
                f"{row['input_records']:>6} | {row['resolved_entities']:>8} | {row['blocked_ms']:>11.2f} | "
                f"{row['naive_ms']:>9.2f} | {row['duckdb_similarity_ms']:>10.2f} | "
                f"{pair_ratio:>19} | {row['comparison_reduction_pct']:>7.1f}%"
            )
        print("=" * 92)
        if args.out:
            args.out.parent.mkdir(parents=True, exist_ok=True)
            args.out.write_text(json.dumps(bench, ensure_ascii=False, indent=2), encoding="utf-8")
        return 0

    if args.audit_local is not None:
        raw_payload = json.loads(args.audit_local.read_text(encoding="utf-8"))
        comps = _extract_competitions_from_json_payload(raw_payload)
        resolved, report = resolve_competition_entities(
            comps,
            source_label=str(args.audit_local),
            drop_without_official_site=args.drop_no_official,
        )
        duck_audit = audit_near_duplicates_duckdb(comps, threshold=0.80)
        print(report.to_console_table())
        print(f"DuckDB Native Similarity Hits (>=0.80 same-season): {len(duck_audit)}")
        if args.out:
            args.out.parent.mkdir(parents=True, exist_ok=True)
            out_data = {
                "report": report.model_dump(mode="json"),
                "duckdb_similarity_hits": duck_audit,
                "resolved_entities": [
                    {
                        "competition_key": c.competition_key,
                        "natural_key": c.natural_key,
                        "season_year": c.season_year,
                        "name": c.name,
                        "url": c.url,
                        "merged_source_urls": c.merged_source_urls,
                    }
                    for c in resolved
                ],
            }
            args.out.write_text(json.dumps(out_data, ensure_ascii=False, indent=2), encoding="utf-8")
        return 0

    if args.audit_r2:
        comps, label = load_raw_silver_from_r2_readonly()
        resolved, report = resolve_competition_entities(
            comps,
            source_label=label,
            drop_without_official_site=args.drop_no_official,
        )
        duck_audit = audit_near_duplicates_duckdb(comps, threshold=0.78)
        print(report.to_console_table())
        print(f"DuckDB Native Similarity Hits (>=0.78 same-season): {len(duck_audit)}")
        for hit in duck_audit[:5]:
            print(
                f"  -> DuckDB JW={hit['jaro_winkler_core']:.3f} | {hit['left_name']!r} ({hit['left_domain']}) "
                f"<-> {hit['right_name']!r} ({hit['right_domain']})"
            )
        if args.out:
            args.out.parent.mkdir(parents=True, exist_ok=True)
            out_data = {
                "report": report.model_dump(mode="json"),
                "duckdb_similarity_hits": duck_audit,
                "resolved_summary": [
                    {
                        "competition_key": c.competition_key,
                        "natural_key": c.natural_key,
                        "season_year": c.season_year,
                        "name": c.name,
                        "url": c.url,
                        "merged_source_urls": c.merged_source_urls,
                    }
                    for c in resolved
                ],
            }
            args.out.write_text(json.dumps(out_data, ensure_ascii=False, indent=2), encoding="utf-8")
        return 0

    print("Specify --audit-local <path>, --audit-r2, or --benchmark.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
