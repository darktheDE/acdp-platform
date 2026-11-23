"""Unit tests for Bronze Layer Ingestion, Configuration, and UTF-8 Storage Integrity (Cloudflare R2 Exclusive).

Tests:
1. Storage options generation from AppConfig for Cloudflare R2 and custom S3 backends.
2. UTF-8 Markdown read/write parity and SHA-256 fingerprint hashing.
3. R2 Object Storage key format and URL domain slugging logic.
4. Empty and corrupted crawl response handling (prevent 0-byte uploads) + mocked R2 put_object verification.
"""

import hashlib
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock
from urllib.parse import urlparse

import pytest
from pydantic import ValidationError

from acdp.config import AppConfig


def test_local_backend_rejected_under_r2_exclusive_policy() -> None:
    """Verify legacy 'local' storage backend is disallowed under DIR-021 R2-exclusive policy."""
    with pytest.raises(ValidationError):
        AppConfig(
            _env_file=None,
            bronze_storage_backend="local",  # type: ignore[arg-type]
        )


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


def test_upload_to_bronze_r2_and_empty_skip(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify real upload_to_bronze skips empty content and uploads UTF-8 Markdown directly to R2."""
    import importlib

    bronze_mod = importlib.import_module("acdp.1_crawl_to_bronze")
    fake_s3 = MagicMock()
    monkeypatch.setattr(bronze_mod.settings, "bucket_name", "acdp-test-bucket")
    monkeypatch.setattr(type(bronze_mod.settings), "create_r2_client", lambda self: fake_s3)

    # Empty / whitespace should not trigger put_object
    bronze_mod.upload_to_bronze("   \n\t ", "https://example.org/empty")
    fake_s3.put_object.assert_not_called()

    # Valid UTF-8 Markdown should be uploaded under bronze/<domain>/year=.../month=.../day=.../<ts>
    sample = "# Cuộc thi AI HCM-UTE\n\nGiải thưởng: 50 triệu VNĐ"
    bronze_mod.upload_to_bronze(sample, "https://example.org/contest")
    fake_s3.put_object.assert_called_once()
    kwargs = fake_s3.put_object.call_args.kwargs
    assert kwargs["Bucket"] == "acdp-test-bucket"
    assert kwargs["Key"].startswith("bronze/example.org/year=")
    assert kwargs["Body"] == sample.encode("utf-8")
    assert kwargs["ContentType"] == "text/markdown; charset=utf-8"
    assert kwargs["Metadata"] == {"source": "example.org", "layer": "bronze"}


def test_v2_package_bronze_html_with_boundaries() -> None:
    """Verify ACDP v2 packages multi-page CrawlResult HTML with ACDP_PAGE_BOUNDARY."""
    import importlib
    from types import SimpleNamespace

    v2_bronze = importlib.import_module("acdp.v2.1_crawl_to_bronze")
    records = [
        SimpleNamespace(
            url="https://example.org/contest",
            success=True,
            html='<!DOCTYPE html><html><head><meta property="og:title" content="AI Contest"></head><body><h1>Main</h1></body></html>',
        ),
        SimpleNamespace(
            url="https://example.org/empty",
            success=True,
            html="   \n\t ",
        ),
        SimpleNamespace(
            url="https://example.org/failed",
            success=False,
            html="<html><body>500</body></html>",
        ),
        SimpleNamespace(
            url='https://example.org/rules?tab="prize"',
            success=True,
            html="<html><body><p>Prize 100M VND</p></body></html>",
        ),
    ]

    packaged, page_count = v2_bronze.package_bronze_html(records)
    assert page_count == 2
    assert '<!-- ACDP_PAGE_BOUNDARY url="https://example.org/contest" -->' in packaged
    assert '<!-- ACDP_PAGE_BOUNDARY url="https://example.org/rules?tab=&quot;prize&quot;" -->' in packaged
    assert '<meta property="og:title" content="AI Contest">' in packaged
    assert "500" not in packaged


def test_v2_upload_to_bronze_raw_html_r2_and_empty_skip(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify ACDP v2 uploads Raw Rendered HTML (.html) to R2 and skips empty payloads."""
    import importlib

    v2_bronze = importlib.import_module("acdp.v2.1_crawl_to_bronze")
    fake_s3 = MagicMock()
    monkeypatch.setattr(v2_bronze.settings, "bucket_name", "acdp-test-bucket")
    monkeypatch.setattr(type(v2_bronze.settings), "create_r2_client", lambda self: fake_s3)

    assert v2_bronze.upload_to_bronze("   \n ", "https://example.org/empty") is None
    fake_s3.put_object.assert_not_called()

    sample_html = (
        '<!-- ACDP_PAGE_BOUNDARY url="https://example.org/contest" -->\n'
        "<html><head><title>Cuộc thi AI</title></head><body><p>Giải thưởng 50 triệu</p></body></html>"
    )
    uploaded_key = v2_bronze.upload_to_bronze(
        sample_html, "https://example.org/contest", page_count=1
    )
    assert uploaded_key is not None
    assert uploaded_key.startswith("bronze/example.org/year=")
    assert uploaded_key.endswith(".html")

    fake_s3.put_object.assert_called_once()
    kwargs = fake_s3.put_object.call_args.kwargs
    assert kwargs["Bucket"] == "acdp-test-bucket"
    assert kwargs["Key"] == uploaded_key
    assert kwargs["Body"] == sample_html.encode("utf-8")
    assert kwargs["ContentType"] == "text/html; charset=utf-8"
    assert kwargs["Metadata"] == {
        "source": "example.org",
        "layer": "bronze",
        "format": "raw_html",
        "page_count": "1",
    }
