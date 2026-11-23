"""Unit tests for ACDP Competition Pydantic v2 Schemas and Data Validation.

Tests:
1. clean_placeholder utility (converts LLM noise strings like 'N/A', 'none', 'unknown' to None).
2. PrizeTier model validation, currency estimation, and scholarship flag.
3. TimelineStage model validation and date range handling.
4. Competition model creation, tag list normalization, and field validators.
5. CompetitionExtractionResult top-level container (Instructor extraction parsing, edge cases).
6. JSON serialization and deserialization round-trip integrity.
"""


from acdp.schemas import (
    Competition,
    CompetitionExtractionResult,
    PrizeTier,
    TimelineStage,
    clean_placeholder,
)


def test_clean_placeholder() -> None:
    """Verify that placeholder strings from LLM outputs are converted to None."""
    assert clean_placeholder("N/A") is None
    assert clean_placeholder("none") is None
    assert clean_placeholder("null") is None
    assert clean_placeholder("Not Specified") is None
    assert clean_placeholder("unknown") is None
    assert clean_placeholder("tbd") is None
    assert clean_placeholder("no prize mentioned") is None
    assert clean_placeholder("No dates mentioned") is None

    # Valid values should be stripped and preserved
    assert clean_placeholder("  VNG Corporation  ") == "VNG Corporation"
    assert clean_placeholder("15.000.000 VND") == "15.000.000 VND"
    assert clean_placeholder(12345) == 12345
    assert clean_placeholder(None) is None


def test_prize_tier_validation() -> None:
    """Verify PrizeTier correctly validates monetary rewards and scholarship attributes."""
    prize = PrizeTier(
        tier="Quán quân",
        reward="30.000.000 VND tiền mặt + Học bổng VNG",
        estimated_value_vnd=30_000_000.0,
        is_scholarship=True,
    )
    assert prize.tier == "Quán quân"
    assert prize.estimated_value_vnd == 30_000_000.0
    assert prize.is_scholarship is True

    # Test default values and placeholder cleaning
    empty_prize = PrizeTier(tier="N/A", reward="Not specified")
    assert empty_prize.tier == ""
    assert empty_prize.reward == ""
    assert empty_prize.estimated_value_vnd is None
    assert empty_prize.is_scholarship is False


def test_timeline_stage_validation() -> None:
    """Verify TimelineStage parses round names and timeline dates."""
    stage = TimelineStage(
        stage_name="Vòng 1: Đăng ký & Nộp hồ sơ",
        start_date="01/09/2026",
        end_date="25/09/2026",
        description="Thí sinh hoàn thiện form đăng ký trực tuyến theo đội thi.",
    )
    assert stage.stage_name == "Vòng 1: Đăng ký & Nộp hồ sơ"
    assert stage.start_date == "01/09/2026"
    assert stage.end_date == "25/09/2026"


def test_competition_creation_and_normalization() -> None:
    """Verify Competition model validates correctly with real-world competition attributes."""
    comp = Competition(
        name="Code Tour 2026",
        tagline="Đấu trường lập trình thuật toán toàn quốc",
        url="https://codetour.org",
        summary="Cuộc thi lập trình thi đấu thường niên thử thách tư duy thuật toán và cấu trúc dữ liệu cho sinh viên.",
        organizers="VNG Corporation, VNG Tech Club",  # Comma-delimited string test
        partners_and_sponsors=["AWS", "none"],
        location="Trực tuyến & TP.HCM",
        mode="hybrid",
        participation_fee="Miễn phí",
        total_prize_pool="100.000.000 VND",
        prizes=[
            PrizeTier(tier="Quán quân", reward="30.000.000 VND", estimated_value_vnd=30_000_000.0),
            PrizeTier(tier="Á quân", reward="15.000.000 VND", estimated_value_vnd=15_000_000.0),
        ],
        timeline_stages=[
            TimelineStage(stage_name="Warm-up", start_date="2026-09-01", end_date="2026-09-10"),
            TimelineStage(stage_name="Chung kết", start_date="2026-10-31", end_date="2026-10-31"),
        ],
        registration_start="2026-09-01",
        registration_deadline="2026-09-25",
        registration_status="open",
        target_audience=["Sinh viên CNTT", "Lập trình viên dưới 25 tuổi"],
        team_size_min=1,
        team_size_max=1,
        team_description="Thi đấu cá nhân",
        category="Competitive Programming; Software Engineering",  # Semicolon-delimited string test
        challenge_overview="Giải quyết 5 bài toán thuật toán trong 180 phút trên hệ thống chấm tự động.",
        submission_platform="CodeTour OJ",
    )

    assert comp.name == "Code Tour 2026"
    assert len(comp.organizers) == 2
    assert "VNG Corporation" in comp.organizers
    # Semicolon-delimited string should be converted to clean list
    assert len(comp.category) == 2
    assert "Competitive Programming" in comp.category
    # 'none' placeholder inside partners_and_sponsors should be pruned
    assert comp.partners_and_sponsors == ["AWS"]
    assert comp.mode == "hybrid"
    assert comp.registration_status == "open"
    assert len(comp.prizes) == 2
    assert comp.team_size_min == 1


def test_competition_extraction_result_container() -> None:
    """Verify top-level CompetitionExtractionResult validates structured LLM extractions."""
    result = CompetitionExtractionResult(
        is_competition=True,
        reasoning="Văn bản chứa đầy đủ thông tin cuộc thi AI Challenge TP.HCM 2026.",
        competitions=[
            Competition(
                name="AI Challenge TP.HCM 2026",
                summary="Cuộc thi Trí tuệ Nhân tạo thành phố Hồ Chí Minh tìm kiếm giải pháp AI cho đô thị thông minh.",
                organizers=["Sở Khoa học và Công nghệ TP.HCM"],
                url="https://aichallenge.hochiminhcity.gov.vn",
            )
        ],
    )
    assert result.is_competition is True
    assert len(result.competitions) == 1
    assert result.competitions[0].name == "AI Challenge TP.HCM 2026"


def test_competition_extraction_result_coercion() -> None:
    """Verify robust coercion of is_competition flags and single-dict competitions."""
    # Boolean string normalization: "yes", "true", "co" -> True
    r1 = CompetitionExtractionResult(is_competition="yes", competitions=[])
    assert r1.is_competition is True

    r2 = CompetitionExtractionResult(is_competition="false", competitions=[])
    assert r2.is_competition is False

    # Single dictionary coerced into list
    comp_dict = {
        "name": "HackAITHON 2026",
        "summary": "Cuộc thi phát triển ứng dụng GenAI ứng dụng thực tế trong 48 giờ.",
        "organizers": ["GDG Ho Chi Minh City"],
    }
    r3 = CompetitionExtractionResult(competitions=comp_dict)
    assert len(r3.competitions) == 1
    assert r3.competitions[0].name == "HackAITHON 2026"


def test_empty_document_handling() -> None:
    """Verify model handles documents with no competitions gracefully."""
    empty_result = CompetitionExtractionResult(
        is_competition=False,
        reasoning="Trang web trả về lỗi 404 Not Found hoặc không phải cuộc thi học thuật.",
        competitions=[],
    )
    assert empty_result.is_competition is False
    assert len(empty_result.competitions) == 0
    assert "404" in empty_result.reasoning


def test_json_roundtrip_integrity() -> None:
    """Verify model export and re-import via JSON preserves data integrity."""
    comp = Competition(
        name="RMIT Hackathon 2026",
        summary="Cuộc thi Hackathon thường niên dành cho sinh viên công nghệ và kinh doanh.",
        organizers=["RMIT University Vietnam"],
        total_prize_pool="50.000.000 VND",
        prizes=[PrizeTier(tier="First Prize", reward="30.000.000 VND", estimated_value_vnd=30_000_000.0)],
        target_audience=["Sinh viên RMIT", "Sinh viên các trường đối tác"],
    )
    result = CompetitionExtractionResult(is_competition=True, competitions=[comp])

    json_str = result.model_dump_json(indent=2)
    assert isinstance(json_str, str)

    # Reconstruct from JSON string
    reloaded = CompetitionExtractionResult.model_validate_json(json_str)
    assert reloaded.is_competition is True
    assert len(reloaded.competitions) == 1
    assert reloaded.competitions[0].name == "RMIT Hackathon 2026"
    assert reloaded.competitions[0].prizes[0].estimated_value_vnd == 30_000_000.0


# ---------------------------------------------------------------------------
# TASK-SLV-02: Silver Parquet Contract & Gap Documentation Tests
# ---------------------------------------------------------------------------


def test_silver_parquet_contract_and_referential_integrity(tmp_path) -> None:
    """Verify export_silver_parquet produces valid competitions & prizes Parquet with unique keys and no orphans."""
    import importlib.util
    from pathlib import Path

    import pyarrow.parquet as pq

    mod_path = Path(__file__).resolve().parents[1] / "src" / "acdp" / "4_analytics_gold.py"
    spec = importlib.util.spec_from_file_location("analytics_gold", mod_path)
    assert spec and spec.loader
    gold_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gold_mod)

    sample = [
        Competition(
            name="Code Tour 2026",
            url="https://codetour.org",
            summary="Cuộc thi lập trình thuật toán.",
            organizers=["VNG"],
            category=["Competitive Programming"],
            mode="hybrid",
            team_size_min=1,
            team_size_max=1,
            total_prize_pool="100.000.000 VND",
            registration_deadline="25/09/2026",
            prizes=[
                PrizeTier(tier="Quán quân", reward="30.000.000 VND", estimated_value_vnd=30_000_000.0),
            ],
            timeline_stages=[
                TimelineStage(stage_name="Warm-up", start_date="2026-09-01", end_date="2026-09-10"),
            ],
        )
    ]

    exported = gold_mod.export_silver_parquet(sample, output_dir=tmp_path)
    comp_path = tmp_path / "competitions.parquet"
    prizes_path = tmp_path / "prizes.parquet"
    assert comp_path in exported and prizes_path in exported

    comp_tbl = pq.read_table(comp_path)
    prize_tbl = pq.read_table(prizes_path)

    required_comp_cols = {
        "competition_key",
        "name",
        "url",
        "summary",
        "organizers",
        "partners_and_sponsors",
        "category",
        "target_audience",
        "team_size_min",
        "team_size_max",
        "mode",
        "location",
        "participation_fee",
        "total_prize_vnd",
        "registration_status",
        "registration_deadline",
        "challenge_overview",
        "submission_platform",
    }
    assert required_comp_cols.issubset(set(comp_tbl.column_names))

    comp_keys = comp_tbl["competition_key"].to_pylist()
    assert len(comp_keys) == len(set(comp_keys)) == 1

    prize_keys = set(prize_tbl["competition_key"].to_pylist())
    assert prize_keys.issubset(set(comp_keys))
    assert {"competition_key", "tier_rank", "tier", "reward", "estimated_value_vnd", "is_scholarship"}.issubset(
        set(prize_tbl.column_names)
    )


def test_silver_schema_v2_gap_g1_g8_resolved() -> None:
    """Verify all Silver schema gaps (G1-G8) audited in TASK-SLV-02 are resolved in ACDP v2."""
    from acdp.v2.gold_star_schema import (
        SILVER_COMPETITIONS_ARROW_SCHEMA,
        SILVER_PRIZES_ARROW_SCHEMA,
        SILVER_TIMELINE_STAGES_ARROW_SCHEMA,
    )
    from acdp.v2.schemas import Competition as CompV2
    from acdp.v2.schemas import PrizeTier as PrizeV2
    from acdp.v2.schemas import TimelineStage as StageV2

    comp_fields = set(CompV2.model_fields.keys())
    prize_fields = set(PrizeV2.model_fields.keys())
    stage_fields = set(StageV2.model_fields.keys())

    assert {"registration_start_date", "registration_deadline_date", "event_start_date", "event_end_date"}.issubset(
        comp_fields
    )
    assert {"start_date_iso", "end_date_iso"}.issubset(stage_fields)
    assert {"is_individual_allowed", "eligibility_level", "allowed_majors", "required_skills"}.issubset(comp_fields)
    assert {"official_rules_url", "organizer_contact", "requires_advisor", "team_registration_deadline"}.issubset(
        comp_fields
    )
    assert {"tier_rank", "quantity", "currency", "prize_type"}.issubset(prize_fields)
    assert {"competition_key", "source_url", "bronze_key", "extracted_at", "extractor_model", "schema_version"}.issubset(
        comp_fields
    )

    assert "registration_deadline_date" in SILVER_COMPETITIONS_ARROW_SCHEMA.names
    assert "quantity" in SILVER_PRIZES_ARROW_SCHEMA.names
    assert "start_date_iso" in SILVER_TIMELINE_STAGES_ARROW_SCHEMA.names


def test_silver_v2_schema_validation_and_g7_rejection() -> None:
    """Verify Schema v2 ISO date normalization, eligibility, skills, advisor fields, and G7 strict PrizeTier."""
    from datetime import date

    import pytest
    from pydantic import ValidationError

    from acdp.v2.schemas import Competition as CompV2
    from acdp.v2.schemas import PrizeTier as PrizeV2
    from acdp.v2.schemas import TimelineStage as StageV2

    with pytest.raises(ValidationError):
        PrizeV2(tier="N/A", reward="Not specified")

    comp = CompV2(
        name="Vietnam AI Challenge 2026",
        url="https://vaic.vn/?utm_source=fb",
        summary="Cuộc thi AI dành cho sinh viên CNTT và KTDL.",
        team_size_min=1,
        team_size_max=4,
        eligibility_level="Sinh viên đại học",
        allowed_majors="CNTT, Khoa học Dữ liệu",
        required_skills=["Python", "PyTorch", "none"],
        registration_deadline="25/09/2026",
        event_start="2026-10-01",
        official_rules_url="https://vaic.vn/rules.pdf",
        organizer_contact="btc@vaic.vn",
        requires_advisor=True,
        team_registration_deadline="20/09/2026",
        prizes=[
            {"tier": "N/A", "reward": "Not specified"},
            {"tier": "Khuyến khích", "reward": "5 triệu VNĐ", "quantity": 3, "estimated_value_vnd": 5_000_000},
        ],
        timeline_stages=[
            StageV2(stage_name="Vòng 1", start_date="01/09/2026", end_date="25/09/2026"),
        ],
    )

    assert comp.registration_deadline_date == date(2026, 9, 25)
    assert comp.event_start_date == date(2026, 10, 1)
    assert comp.team_registration_deadline_date == date(2026, 9, 20)
    assert comp.is_individual_allowed is True
    assert comp.eligibility_level == "undergraduate"
    assert comp.allowed_majors == ["CNTT", "Khoa học Dữ liệu"]
    assert comp.required_skills == ["Python", "PyTorch"]
    assert comp.requires_advisor is True
    assert len(comp.prizes) == 1
    assert comp.prizes[0].quantity == 3
    assert comp.prizes[0].tier_rank == 1
    assert comp.timeline_stages[0].start_date_iso == date(2026, 9, 1)
    assert comp.competition_key and len(comp.competition_key) == 64


def test_silver_v2_explicit_pyarrow_zstd_and_timeline_stages(tmp_path) -> None:
    """Verify v2 export_silver_parquet writes 3 ZSTD Parquet files with explicit schemas and true nulls."""
    from datetime import UTC, datetime

    import pyarrow as pa
    import pyarrow.parquet as pq

    from acdp.v2.gold_star_schema import (
        SILVER_COMPETITIONS_ARROW_SCHEMA,
        SILVER_PRIZES_ARROW_SCHEMA,
        SILVER_TIMELINE_STAGES_ARROW_SCHEMA,
        _deduplicate_competition_payloads,
        export_silver_parquet,
    )

    # Simulate legacy v1 JSON payload with _metadata to verify backward compatibility + lineage enrichment
    v1_payload = {
        "_metadata": {
            "source_url": "https://codetour.org/",
            "source_key": "bronze/codetour.org/year=2026/month=11/day=23/1795416946.html",
            "extracted_at": datetime(2026, 11, 23, 8, 0, tzinfo=UTC).isoformat(),
        },
        "is_competition": True,
        "competitions": [
            {
                "name": "Code Tour 2026",
                "url": "https://codetour.org/",
                "summary": "Cuộc thi lập trình thuật toán.",
                "organizers": ["VNG"],
                "category": ["Competitive Programming"],
                "registration_deadline": "25/09/2026",
                "prizes": [
                    {"tier": "Giải Ba", "reward": "5.000.000 VND", "quantity": 2, "estimated_value_vnd": 5_000_000},
                ],
                "timeline_stages": [
                    {"stage_name": "Warm-up", "start_date": "01/09/2026", "end_date": "10/09/2026"},
                ],
            }
        ],
    }

    comps = _deduplicate_competition_payloads([("v1.json", v1_payload)])
    assert len(comps) == 1
    assert comps[0].source_url == "https://codetour.org/"
    assert comps[0].bronze_key == "bronze/codetour.org/year=2026/month=11/day=23/1795416946.html"

    exported = export_silver_parquet(comps, output_dir=tmp_path)
    comp_path = tmp_path / "competitions.parquet"
    prizes_path = tmp_path / "prizes.parquet"
    stages_path = tmp_path / "timeline_stages.parquet"
    assert set(exported) == {comp_path, prizes_path, stages_path}

    comp_tbl = pq.read_table(comp_path)
    prize_tbl = pq.read_table(prizes_path)
    stage_tbl = pq.read_table(stages_path)

    assert comp_tbl.schema.equals(SILVER_COMPETITIONS_ARROW_SCHEMA)
    assert prize_tbl.schema.equals(SILVER_PRIZES_ARROW_SCHEMA)
    assert stage_tbl.schema.equals(SILVER_TIMELINE_STAGES_ARROW_SCHEMA)

    # Verify ZSTD compression
    for p in (comp_path, prizes_path, stages_path):
        meta = pq.read_metadata(p)
        assert meta.row_group(0).column(0).compression == "ZSTD"

    # Verify true null preservation (not coerced to "") and ISO date32
    assert comp_tbl["tagline"].null_count == 1
    assert comp_tbl["location"].null_count == 1
    assert pa.types.is_date32(comp_tbl.schema.field("registration_deadline_date").type)
    assert comp_tbl["total_prize_vnd"].to_pylist() == [10_000_000]
    assert prize_tbl["quantity"].to_pylist() == [2]
    assert stage_tbl["stage_name"].to_pylist() == ["Warm-up"]
    assert pa.types.is_date32(stage_tbl.schema.field("start_date_iso").type)
