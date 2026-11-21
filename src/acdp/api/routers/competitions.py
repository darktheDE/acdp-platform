"""Competition Explorer & Detail router (/api/v1/competitions/*)."""

from __future__ import annotations

import duckdb
from fastapi import APIRouter, Depends, HTTPException, Query, status

from acdp.api.dependencies import get_duckdb
from acdp.api.schemas.competitions import CompetitionDetailDTO, PaginatedCompetitionsDTO
from acdp.api.services.gold_queries import fetch_competition_detail, fetch_competitions

router = APIRouter(prefix="/competitions", tags=["Competitions"])


@router.get("", response_model=PaginatedCompetitionsDTO)
def list_competitions(
    q: str | None = Query(default=None, max_length=200),
    domain: str | None = Query(default=None, max_length=100),
    mode: str | None = Query(default=None, max_length=32),
    is_free: bool | None = Query(default=None),
    reg_status: str | None = Query(default=None, alias="status", max_length=32),
    sort: str = Query(default="prize_desc", pattern="^(prize_desc|prize_asc|name_asc|deadline_asc)$"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    con: duckdb.DuckDBPyConnection = Depends(get_duckdb),
) -> PaginatedCompetitionsDTO:
    """List, search, and filter academic competitions from Gold mart_competition_explorer."""
    items, total = fetch_competitions(
        con,
        q=q,
        domain=domain,
        mode=mode,
        is_free=is_free,
        status=reg_status,
        sort=sort,
        page=page,
        page_size=page_size,
    )
    return PaginatedCompetitionsDTO(items=items, total=total, page=page, page_size=page_size)


@router.get("/{competition_key}", response_model=CompetitionDetailDTO)
def get_competition_detail(
    competition_key: str,
    con: duckdb.DuckDBPyConnection = Depends(get_duckdb),
) -> CompetitionDetailDTO:
    """Return full competition profile with prize tiers and timeline stages."""
    detail = fetch_competition_detail(con, competition_key)
    if detail is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Competition '{competition_key}' not found.",
        )
    return detail
