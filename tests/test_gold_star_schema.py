"""Unit and integration tests for SPEC-0003 Gold Layer Kimball Star Schema."""

import importlib
import json
from datetime import date
from pathlib import Path

import duckdb

from acdp.schemas import Competition, PrizeTier, TimelineStage

gold = importlib.import_module("acdp.4_analytics_gold")


def test_currency_normalization_edge_cases() -> None:
    """Verify EC-G3 VND, USD, mixed parenthetical, and unquantifiable currency parsing."""
    assert gold.parse_vnd_currency("USD 12,000 in cash plus in-kind gift package", usd_to_vnd_rate=25400) == 304_800_000
    assert gold.parse_vnd_currency("Up to $100,000 + credits", usd_to_vnd_rate=25400) == 2_540_000_000
    assert gold.parse_vnd_currency("10,000 - 20,000 USD", usd_to_vnd_rate=25400) == 508_000_000
    assert gold.parse_vnd_currency("Hơn 2 tỷ VNĐ") == 2_000_000_000
    assert gold.parse_vnd_currency("100 triệu VNĐ") == 100_000_000
    assert gold.parse_vnd_currency("250M+ VND") == 250_000_000
    assert gold.parse_vnd_currency("Up to VND 100M") == 100_000_000
    assert gold.parse_vnd_currency("817,291,840 VND") == 817_291_840
    assert gold.parse_vnd_currency("75.000.000 VNĐ") == 75_000_000
    assert gold.parse_vnd_currency("Hơn 50.000.000++ VND") == 50_000_000
    assert gold.parse_vnd_currency("25,000,000++ VND (bao gồm $1,000 tiền mặt)", usd_to_vnd_rate=25400) == 25_000_000
    assert gold.parse_vnd_currency("Hàng tỷ VNĐ") == 0
    assert gold.parse_vnd_currency("Học bổng 60% chương trình cử nhân tại Đại học Fulbright") == 0
    assert gold.parse_vnd_currency("Học bổng đại học") == 0
    assert gold.parse_vnd_currency(None) == 0


def test_date_resolution_and_academic_terms() -> None:
    """Verify EC-G4 multi-format date parsing and HCM-UTE academic term mapping."""
    assert gold.resolve_date_sk("2026-11-16") == 20261116
    assert gold.map_academic_term(date(2026, 11, 16)) == ("2026-2027", "HK1")

    assert gold.resolve_date_sk("20/01/2027") == 20270120
    assert gold.map_academic_term(date(2027, 1, 20)) == ("2026-2027", "HK2")

    assert gold.resolve_date_sk("17/07/2026") == 20260717
    assert gold.map_academic_term(date(2026, 7, 17)) == ("2025-2026", "Hè")

    assert gold.resolve_date_sk("07/2026") == 20260701
    assert gold.resolve_date_sk("Tháng 11/2026") == 20261101
    assert gold.resolve_date_sk("TBD") == -1
    assert gold.resolve_date_sk("Rolling") == -1
    assert gold.resolve_date_sk(None) == -1


def test_fee_and_team_and_domain_classification() -> None:
    """Verify EC-G5 fee rules, team size buckets, and canonical domain deduplication."""
    assert gold.is_participation_free("Miễn phí") is True
    assert gold.is_participation_free("Free") is True
    assert gold.is_participation_free("0 VND") is True
    assert gold.is_participation_free("50.000 VNĐ") is False
    assert gold.is_participation_free(None) is False

    assert gold.classify_team_profile(1, 1) == "Individual (1)"
    assert gold.classify_team_profile(3, 4) == "Small Team (2-4)"
    assert gold.classify_team_profile(1, 10) == "Large Team (5+)"
    assert gold.classify_team_profile(None, None) == "Unspecified"

    assert gold.classify_competition_domains(["Artificial Intelligence", "Data Science", "NLP"]) == [1]
    assert gold.classify_competition_domains(["AI", "Blockchain", "Hackathon"]) == [1, 2]
    assert gold.classify_competition_domains([]) == [-1]


def test_load_silver_prefers_newest_batch_and_deduplicates(tmp_path: Path) -> None:
    """Verify batch files are never double-counted alongside single-domain JSON files."""
    single_payload = {
        "is_competition": True,
        "competitions": [
            {
                "name": "Stale Single Contest",
                "url": "https://example.org/contest/",
                "summary": "Old summary.",
                "organizers": ["Org A"],
                "category": ["AI"],
            }
        ],
    }
    batch_payload = {
        "results": [
            {
                "competitions": [
                    {
                        "name": "Fresh Batch Contest",
                        "url": "http://example.org/contest?utm_source=fb",
                        "summary": "Updated summary with richer stages and prizes.",
                        "organizers": ["Org A"],
                        "category": ["AI"],
                        "total_prize_pool": "100 triệu VNĐ",
                    }
                ]
            }
        ]
    }
    (tmp_path / "example.org_1000.json").write_text(json.dumps(single_payload), encoding="utf-8")
    (tmp_path / "extractions_2026-11-15_2000.json").write_text(json.dumps(batch_payload), encoding="utf-8")

    comps, source_label = gold.load_silver_competitions_with_source(tmp_path)
    assert source_label == "extractions_2026-11-15_2000.json"
    assert len(comps) == 1
    assert comps[0].name == "Fresh Batch Contest"


def test_star_schema_bridge_allocation_and_edge_cases(tmp_path: Path) -> None:
    """Verify EC-G1 prize preservation via bridge weights and EC-G2 empty nested lists."""
    c1 = Competition(
        name="Multi Domain Hackathon",
        url="https://example.org/multi",
        summary="Cross-disciplinary AI and Blockchain hackathon.",
        organizers=["Tech Uni"],
        partners_and_sponsors=["Partner Cloud"],
        category=["Artificial Intelligence", "Blockchain"],
        mode="hybrid",
        participation_fee="Miễn phí",
        total_prize_pool="100 triệu VNĐ",
        prizes=[PrizeTier(tier="1st", reward="60M", estimated_value_vnd=60_000_000)],
        timeline_stages=[TimelineStage(stage_name="Round 1", start_date="01/10/2026", end_date="15/10/2026")],
        event_start="01/10/2026",
        event_end="15/10/2026",
        registration_status="open",
        team_size_min=2,
        team_size_max=4,
    )
    c2 = Competition(
        name="Bare Announcement Contest",
        url="https://example.org/bare",
        summary="Early announcement without prize tiers or timeline stages.",
        organizers=["Community Club"],
        partners_and_sponsors=[],
        category=["Cybersecurity"],
        mode="online",
        participation_fee=None,
        total_prize_pool="Học bổng toàn phần",
        prizes=[],
        timeline_stages=[],
        registration_deadline="TBD",
        registration_status="upcoming",
    )

    db_path = tmp_path / "test_gold.duckdb"
    gold_dir = tmp_path / "gold"
    exported = gold.build_gold_star_schema(db_path, [c1, c2], source_batch_file="unit_test", gold_dir=gold_dir)
    assert len(exported) == 21
    assert not db_path.with_name("test_gold.duckdb.tmp").exists()

    con = duckdb.connect(str(db_path), read_only=True)
    try:
        kpi = con.execute("SELECT total_competitions, open_competitions, total_prize_pool_vnd, scholarship_competitions FROM mart_kpi_overview").fetchone()
        assert kpi == (2, 1, 100_000_000, 1)

        domain_sum = con.execute("SELECT SUM(allocated_prize_vnd) FROM mart_domain_analytics").fetchone()[0]
        assert abs(float(domain_sum) - float(kpi[2])) <= 1.0

        stage_count = con.execute("SELECT COUNT(*) FROM fact_timeline_stages").fetchone()[0]
        assert stage_count == 1

        sponsor_rows = con.execute(
            "SELECT COUNT(*) FROM bridge_competition_organizer WHERE role_type = 'partner_sponsor'"
        ).fetchone()[0]
        assert sponsor_rows == 1

        unknown_dates = con.execute(
            "SELECT COUNT(*) FROM mart_seasonality_academic WHERE date_known = FALSE"
        ).fetchone()[0]
        assert unknown_dates == 1
    finally:
        con.close()


def test_real_18_competitions_star_schema_integrity(tmp_path: Path) -> None:
    """Verify full Kimball Star Schema build against real repository Silver extractions."""
    extractions_dir = Path("data/extractions")
    competitions, source_label = gold.load_silver_competitions_with_source(extractions_dir)
    assert len(competitions) == 18
    assert all("vnquantum" not in (c.url or "").lower() for c in competitions)

    db_path = tmp_path / "real_gold.duckdb"
    gold.build_gold_star_schema(db_path, competitions, source_batch_file=source_label, gold_dir=None)

    con = duckdb.connect(str(db_path), read_only=True)
    try:
        kpi = con.execute(
            "SELECT total_competitions, total_prize_pool_vnd, unique_domains, unique_organizers FROM mart_kpi_overview"
        ).fetchone()
        assert kpi[0] == 18
        assert kpi[1] > 0
        assert kpi[2] == 5
        assert kpi[3] > 20

        unclassified = con.execute(
            "SELECT COUNT(*) FROM bridge_competition_domain WHERE domain_sk = -1"
        ).fetchone()[0]
        assert unclassified == 0

        domain_sum = con.execute("SELECT SUM(allocated_prize_vnd) FROM mart_domain_analytics").fetchone()[0]
        assert abs(float(domain_sum) - float(kpi[1])) <= 1.0

        # Ensure backward-compatible Gold views query cleanly
        for view_name in (
            "gold_competitions",
            "gold_prizes",
            "gold_category_summary",
            "gold_mode_distribution",
            "gold_seasonality",
            "gold_top_prizes",
        ):
            cnt = con.execute(f"SELECT COUNT(*) FROM {view_name}").fetchone()[0]
            assert cnt > 0
    finally:
        con.close()
