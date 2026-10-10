"""Data contracts and schemas for the Bronze Lakehouse layer.

Includes Pydantic v2 validation models and PyArrow schemas for Delta Lake.
"""

from datetime import datetime, timezone
import hashlib
import json
from typing import Any
import uuid

from pydantic import BaseModel, Field
import pyarrow as pa


class BronzeRecord(BaseModel):
    """Pydantic model representing an immutable raw web ingestion record."""

    raw_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique identifier for the raw crawl event",
    )
    source_url: str = Field(..., description="Target source URL crawled")
    source_domain: str = Field(..., description="Root domain of the target source (e.g. codetour.org)")
    crawled_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp of crawl event in UTC",
    )
    http_status: int = Field(default=200, description="HTTP response status code")
    content_type: str = Field(default="text/html", description="MIME content type")
    content_hash: str = Field(
        ...,
        description="SHA-256 cryptographic hash of uncompressed content for deduplication",
    )
    raw_html_bytes: bytes = Field(
        ...,
        description="Zstandard-compressed raw binary payload",
    )
    metadata_json: str = Field(
        default="{}",
        description="JSON string containing crawler metadata, HTTP headers, and context",
    )

    @classmethod
    def create(
        cls,
        source_url: str,
        source_domain: str,
        raw_html: str,
        compress_fn: Any,
        http_status: int = 200,
        content_type: str = "text/html",
        metadata: dict[str, Any] | None = None,
        crawled_at: datetime | None = None,
    ) -> "BronzeRecord":
        """Factory method to construct a BronzeRecord with automatic hashing and compression."""
        raw_bytes_uncompressed = raw_html.encode("utf-8")
        content_hash = hashlib.sha256(raw_bytes_uncompressed).hexdigest()
        compressed_bytes = compress_fn(raw_html)
        metadata_str = json.dumps(metadata or {}, ensure_ascii=False)

        return cls(
            source_url=source_url,
            source_domain=source_domain,
            crawled_at=crawled_at or datetime.now(timezone.utc),
            http_status=http_status,
            content_type=content_type,
            content_hash=content_hash,
            raw_html_bytes=compressed_bytes,
            metadata_json=metadata_str,
        )


# PyArrow Schema for Delta Lake table persistence
BRONZE_ARROW_SCHEMA = pa.schema([
    pa.field("raw_id", pa.string(), nullable=False),
    pa.field("source_url", pa.string(), nullable=False),
    pa.field("source_domain", pa.string(), nullable=False),
    pa.field("crawled_at", pa.timestamp("us", tz="UTC"), nullable=False),
    pa.field("http_status", pa.int32(), nullable=False),
    pa.field("content_type", pa.string(), nullable=False),
    pa.field("content_hash", pa.string(), nullable=False),
    pa.field("raw_html_bytes", pa.binary(), nullable=False),
    pa.field("metadata_json", pa.string(), nullable=True),
])
