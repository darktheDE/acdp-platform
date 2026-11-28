"""Automated unit & integration tests for TASK-DQ-04 (Entity Resolution & Multi-Season Dedup)."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import duckdb

from acdp.v2 import data_contracts as dc
from acdp.v2 import entity_resolution as er
from acdp.v2 import gold_star_schema as gold
from acdp.v2 import silver_transform
from acdp.v2.schemas import (
    Competition,
    build_natural_key,
    canonicalize_organizers,
    compute_competition_key,
    extract_edition_number,
    extract_season_month,
    extract_season_year,
    normalize_canonical_url,
    normalize_competition_name,
)

FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "dq04" / "multi_source_and_season_batch.json"


def test_rfc3986_url_normalization_and_authority_classification() -> None:
    """Verify URL canonicalization removes www, default ports, tracking params, and root boilerplate."""
    u1 = normalize_canonical_url("HTTP://www.CodeTour.org:80/trang-chu/?utm_source=fb&fbclid=abc#top")
    u2 = normalize_canonical_url("https://codetour.org/vi")
    u3 = normalize_canonical_url("https://codetour.org/")
    assert u1 == u2 == u3 == "https://codetour.org"

    assert er.classify_url_authority("https://codetour.org") == er.SourceAuthority.OFFICIAL
    assert er.classify_url_authority("https://ybox.vn/cuoc-thi/code-tour-2026") == er.SourceAuthority.AGGREGATOR_OR_MEDIA
    assert er.classify_url_authority("https://tracuu.citd.edu.vn/") == er.SourceAuthority.NOISY_OR_INVALID
    assert (
        er.classify_url_authority("https://www.ntu.edu.sg/business/admissions/graduate-studies/msc-programmes")
        == er.SourceAuthority.NOISY_OR_INVALID
    )
    assert er.classify_url_authority("https://forms.gle/abc123") == er.SourceAuthority.NOISY_OR_INVALID


def test_vietnamese_name_and_organizer_canonicalization() -> None:
    """Verify Vietnamese folding, framing prefix stripping, subtitle splitting, and organizer aliases."""
    _, core1 = normalize_competition_name("Datathon 2026: The Gridbreaker")
    _, core2 = normalize_competition_name("Cuộc Thi Khoa Học Dữ Liệu DATATHON 2026")
    assert core1 == core2 == "datathon"

    _, rmit1 = normalize_competition_name("RMIT Hackathon 2026")
    _, rmit2 = normalize_competition_name("RMIT Hack-A-Venture 2026")
    assert rmit1 == "rmit-hackathon"
    assert rmit2 == "rmit-hack-a-venture"

    orgs1 = canonicalize_organizers(["VinTelligence - VinUni Data Science & AI Club", "Trường Đại học VinUni"])
    orgs2 = canonicalize_organizers(["VinUniversity"])
    assert orgs1 == ["vinuni"]
    assert orgs2 == ["vinuni"]


def test_season_year_month_edition_and_natural_key_extraction() -> None:
    """Verify priority cascade for season_year (including cross-year contests), month, and edition."""
    # Cross-year contest: DataStorm 2025 held in Jan 2026 -> season_year must be 2025 from title
    assert (
        extract_season_year(
            "Vietnam Datathon - DataStorm 2025",
            "https://vietnamdatathon.com/",
            event_start_date=date(2026, 1, 17),
        )
        == 2025
    )
    # Cross-year contest: QVIC 2027 reg in Dec 2026 -> season_year must be 2027 from title
    assert (
        extract_season_year(
            "Qualcomm Vietnam Innovation Challenge 2027",
            "https://qvic.vn/",
            registration_deadline_date=date(2026, 12, 1),
        )
        == 2027
    )
    # Monthly recurring DataDNA
    assert extract_season_month("October 2026 DataDNA – Retail Challenge") == 10
    assert extract_season_month("November 2026 DataDNA – Health Challenge") == 11
    # Edition extraction
    assert extract_edition_number("Data for Life mùa 3 - 2025") == 3
    assert extract_edition_number("Data for Life mùa 4 - 2026") == 4

    nk_2025, _ = build_natural_key("Code Tour 2025", ["VNG"], "https://codetour.org", 2025)
    nk_2026, _ = build_natural_key("Code Tour 2026", ["VNG Corporation"], "https://www.codetour.org", 2026)
    assert nk_2025 == "code-tour|vng|2025|codetour.org"
    assert nk_2026 == "code-tour|vng|2026|codetour.org"
    assert compute_competition_key("https://codetour.org", 2025) != compute_competition_key("https://codetour.org", 2026)


def test_multi_source_and_multi_season_fixture_100_percent_accuracy() -> None:
    """Verify 16 raw records resolve to exactly 12 canonical entities with 0 false merges and 100% season split."""
    payload = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    comps = er._extract_competitions_from_json_payload(payload)
    assert len(comps) == 16

    resolved, report = er.resolve_competition_entities(comps, source_label="dq04_fixture")
    assert report.input_count == 16
    assert report.output_count == 12
    assert report.merged_duplicates_count == 4
    assert len(resolved) == 12

    by_name = {c.name: c for c in resolved}
    # 1. Code Tour 2026 (3 sources -> 1) fused official URL, contact, PDF rules, and skills
    ct26 = by_name["Code Tour 2026"]
    assert normalize_canonical_url(ct26.url) == "https://codetour.org"
    assert ct26.organizer_contact == "codetour@vng.com.vn"
    assert ct26.official_rules_url == "https://codetour.org/the-le-2026.pdf"
    assert {"Algorithms", "C++", "Python"}.issubset(set(ct26.required_skills))
    assert len(ct26.merged_source_urls) >= 3
    assert "https://codetour.org/" in ct26.merged_source_urls
    assert any("daihoc.fpt.edu.vn" in u for u in ct26.merged_source_urls)

    # 2. VinUni Datathon 2026 (official + polluted ybox/ntu.edu.sg -> 1) survived with datathon.site
    vinuni = by_name["Datathon 2026: The Gridbreaker"]
    assert normalize_canonical_url(vinuni.url) == "https://datathon.site"
    assert vinuni.organizer_contact == "vintelligence@vinuni.edu.vn"
    assert any("ybox.vn" in u for u in vinuni.merged_source_urls)
    assert "Cuộc Thi Khoa Học Dữ Liệu DATATHON 2026" not in by_name

    # 3. AI Challenge TP.HCM 2026 (2 sources -> 1) coalesced submission_platform
    aichal = [c for c in resolved if "aichallenge.hochiminhcity.gov.vn" in (c.url or "")]
    assert len(aichal) == 1
    assert aichal[0].submission_platform == "AI Challenge Submission Portal"

    # 4. Multi-season separation on SAME domain (2025 vs 2026)
    ct25 = by_name["Code Tour 2025"]
    assert ct25.season_year == 2025 and ct26.season_year == 2026
    assert ct25.competition_key != ct26.competition_key
    assert "Zalo AI Challenge 2025" in by_name and "Zalo AI Challenge 2026" in by_name
    assert by_name["Zalo AI Challenge 2025"].competition_key != by_name["Zalo AI Challenge 2026"].competition_key
    assert "Data for Life mùa 3 - 2025" in by_name and "Data for Life mùa 4 - 2026" in by_name
    assert by_name["Data for Life mùa 3 - 2025"].competition_key != by_name["Data for Life mùa 4 - 2026"].competition_key

    # 5. Same university, same year distinct contests preserved
    assert "RMIT Hackathon 2026" in by_name
    assert "RMIT Hack-A-Venture 2026" in by_name

    # 6. Monthly recurring DataDNA preserved
    assert "October 2026 DataDNA – Retail Analytics Challenge" in by_name
    assert "November 2026 DataDNA – Health System Performance Analytics Challenge" in by_name

    # 7. All 12 competition_keys are unique 64-char SHA-256 hex
    keys = [c.competition_key for c in resolved]
    assert len(keys) == len(set(keys)) == 12
    assert all(k and len(k) == 64 for k in keys)


def test_transitive_chaining_across_seasons_is_blocked() -> None:
    """Verify A(2025) - B(unknown year) - C(2026) never transitively collapses 2025 with 2026."""
    c_2025 = Competition(
        name="Code Tour 2025",
        url="https://codetour.org",
        summary="Cuộc thi lập trình Code Tour 2025.",
        organizers=["VNG"],
    )
    c_unknown = Competition(
        name="Code Tour",
        url="https://codetour.org",
        source_url="https://ybox.vn/cuoc-thi/code-tour",
        summary="Cuộc thi lập trình Code Tour.",
        organizers=["VNG"],
    )
    c_2026 = Competition(
        name="Code Tour 2026",
        url="https://codetour.org",
        summary="Cuộc thi lập trình Code Tour 2026.",
        organizers=["VNG"],
    )
    resolved, report = er.resolve_competition_entities([c_2025, c_unknown, c_2026], source_label="transitive_test")
    years = sorted(c.season_year for c in resolved if c.season_year is not None)
    assert years == [2025, 2026]
    assert report.output_count == 2


def test_drop_without_official_website_guard() -> None:
    """Verify clusters lacking any official/institutional URL are quarantined when drop_without_official_site=True."""
    only_aggregator = Competition(
        name="Unverified Student AI Contest 2026",
        url="https://ybox.vn/cuoc-thi/unverified-2026",
        source_url="https://ybox.vn/cuoc-thi/unverified-2026",
        summary="Cuộc thi AI nhưng không có website chính thức.",
        organizers=["CLB Sinh viên"],
    )
    resolved, report = er.resolve_competition_entities(
        [only_aggregator],
        source_label="no_official_test",
        drop_without_official_site=True,
    )
    assert len(resolved) == 0
    assert report.dropped_no_official_count == 1


def test_silver_transform_season_aware_media_partner_dedup() -> None:
    """Verify silver_transform merges same-season media posts but preserves 2025 media post when 2026 official exists."""
    known_seasons = {("codetour.org", 2026)}

    sig_2026 = silver_transform.DeterministicSignals(
        source_domain="ybox.vn",
        source_url="https://ybox.vn/cuoc-thi/code-tour-2026",
        is_html=True,
        is_media_or_aggregator=True,
        has_official_website=True,
        canonical_official_url="https://codetour.org/",
        og_title="Code Tour 2026",
        detected_years=[2026],
    )
    dec_2026 = silver_transform.evaluate_pre_llm_scope(
        sig_2026,
        "Code Tour 2026 cuộc thi lập trình thuật toán dành cho sinh viên CNTT. " * 6,
        known_official_season_keys=known_seasons,
    )
    assert dec_2026.accepted is False
    assert dec_2026.reason == "media_partner_merged_to_official"

    sig_2025 = silver_transform.DeterministicSignals(
        source_domain="ybox.vn",
        source_url="https://ybox.vn/cuoc-thi/code-tour-2025",
        is_html=True,
        is_media_or_aggregator=True,
        has_official_website=True,
        canonical_official_url="https://codetour.org/",
        og_title="Code Tour 2025",
        detected_years=[2025],
    )
    dec_2025 = silver_transform.evaluate_pre_llm_scope(
        sig_2025,
        "Code Tour 2025 cuộc thi lập trình thuật toán dành cho sinh viên CNTT. " * 6,
        known_official_season_keys=known_seasons,
    )
    assert dec_2025.accepted is True


def test_duckdb_native_similarity_audit_and_end_to_end_silver_gold(tmp_path: Path) -> None:
    """Verify DuckDB jaro_winkler_similarity audit and full ER -> Silver Parquet -> ODCS Gate -> Gold Star Schema."""
    payload = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    raw_comps = er._extract_competitions_from_json_payload(payload)

    duck_hits = er.audit_near_duplicates_duckdb(raw_comps, threshold=0.80)
    assert len(duck_hits) >= 3
    assert any(
        {hit["left_name"], hit["right_name"]}
        == {"Datathon 2026: The Gridbreaker", "Cuộc Thi Khoa Học Dữ Liệu DATATHON 2026"}
        for hit in duck_hits
    )

    # Run _deduplicate_competition_payloads directly like Silver/Gold loader
    deduped = gold._deduplicate_competition_payloads([("fixture.json", payload)])
    assert len(deduped) == 12

    silver_dir = tmp_path / "silver"
    exported_silver = gold.export_silver_parquet(deduped, output_dir=silver_dir, enforce_contract=True)
    assert len(exported_silver) == 3

    gate_report = dc.audit_local_source(silver_dir, fail_fast=True)
    assert gate_report.critical_failed == 0
    assert gate_report.record_counts["competitions"] == 12

    db_path = tmp_path / "gold.duckdb"
    gold_dir = tmp_path / "gold"
    exported_gold = gold.build_gold_star_schema(
        db_path=db_path,
        competitions=deduped,
        source_batch_file="dq04_fixture",
        gold_dir=gold_dir,
        enforce_contract=True,
    )
    assert len(exported_gold) == 15

    con = duckdb.connect(str(db_path), read_only=True)
    try:
        dim_cnt = con.execute("SELECT COUNT(*) FROM dim_competition").fetchone()[0]
        assert dim_cnt == 12
        ct_seasons = con.execute(
            "SELECT COUNT(*) FROM dim_competition WHERE name LIKE 'Code Tour%'"
        ).fetchone()[0]
        assert ct_seasons == 2
    finally:
        con.close()


def test_cli_audit_local_and_benchmark(tmp_path: Path) -> None:
    """Verify CLI --audit-local and --benchmark return exit code 0 and valid JSON outputs."""
    out_local = tmp_path / "local_er.json"
    rc1 = er.main(["--audit-local", str(FIXTURE_PATH), "--out", str(out_local)])
    assert rc1 == 0
    local_json = json.loads(out_local.read_text(encoding="utf-8"))
    assert local_json["report"]["input_count"] == 16
    assert local_json["report"]["output_count"] == 12

    out_bench = tmp_path / "bench_er.json"
    rc2 = er.main(["--benchmark", "--out", str(out_bench)])
    assert rc2 == 0
    bench_json = json.loads(out_bench.read_text(encoding="utf-8"))
    assert len(bench_json["measurements"]) == 4
