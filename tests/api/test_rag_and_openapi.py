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


def test_cloudflare_bge_m3_rag_pipeline_and_config(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify RAG service uses Cloudflare BGE-M3 (1024d), acdp_competitions_bge_m3, and gemini-3.5-flash-lite."""
    from types import SimpleNamespace
    from unittest.mock import MagicMock

    import httpx

    from acdp.api.services import rag_service
    from acdp.config import AppConfig

    cfg = AppConfig(
        _env_file=None,
        aws_endpoint_url="https://acc999.r2.cloudflarestorage.com",
        cloudflare_api_token="cf-test-token",
        qdrant_collection="acdp_competitions",
        embedding_model="qwen3-embedding:4b",
        llm_provider="google/gemma-4-26b-a4b-it",
    )
    assert cfg.get_cloudflare_account_id() == "acc999"
    assert cfg.get_qdrant_collection() == "acdp_competitions_bge_m3"
    assert cfg.get_embedding_model() == "@cf/baai/bge-m3"
    assert cfg.get_chat_model() == "gemini-3.5-flash-lite"

    http_calls: list[tuple[str, dict]] = []

    def fake_post(url: str, headers=None, json=None):
        http_calls.append((url, json))
        return MagicMock(
            status_code=200,
            raise_for_status=lambda: None,
            json=lambda: {"success": True, "errors": [], "result": {"data": [[0.15] * 1024]}},
        )

    fake_http = MagicMock()
    fake_http.post.side_effect = fake_post
    embedder = rag_service.CloudflareBgeM3Embedder(
        account_id="acc999",
        api_token="cf-test-token",
        http_client=fake_http,
    )

    fake_qdrant = MagicMock()
    fake_qdrant.query_points.return_value = SimpleNamespace(
        points=[
            SimpleNamespace(
                payload={
                    "page_content": "Giải nhất trị giá $10,000 tiền mặt.",
                    "metadata": {
                        "domain": "www.vietnamaichallenge.com",
                        "source_url": "https://www.vietnamaichallenge.com",
                        "crawl_date": "2026-11-21",
                    },
                }
            )
        ]
    )

    fake_genai = MagicMock()
    fake_genai.models.generate_content.return_value = SimpleNamespace(
        text="Giải nhất là $10,000 (Nguồn: https://www.vietnamaichallenge.com)."
    )

    monkeypatch.setattr(rag_service, "_get_embeddings", lambda: embedder)
    monkeypatch.setattr(rag_service, "_get_qdrant", lambda: fake_qdrant)
    monkeypatch.setattr(rag_service, "_get_genai", lambda: fake_genai)
    monkeypatch.setattr(rag_service, "settings", cfg)

    res = rag_service._sync_query_rag("Giải thưởng Vietnam AI Challenge là bao nhiêu?")
    assert res.grounded is True
    assert len(res.citations) == 1
    assert res.citations[0].domain == "www.vietnamaichallenge.com"
    assert http_calls[0][0] == "https://api.cloudflare.com/client/v4/accounts/acc999/ai/run/@cf/baai/bge-m3"
    assert http_calls[0][1]["truncate_inputs"] is True
    assert fake_qdrant.query_points.call_args.kwargs["collection_name"] == "acdp_competitions_bge_m3"
    assert len(fake_qdrant.query_points.call_args.kwargs["query"]) == 1024
    assert fake_genai.models.generate_content.call_args.kwargs["model"] == "gemini-3.5-flash-lite"

    # Verify HTTP 401 maps to RagUnavailableError
    req = httpx.Request("POST", embedder.endpoint_url)
    bad_http = MagicMock()
    bad_http.post.return_value = httpx.Response(401, request=req, text="Unauthorized")
    bad_embedder = rag_service.CloudflareBgeM3Embedder("acc999", "bad-tok", http_client=bad_http)
    with pytest.raises(rag_service.RagUnavailableError):
        bad_embedder.embed_query("test")


def test_rag_llm_fallback_chain_and_ttl_cache(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify Gemini -> Groq -> OpenRouter :free fallback chain on HTTP 429 and RagResponseTTLCache (TASK-CLD-06)."""
    from types import SimpleNamespace
    from unittest.mock import MagicMock

    import httpx

    from acdp.api.services import rag_service
    from acdp.config import AppConfig

    rag_service.invalidate_rag_cache()

    cfg = AppConfig(
        _env_file=None,
        aws_endpoint_url="https://acc999.r2.cloudflarestorage.com",
        cloudflare_api_token="cf-test-token",
        gemini_api_key="gem-key",
        groq_api_key="gsk-test-key",
        openrouter_api_key="or-test-key",
        llm_fallback_enabled=True,
        use_litellm_router=False,
        rag_cache_enabled=True,
        rag_cache_ttl_seconds=300,
    )
    chain = cfg.get_llm_fallback_chain()
    assert [t["provider"] for t in chain] == ["gemini", "groq", "openrouter"]
    assert chain[1]["model"] == "llama-3.3-70b-versatile"
    assert chain[2]["model"] == "meta-llama/llama-3.3-70b-instruct:free"

    fake_embedder = MagicMock()
    fake_embedder.embed_query.return_value = [0.2] * 1024

    fake_qdrant = MagicMock()
    fake_qdrant.query_points.return_value = SimpleNamespace(
        points=[
            SimpleNamespace(
                payload={
                    "page_content": "Hạn nộp bài vòng sơ loại là 30/11/2026.",
                    "metadata": {
                        "domain": "challenge.zalo.ai",
                        "source_url": "https://challenge.zalo.ai/rules",
                        "crawl_date": "2026-11-24",
                    },
                }
            )
        ]
    )

    failing_genai = MagicMock()
    failing_genai.models.generate_content.side_effect = RuntimeError("429 RESOURCE_EXHAUSTED")

    monkeypatch.setattr(rag_service, "_get_embeddings", lambda: fake_embedder)
    monkeypatch.setattr(rag_service, "_get_qdrant", lambda: fake_qdrant)
    monkeypatch.setattr(rag_service, "_get_genai", lambda: failing_genai)
    monkeypatch.setattr(rag_service, "settings", cfg)

    # Case 1: Gemini 429 -> Groq succeeds
    called_providers: list[str] = []

    def fake_openai_groq(**kwargs):
        called_providers.append(kwargs["provider"])
        return "Hạn nộp bài là 30/11/2026 (Nguồn: https://challenge.zalo.ai/rules)."

    with patch.object(rag_service, "_generate_with_openai_compatible", side_effect=fake_openai_groq):
        res_groq = rag_service._sync_query_rag("Hạn nộp bài Zalo AI Challenge?")
    assert res_groq.grounded is True
    assert res_groq.provider == "groq"
    assert res_groq.cached is False
    assert called_providers == ["groq"]

    # Case 2: Repeated identical query hits RagResponseTTLCache without calling embedding/Qdrant/LLM again
    res_cached = rag_service._sync_query_rag("  hạn nộp bài zalo ai challenge? ")
    assert res_cached.cached is True
    assert res_cached.provider == "groq"
    assert fake_embedder.embed_query.call_count == 1
    assert rag_service.get_rag_cache_stats()["hits"] == 1

    # Case 3: Gemini 429 AND Groq 429 -> OpenRouter :free succeeds
    rag_service.invalidate_rag_cache()
    called_providers.clear()

    def fake_openai_fail_groq(**kwargs):
        called_providers.append(kwargs["provider"])
        if kwargs["provider"] == "groq":
            req = httpx.Request("POST", kwargs["base_url"])
            raise httpx.HTTPStatusError("429 Too Many Requests", request=req, response=httpx.Response(429, request=req))
        return "Trả lời từ OpenRouter free (Nguồn: https://challenge.zalo.ai/rules)."

    with patch.object(rag_service, "_generate_with_openai_compatible", side_effect=fake_openai_fail_groq):
        res_or = rag_service._sync_query_rag("Thể lệ vòng sơ loại?")
    assert res_or.provider == "openrouter"
    assert called_providers == ["groq", "openrouter"]

    # Case 4: All 3 tiers fail -> RagUnavailableError
    rag_service.invalidate_rag_cache()
    with patch.object(rag_service, "_generate_with_openai_compatible", side_effect=RuntimeError("503 Unavailable")):
        with pytest.raises(rag_service.RagUnavailableError):
            rag_service._sync_query_rag("Câu hỏi thất bại toàn chuỗi?")


def test_rag_litellm_router_fallback_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify USE_LITELLM_ROUTER=true delegates to litellm.completion with fallbacks=[] (TASK-CLD-06)."""
    import sys
    from types import SimpleNamespace
    from unittest.mock import MagicMock

    from acdp.api.services import rag_service
    from acdp.config import AppConfig

    cfg = AppConfig(
        _env_file=None,
        gemini_api_key="gem-key",
        groq_api_key="gsk-key",
        openrouter_api_key="or-key",
        use_litellm_router=True,
    )
    monkeypatch.setattr(rag_service, "settings", cfg)

    mock_litellm = MagicMock()
    mock_litellm.completion.return_value = SimpleNamespace(
        model="groq/llama-3.3-70b-versatile",
        choices=[SimpleNamespace(message=SimpleNamespace(content="Trả lời qua LiteLLM fallback."))],
    )
    monkeypatch.setitem(sys.modules, "litellm", mock_litellm)

    answer, provider = rag_service._generate_answer_with_fallback("Test?", "Ngữ cảnh mẫu")
    assert answer == "Trả lời qua LiteLLM fallback."
    assert provider == "groq"
    call_kwargs = mock_litellm.completion.call_args.kwargs
    assert call_kwargs["model"] == "gemini/gemini-3.5-flash-lite"
    assert call_kwargs["fallbacks"] == [
        "groq/llama-3.3-70b-versatile",
        "openrouter/meta-llama/llama-3.3-70b-instruct:free",
    ]
