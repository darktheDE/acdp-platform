"""Resilient, non-blocking RAG Copilot service with Multi-Provider Fallback & TTL Cache (SPEC-0004, TASK-CLD-06)."""

from __future__ import annotations

import asyncio
import copy
import hashlib
import logging
import os
import threading
import time
from collections import OrderedDict
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, TypeVar
from urllib.parse import urlparse

import httpx
from qdrant_client import QdrantClient
from qdrant_client.http.models import FieldCondition, Filter, MatchValue

from acdp.api.schemas.rag import RagCitationDTO
from acdp.config import settings

logger = logging.getLogger(__name__)

_T = TypeVar("_T")

SYSTEM_PROMPT = """Bạn là trợ lý tư vấn cuộc thi học thuật/công nghệ cho sinh viên của nền tảng ACDP.

Quy tắc bắt buộc:
1. Chỉ trả lời dựa trên phần NGỮ CẢNH được cung cấp. Không dùng kiến thức bên ngoài để bịa thông tin về cuộc thi.
2. Nếu ngữ cảnh không chứa thông tin cần thiết, nói rõ "Dữ liệu hiện có chưa có thông tin này" và gợi ý người dùng xem trang chính thức.
3. Mỗi thông tin về cuộc thi (thời hạn, giải thưởng, điều kiện, thể lệ) phải kèm nguồn dạng (Nguồn: <URL>).
4. Trả lời bằng ngôn ngữ của người dùng, ngắn gọn, ưu tiên gạch đầu dòng khi liệt kê.
5. Lưu ý ngày cào dữ liệu khi nói về trạng thái đăng ký; thông tin có thể đã thay đổi."""

_qdrant_client: QdrantClient | None = None
_embeddings: CloudflareBgeM3Embedder | None = None
_genai_client: Any = None


class RagUnavailableError(RuntimeError):
    """Raised when Qdrant, embedding providers, and all LLM fallback tiers fail or time out."""


@dataclass
class RagResult:
    answer: str
    citations: list[RagCitationDTO]
    grounded: bool
    latency_ms: int
    provider: str = "gemini"
    cached: bool = False


class RagResponseTTLCache:
    """Thread-safe bounded In-Memory TTL Cache for grounded RAG Copilot responses."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._entries: OrderedDict[tuple[str, str, str], tuple[float, RagResult]] = OrderedDict()
        self._hits = 0
        self._misses = 0
        self._evictions = 0

    @staticmethod
    def build_key(
        message: str,
        domain_filter: str | None = None,
        history: list[dict[str, str]] | None = None,
    ) -> tuple[str, str, str]:
        norm_msg = " ".join((message or "").strip().lower().split())
        norm_domain = (domain_filter or "").strip().lower()
        hist_slice = (history or [])[-4:]
        hist_raw = "|".join(f"{h.get('role', '')}:{h.get('content', '')}" for h in hist_slice)
        hist_digest = hashlib.sha256(hist_raw.encode("utf-8")).hexdigest()[:16] if hist_raw else ""
        return (norm_msg, norm_domain, hist_digest)

    def get(self, key: tuple[str, str, str]) -> RagResult | None:
        ttl_seconds = settings.rag_cache_ttl_seconds
        if not settings.rag_cache_enabled or ttl_seconds <= 0:
            return None
        now = time.monotonic()
        with self._lock:
            entry = self._entries.get(key)
            if entry is None:
                self._misses += 1
                return None
            expires_at, value = entry
            if now >= expires_at:
                del self._entries[key]
                self._evictions += 1
                self._misses += 1
                return None
            self._entries.move_to_end(key)
            self._hits += 1
            cloned = copy.deepcopy(value)
            cloned.cached = True
            return cloned

    def set(self, key: tuple[str, str, str], value: RagResult) -> None:
        ttl_seconds = settings.rag_cache_ttl_seconds
        if not settings.rag_cache_enabled or ttl_seconds <= 0 or not value.grounded:
            return
        with self._lock:
            max_entries = max(1, settings.rag_cache_max_entries)
            stored = copy.deepcopy(value)
            stored.cached = False
            self._entries[key] = (time.monotonic() + ttl_seconds, stored)
            self._entries.move_to_end(key)
            while len(self._entries) > max_entries:
                self._entries.popitem(last=False)
                self._evictions += 1

    def invalidate(self) -> None:
        with self._lock:
            self._entries.clear()
            self._hits = 0
            self._misses = 0
            self._evictions = 0

    def stats(self) -> dict[str, Any]:
        with self._lock:
            now = time.monotonic()
            expired_keys = [k for k, (exp, _) in self._entries.items() if now >= exp]
            for k in expired_keys:
                del self._entries[k]
                self._evictions += 1
            total = self._hits + self._misses
            hit_rate = round((self._hits / total) * 100, 2) if total > 0 else 0.0
            return {
                "enabled": settings.rag_cache_enabled and settings.rag_cache_ttl_seconds > 0,
                "ttl_seconds": settings.rag_cache_ttl_seconds,
                "max_entries": settings.rag_cache_max_entries,
                "cached_entries": len(self._entries),
                "hits": self._hits,
                "misses": self._misses,
                "evictions": self._evictions,
                "hit_rate_pct": hit_rate,
            }


_rag_cache = RagResponseTTLCache()


def invalidate_rag_cache() -> None:
    """Clear all cached RAG Copilot responses."""
    _rag_cache.invalidate()


def get_rag_cache_stats() -> dict[str, Any]:
    """Return RAG TTL cache telemetry."""
    return _rag_cache.stats()


def _is_recoverable_rate_or_server_error(exc: Exception) -> bool:
    """Return True for HTTP 429, 5xx, timeout, or transient provider errors."""
    if isinstance(exc, httpx.HTTPStatusError) and exc.response is not None:
        return exc.response.status_code in {408, 429, 500, 502, 503, 504}
    if isinstance(exc, (httpx.TimeoutException, httpx.ConnectError, TimeoutError)):
        return True
    msg = str(exc).upper()
    return any(
        token in msg
        for token in ("429", "RESOURCE_EXHAUSTED", "RATE LIMIT", "QUOTA", "500", "502", "503", "504", "TIMEOUT")
    )


def _embed_with_fastembed_fallback(text: str) -> list[float] | None:
    """Optional CPU BAAI/bge-m3 fallback via fastembed if Cloudflare Workers AI hits 429."""
    try:
        from fastembed import TextEmbedding  # type: ignore[import-not-found]
    except ImportError:
        return None
    try:
        model = TextEmbedding(model_name="BAAI/bge-m3")
        vec = next(iter(model.embed([text if text and text.strip() else " "])))
        return [float(x) for x in vec]
    except Exception as exc:
        logger.warning("FastEmbed CPU fallback failed: %s", exc)
        return None


class CloudflareBgeM3Embedder:
    """Lightweight REST embedder for Cloudflare Workers AI (@cf/baai/bge-m3, 1024 dims)."""

    def __init__(
        self,
        account_id: str,
        api_token: str,
        model: str = "@cf/baai/bge-m3",
        http_client: httpx.Client | None = None,
    ) -> None:
        self.account_id = account_id.strip()
        self.api_token = api_token.strip()
        self.model = model.strip() or "@cf/baai/bge-m3"
        self.http_client = http_client or httpx.Client(timeout=20.0)

    @property
    def endpoint_url(self) -> str:
        return f"https://api.cloudflare.com/client/v4/accounts/{self.account_id}/ai/run/{self.model}"

    def embed_query(self, text: str) -> list[float]:
        """Embed a single query string into a 1024-dim dense vector."""
        if not self.account_id or not self.api_token:
            raise RagUnavailableError(
                "Thiếu CLOUDFLARE_API_TOKEN hoặc CLOUDFLARE_ACCOUNT_ID (không tách được từ AWS_ENDPOINT_URL)."
            )

        payload = {
            "text": [text if text and text.strip() else " "],
            "truncate_inputs": True,
        }
        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
        }
        for attempt in range(2):
            try:
                resp = self.http_client.post(self.endpoint_url, headers=headers, json=payload)
                if resp.status_code in (401, 403):
                    raise RagUnavailableError(
                        f"Lỗi xác thực Cloudflare Workers AI (HTTP {resp.status_code}): kiểm tra CLOUDFLARE_API_TOKEN."
                    )
                if resp.status_code == 429:
                    if attempt == 0:
                        time.sleep(1.5)
                        continue
                    fallback_vec = _embed_with_fastembed_fallback(text)
                    if fallback_vec is not None:
                        return fallback_vec
                    raise RagUnavailableError("Cloudflare Workers AI tạm chạm giới hạn 429.")
                resp.raise_for_status()
                body = resp.json()
                if not body.get("success", False):
                    raise RagUnavailableError(f"Cloudflare Workers AI error: {body.get('errors')}")
                vectors = body["result"]["data"]
                if not vectors or not vectors[0]:
                    raise RagUnavailableError("Cloudflare Workers AI trả về vector rỗng.")
                return [float(x) for x in vectors[0]]
            except RagUnavailableError:
                raise
            except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError) as exc:
                fallback_vec = _embed_with_fastembed_fallback(text) if _is_recoverable_rate_or_server_error(exc) else None
                if fallback_vec is not None:
                    return fallback_vec
                raise RagUnavailableError(f"Cloudflare embedding request failed: {exc}") from exc

        raise RagUnavailableError("Cloudflare embedding failed after retry.")


def _get_qdrant() -> QdrantClient:
    global _qdrant_client
    if _qdrant_client is None:
        url = settings.get_qdrant_url()
        api_key = settings.get_qdrant_api_key()
        _qdrant_client = QdrantClient(url=url, api_key=api_key, timeout=15)
    return _qdrant_client


def _get_backup_qdrant() -> QdrantClient | None:
    """Return backup local/secondary QdrantClient if configured and distinct from active endpoint."""
    if (settings.qdrant_mode or "auto").strip().lower() == "local":
        return None
    primary_url = settings.get_qdrant_url().rstrip("/")
    candidate_url = settings.qdrant_url.strip().rstrip("/")
    if not candidate_url:
        candidate_url = f"http://{settings.qdrant_host}:{settings.qdrant_port}".rstrip("/")
    if not candidate_url or candidate_url == primary_url:
        return None
    api_key = None if candidate_url.startswith("http://") else (settings.qdrant_api_key.strip() or None)
    return QdrantClient(url=candidate_url, api_key=api_key, timeout=10)


def _get_embeddings() -> CloudflareBgeM3Embedder:
    global _embeddings
    if _embeddings is None:
        _embeddings = CloudflareBgeM3Embedder(
            account_id=settings.get_cloudflare_account_id(),
            api_token=settings.cloudflare_api_token,
            model=settings.get_embedding_model(),
        )
    return _embeddings


def _get_genai():
    global _genai_client
    if _genai_client is None:
        from google import genai

        api_key = settings.gemini_api_key or settings.google_api_key or os.getenv("GOOGLE_API_KEY") or None
        _genai_client = genai.Client(api_key=api_key)
    return _genai_client


def check_qdrant_health() -> str:
    """Return 'up' if target Qdrant collection exists, 'degraded' if reachable without collection, else 'down'."""
    try:
        qc = _get_qdrant()
        if qc.collection_exists(settings.get_qdrant_collection()):
            return "up"
        return "degraded"
    except Exception:
        return "down"


@dataclass
class _RetrievedPoint:
    payload: dict[str, Any]


def _fallback_duckdb_gold_search(message: str, domain_filter: str | None = None, limit: int = 4) -> list[_RetrievedPoint]:
    """Tier-3 grounded fallback over DuckDB mart_competition_explorer if Qdrant/Embedding fails."""
    try:
        from acdp.api.db.duckdb_client import get_duckdb_conn

        tokens = [tok.strip().lower() for tok in (message or "").split() if len(tok.strip()) >= 3][:6]
        with get_duckdb_conn() as con:
            rows = con.execute(
                """
                SELECT
                    name,
                    canonical_url,
                    summary,
                    challenge_overview,
                    total_prize_pool_raw,
                    registration_deadline_raw,
                    registration_status,
                    domain_groups
                FROM mart_competition_explorer
                LIMIT 100
                """
            ).fetchall()
    except Exception as exc:
        logger.warning("DuckDB Gold lexical fallback unavailable: %s", exc)
        return []

    scored: list[tuple[int, _RetrievedPoint]] = []
    norm_domain_filter = (domain_filter or "").strip().lower()
    for row in rows:
        name, canonical_url, summary, overview, prize_raw, deadline_raw, reg_status, domain_groups = row
        url_str = str(canonical_url or "").strip()
        if not url_str:
            continue
        domain_host = urlparse(url_str).netloc.lower() or "acdp.vn"
        if norm_domain_filter and norm_domain_filter not in domain_host:
            continue
        blob = f"{name or ''} {summary or ''} {overview or ''} {domain_groups or ''}".lower()
        score = sum(1 for tok in tokens if tok in blob)
        if score == 0 and not norm_domain_filter:
            continue
        content = (
            f"Cuộc thi: {name}. Trạng thái: {reg_status or 'unknown'}. "
            f"Hạn đăng ký: {deadline_raw or 'Chưa rõ'}. "
            f"Giải thưởng: {prize_raw or 'Chưa công bố'}. "
            f"Tóm tắt: {summary or overview or ''}"
        ).strip()
        scored.append(
            (
                score,
                _RetrievedPoint(
                    payload={
                        "page_content": content,
                        "metadata": {
                            "domain": domain_host,
                            "source_url": url_str,
                            "crawl_date": "gold-mart-fallback",
                        },
                    }
                ),
            )
        )

    scored.sort(key=lambda item: item[0], reverse=True)
    return [pt for _, pt in scored[:limit]]


def _retrieve_context_points(
    message: str,
    domain_filter: str | None = None,
    history: list[dict[str, str]] | None = None,
) -> list[Any]:
    """Retrieve grounded context points via Qdrant Cloud -> Qdrant Backup -> DuckDB Gold fallback."""
    query_text = message
    if history and len(message.split()) < 8:
        last_user = next((h["content"] for h in reversed(history) if h.get("role") == "user"), None)
        if last_user:
            query_text = f"{last_user}\n{message}"

    q_filter = (
        Filter(must=[FieldCondition(key="metadata.domain", match=MatchValue(value=domain_filter.strip()))])
        if domain_filter and domain_filter.strip()
        else None
    )
    collection_name = settings.get_qdrant_collection()

    try:
        emb = _get_embeddings()
        query_vec = emb.embed_query(query_text)
        try:
            qc = _get_qdrant()
            res = qc.query_points(
                collection_name=collection_name,
                query=query_vec,
                query_filter=q_filter,
                limit=6,
                score_threshold=0.35,
                with_payload=True,
            )
            return list(res.points)
        except Exception as primary_qdrant_exc:
            backup_qc = _get_backup_qdrant()
            if backup_qc is not None:
                try:
                    res = backup_qc.query_points(
                        collection_name=collection_name,
                        query=query_vec,
                        query_filter=q_filter,
                        limit=6,
                        score_threshold=0.35,
                        with_payload=True,
                    )
                    logger.warning("Primary Qdrant failed (%s); served from backup Qdrant.", primary_qdrant_exc)
                    return list(res.points)
                except Exception:
                    pass
            raise primary_qdrant_exc
    except RagUnavailableError:
        gold_points = _fallback_duckdb_gold_search(message, domain_filter=domain_filter)
        if gold_points:
            logger.warning("Embedding/Qdrant unavailable; served grounded Gold lexical fallback.")
            return gold_points
        raise
    except Exception as exc:
        gold_points = _fallback_duckdb_gold_search(message, domain_filter=domain_filter)
        if gold_points:
            logger.warning("Vector retrieval failed (%s); served grounded Gold lexical fallback.", exc)
            return gold_points
        raise RagUnavailableError(f"Vector retrieval failed: {exc}") from exc


def _build_openai_messages(
    user_prompt: str,
    history: list[dict[str, str]] | None = None,
) -> list[dict[str, str]]:
    messages: list[dict[str, str]] = [{"role": "system", "content": SYSTEM_PROMPT}]
    for turn in (history or [])[-12:]:
        role = "assistant" if turn.get("role") == "assistant" else "user"
        messages.append({"role": role, "content": turn.get("content", "")})
    messages.append({"role": "user", "content": user_prompt})
    return messages


def _generate_with_openai_compatible(
    *,
    provider: str,
    base_url: str,
    api_key: str,
    model: str,
    user_prompt: str,
    history: list[dict[str, str]] | None = None,
    http_client: httpx.Client | None = None,
) -> str:
    """Invoke Groq or OpenRouter OpenAI-compatible /v1/chat/completions endpoint."""
    headers: dict[str, str] = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    if provider == "openrouter":
        headers["HTTP-Referer"] = "https://acdp.hcmute.edu.vn"
        headers["X-Title"] = "ACDP RAG Copilot"

    payload = {
        "model": model,
        "messages": _build_openai_messages(user_prompt, history),
        "temperature": 0.2,
        "max_tokens": settings.rag_max_output_tokens,
    }
    client = http_client or httpx.Client(timeout=20.0)
    close_after = http_client is None
    try:
        resp = client.post(base_url, headers=headers, json=payload)
        resp.raise_for_status()
        body = resp.json()
        choices = body.get("choices") or []
        if not choices:
            raise RuntimeError(f"{provider} returned empty choices")
        content = (choices[0].get("message", {}).get("content") or "").strip()
        if not content:
            raise RuntimeError(f"{provider} returned empty content")
        return content
    finally:
        if close_after:
            client.close()


def _generate_with_litellm_router(
    chain: list[dict[str, str]],
    user_prompt: str,
    history: list[dict[str, str]] | None = None,
) -> tuple[str, str]:
    """Use litellm.completion with fallbacks=[] when USE_LITELLM_ROUTER=true."""
    import litellm  # type: ignore[import-not-found]

    messages = _build_openai_messages(user_prompt, history)
    fallbacks = [tier["litellm_model"] for tier in chain[1:]]
    primary = chain[0]
    response = litellm.completion(
        model=primary["litellm_model"],
        messages=messages,
        fallbacks=fallbacks,
        temperature=0.2,
        max_tokens=settings.rag_max_output_tokens,
    )
    choices = getattr(response, "choices", None) or response["choices"]
    text = (choices[0].message.content or "").strip()
    used_model = str(getattr(response, "model", "") or primary["litellm_model"]).lower()
    provider = "gemini"
    for tier in chain:
        if tier["provider"] in used_model or tier["model"].lower() in used_model:
            provider = tier["provider"]
            break
    return text or "Xin lỗi, tôi chưa tạo được câu trả lời.", provider


def _generate_answer_with_fallback(
    message: str,
    context_text: str,
    history: list[dict[str, str]] | None = None,
    openai_post: Callable[..., str] | None = None,
) -> tuple[str, str]:
    """Execute Gemini -> Groq -> OpenRouter :free LLM fallback chain."""
    user_prompt = f"NGỮ CẢNH:\n{context_text}\n\nCÂU HỎI: {message}"
    chain = settings.get_llm_fallback_chain()

    if settings.use_litellm_router:
        try:
            return _generate_with_litellm_router(chain, user_prompt, history)
        except ImportError:
            logger.warning("litellm not installed; falling back to native httpx fallback chain.")
        except Exception as exc:
            raise RagUnavailableError(f"LiteLLM fallback chain failed: {exc}") from exc

    errors: list[str] = []
    for tier in chain:
        provider = tier["provider"]
        model_name = tier["model"]
        if provider == "gemini":
            try:
                from google.genai import types as genai_types

                client = _get_genai()
                contents = []
                for turn in (history or [])[-12:]:
                    role = "model" if turn.get("role") == "assistant" else "user"
                    contents.append(genai_types.Content(role=role, parts=[genai_types.Part(text=turn["content"])]))
                contents.append(
                    genai_types.Content(
                        role="user",
                        parts=[genai_types.Part(text=user_prompt)],
                    )
                )
                response = client.models.generate_content(
                    model=model_name,
                    contents=contents,
                    config=genai_types.GenerateContentConfig(
                        system_instruction=SYSTEM_PROMPT,
                        temperature=0.2,
                        max_output_tokens=settings.rag_max_output_tokens,
                    ),
                )
                answer = (response.text or "").strip() or "Xin lỗi, tôi chưa tạo được câu trả lời."
                return answer, "gemini"
            except Exception as exc:
                errors.append(f"gemini({model_name}): {exc}")
                logger.warning("LLM Tier-1 Gemini failed (%s); evaluating fallback chain...", exc)
                if not settings.llm_fallback_enabled:
                    break
                continue

        # Tier 2 (Groq) & Tier 3 (OpenRouter :free)
        try:
            caller = openai_post or _generate_with_openai_compatible
            answer = caller(
                provider=provider,
                base_url=tier["base_url"],
                api_key=tier["api_key"],
                model=model_name,
                user_prompt=user_prompt,
                history=history,
            )
            return answer, provider
        except Exception as exc:
            errors.append(f"{provider}({model_name}): {exc}")
            logger.warning("LLM fallback tier %s failed: %s", provider, exc)

    raise RagUnavailableError(f"LLM generation failed across all tiers: {' | '.join(errors)}")


def _sync_query_rag(
    message: str,
    domain_filter: str | None = None,
    history: list[dict[str, str]] | None = None,
) -> RagResult:
    start = time.perf_counter()
    cache_key = RagResponseTTLCache.build_key(message=message, domain_filter=domain_filter, history=history)
    cached_res = _rag_cache.get(cache_key)
    if cached_res is not None:
        cached_res.latency_ms = max(0, int((time.perf_counter() - start) * 1000))
        return cached_res

    points = _retrieve_context_points(message=message, domain_filter=domain_filter, history=history)
    if not points:
        elapsed = int((time.perf_counter() - start) * 1000)
        return RagResult(
            answer="Chưa tìm thấy điều khoản xác thực trong dữ liệu cuộc thi đã thu thập (DIR-004). Vui lòng thử câu hỏi khác hoặc kiểm tra trực tiếp trên trang chính thức của Ban tổ chức.",
            citations=[],
            grounded=False,
            latency_ms=elapsed,
            provider="none",
            cached=False,
        )

    citations: list[RagCitationDTO] = []
    seen_urls: set[str] = set()
    context_blocks: list[str] = []

    for idx, pt in enumerate(points, 1):
        payload = pt.payload or {}
        meta = payload.get("metadata") or {}
        page_content = str(payload.get("page_content") or "")
        domain = str(meta.get("domain") or "unknown")
        source_url = str(meta.get("source_url") or f"https://{domain}")
        crawl_date = str(meta.get("crawl_date") or "")

        context_blocks.append(
            f"--- Đoạn {idx} | URL: {source_url} | Ngày cào: {crawl_date} ---\n{page_content}"
        )
        if source_url not in seen_urls:
            seen_urls.add(source_url)
            citations.append(
                RagCitationDTO(
                    title=domain,
                    url=source_url,
                    domain=domain,
                    snippet=page_content[:260].strip(),
                )
            )

    context_text = "\n\n".join(context_blocks)
    answer, used_provider = _generate_answer_with_fallback(
        message=message,
        context_text=context_text,
        history=history,
    )

    elapsed = int((time.perf_counter() - start) * 1000)
    result = RagResult(
        answer=answer,
        citations=citations,
        grounded=len(citations) > 0,
        latency_ms=elapsed,
        provider=used_provider,
        cached=False,
    )
    _rag_cache.set(cache_key, result)
    return result


async def query_rag(
    message: str,
    domain_filter: str | None = None,
    history: list[dict[str, str]] | None = None,
    timeout_seconds: float = 25.0,
) -> RagResult:
    """Execute RAG retrieval and generation in a worker thread with 25s timeout (EC-A4)."""
    try:
        return await asyncio.wait_for(
            asyncio.to_thread(_sync_query_rag, message, domain_filter, history),
            timeout=timeout_seconds,
        )
    except TimeoutError as exc:
        raise RagUnavailableError("RAG query timed out after 25 seconds.") from exc
