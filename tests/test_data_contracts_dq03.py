"""Automated unit & integration tests for TASK-DQ-03 (Data Contracts & WAP Quality Gates)."""

from __future__ import annotations

import io
import json
from pathlib import Path
from unittest.mock import MagicMock

import duckdb
import pyarrow as pa
import pytest

from acdp.v2 import data_contracts as dc
from acdp.v2 import gold_star_schema as gold
from acdp.v2 import silver_transform
from acdp.v2.schemas import Competition, CompetitionExtractionResult, PrizeTier, TimelineStage

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures" / "dq03"


def _make_valid_comp(name: str = "HCMUTE AI Hackathon 2026", url: str = "https://hcmute-ai.edu.vn") -> Competition:
    return Competition(
        name=name,
        url=url,
        summary="Cuộc thi Trí tuệ Nhân tạo và Khoa học Dữ liệu dành cho sinh viên đại học HCM-UTE.",
        organizers=["FIT HCM-UTE"],
        category=["Artificial Intelligence", "Data Science"],
        target_audience="Sinh viên đại học",
        mode="hybrid",
        eligibility_level="undergraduate",
        registration_status="open",
        registration_start="2026-09-01",
        registration_deadline="2026-10-15",
        event_start="2026-10-20",
        event_end="2026-11-20",
        team_size_min=1,
        team_size_max=4,
        total_prize_pool="50.000.000 VND",
        prizes=[PrizeTier(tier="Quán quân", reward="30.000.000 VND", estimated_value_vnd=30_000_000)],
        timeline_stages=[TimelineStage(stage_name="Vòng 1", start_date="2026-10-20", end_date="2026-11-01")],
        source_url=url,
        bronze_key="bronze/hcmute-ai.edu.vn/year=2026/month=11/day=23/1795417000.html",
    )


def test_odcs_v32_contract_yaml_valid_and_synced() -> None:
    """Verify ODCS v3.2.0 YAML contract loads cleanly and defines all 19 rules."""
    sync_info = dc.validate_odcs_contract_sync()
    assert sync_info["status"] == "ok"
    assert sync_info["apiVersion"] == "v3.2.0"
    assert set(sync_info["tables"]) == {"competitions", "prizes", "timeline_stages"}
    assert sync_info["rules_count"] == 19
    assert set(dc.EXPECTED_RULE_IDS).issubset(set(sync_info["rule_ids"]))


def test_valid_silver_fixture_passes_all_critical_rules_with_zero_false_positives() -> None:
    """Verify clean 2025-2027 competitions (even with optional None fields) pass with 0 CRITICAL failures."""
    report = dc.audit_local_source(FIXTURES_DIR / "valid_silver_batch.json", fail_fast=True)
    assert report.critical_failed == 0
    assert report.circuit_breaker_tripped is False
    assert report.overall_status in {"PASS", "PASS_WITH_WARNINGS"}
    assert report.record_counts["competitions"] == 5
    for rule in report.rules:
        if rule.severity == "CRITICAL":
            assert rule.status == "PASS", f"Unexpected CRITICAL failure on {rule.rule_id}: {rule.sample_violations}"


def test_invalid_silver_fixture_trips_all_expected_critical_rules_c01_to_c11() -> None:
    """Verify deliberate violation fixture fails C01..C08, C10, C11, and empty batch fails C09."""
    report = dc.audit_local_source(FIXTURES_DIR / "invalid_silver_batch.json", fail_fast=False)
    assert report.circuit_breaker_tripped is True
    assert report.overall_status == "FAIL"
    assert report.critical_failed == 10

    failed_ids = {r.rule_id for r in report.rules if r.status == "FAIL"}
    expected = {f"C{i:02d}" for i in range(1, 12) if i != 9}
    assert expected == failed_ids

    # Verify C09 catches empty batch volume
    empty_comp = pa.Table.from_pylist([], schema=gold.SILVER_COMPETITIONS_ARROW_SCHEMA)
    empty_prize = pa.Table.from_pylist([], schema=gold.SILVER_PRIZES_ARROW_SCHEMA)
    empty_stage = pa.Table.from_pylist([], schema=gold.SILVER_TIMELINE_STAGES_ARROW_SCHEMA)
    empty_report = dc.run_silver_quality_gate(
        [],
        empty_comp,
        empty_prize,
        empty_stage,
        source_label="empty_batch",
        min_records=1,
        fail_fast=False,
    )
    assert empty_report.circuit_breaker_tripped is True
    assert "C09" in {r.rule_id for r in empty_report.rules if r.status == "FAIL"}


def test_bronze_to_silver_handoff_gate_c12_pass_and_fail() -> None:
    """Verify C12 Bronze-to-Silver handoff catches invalid key, non-HTTP url, short md, and 404 stub."""
    ok_res = dc.validate_bronze_to_silver_handoff(
        bronze_key="bronze/codetour.org/year=2026/month=11/day=23/1795416946.html",
        source_url="https://codetour.org/",
        clean_md="Cuộc thi lập trình thuật toán dành cho sinh viên CNTT. " * 10,
    )
    assert ok_res.status == "PASS"

    bad_res = dc.validate_bronze_to_silver_handoff(
        bronze_key="bad/prefix/file.txt",
        source_url="ftp://codetour.org",
        clean_md="404 Not Found",
    )
    assert bad_res.status == "FAIL"
    assert bad_res.failed_count >= 3


def test_wap_circuit_breaker_blocks_silver_parquet_publish_on_violation(tmp_path: Path) -> None:
    """Verify export_silver_parquet raises DataContractViolationError and writes 0 Parquet files on violation."""
    dirty_comp = Competition(
        name="MARKETING ARENA 2026",
        url="https://ybox.vn/su-kien/marketing-arena-2026",
        summary="Cuộc thi Marketing và truyền thông thương hiệu toàn quốc.",
        category=["Marketing"],
        mode="offline",
        registration_status="open",
        event_start="2023-05-01",
        event_end="2023-05-10",
    )
    with pytest.raises(dc.DataContractViolationError) as exc_info:
        gold.export_silver_parquet([dirty_comp], output_dir=tmp_path)

    report = exc_info.value.report
    assert report.circuit_breaker_tripped is True
    failed_ids = {r.rule_id for r in report.rules if r.status == "FAIL"}
    assert {"C02", "C05", "C08"}.issubset(failed_ids)
    assert list(tmp_path.glob("*.parquet")) == []


def test_wap_circuit_breaker_blocks_gold_star_schema_publish_on_violation(tmp_path: Path) -> None:
    """Verify build_gold_star_schema stops before creating Gold DuckDB or Parquet on dirty Silver input."""
    dirty_comp = Competition(
        name="No Official Website Contest 2026",
        url=None,
        summary="Cuộc thi AI sinh viên nhưng không có website chính thức.",
        category=["Artificial Intelligence"],
    )
    db_path = tmp_path / "gold.duckdb"
    gold_dir = tmp_path / "gold"
    with pytest.raises(dc.DataContractViolationError) as exc_info:
        gold.build_gold_star_schema(db_path, [dirty_comp], source_batch_file="dirty_test", gold_dir=gold_dir)

    assert "C02" in {r.rule_id for r in exc_info.value.report.rules if r.status == "FAIL"}
    assert not db_path.exists()
    assert not gold_dir.exists()


def test_gold_pre_publish_gate_c13_c14_catches_row_mismatch_and_bridge_drift() -> None:
    """Verify Tier C Gold pre-publish SQL gate detects dim/fact mismatch (C13) and bridge weight drift (C14)."""
    con = duckdb.connect(":memory:")
    try:
        con.execute("CREATE TABLE dim_competition (competition_sk BIGINT, canonical_url VARCHAR, name VARCHAR)")
        con.execute("CREATE TABLE fact_competitions (competition_sk BIGINT, total_prize_vnd BIGINT)")
        con.execute("CREATE TABLE mart_competition_explorer (competition_sk BIGINT)")
        con.execute("CREATE TABLE mart_kpi_overview (total_prize_pool_vnd BIGINT)")
        con.execute("CREATE TABLE mart_domain_analytics (allocated_prize_vnd DOUBLE)")
        con.execute("CREATE TABLE bridge_competition_domain (competition_sk BIGINT, domain_sk INT, allocation_weight DOUBLE)")

        con.execute("INSERT INTO dim_competition VALUES (1, 'https://a.edu.vn', 'Contest A')")
        con.execute("INSERT INTO fact_competitions VALUES (1, 100000000)")
        con.execute("INSERT INTO mart_competition_explorer VALUES (1)")
        con.execute("INSERT INTO mart_kpi_overview VALUES (100000000)")
        con.execute("INSERT INTO mart_domain_analytics VALUES (100000000.0)")
        con.execute("INSERT INTO bridge_competition_domain VALUES (1, 1, 1.0)")

        ok_rules = dc.validate_silver_to_gold_gate(con, expected_silver_count=1)
        assert all(r.status == "PASS" for r in ok_rules)

        # Introduce bridge drift and row parity mismatch
        con.execute("UPDATE bridge_competition_domain SET allocation_weight = 0.75 WHERE competition_sk = 1")
        con.execute("UPDATE mart_domain_analytics SET allocated_prize_vnd = 75000000.0")
        bad_rules = dc.validate_silver_to_gold_gate(con, expected_silver_count=2)
        by_id = {r.rule_id: r for r in bad_rules}
        assert by_id["C13"].status == "FAIL"
        assert by_id["C14"].status == "FAIL"
    finally:
        con.close()


def test_silver_parquet_dir_audit_pass_and_fail_via_duckdb(tmp_path: Path) -> None:
    """Verify audit_local_source validates exported Parquet directories via DuckDB SQL."""
    comp = _make_valid_comp()
    gold.export_silver_parquet([comp], output_dir=tmp_path)
    pass_report = dc.audit_local_source(tmp_path, fail_fast=True)
    assert pass_report.critical_failed == 0
    assert pass_report.record_counts["competitions"] == 1

    # Bypass gate and write a corrupted Parquet directory to verify DuckDB SQL directory audit catches it
    bad_dir = tmp_path / "corrupt_parquet"
    dirty = Competition(
        name="Expired Contest 2022",
        url="https://ybox.vn/cuoc-thi/expired-2022",
        summary="Cuộc thi AI hết hạn từ năm 2022.",
        category=["Artificial Intelligence"],
        event_start="2022-05-01",
        event_end="2022-06-01",
    )
    gold.export_silver_parquet([dirty], output_dir=bad_dir, enforce_contract=False)
    fail_report = dc.audit_local_source(bad_dir, fail_fast=False)
    assert fail_report.circuit_breaker_tripped is True
    failed_ids = {r.rule_id for r in fail_report.rules if r.status == "FAIL"}
    assert {"C02", "C05"}.issubset(failed_ids)


def test_warning_rules_w01_to_w05_never_trip_circuit_breaker(tmp_path: Path) -> None:
    """Verify optional/soft-SLA fields emit WARNING without tripping the circuit breaker."""
    minimal_comp = Competition(
        name="Minimal Valid AI Contest 2026",
        url="https://minimal-ai.edu.vn",
        summary="Cuộc thi Trí tuệ Nhân tạo hợp lệ tối giản dùng để kiểm tra ngưỡng WARNING.",
        category=["Artificial Intelligence"],
        mode="unknown",
        eligibility_level="unknown",
        registration_deadline=None,
        total_prize_pool=None,
        prizes=[],
        bronze_key=None,
        source_url=None,
    )
    exported = gold.export_silver_parquet([minimal_comp], output_dir=tmp_path)
    assert len(exported) == 3

    report = dc.audit_local_source(tmp_path, fail_fast=True)
    assert report.circuit_breaker_tripped is False
    assert report.overall_status == "PASS_WITH_WARNINGS"
    warn_ids = {r.rule_id for r in report.rules if r.status == "WARN"}
    assert {"W01", "W02", "W03", "W04", "W05"}.issubset(warn_ids)


def test_cli_exit_codes_and_json_report_export(tmp_path: Path) -> None:
    """Verify CLI returns 0 on valid fixture, 1 on invalid fixture, and writes JSON rule report."""
    valid_report_path = tmp_path / "valid_report.json"
    invalid_report_path = tmp_path / "invalid_report.json"

    rc_odcs = dc.main(["--validate-odcs"])
    assert rc_odcs == 0

    rc_valid = dc.main(
        [
            "--audit-local",
            str(FIXTURES_DIR / "valid_silver_batch.json"),
            "--save-report",
            str(valid_report_path),
        ]
    )
    assert rc_valid == 0
    assert json.loads(valid_report_path.read_text(encoding="utf-8"))["circuit_breaker_tripped"] is False

    rc_invalid = dc.main(
        [
            "--audit-local",
            str(FIXTURES_DIR / "invalid_silver_batch.json"),
            "--save-report",
            str(invalid_report_path),
        ]
    )
    assert rc_invalid == 1
    inv_payload = json.loads(invalid_report_path.read_text(encoding="utf-8"))
    assert inv_payload["circuit_breaker_tripped"] is True
    assert inv_payload["critical_failed"] == 10


class _InMemoryR2Stub:
    def __init__(self) -> None:
        self.objects: dict[str, dict[str, object]] = {}

    def put_object(self, Bucket: str, Key: str, Body: bytes, **kwargs: object) -> None:
        self.objects[Key] = {"Bucket": Bucket, "Key": Key, "Body": Body, **kwargs}

    def get_object(self, Bucket: str, Key: str) -> dict[str, object]:
        obj = self.objects[Key]
        return {"Body": io.BytesIO(obj["Body"]), "Metadata": {}}  # type: ignore[arg-type]

    def get_paginator(self, operation_name: str):
        parent = self

        class _Paginator:
            def paginate(self, Bucket: str, Prefix: str = ""):
                return [
                    {
                        "Contents": [
                            {"Key": k, "Size": len(v["Body"])}  # type: ignore[arg-type]
                            for k, v in sorted(parent.objects.items())
                            if k.startswith(Prefix)
                        ]
                    }
                ]

        return _Paginator()


def test_silver_transform_strict_gate_blocks_dirty_record(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify silver_transform --strict-gate trips before uploading bad extractions to R2."""
    fake_s3 = _InMemoryR2Stub()
    html_doc = (
        '<!-- ACDP_PAGE_BOUNDARY url="https://bad-ai-contest.edu.vn/" -->\n'
        "<html><body><h1>Bad AI Contest</h1>"
        "<p>Cuộc thi Trí tuệ Nhân tạo dành cho sinh viên đại học năm 2026 với nhiều vòng thi hấp dẫn. "
        "Thông tin giải thưởng và đăng ký tham gia được cập nhật công khai trên cổng thông tin chính thức.</p>"
        "</body></html>"
    )
    fake_s3.put_object(
        "acdp-test",
        "bronze/bad-ai-contest.edu.vn/year=2026/month=11/day=23/1795417999.html",
        html_doc.encode("utf-8"),
    )
    monkeypatch.setattr(silver_transform.settings, "bucket_name", "acdp-test")
    monkeypatch.setattr(type(silver_transform.settings), "create_r2_client", lambda self: fake_s3)
    monkeypatch.setattr(silver_transform, "_create_instructor_client", lambda: MagicMock())

    def _dirty_extract(client, signals, clean_md):
        return CompetitionExtractionResult(
            is_competition=True,
            competitions=[
                Competition(
                    name="Noisy Subdomain Contest 2026",
                    url="https://tracuu.citd.edu.vn",
                    summary="Cuộc thi Trí tuệ Nhân tạo sinh viên bị dính subdomain tra cứu.",
                    category=["Artificial Intelligence"],
                    target_audience="Sinh viên đại học",
                )
            ],
        )

    monkeypatch.setattr(silver_transform, "extract_competition_hybrid", _dirty_extract)

    with pytest.raises(dc.DataContractViolationError) as exc_info:
        silver_transform.run_silver_transform(run_llm=True, target_date="2026-11-23", strict_gate=True)

    assert "C03" in {r.rule_id for r in exc_info.value.report.rules if r.status == "FAIL"}
    assert not any(k.startswith("silver/extractions/") for k in fake_s3.objects)


def test_benchmark_runner_outputs_valid_timings() -> None:
    """Verify programmatic latency benchmark helper returns non-negative timings."""
    bench = dc.run_cli_benchmark(sizes=(5, 10))
    assert len(bench["measurements"]) == 2
    for row in bench["measurements"]:
        assert row["tier_a_pydantic_ms"] >= 0.0
        assert row["tier_b_duckdb_ms"] >= 0.0
