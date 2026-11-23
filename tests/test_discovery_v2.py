"""Unit tests for ACDP v2 3-Tier URL Discovery (TASK-ING-03).

Tests canonicalization, noise filtering, XML/RSS/Atom/GDELT/Hub parsers,
Tier 2 budget guardrails & error fallback, HTTP 304 conditional checks,
and direct Cloudflare R2 manifest upload.
"""

from __future__ import annotations

import asyncio
import importlib
import json
from unittest.mock import MagicMock

import httpx
import pytest

discover_mod = importlib.import_module("acdp.v2.0_discover_urls")


def test_canonicalize_url_and_noise_filter() -> None:
    raw = "HTTPS://Example.EDU.VN:443/cuoc-thi-ai/?utm_source=fb&fbclid=123&b=2&a=1#section"
    canon = discover_mod.canonicalize_url(raw)
    assert canon == "https://example.edu.vn/cuoc-thi-ai?a=1&b=2"

    assert discover_mod.is_noise_url("https://fit.hcmute.edu.vn/lich-thi-hk1-2026") is True
    assert discover_mod.is_noise_url("https://vnexpress.net/tag/hackathon-818560") is True
    assert discover_mod.is_noise_url("https://www.uit.edu.vn/bai-viet/sinh-vien-uit-dat-giai-nhat-cuoc-thi-ai") is True
    assert discover_mod.is_noise_url("https://example.com/banner.png") is True
    assert discover_mod.is_noise_url("https://example.com/hackathon-2026", "AI Hackathon 2026") is False

    # Word-boundary guard: 'tai-cuoc-thi' must NOT trigger 'ai' tech match
    assert discover_mod._is_competition_relevant("https://ybox.vn/cuoc-thi/am-thuc-tai-cuoc-thi-2026", "Cuộc thi ẩm thực") is False
    assert discover_mod._is_competition_relevant("https://ybox.vn/cuoc-thi/ai-hackathon-2026", "AI Hackathon 2026") is True


def test_parse_sitemap_xml_urlset_and_index() -> None:
    index_xml = """<?xml version="1.0" encoding="UTF-8"?>
    <sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
      <sitemap><loc>https://ybox.vn/sitemap-contests.xml</loc></sitemap>
    </sitemapindex>"""
    children, items = discover_mod.parse_sitemap_xml(index_xml, "https://ybox.vn/sitemap.xml")
    assert children == ["https://ybox.vn/sitemap-contests.xml"]
    assert items == []

    urlset_xml = """<?xml version="1.0" encoding="UTF-8"?>
    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
      <url>
        <loc>https://ybox.vn/cuoc-thi/ai-hackathon-2026?utm_source=test</loc>
        <lastmod>2026-11-20T10:00:00Z</lastmod>
      </url>
      <url>
        <loc>https://ybox.vn/tin-tuc/thoi-tiet-hom-nay</loc>
        <lastmod>2026-11-20T10:00:00Z</lastmod>
      </url>
    </urlset>"""
    children2, items2 = discover_mod.parse_sitemap_xml(urlset_xml, "https://ybox.vn/sitemap-contests.xml", lookback_days=30)
    assert children2 == []
    assert len(items2) == 1
    assert items2[0].canonical_url == "https://ybox.vn/cuoc-thi/ai-hackathon-2026"


def test_parse_rss_and_gdelt_and_hub_html() -> None:
    rss_xml = """<?xml version="1.0" encoding="UTF-8"?>
    <rss version="2.0">
      <channel>
        <title>Devpost</title>
        <item>
          <title>Vietnam AI Hackathon 2026</title>
          <link>https://devpost.com/vietnam-ai-2026?ref=rss</link>
          <description>Build AI agents for students</description>
        </item>
      </channel>
    </rss>"""
    rss_items = discover_mod.parse_rss_or_atom(rss_xml, "devpost_rss")
    assert len(rss_items) == 1
    assert rss_items[0].canonical_url == "https://devpost.com/vietnam-ai-2026"

    gdelt_payload = {
        "articles": [
            {"url": "https://tuoitre.vn/ai-challenge-2026-sinh-vien.htm", "title": "AI Challenge 2026", "seendate": "20261122T080000Z"},
            {"url": "https://example.edu.vn/lich-thi-cuoi-ky", "title": "Lịch thi cuối kỳ", "seendate": "20261122T080000Z"},
        ]
    }
    gdelt_items = discover_mod.parse_gdelt_response(gdelt_payload)
    assert len(gdelt_items) == 1
    assert gdelt_items[0].sources == ["gdelt_doc_v2"]

    hub = discover_mod.HubSourceConfig(name="ybox", url="https://ybox.vn/cuoc-thi", link_contains=("/cuoc-thi/",))
    html = """<html><body>
      <a href="/cuoc-thi/vietnam-datathon-2026">Vietnam Datathon 2026 cho sinh viên CNTT</a>
      <a href="/login">Đăng nhập</a>
    </body></html>"""
    hub_items = discover_mod.parse_hub_html(html, hub)
    assert len(hub_items) == 1
    assert hub_items[0].canonical_url == "https://ybox.vn/cuoc-thi/vietnam-datathon-2026"


def test_tier2_budget_cap_and_serper_fallback() -> None:
    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request.url.host)
        if request.url.host == "api.tavily.com":
            return httpx.Response(429, json={"error": "rate limit"})
        if request.url.host == "google.serper.dev":
            return httpx.Response(
                200,
                json={
                    "organic": [
                        {
                            "title": "HCMUTE AI Hackathon 2026",
                            "link": "https://fit.hcmute.edu.vn/hackathon-2026?utm_medium=search",
                            "snippet": "Cuộc thi lập trình AI cho sinh viên",
                        }
                    ]
                },
            )
        return httpx.Response(404)

    async def _run() -> tuple[list, object, list[str]]:
        transport = httpx.MockTransport(handler)
        async with httpx.AsyncClient(transport=transport) as client:
            return await discover_mod.run_tier2_discovery(
                client=client,
                provider_mode="auto",
                max_queries=3,
                tavily_key="tvly-test",
                exa_key="",
                serper_key="serper-test",
            )

    items, budget, errors = asyncio.run(_run())

    assert len(items) == 3
    assert items[0].canonical_url == "https://fit.hcmute.edu.vn/hackathon-2026"
    assert budget.tavily_queries_used == 0
    assert budget.serper_queries_used == 3
    assert len(errors) == 3
    assert "429" in errors[0]


def test_deduplication_and_http_304_check() -> None:
    c1 = discover_mod.DiscoveredCandidate(
        canonical_url="https://codetour.org/",
        raw_url="https://codetour.org/?utm_source=ybox",
        domain="codetour.org",
        title="Code Tour 2026",
        discovery_tier="tier1_zero_quota",
        sources=["hub:ybox"],
    )
    c2 = discover_mod.DiscoveredCandidate(
        canonical_url="https://codetour.org",
        raw_url="https://codetour.org",
        domain="codetour.org",
        title="Code Tour 2026 - Cuộc thi lập trình",
        discovery_tier="tier2_search_api",
        sources=["tavily"],
    )
    deduped, noise_count = discover_mod.deduplicate_and_rank([c1, c2], min_score=0.2)
    assert noise_count == 0
    assert len(deduped) == 1
    assert deduped[0].sources == ["hub:ybox", "tavily"]

    def head_handler(request: httpx.Request) -> httpx.Response:
        if request.headers.get("if-none-match") == '"v1"':
            return httpx.Response(304, headers={"ETag": '"v1"'})
        return httpx.Response(200, headers={"ETag": '"v2"'})

    cache = {"https://codetour.org/": {"etag": '"v1"', "last_modified": ""}}

    async def _run_head() -> tuple[list, list[str]]:
        async with httpx.AsyncClient(transport=httpx.MockTransport(head_handler)) as client:
            return await discover_mod.apply_conditional_http_checks(client, deduped, cache)

    checked, errors = asyncio.run(_run_head())

    assert errors == []
    assert checked[0].http_status == 304
    assert checked[0].needs_crawl is False


def test_upload_manifest_to_r2(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_s3 = MagicMock()
    monkeypatch.setattr(discover_mod.settings, "bucket_name", "acdp-test-bucket")
    monkeypatch.setattr(type(discover_mod.settings), "create_r2_client", lambda self: fake_s3)

    manifest = discover_mod.DiscoveryManifest(
        budget=discover_mod.QueryBudgetReport(max_queries_per_run=12),
        total_raw=1,
        total_deduplicated=1,
        candidates=[
            discover_mod.DiscoveredCandidate(
                canonical_url="https://codetour.org",
                raw_url="https://codetour.org",
                domain="codetour.org",
                discovery_tier="tier1_zero_quota",
                sources=["gdelt_doc_v2"],
                relevance_score=0.75,
            )
        ],
    )
    latest_key, snapshot_key = discover_mod.upload_manifest_to_r2(manifest, http_cache={"https://codetour.org": {"etag": "1"}})
    assert latest_key == "bronze/_discovery/latest_manifest.json"
    assert snapshot_key.startswith("bronze/_discovery/year=")
    assert fake_s3.put_object.call_count == 3
    first_call_body = json.loads(fake_s3.put_object.call_args_list[0].kwargs["Body"].decode("utf-8"))
    assert first_call_body["total_deduplicated"] == 1
