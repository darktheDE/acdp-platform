"""Unit tests for Silver Layer Competition Schema & Data Contracts."""

from datetime import datetime, timezone
import json
import pytest

from acdp.lakehouse.schema import PrizeItem, SilverCompetitionRecord


def test_silver_competition_record_creation():
    """Verify that SilverCompetitionRecord validates and serializes correctly."""
    record = SilverCompetitionRecord(
        canonical_name="Code Tour 2026",
        slug="code-tour-2026",
        aliases=["CodeTour 2026", "Code Tour VNG"],
        source_urls=["https://codetour.org", "https://facebook.com/CodeTourVietnam"],
        primary_source="https://codetour.org",
        registration_link="https://codetour.org/register",
        organizer_name="VNG Corporation",
        organizer_type="enterprise",
        co_organizers=["VNG Tech Club"],
        edition_year=2026,
        registration_start_date="2026-09-01",
        registration_deadline="2026-09-25",
        event_start_date="2026-09-26",
        event_end_date="2026-10-31",
        season_quarter="Q3",
        domain_categories=["Algorithmic Coding", "Software Engineering"],
        technical_tags=["C++", "Python", "Data Structures", "Algorithms"],
        competition_level="national",
        target_audience="Sinh viên các trường đại học, cao đẳng từ 15-24 tuổi trên toàn quốc",
        min_team_size=1,
        max_team_size=1,
        is_individual_allowed=True,
        total_prize_vnd=100_000_000,
        first_prize_vnd=30_000_000,
        prizes=[
            PrizeItem(rank_name="Quán quân", amount_vnd=30_000_000, quantity=1, description="Cúp vàng, tiền mặt và học bổng VNG"),
            PrizeItem(rank_name="Á quân", amount_vnd=15_000_000, quantity=2, description="Kỷ niệm chương và tiền mặt"),
        ],
        summary_description="Cuộc thi lập trình thi đấu quy mô toàn quốc do VNG tổ chức, thử thách tư duy thuật toán.",
        submission_format="Hệ thống chấm trực tuyến OJ (codetour26.oj.io.vn)",
    )

    assert record.canonical_name == "Code Tour 2026"
    assert record.registration_link == "https://codetour.org/register"
    assert record.total_prize_vnd == 100_000_000
    assert len(record.prizes) == 2
    assert record.is_individual_allowed is True

    # Test deterministic fingerprint
    fp = record.generate_fingerprint()
    assert isinstance(fp, str)
    assert len(fp) == 64

    # Test serialization round-trip
    json_dict = record.to_json_dict()
    assert json_dict["slug"] == "code-tour-2026"
    assert json_dict["edition_year"] == 2026
    assert json_dict["prizes"][0]["rank_name"] == "Quán quân"


def test_silver_fingerprint_consistency():
    """Verify that different casings and spaces yield the same fingerprint for deduplication."""
    r1 = SilverCompetitionRecord(
        canonical_name="Code Tour 2026",
        slug="code-tour-2026",
        primary_source="https://codetour.org",
        organizer_name="VNG Corporation",
        edition_year=2026,
    )
    r2 = SilverCompetitionRecord(
        canonical_name="code tour 2026",
        slug="code-tour-2026",
        primary_source="https://facebook.com/codetour",
        organizer_name="vng corporation",
        edition_year=2026,
    )

    assert r1.generate_fingerprint() == r2.generate_fingerprint()
