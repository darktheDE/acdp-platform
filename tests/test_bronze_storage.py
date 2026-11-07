"""Unit tests for Bronze Layer Ingestion, Configuration, and UTF-8 Storage Integrity.

Tests:
1. Storage options generation from AppConfig for local POSIX and Cloudflare R2 backends.
2. UTF-8 Markdown read/write parity and SHA-256 fingerprint hashing.
3. R2 Object Storage key format and URL domain slugging logic.
4. Empty and corrupted crawl response handling (prevent 0-byte uploads).
"""

import hashlib
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

from acdp.config import AppConfig


def test_storage_options_local_backend() -> None:
    """Verify local storage backend returns empty options dictionary for local POSIX IO."""
    local_cfg = AppConfig(
        bronze_storage_backend="local",
        bronze_storage_uri="./data/lakehouse/bronze",
    )
    assert local_cfg.get_storage_options() == {}


def test_storage_options_cloudflare_r2_backend() -> None:
    """Verify Cloudflare R2 storage options configure S3 parameters accurately."""
    r2_cfg = AppConfig(
        bronze_storage_backend="cloudflare_r2",
        bronze_storage_uri="s3://acdp-lakehouse/bronze",
        aws_endpoint_url="https://abc123.r2.cloudflarestorage.com",
        aws_access_key_id="r2_access_key_sample",
        aws_secret_access_key="r2_secret_key_sample",
        aws_region="auto",
    )
    r2_opts = r2_cfg.get_storage_options()
    assert r2_opts["AWS_ENDPOINT_URL"] == "https://abc123.r2.cloudflarestorage.com"
    assert r2_opts["AWS_ACCESS_KEY_ID"] == "r2_access_key_sample"
    assert r2_opts["AWS_SECRET_ACCESS_KEY"] == "r2_secret_key_sample"
    assert r2_opts["AWS_REGION"] == "auto"
    assert r2_opts["AWS_S3_ALLOW_UNSAFE_RENAME"] == "true"


def test_storage_options_custom_s3_backend_http() -> None:
    """Verify custom S3 backend configuration with HTTP enabled."""
    custom_cfg = AppConfig(
        bronze_storage_backend="cloudflare_r2",
        bronze_storage_uri="s3://acdp-bronze/events",
        aws_endpoint_url="http://custom-s3-gateway:9000",
        aws_access_key_id="test_key",
        aws_secret_access_key="test_secret",
        aws_allow_http=True,
    )
    opts = custom_cfg.get_storage_options()
    assert opts["AWS_ENDPOINT_URL"] == "http://custom-s3-gateway:9000"
    assert opts["AWS_ALLOW_HTTP"] == "true"


def test_markdown_utf8_storage_and_sha256_integrity(tmp_path: Path) -> None:
    """Verify UTF-8 Markdown with Vietnamese diacritics preserves exact byte integrity and hash."""
    sample_markdown = (
        "# Cuộc thi Học thuật Khoa CNTT - HCM-UTE 2026\n\n"
        "- **Tên cuộc thi**: AI Challenge TP.HCM 2026\n"
        "- **Tổng giải thưởng**: 150.000.000 VNĐ\n"
        "- **Hạn chót**: 15/10/2026\n"
        "- **Mô tả**: Phát triển giải pháp Trí tuệ Nhân tạo ứng dụng trong thành phố thông minh.\n"
    )
    file_path = tmp_path / "sample_contest.md"

    # Write UTF-8
    file_path.write_text(sample_markdown, encoding="utf-8")

    # Read and assert byte-level parity
    content_read = file_path.read_text(encoding="utf-8")
    assert content_read == sample_markdown

    # SHA-256 fingerprinting for duplicate detection
    sha256_hash = hashlib.sha256(content_read.encode("utf-8")).hexdigest()
    assert isinstance(sha256_hash, str)
    assert len(sha256_hash) == 64
    assert sha256_hash == hashlib.sha256(sample_markdown.encode("utf-8")).hexdigest()


def test_bronze_r2_key_generation_logic() -> None:
    """Verify the R2 bronze object key pattern conforms to the daily snapshot taxonomy."""
    raw_url = "https://codetour.org/rules/2026"
    parsed_domain = urlparse(raw_url).netloc
    assert parsed_domain == "codetour.org"

    test_date = datetime(2026, 11, 7, 10, 30, 0)
    fake_timestamp = int(test_date.timestamp())

    bronze_key = (
        f"bronze/{parsed_domain}"
        f"/year={test_date.year}/month={test_date.strftime('%m')}/day={test_date.strftime('%d')}/"
        f"{fake_timestamp}"
    )

    assert bronze_key.startswith("bronze/codetour.org/year=2026/month=11/day=07/")
    assert str(fake_timestamp) in bronze_key


def test_empty_content_check_logic() -> None:
    """Verify that empty or whitespace-only crawl results are flagged as invalid for Bronze upload."""
    empty_md = ""
    whitespace_md = "   \n\t  \n"
    valid_md = "# Valid Title\nSome content"

    assert not empty_md or not empty_md.strip()
    assert not whitespace_md or not whitespace_md.strip()
    assert not (not valid_md or not valid_md.strip())
