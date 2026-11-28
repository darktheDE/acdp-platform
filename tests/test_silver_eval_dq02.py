"""Automated unit & regression tests for TASK-DQ-02 (Golden Dataset & Silver Evaluator)."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from bs4 import BeautifulSoup

from acdp.v2 import silver_eval, silver_transform
from acdp.v2.schemas import parse_date_value


def _make_minimal_dataset(cases: list[dict]) -> silver_eval.GoldenDataset:
    sha = silver_eval.compute_cases_sha256(cases)
    return silver_eval.GoldenDataset.model_validate(
        {
            "dataset_version": "1.0.0-test",
            "schema_version": "2.0",
            "created_at": "2026-11-28",
            "scope": "unit-test",
            "annotators": ["Tester"],
            "annotation_guidelines": "unit-test",
            "content_sha256": sha,
            "cases": cases,
        }
    )


def test_golden_dataset_v1_schema_and_sha256_integrity() -> None:
    """Verify docs/experiments/data/silver-golden-dataset-v1.json passes Pydantic & SHA-256 checks."""
    ds_path = Path("docs/experiments/data/silver-golden-dataset-v1.json")
    dataset = silver_eval.load_golden_dataset(ds_path, verify_hash=True)

    assert len(dataset.cases) == 10
    case_ids = [c.case_id for c in dataset.cases]
    assert len(set(case_ids)) == 10
    for c in dataset.cases:
        assert c.bronze_key.startswith("bronze/")
        assert c.silver_markdown_key.startswith("silver/markdown/")
        assert c.evidence_snippets, f"{c.case_id} missing evidence_snippets"
        assert c.ground_truth.name


def test_nullable_ie_metrics_tp_fp_fn_tn_and_exact_match() -> None:
    """Verify GT=None & Pred=None scores TN (not TP), while value mismatch scores 1 FP + 1 FN."""
    cases = [
        {
            "case_id": "t1",
            "stratum": "s",
            "domain": "a.vn",
            "bronze_key": "bronze/a.vn/1.html",
            "silver_markdown_key": "silver/markdown/a.vn/1.md",
            "source_url": "https://a.vn",
            "ground_truth": {
                "name": "Contest A",
                "url": "https://a.vn",
                "registration_deadline_date": None,
                "eligibility_level": "undergraduate",
                "total_prize_vnd": 10000000,
            },
        },
        {
            "case_id": "t2",
            "stratum": "s",
            "domain": "b.vn",
            "bronze_key": "bronze/b.vn/2.html",
            "silver_markdown_key": "silver/markdown/b.vn/2.md",
            "source_url": "https://b.vn",
            "ground_truth": {
                "name": "Contest B",
                "url": "https://b.vn",
                "registration_deadline_date": "2026-07-17",
                "eligibility_level": "open",
                "total_prize_vnd": 14000000,
            },
        },
    ]
    ds = _make_minimal_dataset(cases)
    preds = {
        "bronze/a.vn/1.html": {
            "name": "Contest A",
            "url": "http://www.a.vn/",
            "registration_deadline_date": None,
            "eligibility_level": "unknown",  # treated as missing -> FN
            "total_prize_vnd": 10300000,  # within +-5% -> TP
        },
        "bronze/b.vn/2.html": {
            "name": "Contest B",
            "url": "https://b.vn",
            "registration_deadline_date": "2026-07-18",  # wrong date -> 1 FP + 1 FN
            "eligibility_level": "open",
            "total_prize_vnd": 7500000,  # >5% error -> 1 FP + 1 FN
        },
    }
    report = silver_eval.evaluate_predictions(ds, preds)
    by_f = {m.field: m for m in report.field_metrics}

    # url: both match after normalization
    assert (by_f["url"].tp, by_f["url"].fp, by_f["url"].fn, by_f["url"].tn) == (2, 0, 0, 0)
    assert by_f["url"].f1 == 1.0

    # registration_deadline_date: t1 is TN, t2 is value mismatch (FP=1, FN=1)
    dl = by_f["registration_deadline_date"]
    assert (dl.tp, dl.fp, dl.fn, dl.tn) == (0, 1, 1, 1)
    assert dl.exact_match_rate == 0.5
    assert dl.f1 == 0.0

    # eligibility_level: 'unknown' is FN, 'open' is TP
    el = by_f["eligibility_level"]
    assert (el.tp, el.fp, el.fn, el.tn) == (1, 0, 1, 0)
    assert el.precision == 1.0
    assert el.recall == 0.5

    # total_prize_vnd: t1 within 5% (TP=1), t2 wrong (FP=1, FN=1)
    pv = by_f["total_prize_vnd"]
    assert (pv.tp, pv.fp, pv.fn) == (1, 1, 1)
    assert pv.precision == 0.5
    assert pv.recall == 0.5


def test_bipartite_array_f1_is_order_insensitive() -> None:
    """Verify prizes & timeline_stages Bipartite F1 ignores element permutation."""
    gt_prizes = [
        {"tier": "Giải Nhất", "reward": "3.000.000đ", "estimated_value_vnd": 3000000},
        {"tier": "Giải Nhì", "reward": "2.000.000đ", "estimated_value_vnd": 2000000},
    ]
    pred_prizes_reversed = [
        {"tier": "Giải Nhì", "reward": "2.000.000đ", "estimated_value_vnd": 2000000},
        {"tier": "Giải Nhất", "reward": "3.000.000đ", "estimated_value_vnd": 3000000},
    ]
    tp, fp, fn, exact = silver_eval.score_bipartite_array(
        gt_prizes, pred_prizes_reversed, silver_eval._prize_similarity
    )
    assert (tp, fp, fn, exact) == (2, 0, 0, True)

    gt_stages = [
        {"stage_name": "Vòng 1", "start_date_iso": "2026-08-01", "end_date_iso": "2026-08-15"},
        {"stage_name": "Chung kết", "start_date_iso": "2026-09-10", "end_date_iso": "2026-09-10"},
    ]
    pred_stages = [
        {"stage_name": "Chung kết", "start_date_iso": "2026-09-10", "end_date_iso": "2026-09-10"},
    ]
    stp, sfp, sfn, sexact = silver_eval.score_bipartite_array(
        gt_stages, pred_stages, silver_eval._stage_similarity
    )
    assert (stp, sfp, sfn, sexact) == (1, 0, 1, False)


def test_error_taxonomy_classifier_e1_to_e5() -> None:
    """Verify deterministic attribution across all 5 root-cause error categories."""
    case_uit = silver_eval.GoldenCase.model_validate(
        {
            "case_id": "gold-09",
            "stratum": "uni",
            "domain": "www.uit.edu.vn",
            "bronze_key": "bronze/www.uit.edu.vn/1.html",
            "silver_markdown_key": "silver/markdown/www.uit.edu.vn/1.md",
            "source_url": "https://www.uit.edu.vn/bai-viet/dsc-2026",
            "ground_truth": {"name": "UIT DSC 2026", "url": "https://www.uit.edu.vn/bai-viet/dsc-2026"},
        }
    )
    e1_cls, _ = silver_eval.classify_error_cause(
        case_uit, "url", "https://www.uit.edu.vn/bai-viet/dsc-2026", "https://tracuu.citd.edu.vn", {}, {}
    )
    assert e1_cls == "E1_HTML_PARSER_NOISE"

    e2_cls, _ = silver_eval.classify_error_cause(
        case_uit,
        "registration_deadline_date",
        "2026-07-17",
        None,
        {"registration_deadline": "17/07/2026 – 11:00"},
        {},
    )
    assert e2_cls == "E2_DATE_NORMALIZER"

    e3_cls, _ = silver_eval.classify_error_cause(
        case_uit, "eligibility_level", "undergraduate", "unknown", {}, {}
    )
    assert e3_cls == "E3_PROMPT_SCHEMA_DRIFT"

    case_vai = silver_eval.GoldenCase.model_validate(
        {
            "case_id": "gold-07",
            "stratum": "official",
            "domain": "www.vietnamaichallenge.com",
            "bronze_key": "bronze/www.vietnamaichallenge.com/1.html",
            "silver_markdown_key": "silver/markdown/www.vietnamaichallenge.com/1.md",
            "source_url": "https://www.vietnamaichallenge.com/",
            "ground_truth": {"name": "VAIC", "url": "https://www.vietnamaichallenge.com"},
        }
    )
    e4_cls, _ = silver_eval.classify_error_cause(case_vai, "team_size_min", 1, None, {}, {})
    assert e4_cls == "E4_DYNAMIC_SPA_INCOMPLETE"


def test_option_a_date_parser_and_sidebar_noise_regression() -> None:
    """Verify Option A fixes: datetime suffix parsing & nav/sidebar/ad pruning."""
    assert parse_date_value("17/07/2026 – 11:00") == date(2026, 7, 17)
    assert parse_date_value("11:00, 17/07/2026") == date(2026, 7, 17)
    assert parse_date_value("23:59 ngày 15/06/2026") == date(2026, 6, 15)
    assert parse_date_value("TBD") is None

    uit_like_html = (
        "<html><body>"
        '<header><nav>'
        '<a href="https://tracuu.citd.edu.vn/">Chứng chỉ CNTT</a>'
        '<a href="https://www.uit.edu.vn/media/07_nq_hdtdhcntt_09_9_2024_b1b4d3c56b.pdf">Quy chế dân chủ cơ sở</a>'
        "</nav></header>"
        "<main><h1>UIT Data Science Challenge 2026</h1>"
        '<p>Đăng ký tại <a href="https://bit.ly/DANG_KY_DSC_2026">Form</a></p>'
        "</main>"
        "</body></html>"
    )
    soup_uit = BeautifulSoup(uit_like_html, "html.parser")
    officials, rules = silver_transform._extract_links_from_soup(
        soup_uit,
        "https://www.uit.edu.vn/bai-viet/chinh-thuc-khoi-dong-cuoc-thi-uit-data-science-challenge-2026",
        "www.uit.edu.vn",
    )
    assert "https://tracuu.citd.edu.vn" not in officials
    assert rules == []

    ybox_ad_html = (
        "<html><body>"
        '<nav><a href="https://ybox.vn/cuoc-thi">Cuộc thi</a></nav>'
        '<div class="slick-slide"><div class="rpa__media">'
        '<a href="https://www.ntu.edu.sg/business/admissions/graduate-studies/msc-programmes">Ad</a>'
        "</div></div>"
        '<main><p>DATATHON 2026 <a href="https://forms.gle/abc">Đăng ký</a></p></main>'
        "</body></html>"
    )
    pages = [("https://ybox.vn/su-kien/datathon-2026", ybox_ad_html)]
    sig = silver_transform.extract_deterministic_signals(pages, "DATATHON 2026", "ybox.vn", is_html=True)
    assert sig.has_official_website is False
    assert sig.canonical_official_url == ""

    zalo_html = (
        "<html><body>"
        '<nav><a href="https://challenge.zalo.ai/regulations">Regulations</a></nav>'
        "<main><h1>Zalo AI Challenge 2026</h1></main>"
        "</body></html>"
    )
    sig_zalo = silver_transform.extract_deterministic_signals(
        [("https://challenge.zalo.ai/", zalo_html)], "Zalo AI Challenge 2026", "challenge.zalo.ai", is_html=True
    )
    assert sig_zalo.official_rules_urls == ["https://challenge.zalo.ai/regulations"]
