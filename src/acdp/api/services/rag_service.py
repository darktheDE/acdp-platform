"""Lazy, non-blocking RAG Copilot service over Qdrant + Cloudflare BGE-M3 + Gemini (SPEC-0004 §3.3)."""

from __future__ import annotations

import asyncio
import os
import time
from dataclasses import dataclass
from typing import Any

import httpx
from qdrant_client import QdrantClient
from qdrant_client.http.models import FieldCondition, Filter, MatchValue

from acdp.api.schemas.rag import RagCitationDTO
from acdp.config import settings

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
    """Raised when Qdrant, Cloudflare Workers AI embeddings, or Gemini generation fails or times out."""


@dataclass
class RagResult:
    answer: str
    citations: list[RagCitationDTO]
    grounded: bool
    latency_ms: int


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
                raise RagUnavailableError(f"Cloudflare embedding request failed: {exc}") from exc

        raise RagUnavailableError("Cloudflare embedding failed after retry.")


def _get_qdrant() -> QdrantClient:
    global _qdrant_client
    if _qdrant_client is None:
        url = settings.get_qdrant_url()
        api_key = settings.get_qdrant_api_key()
        _qdrant_client = QdrantClient(url=url, api_key=api_key, timeout=15)
    return _qdrant_client


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


def _sync_query_rag(
    message: str,
    domain_filter: str | None = None,
    history: list[dict[str, str]] | None = None,
) -> RagResult:
    start = time.perf_counter()
    try:
        qc = _get_qdrant()
        emb = _get_embeddings()
        query_text = message
        if history and len(message.split()) < 8:
            last_user = next((h["content"] for h in reversed(history) if h.get("role") == "user"), None)
            if last_user:
                query_text = f"{last_user}\n{message}"

        query_vec = emb.embed_query(query_text)
        q_filter = (
            Filter(must=[FieldCondition(key="metadata.domain", match=MatchValue(value=domain_filter.strip()))])
            if domain_filter and domain_filter.strip()
            else None
        )
        res = qc.query_points(
            collection_name=settings.get_qdrant_collection(),
            query=query_vec,
            query_filter=q_filter,
            limit=6,
            score_threshold=0.35,
            with_payload=True,
        )
        points = res.points
    except RagUnavailableError:
        raise
    except Exception as exc:
        raise RagUnavailableError(f"Vector retrieval failed: {exc}") from exc

    if not points:
        elapsed = int((time.perf_counter() - start) * 1000)
        return RagResult(
            answer="Chưa tìm thấy điều khoản xác thực trong dữ liệu cuộc thi đã thu thập (DIR-004). Vui lòng thử câu hỏi khác hoặc kiểm tra trực tiếp trên trang chính thức của Ban tổ chức.",
            citations=[],
            grounded=False,
            latency_ms=elapsed,
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

    try:
        from google.genai import types as genai_types

        client = _get_genai()
        contents = []
        for turn in (history or [])[-12:]:
            role = "model" if turn.get("role") == "assistant" else "user"
            contents.append(genai_types.Content(role=role, parts=[genai_types.Part(text=turn["content"])]))
        context_text = "\n\n".join(context_blocks)
        contents.append(
            genai_types.Content(
                role="user",
                parts=[genai_types.Part(text=f"NGỮ CẢNH:\n{context_text}\n\nCÂU HỎI: {message}")],
            )
        )
        model_name = settings.get_chat_model()
        response = client.models.generate_content(
            model=model_name,
            contents=contents,
            config=genai_types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT, temperature=0.2),
        )
        answer = (response.text or "").strip() or "Xin lỗi, tôi chưa tạo được câu trả lời."
    except Exception as exc:
        raise RagUnavailableError(f"LLM generation failed: {exc}") from exc

    elapsed = int((time.perf_counter() - start) * 1000)
    return RagResult(
        answer=answer,
        citations=citations,
        grounded=len(citations) > 0,
        latency_ms=elapsed,
    )


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
