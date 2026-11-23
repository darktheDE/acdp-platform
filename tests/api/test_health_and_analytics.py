"""Tests for /api/v1/health, /api/v1/analytics/*, and /api/v1/competitions*."""

from __future__ import annotations

import time
from unittest.mock import patch

import pytest
from httpx import AsyncClient


@pytest.mark.anyio
async def test_health_endpoint_reports_db_and_gold_count(api_client: AsyncClient) -> None:
    with patch("acdp.api.routers.health.check_qdrant_health", return_value="up"):
        resp = await api_client.get("/api/v1/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["postgres"] == "up"
    assert body["duckdb"] == "up"
    assert body["qdrant"] == "up"
    assert body["gold_competitions_count"] >= 18


@pytest.mark.anyio
async def test_analytics_overview_and_seasonality_match_gold_star_schema(api_client: AsyncClient) -> None:
    t0 = time.perf_counter()
    resp = await api_client.get("/api/v1/analytics/overview")
    elapsed_ms = (time.perf_counter() - t0) * 1000

    assert resp.status_code == 200
    assert elapsed_ms < 5000, f"Unexpectedly slow analytics query: {elapsed_ms:.1f} ms"
    data = resp.json()
    assert data["kpi"]["total_competitions"] >= 18
    assert data["kpi"]["unique_domains"] == 5
    assert len(data["domains"]) == 5
    assert sum(d["allocated_prize_vnd"] for d in data["domains"]) == data["kpi"]["total_prize_pool_vnd"]
    assert len(data["seasonality"]) > 0
    assert len(data["mode_team_matrix"]) > 0
    assert len(data["top_organizers"]) > 0

    seas_resp = await api_client.get("/api/v1/analytics/seasonality")
    assert seas_resp.status_code == 200
    assert len(seas_resp.json()) == len(data["seasonality"])


@pytest.mark.anyio
async def test_competitions_explorer_filters_detail_and_sql_injection_safety(api_client: AsyncClient) -> None:
    resp = await api_client.get("/api/v1/competitions", params={"page": 1, "page_size": 50})
    assert resp.status_code == 200
    payload = resp.json()
    total_comps = payload["total"]
    assert total_comps >= 18
    assert len(payload["items"]) == total_comps

    # Domain filter
    ai_resp = await api_client.get("/api/v1/competitions", params={"domain": "ai-data-science"})
    assert ai_resp.status_code == 200
    assert 0 < ai_resp.json()["total"] <= total_comps

    # SQL injection attempt (EC-A5) must be safely parameterized, returning 0 matches, not 500
    sqli_resp = await api_client.get("/api/v1/competitions", params={"q": "' OR 1=1; DROP TABLE dim_competition;--"})
    assert sqli_resp.status_code == 200
    assert sqli_resp.json()["total"] == 0

    # Competition detail endpoint
    first_key = payload["items"][0]["competition_key"]
    detail_resp = await api_client.get(f"/api/v1/competitions/{first_key}")
    assert detail_resp.status_code == 200
    detail = detail_resp.json()
    assert detail["competition_key"] == first_key
    assert isinstance(detail["prizes"], list)
    assert isinstance(detail["timeline_stages"], list)

    # Non-existent key returns 404
    missing_resp = await api_client.get("/api/v1/competitions/" + ("0" * 64))
    assert missing_resp.status_code == 404
