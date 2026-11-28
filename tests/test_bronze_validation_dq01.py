"""Automated test suite for TASK-DQ-01: Bronze Validation, Provenance & Idempotency.

Uses an in-memory FakeR2Client faithfully emulating Cloudflare R2 S3 API semantics:
- `IfNoneMatch="*"` conditional write enforcement (HTTP 412 PreconditionFailed)
- `ChecksumAlgorithm="SHA256"` / `ChecksumSHA256` payload verification
- `copy_object` with `MetadataDirective="REPLACE"` for Option A metadata backfill
- Parquet Silver/Gold downstream `bronze_key` lineage resolution
"""

from __future__ import annotations

import base64
import hashlib
import io
from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq
import pytest
from botocore.exceptions import ClientError

from acdp.v2 import bronze_crawl, bronze_validate


class _FakeBody:
    def __init__(self, data: bytes) -> None:
        self._data = data

    def read(self) -> bytes:
        return self._data


class FakeR2Client:
    """In-memory Cloudflare R2 / S3 client implementing conditional writes and checksums."""

    def __init__(self) -> None:
        self.objects: dict[str, dict[str, Any]] = {}
        self.put_calls: list[dict[str, Any]] = []

    def seed_object(
        self,
        key: str,
        body: bytes,
        *,
        content_type: str = "text/html; charset=utf-8",
        metadata: dict[str, str] | None = None,
    ) -> None:
        self.objects[key] = {
            "Body": body,
            "ContentType": content_type,
            "Metadata": dict(metadata or {}),
            "ETag": f'"{hashlib.md5(body).hexdigest()}"',
            "LastModified": datetime.now(UTC),
        }

    def put_object(
        self,
        *,
        Bucket: str,
        Key: str,
        Body: bytes,
        ContentType: str = "application/octet-stream",
        Metadata: dict[str, str] | None = None,
        IfNoneMatch: str | None = None,
        ChecksumAlgorithm: str | None = None,
        ChecksumSHA256: str | None = None,
    ) -> dict[str, Any]:
        self.put_calls.append({"Bucket": Bucket, "Key": Key, "IfNoneMatch": IfNoneMatch})

        if IfNoneMatch == "*" and Key in self.objects:
            raise ClientError(
                {"Error": {"Code": "PreconditionFailed", "Message": "Object already exists"}, "ResponseMetadata": {"HTTPStatusCode": 412}},
                "PutObject",
            )

        if ChecksumAlgorithm == "SHA256" and ChecksumSHA256 is not None:
            expected_b64 = base64.b64encode(hashlib.sha256(Body).digest()).decode("ascii")
            if ChecksumSHA256 != expected_b64:
                raise ClientError(
                    {"Error": {"Code": "BadDigest", "Message": "SHA-256 mismatch"}, "ResponseMetadata": {"HTTPStatusCode": 400}},
                    "PutObject",
                )

        etag = f'"{hashlib.md5(Body).hexdigest()}"'
        self.objects[Key] = {
            "Body": Body,
            "ContentType": ContentType,
            "Metadata": dict(Metadata or {}),
            "ETag": etag,
            "LastModified": datetime.now(UTC),
        }
        return {"ETag": etag}

    def head_object(self, *, Bucket: str, Key: str) -> dict[str, Any]:
        if Key not in self.objects:
            raise ClientError(
                {"Error": {"Code": "NoSuchKey", "Message": "Not found"}, "ResponseMetadata": {"HTTPStatusCode": 404}},
                "HeadObject",
            )
        obj = self.objects[Key]
        return {
            "ContentType": obj["ContentType"],
            "Metadata": dict(obj["Metadata"]),
            "ETag": obj["ETag"],
            "ContentLength": len(obj["Body"]),
            "LastModified": obj["LastModified"],
        }

    def get_object(self, *, Bucket: str, Key: str) -> dict[str, Any]:
        if Key not in self.objects:
            raise ClientError(
                {"Error": {"Code": "NoSuchKey", "Message": "Not found"}, "ResponseMetadata": {"HTTPStatusCode": 404}},
                "GetObject",
            )
        obj = self.objects[Key]
        return {
            "Body": _FakeBody(obj["Body"]),
            "ContentType": obj["ContentType"],
            "Metadata": dict(obj["Metadata"]),
            "ETag": obj["ETag"],
            "LastModified": obj["LastModified"],
        }

    def list_objects_v2(
        self,
        *,
        Bucket: str,
        Prefix: str = "",
        ContinuationToken: str | None = None,
    ) -> dict[str, Any]:
        contents = [
            {
                "Key": k,
                "Size": len(v["Body"]),
                "ETag": v["ETag"],
                "LastModified": v["LastModified"],
            }
            for k, v in sorted(self.objects.items())
            if k.startswith(Prefix)
        ]
        return {"Contents": contents, "IsTruncated": False}

    def copy_object(
        self,
        *,
        Bucket: str,
        CopySource: dict[str, str],
        Key: str,
        MetadataDirective: str = "COPY",
        ContentType: str | None = None,
        Metadata: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        src_key = CopySource["Key"]
        if src_key not in self.objects:
            raise ClientError(
                {"Error": {"Code": "NoSuchKey", "Message": "Not found"}, "ResponseMetadata": {"HTTPStatusCode": 404}},
                "CopyObject",
            )
        src = self.objects[src_key]
        new_meta = dict(Metadata or {}) if MetadataDirective == "REPLACE" else dict(src["Metadata"])
        self.objects[Key] = {
            "Body": src["Body"],
            "ContentType": ContentType or src["ContentType"],
            "Metadata": new_meta,
            "ETag": src["ETag"],
            "LastModified": datetime.now(UTC),
        }
        return {"CopyObjectResult": {"ETag": src["ETag"]}}


def _parquet_bytes(rows: list[dict[str, Any]]) -> bytes:
    buf = io.BytesIO()
    pq.write_table(pa.Table.from_pylist(rows), buf)
    return buf.getvalue()


def test_bronze_upload_attaches_full_provenance_metadata_and_sha256(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_r2 = FakeR2Client()
    monkeypatch.setattr(bronze_crawl.settings, "bucket_name", "acdp-test")

    sample_html = (
        '<!-- ACDP_PAGE_BOUNDARY url="https://codetour.org/" -->\n'
        "<html><head><title>Code Tour 2026</title></head><body><p>Cuộc thi lập trình</p></body></html>"
    )
    fixed_time = datetime(2026, 11, 28, 8, 30, 0, tzinfo=UTC)

    res = bronze_crawl.upload_to_bronze_with_result(
        sample_html,
        "https://codetour.org/",
        page_count=1,
        http_status=200,
        crawl_mode="adaptive",
        crawled_at=fixed_time,
        s3_client=fake_r2,
    )

    assert res.status == "uploaded"
    assert res.bronze_key == f"bronze/codetour.org/year=2026/month=11/day=28/{int(fixed_time.timestamp())}.html"
    assert res.content_hash == hashlib.sha256(sample_html.encode("utf-8")).hexdigest()
    assert res.http_status == "200"
    assert res.crawled_at == "2026-11-28T08:30:00Z"

    head = fake_r2.head_object(Bucket="acdp-test", Key=res.bronze_key)
    meta = head["Metadata"]
    for key in bronze_crawl.REQUIRED_PROVENANCE_KEYS:
        assert key in meta and meta[key]
    assert meta["content_hash"] == res.content_hash
    assert meta["source_url"] == "https://codetour.org/"
    assert meta["http_status"] == "200"


def test_bronze_utf8_vietnamese_diacritics_and_sha256_parity(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_r2 = FakeR2Client()
    monkeypatch.setattr(bronze_crawl.settings, "bucket_name", "acdp-test")

    html_vn = (
        '<!-- ACDP_PAGE_BOUNDARY url="https://dataforlife.vn/" -->\n'
        "<html><body><h1>Cuộc thi Data For Life — Giải thưởng 500 triệu VNĐ</h1></body></html>"
    )
    res = bronze_crawl.upload_to_bronze_with_result(
        html_vn,
        "https://dataforlife.vn/",
        http_status=200,
        s3_client=fake_r2,
    )
    assert res.bronze_key is not None
    stored = fake_r2.get_object(Bucket="acdp-test", Key=res.bronze_key)["Body"].read()
    assert stored.decode("utf-8", errors="strict") == html_vn
    assert hashlib.sha256(stored).hexdigest() == res.content_hash


def test_bronze_idempotent_recrawl_same_content_creates_no_duplicate(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_r2 = FakeR2Client()
    monkeypatch.setattr(bronze_crawl.settings, "bucket_name", "acdp-test")

    html_payload = '<!-- ACDP_PAGE_BOUNDARY url="https://thucchien.ai/" -->\n<html><body>AI Contest</body></html>'
    t1 = datetime(2026, 11, 28, 9, 0, 0, tzinfo=UTC)
    t2 = datetime(2026, 11, 28, 9, 5, 0, tzinfo=UTC)

    pass1 = bronze_crawl.upload_to_bronze_with_result(
        html_payload,
        "https://thucchien.ai/",
        http_status=200,
        crawled_at=t1,
        s3_client=fake_r2,
    )
    pass2 = bronze_crawl.upload_to_bronze_with_result(
        html_payload,
        "https://thucchien.ai/",
        http_status=200,
        crawled_at=t2,
        s3_client=fake_r2,
    )

    assert pass1.status == "uploaded"
    assert pass2.status == "skipped_unchanged"
    assert pass2.bronze_key is None
    assert pass2.existing_key == pass1.bronze_key
    assert len(fake_r2.objects) == 1
    assert len(fake_r2.put_calls) == 1


def test_bronze_changed_content_appends_new_immutable_version(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_r2 = FakeR2Client()
    monkeypatch.setattr(bronze_crawl.settings, "bucket_name", "acdp-test")

    v1_html = '<!-- ACDP_PAGE_BOUNDARY url="https://codetour.org/" -->\n<html><body>Version 1</body></html>'
    v2_html = '<!-- ACDP_PAGE_BOUNDARY url="https://codetour.org/" -->\n<html><body>Version 2: Prize updated</body></html>'

    res1 = bronze_crawl.upload_to_bronze_with_result(
        v1_html,
        "https://codetour.org/",
        http_status=200,
        crawled_at=datetime(2026, 11, 28, 10, 0, 0, tzinfo=UTC),
        s3_client=fake_r2,
    )
    res2 = bronze_crawl.upload_to_bronze_with_result(
        v2_html,
        "https://codetour.org/",
        http_status=200,
        crawled_at=datetime(2026, 11, 28, 10, 1, 0, tzinfo=UTC),
        s3_client=fake_r2,
    )

    assert res1.status == "uploaded" and res2.status == "uploaded"
    assert res1.bronze_key != res2.bronze_key
    assert len(fake_r2.objects) == 2
    assert fake_r2.objects[res1.bronze_key]["Body"].decode("utf-8") == v1_html
    assert fake_r2.objects[res2.bronze_key]["Body"].decode("utf-8") == v2_html


def test_bronze_if_none_match_prevents_overwrite_and_retries_next_second(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_r2 = FakeR2Client()
    monkeypatch.setattr(bronze_crawl.settings, "bucket_name", "acdp-test")

    ts_dt = datetime(2026, 11, 28, 11, 0, 0, tzinfo=UTC)
    html1 = '<!-- ACDP_PAGE_BOUNDARY url="https://codetour.org/" -->\n<html><body>First</body></html>'
    html2 = '<!-- ACDP_PAGE_BOUNDARY url="https://codetour.org/" -->\n<html><body>Second different</body></html>'

    res1 = bronze_crawl.upload_to_bronze_with_result(
        html1,
        "https://codetour.org/",
        http_status=200,
        crawled_at=ts_dt,
        s3_client=fake_r2,
    )
    res2 = bronze_crawl.upload_to_bronze_with_result(
        html2,
        "https://codetour.org/",
        http_status=200,
        crawled_at=ts_dt,
        s3_client=fake_r2,
    )

    assert res1.status == "uploaded" and res2.status == "uploaded"
    assert res2.immutable_conflict_retries == 1
    assert res1.bronze_key != res2.bronze_key
    assert res2.bronze_key.endswith(f"/{int(ts_dt.timestamp()) + 1}.html")
    assert fake_r2.objects[res1.bronze_key]["Body"].decode("utf-8") == html1


def test_bronze_empty_or_whitespace_payload_skipped(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_r2 = FakeR2Client()
    monkeypatch.setattr(bronze_crawl.settings, "bucket_name", "acdp-test")

    res = bronze_crawl.upload_to_bronze_with_result(
        "   \n\t ",
        "https://example.org/",
        http_status=403,
        s3_client=fake_r2,
    )
    assert res.status == "skipped_empty"
    assert res.bronze_key is None
    assert len(fake_r2.objects) == 0


def test_extract_primary_http_status_from_crawl_results() -> None:
    records = [
        SimpleNamespace(success=False, html="<html>err</html>", status_code=500),
        SimpleNamespace(success=True, html="   ", status_code=204),
        SimpleNamespace(success=True, html="<html>ok</html>", status_code=None, redirected_status_code=200),
    ]
    assert bronze_crawl.extract_primary_http_status(records) == 200
    assert bronze_crawl.extract_primary_http_status([SimpleNamespace(success=True, html="<html>ok</html>")]) is None


def test_bronze_audit_passes_for_compliant_v2_and_downstream_silver_gold(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_r2 = FakeR2Client()
    monkeypatch.setattr(bronze_crawl.settings, "bucket_name", "acdp-test")

    html_ok = '<!-- ACDP_PAGE_BOUNDARY url="https://codetour.org/" -->\n<html><body>Code Tour</body></html>'
    up = bronze_crawl.upload_to_bronze_with_result(
        html_ok,
        "https://codetour.org/",
        http_status=200,
        crawled_at=datetime(2026, 11, 28, 12, 0, 0, tzinfo=UTC),
        s3_client=fake_r2,
    )
    assert up.bronze_key is not None

    # Seed legacy v1 (.md) and system objects which must NOT fail v2 audit
    fake_r2.seed_object("bronze/old.org/year=2026/month=10/day=31/1793441233", b"# Legacy MD", content_type="text/markdown; charset=utf-8")
    fake_r2.seed_object("bronze/_discovery/latest_manifest.json", b"{}", content_type="application/json")

    # Seed Silver and Gold Parquet linking back to Bronze
    fake_r2.seed_object(
        "silver/competitions.parquet",
        _parquet_bytes([{"competition_key": "ck-1", "name": "Code Tour", "bronze_key": up.bronze_key}]),
        content_type="application/octet-stream",
    )
    fake_r2.seed_object(
        "gold/dim_competition.parquet",
        _parquet_bytes([{"competition_key": "ck-1", "name": "Code Tour"}]),
        content_type="application/octet-stream",
    )

    report = bronze_validate.audit_bronze_bucket(s3_client=fake_r2, bucket_name="acdp-test")
    assert report.overall_status == "PASS"
    assert report.v2_html_count == 1
    assert report.v1_legacy_count == 1
    assert report.system_count == 1
    assert report.provenance_pass_rate == 100.0
    assert report.hash_integrity_pass_rate == 100.0
    assert report.utf8_pass_rate == 100.0
    assert report.downstream.silver_resolved_in_bronze == 1
    assert report.downstream.gold_linked_to_silver == 1


def test_bronze_audit_detects_missing_metadata_and_hash_tampering() -> None:
    fake_r2 = FakeR2Client()
    raw = b'<!-- ACDP_PAGE_BOUNDARY url="https://tamper.org/" -->\n<html><body>Original</body></html>'
    fake_r2.seed_object(
        "bronze/tamper.org/year=2026/month=11/day=23/1795418000.html",
        raw,
        metadata={
            "source": "tamper.org",
            "source_url": "https://tamper.org/",
            "layer": "bronze",
            "format": "raw_html",
            "page_count": "1",
            "content_hash": "0" * 64,
            "content_bytes": str(len(raw)),
            "crawled_at": "2026-11-23T06:00:00Z",
            "crawl_mode": "adaptive",
            # missing http_status
        },
    )
    report = bronze_validate.audit_bronze_bucket(s3_client=fake_r2, bucket_name="acdp-test", check_downstream=False)
    assert report.overall_status == "FAIL"
    v2_obj = next(o for o in report.objects if o.tier == "v2_html")
    assert v2_obj.hash_matches is False
    assert v2_obj.metadata_complete is False
    assert "http_status" in v2_obj.missing_metadata_keys
    assert "sha256_integrity_mismatch" in v2_obj.issues


def test_bronze_audit_detects_invalid_utf8_and_missing_boundary() -> None:
    fake_r2 = FakeR2Client()
    bad_bytes = b"\xff\xfe<html><body>No boundary & bad UTF8</body></html>"
    digest = hashlib.sha256(bad_bytes).hexdigest()
    fake_r2.seed_object(
        "bronze/bad.org/year=2026/month=11/day=23/1795418000.html",
        bad_bytes,
        metadata={
            "source": "bad.org",
            "source_url": "https://bad.org/",
            "layer": "bronze",
            "format": "raw_html",
            "page_count": "1",
            "content_hash": digest,
            "content_bytes": str(len(bad_bytes)),
            "crawled_at": "2026-11-23T06:00:00Z",
            "http_status": "200",
            "crawl_mode": "adaptive",
        },
    )
    report = bronze_validate.audit_bronze_bucket(s3_client=fake_r2, bucket_name="acdp-test", check_downstream=False)
    assert report.overall_status == "FAIL"
    v2_obj = next(o for o in report.objects if o.tier == "v2_html")
    assert v2_obj.utf8_valid is False
    assert any(i.startswith("invalid_utf8:") for i in v2_obj.issues)


def test_bronze_audit_detects_uncontrolled_duplicate_and_dangling_silver() -> None:
    fake_r2 = FakeR2Client()
    html_bytes = b'<!-- ACDP_PAGE_BOUNDARY url="https://dup.org/" -->\n<html><body>Same</body></html>'
    digest = hashlib.sha256(html_bytes).hexdigest()
    base_meta = {
        "source": "dup.org",
        "source_url": "https://dup.org/",
        "layer": "bronze",
        "format": "raw_html",
        "page_count": "1",
        "content_hash": digest,
        "content_bytes": str(len(html_bytes)),
        "crawled_at": "2026-11-23T06:00:00Z",
        "http_status": "200",
        "crawl_mode": "adaptive",
    }
    fake_r2.seed_object("bronze/dup.org/year=2026/month=11/day=23/1795418000.html", html_bytes, metadata=base_meta)
    fake_r2.seed_object("bronze/dup.org/year=2026/month=11/day=23/1795418099.html", html_bytes, metadata=base_meta)
    fake_r2.seed_object(
        "silver/competitions.parquet",
        _parquet_bytes([{"competition_key": "ck-missing", "name": "Ghost", "bronze_key": "bronze/missing/123.html"}]),
        content_type="application/octet-stream",
    )

    report = bronze_validate.audit_bronze_bucket(s3_client=fake_r2, bucket_name="acdp-test")
    assert report.overall_status == "FAIL"
    assert len(report.duplicate_content_groups) == 1
    assert report.downstream.silver_dangling_keys == ["bronze/missing/123.html"]


def test_bronze_backfill_preserves_exact_bytes_and_populates_provenance(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_r2 = FakeR2Client()
    monkeypatch.setattr(bronze_crawl.settings, "bucket_name", "acdp-test")

    key = "bronze/vietnamdatathon.com/year=2026/month=11/day=23/1795418000.html"
    raw = '<!-- ACDP_PAGE_BOUNDARY url="https://vietnamdatathon.com/" -->\n<html><body>Datathon Tiếng Việt</body></html>'.encode()
    expected_sha = hashlib.sha256(raw).hexdigest()
    fake_r2.seed_object(
        key,
        raw,
        metadata={"source": "vietnamdatathon.com", "layer": "bronze", "format": "raw_html", "page_count": "1"},
    )

    dry = bronze_validate.backfill_v2_bronze_metadata(s3_client=fake_r2, bucket_name="acdp-test", dry_run=True)
    assert dry["backfilled"] == 1
    assert "content_hash" not in fake_r2.head_object(Bucket="acdp-test", Key=key)["Metadata"]

    applied = bronze_validate.backfill_v2_bronze_metadata(s3_client=fake_r2, bucket_name="acdp-test", dry_run=False)
    assert applied["backfilled"] == 1
    assert applied["byte_verified_ok"] == 1
    assert applied["errors"] == []

    after_report = bronze_validate.audit_bronze_bucket(s3_client=fake_r2, bucket_name="acdp-test", check_downstream=False)
    assert after_report.overall_status == "PASS"
    assert after_report.provenance_pass_rate == 100.0
    assert after_report.objects[0].computed_sha256 == expected_sha
    assert after_report.objects[0].source_url == "https://vietnamdatathon.com/"

    # Verify verify_idempotent_recrawl passes against the backfilled snapshot
    recrawl = bronze_validate.verify_idempotent_recrawl("https://vietnamdatathon.com/", s3_client=fake_r2, bucket_name="acdp-test")
    assert recrawl["overall_status"] == "PASS"
    assert recrawl["pass1_status"] == "skipped_unchanged"
    assert recrawl["pass2_status"] == "skipped_unchanged"
    assert recrawl["if_none_match_blocked"] is True
    assert recrawl["if_none_match_http_status"] == 412
    assert recrawl["target_object_intact_after_probe"] is True
