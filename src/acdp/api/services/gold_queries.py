"""Parameterized DuckDB Gold Star Schema queries (SPEC-0003 & SPEC-0004 EC-A5)."""

from __future__ import annotations

from typing import Any

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

_ALLOWED_SORTS: dict[str, str] = {
    "prize_desc": "total_prize_vnd DESC, name ASC",
    "prize_asc": "total_prize_vnd ASC, name ASC",
    "name_asc": "name ASC",
    "deadline_asc": "registration_deadline_raw ASC NULLS LAST, name ASC",
}


def fetch_analytics_overview(con: duckdb.DuckDBPyConnection) -> AnalyticsDashboardDTO:
    """Fetch KPI overview, domain analytics, seasonality, mode/team matrix, and top organizers."""
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

    seasonality = fetch_seasonality(con)

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


def fetch_seasonality(con: duckdb.DuckDBPyConnection) -> list[SeasonalityMetricDTO]:
    """Fetch academic term & monthly competition seasonality from mart_seasonality_academic."""
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
    """Filter and paginate competitions from mart_competition_explorer using prepared placeholders."""
    clauses: list[str] = []
    params: list[Any] = []

    if q and q.strip():
        like = f"%{q.strip()}%"
        clauses.append("(name ILIKE ? OR COALESCE(summary, '') ILIKE ? OR COALESCE(tagline, '') ILIKE ?)")
        params.extend([like, like, like])
    if domain and domain.strip():
        clauses.append("list_contains(domain_slugs, ?)")
        params.append(domain.strip().lower())
    if mode and mode.strip():
        clauses.append("LOWER(mode_canonical) = LOWER(?)")
        params.append(mode.strip())
    if is_free is not None:
        clauses.append("is_free = ?")
        params.append(is_free)
    if status and status.strip():
        clauses.append("LOWER(COALESCE(registration_status, '')) = LOWER(?)")
        params.append(status.strip())

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


def fetch_competition_detail(con: duckdb.DuckDBPyConnection, competition_key: str) -> CompetitionDetailDTO | None:
    """Fetch complete competition profile including prize tiers and timeline stages."""
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
    """Return {competition_key: (mode_canonical, total_prize_vnd)} for saved bookmarks."""
    if not keys:
        return {}
    placeholders = ", ".join(["?"] * len(keys))
    rows = con.execute(
        f"""
        SELECT competition_key, mode_canonical, total_prize_vnd
        FROM mart_competition_explorer
        WHERE competition_key IN ({placeholders})
        """,
        keys,
    ).fetchall()
    return {str(r[0]): (str(r[1]), int(r[2] or 0)) for r in rows}
