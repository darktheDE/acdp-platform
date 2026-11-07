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
