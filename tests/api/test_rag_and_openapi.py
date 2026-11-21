"""Tests for /api/v1/rag/* (grounded, ungrounded, 503 outage, persistence) & OpenAPI 3.1 contract."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient
from openapi_spec_validator import validate

from acdp.api.main import app
from acdp.api.schemas.rag import RagCitationDTO
from acdp.api.services.rag_service import RagResult, RagUnavailableError


def test_openapi_31_contract_is_valid() -> None:
    """Validate FastAPI generated OpenAPI 3.1 schema without errors."""
    schema = app.openapi()
    validate(schema)
    paths = schema["paths"]
    for expected in (
        "/api/v1/health",
        "/api/v1/analytics/overview",
        "/api/v1/analytics/seasonality",
        "/api/v1/competitions",
        "/api/v1/competitions/{competition_key}",
        "/api/v1/auth/register",
        "/api/v1/auth/login",
        "/api/v1/bookmarks",
        "/api/v1/rag/chat",
    ):
        assert expected in paths, f"Missing OpenAPI path: {expected}"


@pytest.mark.anyio
async def test_rag_chat_persistence_ungrounded_and_outage(api_client: AsyncClient) -> None:
    em = f"test_{uuid.uuid4().hex[:8]}@hcmute.edu.vn"
    pw = "RagPass123!"
    await api_client.post("/api/v1/auth/register", json={"email": em, "full_name": "Rag User", "password": pw})
    login = await api_client.post("/api/v1/auth/login", json={"email": em, "password": pw})
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    mocked_ok = RagResult(
        answer="Tổng giải thưởng Zalo AI Challenge 2026 là $12,000 (Nguồn: https://challenge.zalo.ai).",
        citations=[
            RagCitationDTO(
                title="challenge.zalo.ai",
                url="https://challenge.zalo.ai",
                domain="challenge.zalo.ai",
                snippet="Tổng giải thưởng lên tới 12,000 USD...",
            )
        ],
        grounded=True,
        latency_ms=145,
    )
    with patch("acdp.api.routers.rag.query_rag", new=AsyncMock(return_value=mocked_ok)):
        r1 = await api_client.post(
            "/api/v1/rag/chat",
            json={"message": "Giải thưởng Zalo AI Challenge?", "domain_filter": "challenge.zalo.ai"},
            headers=headers,
        )
    assert r1.status_code == 200
    body = r1.json()
    assert body["grounded"] is True
    assert len(body["citations"]) == 1
    session_id = body["session_id"]

    # Verify session & messages persisted in PostgreSQL 18
    sess_resp = await api_client.get("/api/v1/rag/sessions", headers=headers)
    assert sess_resp.status_code == 200
    assert any(s["id"] == session_id for s in sess_resp.json())

    msg_resp = await api_client.get(f"/api/v1/rag/sessions/{session_id}/messages", headers=headers)
    assert msg_resp.status_code == 200
    assert len(msg_resp.json()) == 2
    assert msg_resp.json()[1]["citations"][0]["url"] == "https://challenge.zalo.ai"

    # Ungrounded response (DIR-004)
    mocked_ungrounded = RagResult(
        answer="Chưa tìm thấy điều khoản xác thực.",
        citations=[],
        grounded=False,
        latency_ms=40,
    )
    with patch("acdp.api.routers.rag.query_rag", new=AsyncMock(return_value=mocked_ungrounded)):
        r2 = await api_client.post(
            "/api/v1/rag/chat",
            json={"session_id": session_id, "message": "Cuộc thi không tồn tại là gì?"},
            headers=headers,
        )
    assert r2.status_code == 200
    assert r2.json()["grounded"] is False
    assert r2.json()["citations"] == []

    # Outage / timeout returns HTTP 503 (EC-A4)
    with patch("acdp.api.routers.rag.query_rag", new=AsyncMock(side_effect=RagUnavailableError("timeout"))):
        r3 = await api_client.post(
            "/api/v1/rag/chat",
            json={"message": "Test timeout"},
        )
    assert r3.status_code == 503
