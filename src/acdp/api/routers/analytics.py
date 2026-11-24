"""Gold Analytics OLAP router (/api/v1/analytics/*)."""

from __future__ import annotations

import duckdb
from fastapi import APIRouter, Depends

from acdp.api.dependencies import get_duckdb
from acdp.api.schemas.analytics import AnalyticsDashboardDTO, SeasonalityMetricDTO
from acdp.api.services.gold_queries import fetch_analytics_overview, fetch_seasonality

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/overview", response_model=AnalyticsDashboardDTO)
def get_analytics_overview(con: duckdb.DuckDBPyConnection = Depends(get_duckdb)) -> AnalyticsDashboardDTO:
    """Return full Gold Star Schema dashboard metrics for /dashboard."""
    return fetch_analytics_overview(con)


@router.get("/seasonality", response_model=list[SeasonalityMetricDTO])
def get_analytics_seasonality(con: duckdb.DuckDBPyConnection = Depends(get_duckdb)) -> list[SeasonalityMetricDTO]:
    """Return academic-term & monthly competition seasonality."""
    return fetch_seasonality(con)
