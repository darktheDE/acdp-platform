"""Parameterized DuckDB Gold Star Schema queries with In-Memory TTL Cache (SPEC-0003, SPEC-0004, TASK-CLD-05)."""

from __future__ import annotations

import copy
import threading
import time
from collections import OrderedDict
from collections.abc import Callable
from typing import Any, TypeVar

import duckdb

from acdp.api.schemas.analytics import (
    AnalyticsDashboardDTO,
    DomainMetricDTO,
    KpiOverviewDTO,
    ModeTeamMetricDTO,
    OrganizerMetricDTO,
    SeasonalityMetricDTO,
)
from acdp.api.schemas.competitions import (
    CompetitionDetailDTO,
    CompetitionSummaryDTO,
    PrizeTierDTO,
    TimelineStageDTO,
)
from acdp.config import settings

_T = TypeVar("_T")

_COVERED_GOLD_MARTS: tuple[str, ...] = (
    "mart_kpi_overview",
    "mart_domain_analytics",
    "mart_seasonality_academic",
    "mart_organizer_ecosystem",
    "mart_team_and_mode_matrix",
    "mart_competition_explorer",
)

_ALLOWED_SORTS: dict[str, str] = {
    "prize_desc": "total_prize_vnd DESC, name ASC",
    "prize_asc": "total_prize_vnd ASC, name ASC",
    "name_asc": "name ASC",
    "deadline_asc": "registration_deadline_raw ASC NULLS LAST, name ASC",
}


class GoldMartsTTLCache:
    """Thread-safe bounded In-Memory TTL Cache for Gold mart_* query results."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._entries: OrderedDict[tuple[Any, ...], tuple[float, Any]] = OrderedDict()
        self._hits = 0
        self._misses = 0
        self._evictions = 0

    def get_or_set(self, key: tuple[Any, ...], loader: Callable[[], _T]) -> _T:
        """Return cached value within TTL or compute, cache, and return a fresh result."""
        ttl_seconds = settings.gold_mart_cache_ttl_seconds
        if not settings.gold_mart_cache_enabled or ttl_seconds <= 0:
            return loader()

        now = time.monotonic()
        with self._lock:
            entry = self._entries.get(key)
            if entry is not None:
                expires_at, value = entry
                if now < expires_at:
                    self._entries.move_to_end(key)
                    self._hits += 1
                    return copy.deepcopy(value)
                del self._entries[key]
                self._evictions += 1

        value = loader()

        with self._lock:
            max_entries = max(1, settings.gold_mart_cache_max_entries)
            self._entries[key] = (time.monotonic() + ttl_seconds, copy.deepcopy(value))
            self._entries.move_to_end(key)
            while len(self._entries) > max_entries:
                self._entries.popitem(last=False)
                self._evictions += 1
            self._misses += 1

        return value

    def invalidate(self) -> None:
        """Clear all cached Gold Mart entries and reset hit/miss counters."""
        with self._lock:
            self._entries.clear()
            self._hits = 0
            self._misses = 0
            self._evictions = 0

    def stats(self) -> dict[str, Any]:
        """Return cache telemetry including hit rate across the 6 Gold mart_* tables."""
        with self._lock:
            now = time.monotonic()
            expired_keys = [k for k, (exp, _) in self._entries.items() if now >= exp]
            for k in expired_keys:
                del self._entries[k]
                self._evictions += 1

            total_requests = self._hits + self._misses
            hit_rate_pct = round((self._hits / total_requests) * 100, 2) if total_requests > 0 else 0.0
            return {
                "enabled": settings.gold_mart_cache_enabled and settings.gold_mart_cache_ttl_seconds > 0,
                "ttl_seconds": settings.gold_mart_cache_ttl_seconds,
                "max_entries": settings.gold_mart_cache_max_entries,
                "cached_entries": len(self._entries),
                "hits": self._hits,
                "misses": self._misses,
                "evictions": self._evictions,
                "hit_rate_pct": hit_rate_pct,
                "covered_marts": list(_COVERED_GOLD_MARTS),
            }


_gold_mart_cache = GoldMartsTTLCache()


def invalidate_gold_mart_cache() -> None:
    """Invalidate the Gold Marts TTL cache (called after R2 refresh or in test resets)."""
    _gold_mart_cache.invalidate()


def get_gold_mart_cache_stats() -> dict[str, Any]:
    """Return current In-Memory TTL Cache statistics for the 6 Gold mart_* tables."""
    return _gold_mart_cache.stats()


def _load_seasonality(con: duckdb.DuckDBPyConnection) -> list[SeasonalityMetricDTO]:
    rows = con.execute("""
        SELECT year, month, academic_year, academic_term, competition_count, total_prize_vnd
        FROM mart_seasonality_academic
        ORDER BY year ASC NULLS LAST, month ASC NULLS LAST
    """).fetchall()
    return [
        SeasonalityMetricDTO(
            year=int(r[0]) if r[0] is not None else None,
            month=int(r[1]) if r[1] is not None else None,
            academic_year=str(r[2]),
            academic_term=str(r[3]),  # type: ignore[arg-type]
            competition_count=int(r[4]),
            total_prize_vnd=int(r[5] or 0),
        )
        for r in rows
    ]


def fetch_analytics_overview(con: duckdb.DuckDBPyConnection) -> AnalyticsDashboardDTO:
    """Fetch KPI overview, domain analytics, seasonality, mode/team matrix, and top organizers (TTL cached)."""

    def _load() -> AnalyticsDashboardDTO:
        kpi_row = con.execute("""
            SELECT
                total_competitions,
                open_competitions,
                total_prize_pool_vnd,
                free_participation_pct,
                scholarship_competitions,
                avg_team_size_max,
                unique_domains,
                unique_organizers
            FROM mart_kpi_overview
        """).fetchone()

        kpi = (
            KpiOverviewDTO(
                total_competitions=int(kpi_row[0]),
                open_competitions=int(kpi_row[1]),
                total_prize_pool_vnd=int(kpi_row[2]),
                free_participation_pct=float(kpi_row[3] or 0.0),
                scholarship_competitions=int(kpi_row[4]),
                avg_team_size_max=float(kpi_row[5] or 0.0),
                unique_domains=int(kpi_row[6]),
                unique_organizers=int(kpi_row[7]),
            )
            if kpi_row
            else KpiOverviewDTO(
                total_competitions=0,
                open_competitions=0,
                total_prize_pool_vnd=0,
                free_participation_pct=0.0,
                scholarship_competitions=0,
                avg_team_size_max=0.0,
                unique_domains=0,
                unique_organizers=0,
            )
        )

        domain_rows = con.execute("""
            SELECT domain_slug, domain_group, competition_count, ROUND(allocated_prize_vnd), free_count
            FROM mart_domain_analytics
            ORDER BY display_order ASC
        """).fetchall()
        domains = [
            DomainMetricDTO(
                domain_slug=str(r[0]),
                domain_group=str(r[1]),
                competition_count=int(r[2]),
                allocated_prize_vnd=int(r[3] or 0),
                free_count=int(r[4]),
            )
            for r in domain_rows
        ]

        seasonality = _load_seasonality(con)

        matrix_rows = con.execute("""
            SELECT mode_canonical, team_profile, competition_count, total_prize_vnd
            FROM mart_team_and_mode_matrix
            ORDER BY competition_count DESC, mode_canonical ASC
        """).fetchall()
        mode_team_matrix = [
            ModeTeamMetricDTO(
                mode_canonical=str(r[0]),  # type: ignore[arg-type]
                team_profile=str(r[1]),
                competition_count=int(r[2]),
                total_prize_vnd=int(r[3] or 0),
            )
            for r in matrix_rows
        ]

        org_rows = con.execute("""
            SELECT organizer_slug, organizer_name, organizer_tier, role_type, competition_count, ROUND(allocated_prize_vnd)
            FROM mart_organizer_ecosystem
            ORDER BY competition_count DESC, allocated_prize_vnd DESC, organizer_name ASC
            LIMIT 20
        """).fetchall()
        top_organizers = [
            OrganizerMetricDTO(
                organizer_slug=str(r[0]),
                organizer_name=str(r[1]),
                organizer_tier=str(r[2]),
                role_type=str(r[3]),  # type: ignore[arg-type]
                competition_count=int(r[4]),
                allocated_prize_vnd=int(r[5] or 0),
            )
            for r in org_rows
        ]

        return AnalyticsDashboardDTO(
            kpi=kpi,
            domains=domains,
            seasonality=seasonality,
            mode_team_matrix=mode_team_matrix,
            top_organizers=top_organizers,
        )

    return _gold_mart_cache.get_or_set(("overview",), _load)


def fetch_seasonality(con: duckdb.DuckDBPyConnection) -> list[SeasonalityMetricDTO]:
    """Fetch academic term & monthly competition seasonality from mart_seasonality_academic (TTL cached)."""
    return _gold_mart_cache.get_or_set(("seasonality",), lambda: _load_seasonality(con))


def fetch_competitions(
    con: duckdb.DuckDBPyConnection,
    *,
    q: str | None = None,
    domain: str | None = None,
    mode: str | None = None,
    is_free: bool | None = None,
    status: str | None = None,
    sort: str = "prize_desc",
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[CompetitionSummaryDTO], int]:
    """Filter and paginate competitions from mart_competition_explorer using prepared placeholders (TTL cached)."""
    q_norm = q.strip() if q and q.strip() else None
    domain_norm = domain.strip().lower() if domain and domain.strip() else None
    mode_norm = mode.strip().lower() if mode and mode.strip() else None
    status_norm = status.strip().lower() if status and status.strip() else None
    cache_key = ("competitions", q_norm, domain_norm, mode_norm, is_free, status_norm, sort, page, page_size)

    def _load() -> tuple[list[CompetitionSummaryDTO], int]:
        clauses: list[str] = []
        params: list[Any] = []

        if q_norm:
            like = f"%{q_norm}%"
            clauses.append("(name ILIKE ? OR COALESCE(summary, '') ILIKE ? OR COALESCE(tagline, '') ILIKE ?)")
            params.extend([like, like, like])
        if domain_norm:
            clauses.append("list_contains(domain_slugs, ?)")
            params.append(domain_norm)
        if mode_norm:
            clauses.append("LOWER(mode_canonical) = LOWER(?)")
            params.append(mode_norm)
        if is_free is not None:
            clauses.append("is_free = ?")
            params.append(is_free)
        if status_norm:
            clauses.append("LOWER(COALESCE(registration_status, '')) = LOWER(?)")
            params.append(status_norm)

        where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        order_sql = _ALLOWED_SORTS.get(sort, _ALLOWED_SORTS["prize_desc"])

        total_row = con.execute(f"SELECT COUNT(*) FROM mart_competition_explorer {where_sql}", params).fetchone()
        total = int(total_row[0]) if total_row else 0

        offset = (page - 1) * page_size
        rows = con.execute(
            f"""
            SELECT
                competition_key,
                name,
                tagline,
                canonical_url,
                mode_canonical,
                is_free,
                total_prize_vnd,
                has_scholarship,
                registration_status,
                registration_deadline_raw,
                domain_groups,
                domain_slugs,
                team_size_min,
                team_size_max,
                team_profile
            FROM mart_competition_explorer
            {where_sql}
            ORDER BY {order_sql}
            LIMIT ? OFFSET ?
            """,
            [*params, page_size, offset],
        ).fetchall()

        items = [
            CompetitionSummaryDTO(
                competition_key=str(r[0]),
                name=str(r[1]),
                tagline=r[2],
                canonical_url=str(r[3]),
                mode_canonical=str(r[4]),
                is_free=bool(r[5]),
                total_prize_vnd=int(r[6] or 0),
                has_scholarship=bool(r[7]),
                registration_status=r[8],
                registration_deadline_raw=r[9],
                domain_groups=list(r[10] or []),
                domain_slugs=list(r[11] or []),
                team_size_min=int(r[12]) if r[12] is not None else None,
                team_size_max=int(r[13]) if r[13] is not None else None,
                team_profile=r[14],
            )
            for r in rows
        ]
        return items, total

    return _gold_mart_cache.get_or_set(cache_key, _load)


def fetch_competition_detail(con: duckdb.DuckDBPyConnection, competition_key: str) -> CompetitionDetailDTO | None:
    """Fetch complete competition profile including prize tiers and timeline stages (TTL cached)."""

    def _load() -> CompetitionDetailDTO | None:
        row = con.execute(
            """
            SELECT
                competition_sk,
                competition_key,
                name,
                tagline,
                canonical_url,
                mode_canonical,
                is_free,
                total_prize_vnd,
                has_scholarship,
                registration_status,
                registration_deadline_raw,
                domain_groups,
                domain_slugs,
                team_size_min,
                team_size_max,
                team_profile,
                summary,
                target_audience,
                location,
                submission_platform,
                challenge_overview,
                organizers,
                partners_and_sponsors
            FROM mart_competition_explorer
            WHERE competition_key = ?
            """,
            [competition_key],
        ).fetchone()
        if row is None:
            return None

        comp_sk = int(row[0])
        prize_rows = con.execute(
            """
            SELECT tier_rank, tier_name, reward_description, estimated_value_vnd, is_scholarship
            FROM fact_prize_tiers
            WHERE competition_sk = ?
            ORDER BY tier_rank ASC
            """,
            [comp_sk],
        ).fetchall()
        stage_rows = con.execute(
            """
            SELECT stage_order, stage_name, start_date_raw, end_date_raw, description
            FROM fact_timeline_stages
            WHERE competition_sk = ?
            ORDER BY stage_order ASC
            """,
            [comp_sk],
        ).fetchall()

        return CompetitionDetailDTO(
            competition_key=str(row[1]),
            name=str(row[2]),
            tagline=row[3],
            canonical_url=str(row[4]),
            mode_canonical=str(row[5]),
            is_free=bool(row[6]),
            total_prize_vnd=int(row[7] or 0),
            has_scholarship=bool(row[8]),
            registration_status=row[9],
            registration_deadline_raw=row[10],
            domain_groups=list(row[11] or []),
            domain_slugs=list(row[12] or []),
            team_size_min=int(row[13]) if row[13] is not None else None,
            team_size_max=int(row[14]) if row[14] is not None else None,
            team_profile=row[15],
            summary=row[16],
            target_audience=row[17],
            location=row[18],
            submission_platform=row[19],
            challenge_overview=row[20],
            organizers=list(row[21] or []),
            partners_and_sponsors=list(row[22] or []),
            prizes=[
                PrizeTierDTO(
                    tier_rank=int(p[0]),
                    tier_name=str(p[1]),
                    reward_description=str(p[2]),
                    estimated_value_vnd=int(p[3] or 0),
                    is_scholarship=bool(p[4]),
                )
                for p in prize_rows
            ],
            timeline_stages=[
                TimelineStageDTO(
                    stage_order=int(s[0]),
                    stage_name=str(s[1]),
                    start_date_raw=s[2],
                    end_date_raw=s[3],
                    description=s[4],
                )
                for s in stage_rows
            ],
        )

    return _gold_mart_cache.get_or_set(("competition_detail", competition_key), _load)


def check_competition_name(con: duckdb.DuckDBPyConnection, competition_key: str) -> str | None:
    """Return canonical competition name if competition_key exists in Gold, else None."""
    row = con.execute(
        "SELECT name FROM dim_competition WHERE competition_key = ?",
        [competition_key],
    ).fetchone()
    return str(row[0]) if row else None


def fetch_gold_metadata_map(
    con: duckdb.DuckDBPyConnection, keys: list[str]
) -> dict[str, tuple[str, int]]:
    """Return {competition_key: (mode_canonical, total_prize_vnd)} for saved bookmarks (TTL cached)."""
    if not keys:
        return {}
    sorted_keys = tuple(sorted(set(keys)))

    def _load() -> dict[str, tuple[str, int]]:
        placeholders = ", ".join(["?"] * len(sorted_keys))
        rows = con.execute(
            f"""
            SELECT competition_key, mode_canonical, total_prize_vnd
            FROM mart_competition_explorer
            WHERE competition_key IN ({placeholders})
            """,
            list(sorted_keys),
        ).fetchall()
        return {str(r[0]): (str(r[1]), int(r[2] or 0)) for r in rows}

    return _gold_mart_cache.get_or_set(("metadata_map", sorted_keys), _load)
