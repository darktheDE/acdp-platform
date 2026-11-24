"""Module 3: Bronze-to-Qdrant Vector Ingestion Pipeline (Cloudflare Workers AI BGE-M3).

Flow:
    1. Đọc snapshot mới nhất của từng domain theo ngày cào trên R2 (tầng Bronze).
    2. Làm sạch Markdown và chia chunk bằng SemanticChunker.
    3. Embedding (Cloudflare Workers AI @cf/baai/bge-m3, 1024 dims) và upsert vào Qdrant Cloud.

(Giao diện chat đã được chuyển hoàn toàn sang Next.js Web Copilot & FastAPI `src/acdp/api/services/rag_service.py`.)

Cách chạy:
    uv run python src/acdp/3_ingest_to_qdrant.py
    uv run python src/acdp/3_ingest_to_qdrant.py --date 2026-11-21
"""

import argparse
import os
import random
import re
import sys
import time
import uuid
from collections import defaultdict
from datetime import datetime
from urllib.parse import urlparse

import httpx
from dotenv import find_dotenv, load_dotenv
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_experimental.text_splitter import SemanticChunker
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.http.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PayloadSchemaType,
    VectorParams,
)

from acdp.config import settings

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv(find_dotenv(usecwd=True))

# ==============================================================================
# CẤU HÌNH
# ==============================================================================
QDRANT_API_KEY = settings.get_qdrant_api_key()
QDRANT_CLUSTER_ENDPOINT = settings.get_qdrant_url()
QDRANT_COLLECTION = settings.get_qdrant_collection()

BUCKET_NAME = settings.bucket_name or os.getenv("BUCKET_NAME")
ENDPOINT_URL = settings.aws_endpoint_url or os.getenv("AWS_ENDPOINT_URL")

CLOUDFLARE_API_TOKEN = settings.cloudflare_api_token or os.getenv("CLOUDFLARE_API_TOKEN")
CLOUDFLARE_ACCOUNT_ID = settings.get_cloudflare_account_id() or (
    urlparse(ENDPOINT_URL).netloc.split(".", 1)[0] if ENDPOINT_URL else ""
)

EMBEDDING_MODEL = settings.get_embedding_model()
EMBEDDING_DIM = int(os.getenv("CLOUDFLARE_EMBEDDING_DIM", "1024"))

EMBED_BATCH_SIZE = int(os.getenv("EMBED_BATCH_SIZE", "32"))
EMBED_MAX_BATCH_CHARS = int(os.getenv("EMBED_MAX_BATCH_CHARS", "24000"))
EMBED_PACE_DELAY = float(os.getenv("EMBED_PACE_DELAY", "0.15"))
EMBED_MAX_RETRIES = int(os.getenv("EMBED_MAX_RETRIES", "4"))


# ==============================================================================
# KHỞI TẠO CLIENT & EMBEDDINGS (CLOUDFLARE WORKERS AI @cf/baai/bge-m3)
# ==============================================================================
class EmbeddingRateLimitError(RuntimeError):
    """Ngoại lệ khi API Embedding trả về HTTP 429 vượt quá số lần thử lại."""


def _is_rate_limit_error(exc: Exception) -> bool:
    if isinstance(exc, httpx.HTTPStatusError) and exc.response.status_code == 429:
        return True
    msg = str(exc).upper()
    return "429" in msg or "RESOURCE_EXHAUSTED" in msg or "RATE LIMIT" in msg


class CloudflareWorkersAIEmbeddings(Embeddings):
    """Bọc Cloudflare Workers AI REST API (@cf/baai/bge-m3) với batching động và retry."""

    def __init__(
        self,
        account_id: str | None = CLOUDFLARE_ACCOUNT_ID,
        api_token: str | None = CLOUDFLARE_API_TOKEN,
        model: str = EMBEDDING_MODEL,
        batch_size: int = EMBED_BATCH_SIZE,
        max_batch_chars: int = EMBED_MAX_BATCH_CHARS,
        pace_delay: float = EMBED_PACE_DELAY,
        max_retries: int = EMBED_MAX_RETRIES,
        http_client: httpx.Client | None = None,
    ):
        self.account_id = (account_id or "").strip()
        self.api_token = (api_token or "").strip()
        self.model = model
        self.batch_size = batch_size
        self.max_batch_chars = max_batch_chars
        self.pace_delay = pace_delay
        self.max_retries = max_retries
        self.http_client = http_client or httpx.Client(timeout=60.0)

    @property
    def endpoint_url(self) -> str:
        return f"https://api.cloudflare.com/client/v4/accounts/{self.account_id}/ai/run/{self.model}"

    def _embed_with_retry(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        if not self.account_id or not self.api_token:
            raise RuntimeError(
                "Thiếu CLOUDFLARE_API_TOKEN hoặc CLOUDFLARE_ACCOUNT_ID (không trích được từ AWS_ENDPOINT_URL). "
                "Vui lòng kiểm tra file .env."
            )

        payload = {
            "text": [t if t and t.strip() else " " for t in texts],
            "truncate_inputs": True,
        }
        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
        }

        for attempt in range(1, self.max_retries + 1):
            try:
                resp = self.http_client.post(self.endpoint_url, headers=headers, json=payload)
                if resp.status_code in (401, 403):
                    raise PermissionError(
                        f"Lỗi xác thực Cloudflare Workers AI (HTTP {resp.status_code}). "
                        f"Kiểm tra quyền 'Workers AI: Read/Edit' của CLOUDFLARE_API_TOKEN: {resp.text[:200]}"
                    )
                resp.raise_for_status()
                body = resp.json()
                if not body.get("success", False):
                    raise RuntimeError(f"Cloudflare Workers AI trả về lỗi: {body.get('errors')}")
                vectors = body["result"]["data"]
                if len(vectors) != len(texts):
                    raise RuntimeError(
                        f"Số vector trả về ({len(vectors)}) không khớp số văn bản gửi lên ({len(texts)})."
                    )
                return vectors
            except PermissionError:
                raise
            except (httpx.HTTPError, KeyError, ValueError, RuntimeError) as exc:
                is_429 = _is_rate_limit_error(exc)
                if attempt == self.max_retries:
                    if is_429:
                        raise EmbeddingRateLimitError(
                            f"Chạm giới hạn Cloudflare Workers AI (HTTP 429) sau {self.max_retries} lần thử: {exc}"
                        ) from exc
                    raise

                if is_429:
                    wait = (10 * (2 ** (attempt - 1))) + random.uniform(0.5, 2.0)
                    print(f"    [429 rate-limit retry {attempt}/{self.max_retries}] Chờ {wait:.1f}s...")
                else:
                    wait = 5 * attempt
                    print(f"    [embed retry {attempt}/{self.max_retries}] {str(exc)[:120]} -> chờ {wait}s")
                time.sleep(wait)

        raise RuntimeError("Không thể hoàn thành yêu cầu embedding tới Cloudflare Workers AI.")

    def _iter_batches(self, texts: list[str]):
        batch: list[str] = []
        batch_chars = 0
        for text in texts:
            text_len = len(text)
            if batch and (len(batch) >= self.batch_size or batch_chars + text_len > self.max_batch_chars):
                yield batch
                batch = []
                batch_chars = 0
            batch.append(text)
            batch_chars += text_len
        if batch:
            yield batch

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for idx, batch in enumerate(self._iter_batches(texts)):
            if idx > 0 and self.pace_delay > 0:
                time.sleep(self.pace_delay)
            vectors.extend(self._embed_with_retry(batch))
        return vectors

    def embed_query(self, text: str) -> list[float]:
        return self._embed_with_retry([text])[0]


embeddings = CloudflareWorkersAIEmbeddings()
qdrant_client = QdrantClient(url=QDRANT_CLUSTER_ENDPOINT, api_key=QDRANT_API_KEY)
s3_client = settings.create_r2_client()


# ==============================================================================
# BƯỚC 1: ĐỌC SNAPSHOT MỚI NHẤT THEO NGÀY TRÊN R2
# ==============================================================================
BRONZE_KEY_PATTERN = re.compile(
    r"^bronze/([^/]+)/year=(\d{4})/month=(\d{2})/day=(\d{2})/(\d+)$"
)


def list_latest_bronze_snapshots(target_date: str | None = None) -> tuple[str, list[dict]]:
    """Trả về (ngày được chọn, danh sách snapshot mới nhất của mỗi domain trong ngày đó)."""
    items = []
    paginator = s3_client.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=BUCKET_NAME, Prefix="bronze/"):
        for obj in page.get("Contents", []):
            match = BRONZE_KEY_PATTERN.match(obj["Key"])
            if not match or obj.get("Size", 0) == 0:
                continue
            domain, year, month, day, ts = match.groups()
            items.append({
                "key": obj["Key"],
                "domain": domain,
                "date": f"{year}-{month}-{day}",
                "timestamp": int(ts),
            })

    if not items:
        raise RuntimeError("Không tìm thấy snapshot hợp lệ nào trong bronze/.")

    available_dates = sorted({it["date"] for it in items})
    if target_date:
        if target_date not in available_dates:
            raise ValueError(f"Ngày {target_date} không có dữ liệu. Khả dụng: {available_dates}")
        chosen_date = target_date
    else:
        today = datetime.now().strftime("%Y-%m-%d")
        chosen_date = today if today in available_dates else available_dates[-1]

    by_domain = defaultdict(list)
    for it in items:
        if it["date"] == chosen_date:
            by_domain[it["domain"]].append(it)

    latest = [max(group, key=lambda x: x["timestamp"]) for group in by_domain.values()]
    return chosen_date, sorted(latest, key=lambda x: x["domain"])


def clean_markdown(raw_md: str) -> str:
    """Loại bỏ ảnh, link rỗng, link neo điều hướng và dòng trùng lặp liên tiếp."""
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", raw_md)
    text = re.sub(r"\[\s*\]\([^)]*\)", "", text)
    text = re.sub(r"\[([^\]]+)\]\(#[^)]*\)", r"\1", text)

    seen, lines = set(), []
    for line in text.splitlines():
        key = line.strip()
        if key and len(key) > 30 and key in seen:
            continue
        seen.add(key)
        lines.append(line)
    text = "\n".join(lines)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def load_competition_documents(target_date: str | None = None) -> tuple[str, list[Document]]:
    """Mỗi domain (mỗi cuộc thi) -> 1 Document chứa nội dung Markdown đã làm sạch."""
    chosen_date, snapshots = list_latest_bronze_snapshots(target_date)
    docs = []
    for snap in snapshots:
        body = s3_client.get_object(Bucket=BUCKET_NAME, Key=snap["key"])["Body"]
        content = clean_markdown(body.read().decode("utf-8", errors="replace"))
        if not content:
            continue
        docs.append(Document(
            page_content=content,
            metadata={
                "domain": snap["domain"],
                "source_url": f"https://{snap['domain']}",
                "source_key": snap["key"],
                "crawl_date": snap["date"],
                "crawl_timestamp": snap["timestamp"],
            },
        ))
    return chosen_date, docs


# ==============================================================================
# BƯỚC 2: SEMANTIC CHUNKING
# ==============================================================================
def build_chunker() -> SemanticChunker:
    return SemanticChunker(
        embeddings=embeddings,
        breakpoint_threshold_type="percentile",
        breakpoint_threshold_amount=90,
        sentence_split_regex=r"(?<=[.?!])\s+|\n+",
        min_chunk_size=200,
    )


def chunk_single_document(chunker: SemanticChunker, doc: Document) -> list[Document]:
    parts = chunker.split_documents([doc])
    for idx, part in enumerate(parts):
        part.page_content = f"[Nguồn: {doc.metadata['domain']}]\n{part.page_content}"
        part.metadata["chunk_index"] = idx
    print(f"  - {doc.metadata['domain']}: {len(doc.page_content):,} ký tự -> {len(parts)} chunk")
    return parts


# ==============================================================================
# BƯỚC 3: EMBEDDING + QDRANT UPSERT
# ==============================================================================
def ensure_collection() -> None:
    if qdrant_client.collection_exists(QDRANT_COLLECTION):
        info = qdrant_client.get_collection(QDRANT_COLLECTION)
        vec_cfg = info.config.params.vectors
        existing_dim = vec_cfg.size if isinstance(vec_cfg, VectorParams) else None
        if existing_dim is not None and existing_dim != EMBEDDING_DIM:
            raise RuntimeError(
                f"Collection '{QDRANT_COLLECTION}' đang có {existing_dim} chiều, "
                f"không khớp {EMBEDDING_DIM} chiều của '{EMBEDDING_MODEL}'. "
                "Hãy dùng tên collection mới qua QDRANT_COLLECTION."
            )
        return

    dim = len(embeddings.embed_query("dimension probe"))
    qdrant_client.create_collection(
        collection_name=QDRANT_COLLECTION,
        vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
    )
    qdrant_client.create_payload_index(
        collection_name=QDRANT_COLLECTION,
        field_name="metadata.domain",
        field_schema=PayloadSchemaType.KEYWORD,
    )
    print(f">> Đã tạo collection '{QDRANT_COLLECTION}' (dim={dim}).")


def get_vector_store() -> QdrantVectorStore:
    ensure_collection()
    return QdrantVectorStore(
        client=qdrant_client,
        collection_name=QDRANT_COLLECTION,
        embedding=embeddings,
    )


def ingest(target_date: str | None = None) -> None:
    """Nạp snapshot mới nhất của ngày mục tiêu từ R2 Bronze vào Qdrant theo từng domain."""
    chosen_date, docs = load_competition_documents(target_date)
    print(
        f">> Ngày cào: {chosen_date} | Số cuộc thi (domain): {len(docs)} "
        f"| Model: {EMBEDDING_MODEL} ({EMBEDDING_DIM}d) | Collection: {QDRANT_COLLECTION}"
    )
    if not docs:
        return

    chunker = build_chunker()
    store = get_vector_store()
    completed_domains: list[str] = []
    total_chunks = 0

    for idx, doc in enumerate(docs, 1):
        domain = doc.metadata["domain"]
        print(f">> [{idx}/{len(docs)}] Đang chunk & embed domain: {domain} ...")
        try:
            parts = chunk_single_document(chunker, doc)
            ids = [
                str(uuid.uuid5(uuid.NAMESPACE_URL,
                               f"{c.metadata['source_key']}#{c.metadata['chunk_index']}"))
                for c in parts
            ]
            qdrant_client.delete(
                collection_name=QDRANT_COLLECTION,
                points_selector=Filter(must=[
                    FieldCondition(key="metadata.domain", match=MatchValue(value=domain))
                ]),
            )
            store.add_documents(parts, ids=ids, batch_size=EMBED_BATCH_SIZE)
            completed_domains.append(domain)
            total_chunks += len(parts)
        except EmbeddingRateLimitError as exc:
            remaining = [d.metadata["domain"] for d in docs[idx - 1:]]
            print(f"\n>> [429 STOP] {exc}")
            print(f">> Đã hoàn tất ({len(completed_domains)}/{len(docs)}): {completed_domains}")
            print(f">> Chưa hoàn tất ({len(remaining)}): {remaining}")
            raise SystemExit(1) from exc

    print(f">> Hoàn tất ingest {total_chunks} chunk ({len(completed_domains)} domain) vào '{QDRANT_COLLECTION}'.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ACDP Bronze-to-Qdrant Vector Ingestion Pipeline")
    parser.add_argument("--date", type=str, default=None, help="Ngày cào mục tiêu (YYYY-MM-DD)")
    parser.add_argument("--ingest", action="store_true", help="(Tương thích cũ) Chạy ingest vào Qdrant")
    args = parser.parse_args()
    ingest(target_date=args.date)
