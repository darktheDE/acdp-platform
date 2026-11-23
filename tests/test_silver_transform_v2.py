"""Unit & mocked integration tests for ACDP v2 Silver Transform & RAG Ingest (TASK-SLV-03)."""

from __future__ import annotations

import io
from unittest.mock import MagicMock

import pytest

from acdp.schemas import Competition, CompetitionExtractionResult
from acdp.v2 import rag_ingest, silver_transform


class InMemoryR2Client:
    """Minimal in-memory boto3 S3/R2 stub for deterministic Bronze->Silver->RAG tests."""

    def __init__(self) -> None:
        self.objects: dict[str, dict[str, object]] = {}

    def put_object(
        self,
        Bucket: str,
        Key: str,
        Body: bytes,
        ContentType: str = "application/octet-stream",
        Metadata: dict[str, str] | None = None,
    ) -> None:
        self.objects[Key] = {
            "Bucket": Bucket,
            "Key": Key,
            "Body": Body,
            "ContentType": ContentType,
            "Metadata": dict(Metadata or {}),
        }

    def get_object(self, Bucket: str, Key: str) -> dict[str, object]:
        obj = self.objects[Key]
        return {
            "Body": io.BytesIO(obj["Body"]),  # type: ignore[arg-type]
            "Metadata": obj["Metadata"],
            "ContentType": obj["ContentType"],
        }

    def get_paginator(self, operation_name: str):
        assert operation_name == "list_objects_v2"
        parent = self

        class _Paginator:
            def paginate(self, Bucket: str, Prefix: str = ""):
                contents = [
                    {"Key": k, "Size": len(v["Body"])}  # type: ignore[arg-type]
                    for k, v in sorted(parent.objects.items())
                    if k.startswith(Prefix)
                ]
                yield {"Contents": contents}

        return _Paginator()


def test_split_bronze_pages_and_in_ram_clean_markdown() -> None:
    """Verify ACDP_PAGE_BOUNDARY splitting and in-RAM DefaultMarkdownGenerator conversion."""
    raw_html = (
        '<!-- ACDP_PAGE_BOUNDARY url="https://codetour.org/?tab=&quot;main&quot;" -->\n'
        "<!DOCTYPE html><html><head>"
        '<title>Code Tour 2026</title>'
        '<meta property="og:title" content="Code Tour 2026 - VNG">'
        "<style>body { color: red; }</style>"
        '<script type="application/ld+json">{"@type":"Event","name":"Code Tour 2026"}</script>'
        "</head><body>"
        "<h1>Code Tour 2026</h1>"
        "<p>Cuộc thi lập trình thuật toán dành cho sinh viên CNTT. Giải thưởng 100 triệu VNĐ.</p>"
        '<img src="banner.png" alt="banner">'
        "</body></html>\n\n"
        '<!-- ACDP_PAGE_BOUNDARY url="https://codetour.org/rules" -->\n'
        "<html><body><h2>Thể lệ</h2><p>Mỗi đội 1-3 sinh viên, thi online và chung kết offline.</p></body></html>"
    )
    assert silver_transform.is_html_payload(raw_html, "markdown") is True
    pages = silver_transform.split_bronze_pages(raw_html, "codetour.org")
    assert len(pages) == 2
    assert pages[0][0] == 'https://codetour.org/?tab="main"'
    assert pages[1][0] == "https://codetour.org/rules"

    clean_md = silver_transform.html_to_clean_markdown(pages)
    assert "Code Tour 2026" in clean_md
    assert "100 triệu VNĐ" in clean_md
    assert "Mỗi đội 1-3 sinh viên" in clean_md
    assert "color: red" not in clean_md
    assert "banner.png" not in clean_md
    assert "<!-- source_page: https://codetour.org/rules -->" in clean_md


def test_deterministic_extraction_jsonld_og_official_links_and_regex() -> None:
    """Verify JSON-LD, og:*, official website resolution, .pdf rulebook, and regex hints."""
    ybox_html = (
        "<html><head>"
        '<meta property="og:title" content="Cuộc thi AI Arena Vietnam 2026">'
        '<meta property="og:description" content="Đấu trường AI toàn quốc cho sinh viên">'
        '<script type="application/ld+json">'
        '{"@context":"https://schema.org","@graph":[{"@type":"Event","name":"AI Arena Vietnam 2026","startDate":"2026-10-15","organizer":{"name":"ĐHQGHN"}}]}'
        "</script></head><body>"
        "<h1>AI Arena Vietnam 2026</h1>"
        "<p>Cuộc thi Trí tuệ Nhân tạo dành cho sinh viên đại học toàn quốc. "
        "Tổng giải thưởng 500 triệu VNĐ. Miễn phí tham gia. Mỗi đội 3 thành viên. "
        "Hạn đăng ký 30/11/2026. Thi đấu online và chung kết trực tiếp tại Hà Nội.</p>"
        '<a href="https://facebook.com/aiarena">Fanpage</a>'
        '<a href="https://ai-arena-vietnam.vnu.edu.vn/">Website chính thức cuộc thi</a>'
        '<a href="https://ai-arena-vietnam.vnu.edu.vn/the-le-2026.pdf">Tải thể lệ PDF</a>'
        "</body></html>"
    )
    pages = [("https://ybox.vn/cuoc-thi/ai-arena-vietnam-2026", ybox_html)]
    clean_md = silver_transform.html_to_clean_markdown(pages)
    signals = silver_transform.extract_deterministic_signals(pages, clean_md, "ybox.vn", is_html=True)

    assert signals.is_media_or_aggregator is True
    assert signals.has_official_website is True
    assert signals.canonical_official_url == "https://ai-arena-vietnam.vnu.edu.vn/"
    assert signals.official_rules_urls == ["https://ai-arena-vietnam.vnu.edu.vn/the-le-2026.pdf"]
    assert signals.json_ld["name"] == "AI Arena Vietnam 2026"
    assert signals.json_ld["organizer"] == "ĐHQGHN"
    assert "30/11/2026" in signals.detected_dates
    assert 2026 in signals.detected_years
    assert signals.detected_team_bounds == (3, 3)
    assert signals.detected_mode == "hybrid"
    assert signals.detected_fee == "Miễn phí"


def test_dir022_scope_gate_and_media_partner_dedup() -> None:
    """Verify DIR-022 rejects non-IT, school-only, out-of-year, no-official-site, and merges media posts."""
    # 1. Non-IT contest (Marketing)
    mkt_md = "Cuộc thi Marketing Arena 2026 dành cho sinh viên kinh tế và truyền thông thương hiệu toàn quốc. " * 6
    mkt_signals = silver_transform.DeterministicSignals(
        source_domain="marketingarena.vn",
        source_url="https://marketingarena.vn",
        is_html=True,
        canonical_official_url="https://marketingarena.vn",
        has_official_website=True,
        detected_years=[2026],
    )
    assert silver_transform.evaluate_pre_llm_scope(mkt_signals, mkt_md).reason == "out_of_scope_non_tech"

    # 2. School-only contest (Tin học trẻ THCS/THPT)
    school_md = "Hội thi Tin học trẻ thành phố Huế năm 2026 dành cho học sinh tiểu học, THCS và THPT thi lập trình. " * 5
    school_signals = silver_transform.DeterministicSignals(
        source_domain="huongtra.hue.gov.vn",
        source_url="https://huongtra.hue.gov.vn/tin-tuc/hoi-thi-tin-hoc-tre",
        is_html=True,
        canonical_official_url="https://huongtra.hue.gov.vn/tin-tuc/hoi-thi-tin-hoc-tre",
        has_official_website=True,
        detected_years=[2026],
    )
    assert silver_transform.evaluate_pre_llm_scope(school_signals, school_md).reason == "out_of_scope_non_university"

    # 3. Out-of-year archive (2023)
    old_md = "Cuộc thi Hackathon AI sinh viên đại học công nghệ thông tin toàn quốc năm 2023 với tổng giải thưởng 100 triệu. " * 5
    old_signals = silver_transform.DeterministicSignals(
        source_domain="oldhack.vn",
        source_url="https://oldhack.vn",
        is_html=True,
        canonical_official_url="https://oldhack.vn",
        has_official_website=True,
        detected_years=[2023],
    )
    assert silver_transform.evaluate_pre_llm_scope(old_signals, old_md, reference_year=2026).reason == "out_of_scope_year"

    # 4. Media partner with no official website
    no_site_md = "Thông báo cuộc thi Khoa học Dữ liệu AI sinh viên năm 2026, đăng ký qua Google Form. " * 5
    no_site_signals = silver_transform.DeterministicSignals(
        source_domain="ybox.vn",
        source_url="https://ybox.vn/cuoc-thi/no-official",
        is_html=True,
        is_media_or_aggregator=True,
        has_official_website=False,
        canonical_official_url="",
        detected_years=[2026],
    )
    assert silver_transform.evaluate_pre_llm_scope(no_site_signals, no_site_md).reason == "no_official_website"

    # 5. Media partner merged into official site already present in Bronze
    merged_signals = silver_transform.DeterministicSignals(
        source_domain="daihoc.fpt.edu.vn",
        source_url="https://daihoc.fpt.edu.vn/hcm/code-tour-2026",
        is_html=True,
        is_media_or_aggregator=True,
        has_official_website=True,
        canonical_official_url="https://codetour.org",
        detected_years=[2026],
    )
    decision = silver_transform.evaluate_pre_llm_scope(
        merged_signals,
        "Code Tour 2026 cuộc thi lập trình thuật toán dành cho sinh viên CNTT toàn quốc. " * 5,
        known_official_domains={"codetour.org"},
    )
    assert decision.accepted is False
    assert decision.reason == "media_partner_merged_to_official"
    assert decision.merged_into_official_key == "codetour.org"


def test_post_llm_guards_enforce_canonical_url() -> None:
    """Verify post-LLM guards override aggregator URLs with resolved canonical official URL."""
    signals = silver_transform.DeterministicSignals(
        source_domain="ybox.vn",
        source_url="https://ybox.vn/cuoc-thi/datathon-2026",
        is_html=True,
        is_media_or_aggregator=True,
        has_official_website=True,
        canonical_official_url="https://www.datathon.site",
    )
    raw = CompetitionExtractionResult(
        is_competition=True,
        competitions=[
            Competition(
                name="Vietnam Datathon 2026",
                url="https://ybox.vn/cuoc-thi/datathon-2026",
                summary="Cuộc thi Khoa học Dữ liệu dành cho sinh viên đại học toàn quốc.",
                category=["Data Science"],
                target_audience="Sinh viên đại học",
                registration_deadline="15/11/2026",
            )
        ],
    )
    guarded = silver_transform.apply_post_llm_guards(raw, signals, reference_year=2026)
    assert guarded.is_competition is True
    assert len(guarded.competitions) == 1
    assert guarded.competitions[0].url == "https://www.datathon.site"


def test_end_to_end_silver_transform_and_rag_ingest_from_silver(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify full Bronze->Silver(Markdown+JSON)->RAG(Silver-only) flow with mocked R2 and LLM."""
    fake_s3 = InMemoryR2Client()

    # 1. Official HTML in Bronze
    codetour_html = (
        '<!-- ACDP_PAGE_BOUNDARY url="https://codetour.org/" -->\n'
        "<html><head><title>Code Tour 2026</title></head><body>"
        "<h1>Code Tour 2026</h1>"
        "<p>Cuộc thi lập trình thuật toán dành cho sinh viên CNTT và kỹ sư công nghệ trẻ toàn quốc năm 2026. "
        "Tổng giá trị giải thưởng lên tới 100 triệu VNĐ cùng nhiều cơ hội thực tập tại VNG Corporation. "
        "Hạn đăng ký 20/11/2026. Hình thức thi đấu vòng loại online và vòng chung kết trực tiếp tại TP.HCM.</p>"
        "</body></html>"
    )
    fake_s3.put_object(
        "acdp-test",
        "bronze/codetour.org/year=2026/month=11/day=23/1795416946.html",
        codetour_html.encode("utf-8"),
    )

    # 2. Media-partner #1 on ybox.vn pointing to codetour.org -> must merge/skip LLM
    ybox_dup_html = (
        '<!-- ACDP_PAGE_BOUNDARY url="https://ybox.vn/cuoc-thi/code-tour-2026" -->\n'
        "<html><body><h1>Code Tour 2026</h1>"
        "<p>Cuộc thi lập trình thuật toán dành cho sinh viên CNTT toàn quốc năm 2026 do VNG tổ chức. "
        "Sinh viên tham gia giải quyết các bài toán cấu trúc dữ liệu và giải thuật trong 180 phút. "
        "Xem thông tin chi tiết và thể lệ chính thức tại trang chủ bên dưới.</p>"
        '<a href="https://codetour.org/">Trang chủ chính thức</a></body></html>'
    )
    fake_s3.put_object(
        "acdp-test",
        "bronze/ybox.vn/year=2026/month=11/day=23/1795418230.html",
        ybox_dup_html.encode("utf-8"),
    )

    # 3. Media-partner #2 on SAME domain ybox.vn with NO official site -> preserved as distinct URL, then dropped
    ybox_nosite_html = (
        '<!-- ACDP_PAGE_BOUNDARY url="https://ybox.vn/cuoc-thi/no-official-site" -->\n'
        "<html><body><h1>Cuộc thi AI Nội Bộ 2026</h1>"
        "<p>Cuộc thi trí tuệ nhân tạo và khoa học dữ liệu dành cho sinh viên đại học năm 2026. "
        "Thí sinh đăng ký tham gia trực tiếp qua biểu mẫu trực tuyến của ban truyền thông, "
        "không có website chính thức riêng của cuộc thi.</p>"
        '<a href="https://forms.gle/abc123">Đăng ký</a></body></html>'
    )
    fake_s3.put_object(
        "acdp-test",
        "bronze/ybox.vn/year=2026/month=11/day=23/1795418261.html",
        ybox_nosite_html.encode("utf-8"),
    )

    # 4. Legacy Markdown in Bronze (backward compatibility test)
    legacy_md = (
        "# RMIT Hackathon 2026\n\n"
        "Cuộc thi Hackathon AI & An toàn thông tin dành cho sinh viên đại học và sau đại học năm 2026. "
        "Mỗi đội gồm 4 sinh viên đến từ các trường đại học tại Việt Nam và quốc tế. "
        "Tổng giải thưởng 100 triệu VNĐ, hạn đăng ký 30/11/2026, thi offline tại TP.HCM và Hà Nội."
    )
    fake_s3.put_object(
        "acdp-test",
        "bronze/rmit-hackathon.com/year=2026/month=11/day=23/1795417036",
        legacy_md.encode("utf-8"),
    )

    monkeypatch.setattr(silver_transform.settings, "bucket_name", "acdp-test")
    monkeypatch.setattr(type(silver_transform.settings), "create_r2_client", lambda self: fake_s3)

    def _fake_extract(client, signals, clean_md):
        if signals.source_domain == "codetour.org":
            return CompetitionExtractionResult(
                is_competition=True,
                competitions=[
                    Competition(
                        name="Code Tour 2026",
                        url="https://codetour.org",
                        summary="Cuộc thi lập trình thuật toán toàn quốc cho sinh viên CNTT.",
                        category=["Competitive Programming"],
                        target_audience="Sinh viên CNTT",
                        registration_deadline="20/11/2026",
                    )
                ],
            )
        return CompetitionExtractionResult(
            is_competition=True,
            competitions=[
                Competition(
                    name="RMIT Hackathon 2026",
                    url="https://rmit-hackathon.com",
                    summary="Cuộc thi Hackathon AI và Bảo mật cho sinh viên đại học.",
                    category=["Artificial Intelligence", "Cybersecurity"],
                    target_audience="Sinh viên đại học",
                    registration_deadline="30/11/2026",
                )
            ],
        )

    monkeypatch.setattr(silver_transform, "_create_instructor_client", lambda: MagicMock())
    monkeypatch.setattr(silver_transform, "extract_competition_hybrid", _fake_extract)

    summary = silver_transform.run_silver_transform(run_llm=True, target_date="2026-11-23")
    assert summary["total_snapshots"] == 4
    assert summary["uploaded_markdown_count"] == 2
    assert summary["uploaded_json_count"] == 2
    assert summary["drop_breakdown"]["media_partner_merged_to_official"] == 1
    assert summary["drop_breakdown"]["no_official_website"] == 1

    # Verify silver/markdown/ and silver/extractions/ keys exist
    assert "silver/markdown/codetour.org/year=2026/month=11/day=23/1795416946.md" in fake_s3.objects
    assert "silver/markdown/rmit-hackathon.com/year=2026/month=11/day=23/1795417036.md" in fake_s3.objects
    assert "silver/extractions/codetour.org/year=2026/month=11/day=23/1795416946.json" in fake_s3.objects

    # Verify RAG ingest reads strictly from silver/markdown/ (never bronze/)
    monkeypatch.setattr(rag_ingest.settings, "bucket_name", "acdp-test")
    monkeypatch.setattr(type(rag_ingest.settings), "create_r2_client", lambda self: fake_s3)

    # Remove bronze objects to prove rag_ingest does not touch bronze/
    for key in list(fake_s3.objects.keys()):
        if key.startswith("bronze/"):
            del fake_s3.objects[key]

    chosen_date, docs = rag_ingest.load_competition_documents_from_silver(
        s3_client=fake_s3,
        bucket_name="acdp-test",
        target_date="2026-11-23",
    )
    assert chosen_date == "2026-11-23"
    assert len(docs) == 2
    assert {d.metadata["competition_name"] for d in docs} == {"Code Tour 2026", "RMIT Hackathon 2026"}
    assert all(d.metadata["source_key"].startswith("silver/markdown/") for d in docs)
    assert all(d.metadata["layer"] == "silver" for d in docs)

    dry_res = rag_ingest.ingest(target_date="2026-11-23", dry_run=True)
    assert dry_res["docs_loaded"] == 2
    assert dry_res["dry_run"] is True
