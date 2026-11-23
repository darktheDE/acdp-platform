"""TASK-SLV-03: Silver-to-Qdrant Vector Ingestion Pipeline (ACDP v2).

Replaces the Bronze-reading anti-pattern in `src/acdp/3_ingest_to_qdrant.py`
per TASK-BRZ-01, TASK-SLV-03, and DIR-021:
1. Reads Clean Markdown strictly from Cloudflare R2 `silver/markdown/`.
2. Enriches metadata (`canonical_url`, `competition_name`, `domain`, `crawl_date`)
   from R2 object metadata and matching `silver/extractions/` JSON records.
3. Runs SemanticChunker + Cloudflare Workers AI `@cf/baai/bge-m3` (1024 dims)
   and upserts deterministic UUIDv5 points into Qdrant Cloud.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import re
import sys
import time
import uuid
from collections import defaultdict
from datetime import UTC, datetime
from typing import Any
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

SILVER_MD_KEY_PATTERN = re.compile(
    r"^silver/markdown/([^/]+)/year=(\d{4})/month=(\d{2})/day=(\d{2})/(\d+)\.md$"
)
SILVER_JSON_KEY_PATTERN = re.compile(
    r"^silver/extractions/([^/]+)/year=(\d{4})/month=(\d{2})/day=(\d{2})/(\d+)\.json$"
)

EMBED_BATCH_SIZE = int(os.getenv("EMBED_BATCH_SIZE", "32"))
EMBED_MAX_BATCH_CHARS = int(os.getenv("EMBED_MAX_BATCH_CHARS", "24000"))
EMBED_PACE_DELAY = float(os.getenv("EMBED_PACE_DELAY", "0.15"))
EMBED_MAX_RETRIES = int(os.getenv("EMBED_MAX_RETRIES", "4"))


class EmbeddingRateLimitError(RuntimeError):
    """Raised when Cloudflare Workers AI returns HTTP 429 after exhausting retries."""


def _is_rate_limit_error(exc: Exception) -> bool:
    if isinstance(exc, httpx.HTTPStatusError) and exc.response.status_code == 429:
        return True
    msg = str(exc).upper()
    return "429" in msg or "RESOURCE_EXHAUSTED" in msg or "RATE LIMIT" in msg


class CloudflareWorkersAIEmbeddings(Embeddings):
    """Cloudflare Workers AI REST embedder (@cf/baai/bge-m3) with batching and 429 retry."""

    def __init__(
        self,
        account_id: str | None = None,
        api_token: str | None = None,
        model: str | None = None,
        batch_size: int = EMBED_BATCH_SIZE,
        max_batch_chars: int = EMBED_MAX_BATCH_CHARS,
        pace_delay: float = EMBED_PACE_DELAY,
        max_retries: int = EMBED_MAX_RETRIES,
        http_client: httpx.Client | None = None,
    ) -> None:
        self.account_id = (account_id or settings.get_cloudflare_account_id() or "").strip()
        if not self.account_id and settings.aws_endpoint_url:
            self.account_id = urlparse(settings.aws_endpoint_url).netloc.split(".", 1)[0]
        self.api_token = (api_token or settings.cloudflare_api_token or os.getenv("CLOUDFLARE_API_TOKEN", "")).strip()
        self.model = model or settings.get_embedding_model()
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
                "Thiếu CLOUDFLARE_API_TOKEN hoặc CLOUDFLARE_ACCOUNT_ID. Vui lòng kiểm tra file .env."
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
                        f"Lỗi xác thực Cloudflare Workers AI (HTTP {resp.status_code}): {resp.text[:200]}"
                    )
                resp.raise_for_status()
                body = resp.json()
                if not body.get("success", False):
                    raise RuntimeError(f"Cloudflare Workers AI error: {body.get('errors')}")
                vectors = body["result"]["data"]
                if len(vectors) != len(texts):
                    raise RuntimeError(
                        f"Vector count mismatch: {len(vectors)} != {len(texts)}"
                    )
                return vectors
            except PermissionError:
                raise
            except (httpx.HTTPError, KeyError, ValueError, RuntimeError) as exc:
                is_429 = _is_rate_limit_error(exc)
                if attempt == self.max_retries:
                    if is_429:
                        raise EmbeddingRateLimitError(
                            f"Cloudflare Workers AI HTTP 429 after {self.max_retries} attempts: {exc}"
                        ) from exc
                    raise
                wait = (10 * (2 ** (attempt - 1))) + random.uniform(0.5, 2.0) if is_429 else 5 * attempt
                time.sleep(wait)
        raise RuntimeError("Failed to complete Cloudflare Workers AI embedding request.")

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


def list_latest_silver_markdown_snapshots(
    s3_client: Any,
    bucket_name: str,
    target_date: str | None = None,
) -> tuple[str, list[dict[str, Any]]]:
    """List latest Clean Markdown objects from R2 `silver/markdown/` for the target date."""
    items: list[dict[str, Any]] = []
    paginator = s3_client.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket_name, Prefix="silver/markdown/"):
        for obj in page.get("Contents", []):
            match = SILVER_MD_KEY_PATTERN.match(obj["Key"])
            if not match or obj.get("Size", 0) == 0:
                continue
            domain, year, month, day, ts = match.groups()
            items.append(
                {
                    "key": obj["Key"],
                    "domain": domain,
                    "date": f"{year}-{month}-{day}",
                    "timestamp": int(ts),
                }
            )

    if not items:
        raise RuntimeError(
            "Không tìm thấy Clean Markdown nào trong silver/markdown/. "
            "Hãy chạy `uv run python -m acdp.v2.silver_transform --extract` trước."
        )

    available_dates = sorted({it["date"] for it in items})
    if target_date:
        if target_date not in available_dates:
            raise ValueError(f"Ngày {target_date} không có trong silver/markdown/. Khả dụng: {available_dates}")
        chosen_date = target_date
    else:
        today = datetime.now(UTC).strftime("%Y-%m-%d")
        chosen_date = today if today in available_dates else available_dates[-1]

    by_domain: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for it in items:
        if it["date"] == chosen_date:
            by_domain[it["domain"]].append(it)

    latest = [max(group, key=lambda x: x["timestamp"]) for group in by_domain.values()]
    return chosen_date, sorted(latest, key=lambda x: x["domain"])


def load_silver_extraction_index(
    s3_client: Any,
    bucket_name: str,
    target_date: str,
) -> dict[tuple[str, int], dict[str, Any]]:
    """Load Silver extraction metadata keyed by (domain, timestamp) for citation enrichment."""
    index: dict[tuple[str, int], dict[str, Any]] = {}
    paginator = s3_client.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket_name, Prefix="silver/extractions/"):
        for obj in page.get("Contents", []):
            match = SILVER_JSON_KEY_PATTERN.match(obj["Key"])
            if not match or obj.get("Size", 0) == 0:
                continue
            domain, year, month, day, ts = match.groups()
            if f"{year}-{month}-{day}" != target_date:
                continue
            try:
                body = s3_client.get_object(Bucket=bucket_name, Key=obj["Key"])["Body"]
                payload = json.loads(body.read().decode("utf-8", errors="replace"))
                comps = payload.get("competitions") or []
                first_comp = comps[0] if comps else {}
                meta = payload.get("_metadata") or {}
                index[(domain, int(ts))] = {
                    "competition_name": first_comp.get("name") or domain,
                    "canonical_url": first_comp.get("url") or meta.get("canonical_official_url") or "",
                    "category": first_comp.get("category") or [],
                    "mode": first_comp.get("mode") or "unknown",
                    "registration_status": first_comp.get("registration_status") or "unknown",
                }
            except (json.JSONDecodeError, KeyError, TypeError):
                continue
    return index


def load_competition_documents_from_silver(
    s3_client: Any,
    bucket_name: str,
    target_date: str | None = None,
) -> tuple[str, list[Document]]:
    """Load Clean Markdown Documents strictly from R2 `silver/markdown/`."""
    chosen_date, snapshots = list_latest_silver_markdown_snapshots(
        s3_client=s3_client,
        bucket_name=bucket_name,
        target_date=target_date,
    )
    ext_index = load_silver_extraction_index(s3_client, bucket_name, chosen_date)
    docs: list[Document] = []

    for snap in snapshots:
        resp = s3_client.get_object(Bucket=bucket_name, Key=snap["key"])
        content = resp["Body"].read().decode("utf-8", errors="replace").strip()
        if not content:
            continue
        obj_meta = resp.get("Metadata") or {}
        ext_meta = ext_index.get((snap["domain"], snap["timestamp"]), {})

        canonical_url = (
            ext_meta.get("canonical_url")
            or obj_meta.get("canonical_url")
            or obj_meta.get("source_url")
            or f"https://{snap['domain']}"
        )
        comp_name = ext_meta.get("competition_name") or snap["domain"]
        docs.append(
            Document(
                page_content=content,
                metadata={
                    "domain": snap["domain"],
                    "competition_name": comp_name,
                    "source_url": canonical_url,
                    "canonical_url": canonical_url,
                    "source_key": snap["key"],
                    "bronze_key": obj_meta.get("bronze_key", ""),
                    "crawl_date": snap["date"],
                    "crawl_timestamp": snap["timestamp"],
                    "category": ext_meta.get("category", []),
                    "mode": ext_meta.get("mode", "unknown"),
                    "registration_status": ext_meta.get("registration_status", "unknown"),
                    "layer": "silver",
                },
            )
        )
    return chosen_date, docs


def build_chunker(embeddings: Embeddings) -> SemanticChunker:
    return SemanticChunker(
        embeddings=embeddings,
        breakpoint_threshold_type="percentile",
        breakpoint_threshold_amount=90,
        sentence_split_regex=r"(?<=[.?!])\s+|\n+",
        min_chunk_size=200,
    )


def chunk_single_document(chunker: SemanticChunker, doc: Document) -> list[Document]:
    parts = chunker.split_documents([doc])
    label = doc.metadata.get("competition_name") or doc.metadata["domain"]
    url = doc.metadata.get("canonical_url") or doc.metadata["source_url"]
    for idx, part in enumerate(parts):
        part.page_content = f"[Nguồn: {label} | URL: {url}]\n{part.page_content}"
        part.metadata["chunk_index"] = idx
    return parts


def ensure_collection(
    qdrant_client: QdrantClient,
    embeddings: Embeddings,
    collection_name: str,
    expected_dim: int,
) -> None:
    if qdrant_client.collection_exists(collection_name):
        info = qdrant_client.get_collection(collection_name)
        vec_cfg = info.config.params.vectors
        existing_dim = vec_cfg.size if isinstance(vec_cfg, VectorParams) else None
        if existing_dim is not None and existing_dim != expected_dim:
            raise RuntimeError(
                f"Collection '{collection_name}' dim={existing_dim} != expected {expected_dim}."
            )
        return

    dim = len(embeddings.embed_query("dimension probe"))
    qdrant_client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
    )
    for field_name in ("metadata.domain", "metadata.canonical_url"):
        qdrant_client.create_payload_index(
            collection_name=collection_name,
            field_name=field_name,
            field_schema=PayloadSchemaType.KEYWORD,
        )


def ingest(
    target_date: str | None = None,
    dry_run: bool = False,
    max_docs: int = 0,
) -> dict[str, Any]:
    """Ingest Clean Markdown from R2 `silver/markdown/` into Qdrant Cloud."""
    if not settings.bucket_name:
        raise RuntimeError("BUCKET_NAME is required in .env.")

    s3_client = settings.create_r2_client()
    chosen_date, docs = load_competition_documents_from_silver(
        s3_client=s3_client,
        bucket_name=settings.bucket_name,
        target_date=target_date,
    )
    if max_docs > 0:
        docs = docs[:max_docs]

    collection_name = settings.get_qdrant_collection()
    embedding_dim = int(os.getenv("CLOUDFLARE_EMBEDDING_DIM", "1024"))
    print(
        f">> Silver RAG Ingest | Date: {chosen_date} | Docs: {len(docs)} "
        f"| Model: {settings.get_embedding_model()} ({embedding_dim}d) | Collection: {collection_name}"
    )

    if dry_run or not docs:
        for d in docs:
            print(
                f"  [DRY-RUN] {d.metadata['domain']} -> {d.metadata['canonical_url']} "
                f"({len(d.page_content):,} chars)"
            )
        return {"chosen_date": chosen_date, "docs_loaded": len(docs), "total_chunks": 0, "dry_run": dry_run}

    embeddings = CloudflareWorkersAIEmbeddings()
    qdrant_client = QdrantClient(
        url=settings.get_qdrant_url(),
        api_key=settings.qdrant_api_key or os.getenv("QDRANT_API_KEY") or None,
    )
    ensure_collection(qdrant_client, embeddings, collection_name, embedding_dim)
    chunker = build_chunker(embeddings)
    store = QdrantVectorStore(
        client=qdrant_client,
        collection_name=collection_name,
        embedding=embeddings,
    )

    total_chunks = 0
    completed_domains: list[str] = []
    for idx, doc in enumerate(docs, 1):
        domain = doc.metadata["domain"]
        print(f">> [{idx}/{len(docs)}] Chunking & embedding from silver/markdown/: {domain} ...")
        try:
            parts = chunk_single_document(chunker, doc)
            ids = [
                str(uuid.uuid5(uuid.NAMESPACE_URL, f"{c.metadata['source_key']}#{c.metadata['chunk_index']}"))
                for c in parts
            ]
            qdrant_client.delete(
                collection_name=collection_name,
                points_selector=Filter(
                    must=[FieldCondition(key="metadata.domain", match=MatchValue(value=domain))]
                ),
            )
            store.add_documents(parts, ids=ids, batch_size=EMBED_BATCH_SIZE)
            completed_domains.append(domain)
            total_chunks += len(parts)
        except EmbeddingRateLimitError as exc:
            print(f"\n>> [429 STOP] {exc}")
            raise SystemExit(1) from exc

    print(f">> Hoàn tất ingest {total_chunks} chunk ({len(completed_domains)} domain) từ silver/markdown/ vào '{collection_name}'.")
    return {
        "chosen_date": chosen_date,
        "docs_loaded": len(docs),
        "completed_domains": completed_domains,
        "total_chunks": total_chunks,
        "dry_run": False,
    }


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="ACDP v2 Silver-to-Qdrant Vector Ingestion")
    parser.add_argument("--date", type=str, default=None, help="Target Silver date (YYYY-MM-DD)")
    parser.add_argument("--dry-run", action="store_true", help="Load Silver Markdown only without embedding/upsert")
    parser.add_argument("--max-docs", type=int, default=0, help="Optional cap on Silver documents to ingest")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)
    ingest(target_date=args.date, dry_run=args.dry_run, max_docs=args.max_docs)


if __name__ == "__main__":
    main()
