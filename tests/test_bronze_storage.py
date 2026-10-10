"""Unit and Integration Tests for Bronze Lakehouse Storage Engine.

Tests:
1. Zstandard compression & decompression bit-level integrity.
2. BronzeRecord creation and content hash generation.
3. Storage options generation for Tri-Storage backends (Local, SeaweedFS, Cloudflare R2).
4. Delta Lake writing, appending, and time-travel versioning (Zero-JVM).
5. DuckDB delta_scan in-process analytical querying.
"""

from datetime import datetime, timezone
import hashlib
from pathlib import Path

from deltalake import DeltaTable
import duckdb
import pytest

from acdp.config import AppConfig
from acdp.lakehouse.bronze import (
    compress_payload,
    decompress_payload,
    optimize_bronze_table,
    query_bronze_with_duckdb,
    write_bronze_batch,
)
from acdp.lakehouse.schema import BronzeRecord


def test_compression_decompression_parity() -> None:
    """Verify that compressing and decompressing preserves the exact string."""
    sample_html = (
        "<!DOCTYPE html><html><head><title>Test Hackathon</title></head>"
        "<body><h1>Cuộc thi Học thuật FIT-HCMUTE 2026</h1>"
        "<p>Giải nhất: 15.000.000 VND</p></body></html>"
    )
    compressed = compress_payload(sample_html)
    assert isinstance(compressed, bytes)
    assert len(compressed) < len(sample_html.encode("utf-8"))

    decompressed = decompress_payload(compressed)
    assert decompressed == sample_html


def test_bronze_record_factory() -> None:
    """Verify BronzeRecord factory computes correct SHA-256 and metadata."""
    sample_html = "<html><body>Event Announcement</body></html>"
    expected_hash = hashlib.sha256(sample_html.encode("utf-8")).hexdigest()

    record = BronzeRecord.create(
        source_url="https://codetour.org",
        source_domain="codetour.org",
        raw_html=sample_html,
        compress_fn=compress_payload,
        http_status=200,
        metadata={"crawler": "crawl4ai"},
    )

    assert record.source_url == "https://codetour.org"
    assert record.source_domain == "codetour.org"
    assert record.content_hash == expected_hash
    assert record.http_status == 200
    assert "crawler" in record.metadata_json
    assert decompress_payload(record.raw_html_bytes) == sample_html


def test_storage_options_backends() -> None:
    """Verify storage_options generation for local, seaweedfs, and cloudflare_r2."""
    # 1. Local backend
    local_cfg = AppConfig(
        bronze_storage_backend="local",
        bronze_storage_uri="./data/lakehouse/bronze",
    )
    assert local_cfg.get_storage_options() == {}

    # 2. SeaweedFS backend
    seaweed_cfg = AppConfig(
        bronze_storage_backend="seaweedfs",
        bronze_storage_uri="s3://acdp-bronze/events",
        aws_endpoint_url="http://localhost:8333",
        aws_access_key_id="test_key",
        aws_secret_access_key="test_secret",
        aws_allow_http=True,
    )
    seaweed_opts = seaweed_cfg.get_storage_options()
    assert seaweed_opts["AWS_ENDPOINT_URL"] == "http://localhost:8333"
    assert seaweed_opts["AWS_ACCESS_KEY_ID"] == "test_key"
    assert seaweed_opts["AWS_SECRET_ACCESS_KEY"] == "test_secret"
    assert seaweed_opts["AWS_ALLOW_HTTP"] == "true"
    assert seaweed_opts["AWS_S3_ALLOW_UNSAFE_RENAME"] == "true"

    # 3. Cloudflare R2 backend
    r2_cfg = AppConfig(
        bronze_storage_backend="cloudflare_r2",
        bronze_storage_uri="s3://acdp-bronze/events",
        aws_endpoint_url="https://abc123.r2.cloudflarestorage.com",
        aws_access_key_id="r2_key",
        aws_secret_access_key="r2_secret",
        aws_region="auto",
    )
    r2_opts = r2_cfg.get_storage_options()
    assert r2_opts["AWS_ENDPOINT_URL"] == "https://abc123.r2.cloudflarestorage.com"
    assert r2_opts["AWS_ACCESS_KEY_ID"] == "r2_key"
    assert r2_opts["AWS_SECRET_ACCESS_KEY"] == "r2_secret"
    assert r2_opts["AWS_REGION"] == "auto"


def test_delta_lake_local_write_and_append(tmp_path: Path) -> None:
    """Verify Delta Lake batch write, version tracking, and compaction on local filesystem."""
    test_table_dir = tmp_path / "lakehouse_bronze"
    test_cfg = AppConfig(
        bronze_storage_backend="local",
        bronze_storage_uri=str(test_table_dir),
    )

    records_batch_1 = [
        BronzeRecord.create(
            source_url="https://fit.hcmute.edu.vn/event/1",
            source_domain="fit.hcmute.edu.vn",
            raw_html="<html><body>Event 1 Payload</body></html>",
            compress_fn=compress_payload,
        ),
        BronzeRecord.create(
            source_url="https://fit.hcmute.edu.vn/event/2",
            source_domain="fit.hcmute.edu.vn",
            raw_html="<html><body>Event 2 Payload</body></html>",
            compress_fn=compress_payload,
        ),
    ]

    # Batch 1 write
    count_1 = write_bronze_batch(records_batch_1, config=test_cfg)
    assert count_1 == 2

    dt = DeltaTable(str(test_table_dir))
    assert dt.version() == 0
    assert len(dt.file_uris()) >= 1

    # Batch 2 append
    records_batch_2 = [
        BronzeRecord.create(
            source_url="https://codetour.org/2026",
            source_domain="codetour.org",
            raw_html="<html><body>Code Tour 2026</body></html>",
            compress_fn=compress_payload,
        ),
    ]
    count_2 = write_bronze_batch(records_batch_2, config=test_cfg, mode="append")
    assert count_2 == 1

    dt_updated = DeltaTable(str(test_table_dir))
    assert dt_updated.version() == 1
    assert dt_updated.to_pyarrow_table().num_rows == 3

    # Compaction optimize call
    optimize_bronze_table(config=test_cfg)


def test_duckdb_query_local_delta(tmp_path: Path) -> None:
    """Verify DuckDB queries Delta Lake table correctly via delta extension."""
    test_table_dir = tmp_path / "duckdb_test_bronze"
    test_cfg = AppConfig(
        bronze_storage_backend="local",
        bronze_storage_uri=str(test_table_dir),
    )

    html_content = "<html><body>Testing DuckDB Integration</body></html>"
    record = BronzeRecord.create(
        source_url="https://aichallenge.hochiminhcity.gov.vn",
        source_domain="aichallenge.hochiminhcity.gov.vn",
        raw_html=html_content,
        compress_fn=compress_payload,
        http_status=200,
    )

    write_bronze_batch([record], config=test_cfg)

    # Query via DuckDB
    escaped_path = str(test_table_dir).replace("\\", "/")
    query = f"""
        SELECT 
            raw_id, 
            source_domain, 
            http_status,
            octet_length(raw_html_bytes) as compressed_len
        FROM delta_scan('{escaped_path}')
    """
    rel = query_bronze_with_duckdb(query, config=test_cfg)
    arrow_tbl = rel.arrow().read_all()

    assert arrow_tbl.num_rows == 1
    assert arrow_tbl.column("source_domain")[0].as_py() == "aichallenge.hochiminhcity.gov.vn"
    assert arrow_tbl.column("http_status")[0].as_py() == 200
    assert arrow_tbl.column("compressed_len")[0].as_py() > 0


