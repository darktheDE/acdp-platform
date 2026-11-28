"""OWASP Top 10 (2025/2026) & LLM10:2025 Security Hardening tests (TASK-SEC-01)."""

from __future__ import annotations

import sys
import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from acdp.api.middleware.security import (
    MultiTierRateLimiter,
    SecurityHardeningMiddleware,
    register_security_exception_handlers,
    reset_rate_limiter,
)
from acdp.api.schemas.rag import RagCitationDTO
from acdp.api.services.rag_service import RagResult
from acdp.config import DEFAULT_DEV_JWT_SECRET, AppConfig, settings


async def _register_and_login(client: AsyncClient) -> dict[str, str]:
    email = f"test_{uuid.uuid4().hex[:8]}@hcmute.edu.vn"
    password = "SecurePass123!"
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "full_name": "Sec User", "password": password},
    )
    assert reg.status_code == 201
    login = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert login.status_code == 200
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


@pytest.mark.anyio
async def test_g3_rag_chat_and_query_require_authentication(api_client: AsyncClient) -> None:
    """Gate G3 (OWASP A01:2025): Anonymous requests to /rag/chat and /rag/query return 401."""
    for path in ("/api/v1/rag/chat", "/api/v1/rag/query"):
        no_auth = await api_client.post(path, json={"message": "Giải thưởng cuộc thi AI là bao nhiêu?"})
        assert no_auth.status_code == 401

        bad_auth = await api_client.post(
            path,
            json={"message": "Giải thưởng cuộc thi AI là bao nhiêu?"},
            headers={"Authorization": "Bearer invalid.jwt.token"},
        )
        assert bad_auth.status_code == 401


@pytest.mark.anyio
async def test_g4_ai_rate_limiting_per_user_day_and_global_rpm(
    api_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Gate G4 (LLM10:2025): Enforce 5/min/user, 30/day/user, and 10 RPM global before calling RAG."""
    reset_rate_limiter()
    headers_u1 = await _register_and_login(api_client)
    headers_u2 = await _register_and_login(api_client)
    headers_u3 = await _register_and_login(api_client)

    mocked_ok = RagResult(
        answer="Giải thưởng là $10,000 (Nguồn: https://challenge.zalo.ai).",
        citations=[
            RagCitationDTO(
                title="challenge.zalo.ai",
                url="https://challenge.zalo.ai",
                domain="challenge.zalo.ai",
                snippet="Giải thưởng 10,000 USD",
            )
        ],
        grounded=True,
        latency_ms=50,
    )
    mock_query = AsyncMock(return_value=mocked_ok)

    with patch("acdp.api.routers.rag.query_rag", new=mock_query):
        # User 1 succeeds 5 times in 1 minute
        for idx in range(5):
            resp = await api_client.post(
                "/api/v1/rag/chat",
                json={"message": f"Câu hỏi hợp lệ số {idx + 1}"},
                headers=headers_u1,
            )
            assert resp.status_code == 200
        assert mock_query.call_count == 5

        # 6th request for User 1 within 1 minute is blocked with 429 + Retry-After before RAG executes
        blocked = await api_client.post(
            "/api/v1/rag/chat",
            json={"message": "Câu hỏi vượt ngưỡng phút"},
            headers=headers_u1,
        )
        assert blocked.status_code == 429
        assert int(blocked.headers["Retry-After"]) >= 1
        assert blocked.headers["X-RateLimit-Tier"] == "ai_user_minute"
        assert mock_query.call_count == 5

        # User 2 takes the next 5 slots (total global = 10 RPM), then User 3 hits Global 10 RPM cap
        for idx in range(5):
            resp = await api_client.post(
                "/api/v1/rag/query",
                json={"message": f"User 2 câu hỏi {idx + 1}"},
                headers=headers_u2,
            )
            assert resp.status_code == 200
        assert mock_query.call_count == 10

        global_blocked = await api_client.post(
            "/api/v1/rag/chat",
            json={"message": "User 3 vượt global RPM"},
            headers=headers_u3,
        )
        assert global_blocked.status_code == 429
        assert int(global_blocked.headers["Retry-After"]) >= 1
        assert global_blocked.headers["X-RateLimit-Tier"] == "ai_global_rpm"
        assert mock_query.call_count == 10

    # Verify daily 30/day/user ceiling using an isolated MultiTierRateLimiter
    monkeypatch.setattr(settings, "rate_limit_ai_per_minute", 100)
    monkeypatch.setattr(settings, "rate_limit_ai_global_rpm", 100)
    monkeypatch.setattr(settings, "rate_limit_ai_per_day", 30)
    limiter = MultiTierRateLimiter()
    for _ in range(30):
        assert limiter.check_ai_limit("user-daily-check").allowed is True
    day_blocked = limiter.check_ai_limit("user-daily-check")
    assert day_blocked.allowed is False
    assert day_blocked.tier == "ai_user_day"
    assert day_blocked.retry_after >= 1


@pytest.mark.anyio
async def test_g4_auth_and_public_rate_limiting_per_ip(
    api_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Gate G4 (OWASP A07:2025): Auth limited to 10/min/IP, Public limited to 60/min/IP, /health exempt."""
    reset_rate_limiter()
    # Auth tier: 10 req/min/IP on /auth/login
    for _ in range(10):
        resp = await api_client.post(
            "/api/v1/auth/login",
            json={"email": "nobody@hcmute.edu.vn", "password": "wrong-password"},
            headers={"X-Forwarded-For": "203.0.113.10"},
        )
        assert resp.status_code == 401

    auth_blocked = await api_client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@hcmute.edu.vn", "password": "wrong-password"},
        headers={"X-Forwarded-For": "203.0.113.10"},
    )
    assert auth_blocked.status_code == 429
    assert int(auth_blocked.headers["Retry-After"]) >= 1
    assert auth_blocked.headers["X-RateLimit-Tier"] == "auth_ip_minute"

    # Public tier: 60 req/min/IP; test with tightened config override and verify /health remains exempt
    reset_rate_limiter()
    monkeypatch.setattr(settings, "rate_limit_public_per_minute", 3)
    for _ in range(3):
        ok_resp = await api_client.get(
            "/api/v1/analytics/seasonality",
            headers={"X-Forwarded-For": "203.0.113.20"},
        )
        assert ok_resp.status_code == 200

    pub_blocked = await api_client.get(
        "/api/v1/analytics/seasonality",
        headers={"X-Forwarded-For": "203.0.113.20"},
    )
    assert pub_blocked.status_code == 429
    assert pub_blocked.headers["X-RateLimit-Tier"] == "public_ip_minute"

    with patch("acdp.api.routers.health.check_qdrant_health", return_value="up"):
        health_resp = await api_client.get(
            "/api/v1/health",
            headers={"X-Forwarded-For": "203.0.113.20"},
        )
    assert health_resp.status_code == 200


def test_g4_llm_max_output_tokens_capped_at_600(monkeypatch: pytest.MonkeyPatch) -> None:
    """Gate G4 (LLM10:2025): Gemini, Groq/OpenRouter, and LiteLLM enforce max_output_tokens=600."""
    from acdp.api.services import rag_service

    cfg = AppConfig(
        _env_file=None,
        gemini_api_key="gem-key",
        groq_api_key="groq-key",
        openrouter_api_key="or-key",
        llm_fallback_enabled=True,
        use_litellm_router=False,
        rag_max_output_tokens=600,
    )
    assert cfg.rag_max_output_tokens == 600
    monkeypatch.setattr(rag_service, "settings", cfg)

    # 1. Gemini GenerateContentConfig
    fake_genai = MagicMock()
    fake_genai.models.generate_content.return_value = SimpleNamespace(text="Trả lời ngắn gọn.")
    monkeypatch.setattr(rag_service, "_get_genai", lambda: fake_genai)

    ans, provider = rag_service._generate_answer_with_fallback("Thể lệ?", "Ngữ cảnh mẫu.")
    assert provider == "gemini"
    assert ans == "Trả lời ngắn gọn."
    genai_cfg = fake_genai.models.generate_content.call_args.kwargs["config"]
    assert genai_cfg.max_output_tokens == 600

    # 2. OpenAI-compatible (Groq / OpenRouter)
    captured_payloads: list[dict] = []

    def fake_post(url: str, headers=None, json=None):
        captured_payloads.append(json)
        return MagicMock(
            status_code=200,
            raise_for_status=lambda: None,
            json=lambda: {"choices": [{"message": {"content": "OK Groq"}}]},
        )

    fake_http = MagicMock()
    fake_http.post.side_effect = fake_post
    out = rag_service._generate_with_openai_compatible(
        provider="groq",
        base_url="https://api.groq.com/openai/v1/chat/completions",
        api_key="gsk-test",
        model="llama-3.3-70b-versatile",
        user_prompt="Prompt",
        http_client=fake_http,
    )
    assert out == "OK Groq"
    assert captured_payloads[0]["max_tokens"] == 600

    # 3. LiteLLM router
    mock_litellm = MagicMock()
    mock_litellm.completion.return_value = SimpleNamespace(
        model="gemini/gemini-3.5-flash-lite",
        choices=[SimpleNamespace(message=SimpleNamespace(content="OK LiteLLM"))],
    )
    monkeypatch.setitem(sys.modules, "litellm", mock_litellm)
    litellm_ans, _ = rag_service._generate_with_litellm_router(
        cfg.get_llm_fallback_chain(),
        "Prompt",
    )
    assert litellm_ans == "OK LiteLLM"
    assert mock_litellm.completion.call_args.kwargs["max_tokens"] == 600


@pytest.mark.anyio
async def test_g5_hide_public_docs_and_protect_admin_docs(
    api_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Gate G5 (OWASP A02:2025): Public /docs, /redoc, /openapi.json return 404 in production; /api/v1/admin/docs requires Admin."""
    monkeypatch.setattr(settings, "environment", "production")
    for hidden_path in ("/docs", "/redoc", "/openapi.json"):
        resp = await api_client.get(hidden_path)
        assert resp.status_code == 404
        assert resp.headers["X-Content-Type-Options"] == "nosniff"
        assert resp.headers["Strict-Transport-Security"].startswith("max-age=63072000")

    monkeypatch.setattr(settings, "environment", "development")
    assert (await api_client.get("/docs")).status_code == 200
    assert (await api_client.get("/openapi.json")).status_code == 200
    assert (await api_client.get("/redoc")).status_code == 404

    # Anonymous and non-admin student are blocked from /api/v1/admin/docs and /api/v1/admin/openapi.json
    assert (await api_client.get("/api/v1/admin/docs")).status_code == 401
    assert (await api_client.get("/api/v1/admin/openapi.json")).status_code == 401

    student_headers = await _register_and_login(api_client)
    assert (await api_client.get("/api/v1/admin/docs", headers=student_headers)).status_code == 403
    assert (await api_client.get("/api/v1/admin/openapi.json", headers=student_headers)).status_code == 403

    # Admin email listed in ADMIN_EMAILS receives admin access to /api/v1/admin/docs & openapi.json
    admin_email = f"test_admin_{uuid.uuid4().hex[:8]}@hcmute.edu.vn"
    monkeypatch.setattr(settings, "admin_emails", admin_email)
    reg = await api_client.post(
        "/api/v1/auth/register",
        json={"email": admin_email, "full_name": "Admin User", "password": "AdminPass123!"},
    )
    assert reg.status_code == 201
    assert reg.json()["role"] == "admin"
    login = await api_client.post(
        "/api/v1/auth/login",
        json={"email": admin_email, "password": "AdminPass123!"},
    )
    assert login.status_code == 200
    admin_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    docs_resp = await api_client.get("/api/v1/admin/docs", headers=admin_headers)
    assert docs_resp.status_code == 200
    assert "Swagger UI" in docs_resp.text
    assert "/api/v1/admin/openapi.json" in docs_resp.text

    openapi_resp = await api_client.get("/api/v1/admin/openapi.json", headers=admin_headers)
    assert openapi_resp.status_code == 200
    assert "/api/v1/admin/users" in openapi_resp.json()["paths"]


@pytest.mark.anyio
async def test_g6_admin_rbac_kill_switch_and_cache_refresh(
    api_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Gate G6 (TASK-SEC-02): Enforce RBAC, user deactivation kill-switch, and R2/RAG cache refresh."""
    reset_rate_limiter()
    admin_email = f"test_admin_{uuid.uuid4().hex[:8]}@hcmute.edu.vn"
    spam_email = f"test_spam_{uuid.uuid4().hex[:8]}@hcmute.edu.vn"

    monkeypatch.setattr(settings, "admin_emails", admin_email)
    await api_client.post(
        "/api/v1/auth/register",
        json={"email": admin_email, "full_name": "Root Admin", "password": "AdminPass123!"},
    )
    admin_login = await api_client.post(
        "/api/v1/auth/login",
        json={"email": admin_email, "password": "AdminPass123!"},
    )
    assert admin_login.status_code == 200
    admin_id = admin_login.json()["user"]["id"]
    admin_headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}

    spam_reg = await api_client.post(
        "/api/v1/auth/register",
        json={"email": spam_email, "full_name": "Spam Student", "password": "StudentPass123!"},
    )
    assert spam_reg.status_code == 201
    assert spam_reg.json()["role"] == "student"
    spam_id = spam_reg.json()["id"]
    spam_login = await api_client.post(
        "/api/v1/auth/login",
        json={"email": spam_email, "password": "StudentPass123!"},
    )
    spam_headers = {"Authorization": f"Bearer {spam_login.json()['access_token']}"}

    # Student is blocked 403 on all /api/v1/admin/* endpoints
    assert (await api_client.get("/api/v1/admin/telemetry", headers=spam_headers)).status_code == 403
    assert (await api_client.get("/api/v1/admin/users", headers=spam_headers)).status_code == 403
    assert (
        await api_client.post("/api/v1/admin/cache/refresh", json={"target": "all"}, headers=spam_headers)
    ).status_code == 403

    # Admin inspects telemetry and users
    tel_resp = await api_client.get("/api/v1/admin/telemetry", headers=admin_headers)
    assert tel_resp.status_code == 200
    assert tel_resp.json()["users_summary"]["total_users"] >= 2

    users_resp = await api_client.get("/api/v1/admin/users", params={"q": spam_email}, headers=admin_headers)
    assert users_resp.status_code == 200
    assert len(users_resp.json()) == 1
    assert users_resp.json()[0]["email"] == spam_email

    # Admin cannot self-deactivate or self-demote
    self_block = await api_client.patch(
        f"/api/v1/admin/users/{admin_id}",
        json={"is_active": False},
        headers=admin_headers,
    )
    assert self_block.status_code == 400

    # Admin promotes student to lecturer, then blocks spam account
    promote = await api_client.patch(
        f"/api/v1/admin/users/{spam_id}",
        json={"role": "lecturer"},
        headers=admin_headers,
    )
    assert promote.status_code == 200
    assert promote.json()["role"] == "lecturer"

    block = await api_client.patch(
        f"/api/v1/admin/users/{spam_id}",
        json={"is_active": False},
        headers=admin_headers,
    )
    assert block.status_code == 200
    assert block.json()["is_active"] is False

    # Blocked user's existing JWT is immediately rejected (401) on /auth/me and /rag/chat, and login fails
    assert (await api_client.get("/api/v1/auth/me", headers=spam_headers)).status_code == 401
    assert (
        await api_client.post("/api/v1/rag/chat", json={"message": "Spam query"}, headers=spam_headers)
    ).status_code == 401
    assert (
        await api_client.post(
            "/api/v1/auth/login",
            json={"email": spam_email, "password": "StudentPass123!"},
        )
    ).status_code == 401

    # Admin refreshes DuckDB R2 & RAG cache and resets rate limiter
    with patch(
        "acdp.api.routers.admin.refresh_duckdb_r2_connection",
        return_value={"mode": "r2_httpfs_memory_table", "entities_loaded": 15, "competitions_count": 10},
    ):
        refresh_all = await api_client.post(
            "/api/v1/admin/cache/refresh",
            json={"target": "all"},
            headers=admin_headers,
        )
    assert refresh_all.status_code == 200
    assert refresh_all.json()["duckdb_r2"]["entities_loaded"] == 15

    refresh_rl = await api_client.post(
        "/api/v1/admin/cache/refresh",
        json={"target": "rate_limit"},
        headers=admin_headers,
    )
    assert refresh_rl.status_code == 200
    assert refresh_rl.json()["rate_limit_reset"] is True


def test_g2_fail_fast_jwt_secret_validation_in_production() -> None:
    """Gate G2 (OWASP A04:2025): Reject default or short JWT_SECRET_KEY when ENVIRONMENT=production."""
    # Development allows default secret
    dev_cfg = AppConfig(_env_file=None, environment="development", jwt_secret_key=DEFAULT_DEV_JWT_SECRET)
    dev_cfg.validate_production_security()

    # Production rejects default dev secret
    prod_default = AppConfig(_env_file=None, environment="production", jwt_secret_key=DEFAULT_DEV_JWT_SECRET)
    with pytest.raises(RuntimeError, match="SECURITY FAIL-FAST"):
        prod_default.validate_production_security()

    # Production rejects short secret (< 32 chars)
    prod_short = AppConfig(_env_file=None, environment="production", jwt_secret_key="too-short-secret")
    with pytest.raises(RuntimeError, match="SECURITY FAIL-FAST"):
        prod_short.validate_production_security()

    # Production accepts strong >= 32-char custom secret
    prod_strong = AppConfig(
        _env_file=None,
        environment="production",
        jwt_secret_key="9f8e7d6c5b4a3928172635445566778899aabbccddeeff00",
    )
    prod_strong.validate_production_security()


@pytest.mark.anyio
async def test_g7_security_headers_and_global_exception_masking(
    api_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Gate G7 (OWASP A02/A10:2025): Enforce OWASP headers and mask stack traces on HTTP 500."""
    with patch("acdp.api.routers.health.check_qdrant_health", return_value="up"):
        resp = await api_client.get("/api/v1/health")
    assert resp.status_code == 200
    assert resp.headers["X-Content-Type-Options"] == "nosniff"
    assert resp.headers["X-Frame-Options"] == "DENY"
    assert resp.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
    assert resp.headers["Permissions-Policy"] == "geolocation=(), microphone=(), camera=()"
    assert resp.headers["X-XSS-Protection"] == "0"
    assert "frame-ancestors 'none'" in resp.headers["Content-Security-Policy"]

    # Isolated app verifying unhandled exceptions are masked without leaking secrets or tracebacks
    test_app = FastAPI()
    register_security_exception_handlers(test_app)
    test_app.add_middleware(SecurityHardeningMiddleware)

    @test_app.get("/api/v1/boom")
    async def boom() -> dict[str, str]:
        raise RuntimeError("DB_PASSWORD=super_secret_leaked_value")

    monkeypatch.setattr(settings, "environment", "production")
    async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as err_client:
        err_resp = await err_client.get("/api/v1/boom")

    assert err_resp.status_code == 500
    body = err_resp.json()
    assert body == {"detail": "Internal server error.", "error_code": "INTERNAL_SERVER_ERROR"}
    assert "super_secret_leaked_value" not in err_resp.text
    assert "Traceback" not in err_resp.text
    assert err_resp.headers["X-Content-Type-Options"] == "nosniff"
    assert err_resp.headers["Strict-Transport-Security"].startswith("max-age=63072000")
