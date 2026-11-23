"""TASK-ING-03: 3-Tier Academic Competition URL Discovery Module (ACDP v2).

Implements the 3-tier discovery architecture validated in TASK-ING-01:
- Tier 1 (Zero Quota, 0 VND): Sitemap XML, RSS/Atom feeds, GDELT Doc 2.0 API,
  and public Vietnamese competition hubs (ybox.vn, khoahoctre.com.vn, vnoi.info,
  topdev.vn, lu.ma).
- Tier 2 (Free-Tier Search APIs, < 5% monthly cap): Tavily, Exa.ai, and Serper.dev
  fallback with strict per-run query budget enforcement.
- Tier 3 (Pre-Crawl Gatekeeper): URL canonicalization, academic noise filtering,
  multi-source deduplication, relevance scoring, HTTP HEAD/ETag conditional checks,
  and direct Cloudflare R2 manifest persistence (DIR-021).
"""

from __future__ import annotations

import argparse
import asyncio
import json
import re
import sys
import uuid
from datetime import UTC, datetime, timedelta
from typing import Literal
from urllib.parse import parse_qsl, urlencode, urljoin, urlparse, urlunparse

import defusedxml.ElementTree as ET
import httpx
from bs4 import BeautifulSoup
from pydantic import BaseModel, Field

from acdp.config import settings
from acdp.v2.discovery_sources import (
    CURATED_SEED_URLS,
    DEFAULT_GDELT_QUERIES,
    DEFAULT_RSS_FEEDS,
    DEFAULT_SITEMAP_URLS,
    DEFAULT_TIER2_QUERIES,
    DEFAULT_VIETNAM_HUBS,
    NOISE_KEYWORDS,
    RELEVANCE_KEYWORDS_HIGH,
    RELEVANCE_KEYWORDS_MEDIUM,
    STATIC_ASSET_EXTENSIONS,
    TECH_DOMAIN_KEYWORDS,
    TRACKING_QUERY_PARAMS,
    HubSourceConfig,
)

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

R2_DISCOVERY_LATEST_KEY = "bronze/_discovery/latest_manifest.json"
R2_DISCOVERY_HTTP_CACHE_KEY = "bronze/_discovery/http_cache.json"

DEFAULT_HTTP_HEADERS = {
    "User-Agent": "ACDP-DiscoveryBot/2.0 (+https://github.com/acdp-platform; academic-research)",
    "Accept": "text/html,application/xhtml+xml,application/xml,application/json;q=0.9,*/*;q=0.8",
}

# ---------------------------------------------------------------------------
# Pydantic v2 Contracts
# ---------------------------------------------------------------------------


class DiscoveredCandidate(BaseModel):
    """Deduplicated competition URL candidate ready for Bronze ingestion."""

    canonical_url: str
    raw_url: str
    domain: str
    title: str = ""
    snippet: str = ""
    discovery_tier: Literal["tier1_zero_quota", "tier2_search_api", "seed_baseline"]
    sources: list[str] = Field(default_factory=list)
    published_at: str | None = None
    lastmod: str | None = None
    etag: str | None = None
    last_modified_header: str | None = None
    http_status: int | None = None
    needs_crawl: bool = True
    relevance_score: float = Field(default=0.0, ge=0.0, le=1.0)
    discovered_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())


class QueryBudgetReport(BaseModel):
    """Tracks Tier 2 API usage against the < 5% Free-Tier monthly cap."""

    max_queries_per_run: int = 12
    tavily_queries_used: int = 0
    tavily_credits_used: int = 0
    exa_queries_used: int = 0
    serper_queries_used: int = 0
    tavily_monthly_pct_projected: float = 0.0
    exa_monthly_pct_projected: float = 0.0


class DiscoveryManifest(BaseModel):
    """Complete output manifest produced by a 3-tier discovery run."""

    run_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    generated_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    budget: QueryBudgetReport
    total_raw: int = 0
    total_filtered_noise: int = 0
    total_deduplicated: int = 0
    errors: list[str] = Field(default_factory=list)
    candidates: list[DiscoveredCandidate] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# URL Canonicalization, Filtering & Scoring
# ---------------------------------------------------------------------------


def canonicalize_url(raw_url: str) -> str:
    """Normalize URL scheme/host, strip tracking parameters, fragments, and redundant slashes."""
    stripped = raw_url.strip()
    if not stripped:
        return ""
    parsed = urlparse(stripped)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return ""

    scheme = parsed.scheme.lower()
    netloc = parsed.netloc.lower()
    if netloc.endswith(":80") and scheme == "http":
        netloc = netloc[:-3]
    elif netloc.endswith(":443") and scheme == "https":
        netloc = netloc[:-4]

    cleaned_params = [
        (k, v)
        for k, v in parse_qsl(parsed.query, keep_blank_values=False)
        if k.lower() not in TRACKING_QUERY_PARAMS and not k.lower().startswith("utm_")
    ]
    query = urlencode(sorted(cleaned_params))

    path = parsed.path or "/"
    if path != "/" and path.endswith("/"):
        path = path.rstrip("/")

    return urlunparse((scheme, netloc, path, "", query, ""))


def is_noise_url(url: str, title: str = "", snippet: str = "") -> bool:
    """Return True if URL points to static assets, auth pages, or non-competition academic noise."""
    lowered_url = url.lower()
    path_only = urlparse(lowered_url).path
    if any(path_only.endswith(ext) for ext in STATIC_ASSET_EXTENSIONS):
        return True

    combined = f"{lowered_url} {title.lower()} {snippet.lower()}"
    return any(noise in combined for noise in NOISE_KEYWORDS)


def compute_relevance_score(
    url: str,
    title: str = "",
    snippet: str = "",
    source_count: int = 1,
    discovery_tier: str = "tier1_zero_quota",
) -> float:
    """Compute heuristic relevance score in [0.0, 1.0] for competition prioritization."""
    text = f"{url.lower()} {title.lower()} {snippet.lower()}"
    score = 0.15

    high_hits = sum(1 for kw in RELEVANCE_KEYWORDS_HIGH if kw in text)
    med_hits = sum(1 for kw in RELEVANCE_KEYWORDS_MEDIUM if _contains_keyword(text, kw))
    score += min(0.42, high_hits * 0.18)
    score += min(0.22, med_hits * 0.05)

    parsed = urlparse(url)
    domain = parsed.netloc.lower()
    path = parsed.path.strip("/")
    if domain.endswith(".edu.vn") or domain.endswith(".gov.vn"):
        score += 0.08
    if not path or any(tok in domain for tok in ("hackathon", "datathon", "challenge", "codetour", "thucchien")):
        score += 0.12
    if discovery_tier == "seed_baseline":
        score += 0.25
    if source_count > 1:
        score += min(0.15, (source_count - 1) * 0.08)

    return round(min(1.0, score), 4)


_SHORT_BOUNDARY_KEYWORDS = frozenset({"ai", "data", "cntt", "icpc", "olp"})
_SHORT_PATTERNS = {kw: re.compile(rf"\b{re.escape(kw)}\b") for kw in _SHORT_BOUNDARY_KEYWORDS}


def _contains_keyword(text: str, kw: str) -> bool:
    if kw in _SHORT_PATTERNS:
        return bool(_SHORT_PATTERNS[kw].search(text))
    return kw in text


def _is_competition_relevant(url: str, title: str = "", snippet: str = "") -> bool:
    """Quick gate to ensure Tier 1 bulk feeds retain only tech/academic competitions."""
    text = f"{url.lower()} {title.lower()} {snippet.lower()}"
    has_tech = any(_contains_keyword(text, kw) for kw in TECH_DOMAIN_KEYWORDS)
    has_contest = any(kw in text for kw in (*RELEVANCE_KEYWORDS_HIGH, "cuộc thi", "cuoc-thi", "hội thi", "hoi-thi", "challenge"))
    return has_tech and has_contest


# ---------------------------------------------------------------------------
# Tier 1: Zero-Quota Discovery (Sitemap, RSS/Atom, GDELT Doc 2.0, Hubs)
# ---------------------------------------------------------------------------


def parse_sitemap_xml(
    xml_text: str,
    base_url: str,
    lookback_days: int = 60,
) -> tuple[list[str], list[DiscoveredCandidate]]:
    """Parse Sitemap XML (<urlset> or <sitemapindex>), returning child sitemap URLs and candidates."""
    root = ET.fromstring(xml_text)
    tag_name = root.tag.rsplit("}", 1)[-1].lower()
    cutoff = datetime.now(UTC) - timedelta(days=lookback_days)

    child_sitemaps: list[str] = []
    candidates: list[DiscoveredCandidate] = []

    if tag_name == "sitemapindex":
        for sm in root:
            loc = _find_xml_text(sm, "loc")
            if loc:
                child_sitemaps.append(loc.strip())
        return child_sitemaps, candidates

    if tag_name == "urlset":
        domain = urlparse(base_url).netloc.lower()
        for url_el in root:
            loc = _find_xml_text(url_el, "loc")
            if not loc:
                continue
            lastmod_raw = _find_xml_text(url_el, "lastmod")
            if lastmod_raw and not _is_recent_iso_date(lastmod_raw, cutoff):
                continue

            canon = canonicalize_url(loc)
            if not canon or is_noise_url(canon):
                continue
            if not _is_competition_relevant(canon):
                continue

            candidates.append(
                DiscoveredCandidate(
                    canonical_url=canon,
                    raw_url=loc.strip(),
                    domain=urlparse(canon).netloc,
                    discovery_tier="tier1_zero_quota",
                    sources=[f"sitemap:{domain}"],
                    lastmod=lastmod_raw,
                )
            )

    return child_sitemaps, candidates


def parse_rss_or_atom(xml_text: str, source_name: str) -> list[DiscoveredCandidate]:
    """Parse RSS 2.0 (<item>) or Atom (<entry>) XML into DiscoveredCandidate items."""
    root = ET.fromstring(xml_text)
    root_tag = root.tag.rsplit("}", 1)[-1].lower()
    candidates: list[DiscoveredCandidate] = []

    if root_tag == "rss":
        channel = next((c for c in root if c.tag.rsplit("}", 1)[-1].lower() == "channel"), None)
        items = [el for el in (channel or []) if el.tag.rsplit("}", 1)[-1].lower() == "item"]
        for item in items:
            link = _find_xml_text(item, "link")
            title = _find_xml_text(item, "title") or ""
            desc = _find_xml_text(item, "description") or ""
            pub_date = _find_xml_text(item, "pubDate")
            if not link:
                continue
            canon = canonicalize_url(link)
            if not canon or is_noise_url(canon, title, desc):
                continue
            candidates.append(
                DiscoveredCandidate(
                    canonical_url=canon,
                    raw_url=link.strip(),
                    domain=urlparse(canon).netloc,
                    title=title.strip(),
                    snippet=desc.strip()[:400],
                    discovery_tier="tier1_zero_quota",
                    sources=[source_name],
                    published_at=pub_date,
                )
            )
    elif root_tag == "feed":
        entries = [el for el in root if el.tag.rsplit("}", 1)[-1].lower() == "entry"]
        for entry in entries:
            link = ""
            for child in entry:
                if child.tag.rsplit("}", 1)[-1].lower() == "link":
                    href = child.attrib.get("href", "").strip()
                    if href:
                        link = href
                        break
                    if child.text:
                        link = child.text.strip()
                        break
            title = _find_xml_text(entry, "title") or ""
            summary = _find_xml_text(entry, "summary") or _find_xml_text(entry, "content") or ""
            updated = _find_xml_text(entry, "updated") or _find_xml_text(entry, "published")
            if not link:
                continue
            canon = canonicalize_url(link)
            if not canon or is_noise_url(canon, title, summary):
                continue
            candidates.append(
                DiscoveredCandidate(
                    canonical_url=canon,
                    raw_url=link,
                    domain=urlparse(canon).netloc,
                    title=title.strip(),
                    snippet=summary.strip()[:400],
                    discovery_tier="tier1_zero_quota",
                    sources=[source_name],
                    published_at=updated,
                )
            )

    return candidates


def parse_gdelt_response(payload: dict) -> list[DiscoveredCandidate]:
    """Convert GDELT Doc 2.0 JSON article list into DiscoveredCandidate items."""
    articles = payload.get("articles") or []
    candidates: list[DiscoveredCandidate] = []
    for art in articles:
        raw_url = str(art.get("url") or "").strip()
        title = str(art.get("title") or "").strip()
        if not raw_url:
            continue
        canon = canonicalize_url(raw_url)
        if not canon or is_noise_url(canon, title):
            continue
        candidates.append(
            DiscoveredCandidate(
                canonical_url=canon,
                raw_url=raw_url,
                domain=urlparse(canon).netloc,
                title=title,
                discovery_tier="tier1_zero_quota",
                sources=["gdelt_doc_v2"],
                published_at=art.get("seendate"),
            )
        )
    return candidates


def parse_hub_html(html_text: str, hub: HubSourceConfig) -> list[DiscoveredCandidate]:
    """Extract competition links from public Vietnamese/event hub HTML pages."""
    soup = BeautifulSoup(html_text, "lxml")
    candidates: list[DiscoveredCandidate] = []

    for anchor in soup.find_all("a", href=True):
        href = str(anchor["href"]).strip()
        if not href or href.startswith(("#", "javascript:", "mailto:", "tel:")):
            continue
        absolute_url = urljoin(hub.url, href)
        canon = canonicalize_url(absolute_url)
        if not canon:
            continue

        title = " ".join(anchor.get_text(" ", strip=True).split())
        if len(title) < 8:
            continue
        if is_noise_url(canon, title):
            continue

        if hub.link_contains and not any(token in canon.lower() for token in hub.link_contains):
            continue
        if not _is_competition_relevant(canon, title):
            continue

        candidates.append(
            DiscoveredCandidate(
                canonical_url=canon,
                raw_url=absolute_url,
                domain=urlparse(canon).netloc,
                title=title[:200],
                discovery_tier="tier1_zero_quota",
                sources=[f"hub:{hub.name}"],
            )
        )

    return candidates


async def run_tier1_discovery(
    client: httpx.AsyncClient,
    sitemaps: list[str] | None = None,
    rss_feeds: list[tuple[str, str]] | None = None,
    gdelt_queries: list[str] | None = None,
    hubs: list[HubSourceConfig] | None = None,
) -> tuple[list[DiscoveredCandidate], list[str]]:
    """Execute all Tier 1 zero-quota sources concurrently with per-source error isolation."""
    results: list[DiscoveredCandidate] = []
    errors: list[str] = []

    async def _fetch_sitemap(sm_url: str, depth: int = 0) -> None:
        if depth > 1:
            return
        try:
            resp = await client.get(sm_url, timeout=15.0)
            resp.raise_for_status()
            if "<urlset" not in resp.text and "<sitemapindex" not in resp.text:
                errors.append(f"[Tier1:Sitemap] {sm_url} -> Not a valid XML sitemap")
                return
            children, items = parse_sitemap_xml(resp.text, sm_url)
            results.extend(items)
            for child in children[:5]:
                await _fetch_sitemap(child, depth + 1)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"[Tier1:Sitemap] {sm_url} -> {type(exc).__name__}: {exc}")

    async def _fetch_rss(name: str, feed_url: str) -> None:
        try:
            resp = await client.get(feed_url, timeout=15.0)
            resp.raise_for_status()
            results.extend(parse_rss_or_atom(resp.text, name))
        except Exception as exc:  # noqa: BLE001
            errors.append(f"[Tier1:RSS] {name} ({feed_url}) -> {type(exc).__name__}: {exc}")

    async def _fetch_gdelt_batch(queries: list[str]) -> None:
        # GDELT Doc 2.0 enforces ~1 request per 5 seconds; run sequentially to avoid 429.
        for idx, query in enumerate(queries):
            if idx > 0:
                await asyncio.sleep(5.5)
            try:
                resp = await client.get(
                    "https://api.gdeltproject.org/api/v2/doc/doc",
                    params={
                        "query": query,
                        "mode": "artlist",
                        "format": "json",
                        "timespan": "1m",
                        "maxrecords": 40,
                    },
                    timeout=15.0,
                )
                resp.raise_for_status()
                results.extend(parse_gdelt_response(resp.json()))
            except Exception as exc:  # noqa: BLE001
                errors.append(f"[Tier1:GDELT] query={query!r} -> {type(exc).__name__}: {exc}")

    async def _fetch_hub(hub: HubSourceConfig) -> None:
        try:
            resp = await client.get(hub.url, timeout=15.0)
            resp.raise_for_status()
            results.extend(parse_hub_html(resp.text, hub))
        except Exception as exc:  # noqa: BLE001
            errors.append(f"[Tier1:Hub] {hub.name} ({hub.url}) -> {type(exc).__name__}: {exc}")

    gdelt_list = gdelt_queries if gdelt_queries is not None else DEFAULT_GDELT_QUERIES
    tasks = [
        *(_fetch_sitemap(u) for u in (sitemaps if sitemaps is not None else DEFAULT_SITEMAP_URLS)),
        *(_fetch_rss(name, u) for name, u in (rss_feeds if rss_feeds is not None else DEFAULT_RSS_FEEDS)),
        *(_fetch_hub(h) for h in (hubs if hubs is not None else DEFAULT_VIETNAM_HUBS)),
    ]
    if gdelt_list:
        tasks.append(_fetch_gdelt_batch(gdelt_list))
    if tasks:
        await asyncio.gather(*tasks)

    return results, errors


# ---------------------------------------------------------------------------
# Tier 2: Free-Tier Search APIs (Tavily, Exa.ai, Serper.dev Fallback)
# ---------------------------------------------------------------------------


async def search_tavily(
    client: httpx.AsyncClient,
    query: str,
    api_key: str,
    max_results: int = 8,
) -> list[DiscoveredCandidate]:
    """Query Tavily REST API (search_depth='basic' = 1 credit/query)."""
    resp = await client.post(
        "https://api.tavily.com/search",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "query": query,
            "search_depth": "basic",
            "topic": "general",
            "max_results": max_results,
            "include_answer": False,
            "include_raw_content": False,
        },
        timeout=20.0,
    )
    resp.raise_for_status()
    data = resp.json()
    items: list[DiscoveredCandidate] = []
    for row in data.get("results") or []:
        raw_url = str(row.get("url") or "").strip()
        title = str(row.get("title") or "").strip()
        snippet = str(row.get("content") or "").strip()
        canon = canonicalize_url(raw_url)
        if not canon or is_noise_url(canon, title, snippet):
            continue
        items.append(
            DiscoveredCandidate(
                canonical_url=canon,
                raw_url=raw_url,
                domain=urlparse(canon).netloc,
                title=title,
                snippet=snippet[:400],
                discovery_tier="tier2_search_api",
                sources=["tavily"],
                published_at=row.get("published_date"),
            )
        )
    return items


async def search_exa(
    client: httpx.AsyncClient,
    query: str,
    api_key: str,
    num_results: int = 8,
) -> list[DiscoveredCandidate]:
    """Query Exa.ai REST Search API."""
    resp = await client.post(
        "https://api.exa.ai/search",
        headers={
            "x-api-key": api_key,
            "Content-Type": "application/json",
        },
        json={
            "query": query,
            "type": "auto",
            "numResults": num_results,
            "contents": {"highlights": True},
        },
        timeout=20.0,
    )
    resp.raise_for_status()
    data = resp.json()
    items: list[DiscoveredCandidate] = []
    for row in data.get("results") or []:
        raw_url = str(row.get("url") or "").strip()
        title = str(row.get("title") or "").strip()
        highlights = row.get("highlights") or []
        snippet = " ".join(str(h) for h in highlights) if highlights else str(row.get("text") or "")
        canon = canonicalize_url(raw_url)
        if not canon or is_noise_url(canon, title, snippet):
            continue
        items.append(
            DiscoveredCandidate(
                canonical_url=canon,
                raw_url=raw_url,
                domain=urlparse(canon).netloc,
                title=title,
                snippet=snippet[:400],
                discovery_tier="tier2_search_api",
                sources=["exa"],
                published_at=row.get("publishedDate"),
            )
        )
    return items


async def search_serper(
    client: httpx.AsyncClient,
    query: str,
    api_key: str,
    num_results: int = 8,
) -> list[DiscoveredCandidate]:
    """Query Serper.dev Google SERP fallback API."""
    resp = await client.post(
        "https://google.serper.dev/search",
        headers={
            "X-API-KEY": api_key,
            "Content-Type": "application/json",
        },
        json={"q": query, "gl": "vn", "hl": "vi", "num": num_results},
        timeout=20.0,
    )
    resp.raise_for_status()
    data = resp.json()
    items: list[DiscoveredCandidate] = []
    for row in data.get("organic") or []:
        raw_url = str(row.get("link") or "").strip()
        title = str(row.get("title") or "").strip()
        snippet = str(row.get("snippet") or "").strip()
        canon = canonicalize_url(raw_url)
        if not canon or is_noise_url(canon, title, snippet):
            continue
        items.append(
            DiscoveredCandidate(
                canonical_url=canon,
                raw_url=raw_url,
                domain=urlparse(canon).netloc,
                title=title,
                snippet=snippet[:400],
                discovery_tier="tier2_search_api",
                sources=["serper"],
                published_at=row.get("date"),
            )
        )
    return items


async def run_tier2_discovery(
    client: httpx.AsyncClient,
    provider_mode: Literal["auto", "tavily", "exa", "serper", "none"] = "auto",
    max_queries: int = 12,
    include_pdf_queries: bool = False,
    tavily_key: str = "",
    exa_key: str = "",
    serper_key: str = "",
) -> tuple[list[DiscoveredCandidate], QueryBudgetReport, list[str]]:
    """Execute budget-capped Tier 2 Search API queries with error-only fallback."""
    budget = QueryBudgetReport(max_queries_per_run=max_queries)
    errors: list[str] = []
    results: list[DiscoveredCandidate] = []

    if provider_mode == "none" or max_queries <= 0:
        return results, budget, errors

    available: list[str] = []
    if provider_mode == "auto":
        if tavily_key:
            available.append("tavily")
        if exa_key:
            available.append("exa")
        if serper_key:
            available.append("serper")
    else:
        key_map = {"tavily": tavily_key, "exa": exa_key, "serper": serper_key}
        if key_map.get(provider_mode):
            available.append(provider_mode)

    if not available:
        errors.append(
            "[Tier2:Config] Không có API key hợp lệ (TAVILY_API_KEY / EXA_API_KEY / SERPER_API_KEY). "
            "Bỏ qua Tier 2 và chỉ sử dụng kết quả Tier 1."
        )
        return results, budget, errors

    queries = [
        (tag, q)
        for tag, q in DEFAULT_TIER2_QUERIES
        if include_pdf_queries or not tag.startswith("D_")
    ][:max_queries]

    for idx, (tag, query) in enumerate(queries):
        # Round-robin between Tavily and Exa when both are configured; Serper only as fallback
        primary_pool = [p for p in available if p in {"tavily", "exa"}]
        if primary_pool:
            ordered_providers = [primary_pool[idx % len(primary_pool)]] + [
                p for p in available if p != primary_pool[idx % len(primary_pool)]
            ]
        else:
            ordered_providers = list(available)

        for prov in ordered_providers:
            try:
                if prov == "tavily":
                    items = await search_tavily(client, query, tavily_key)
                    budget.tavily_queries_used += 1
                    budget.tavily_credits_used += 1
                elif prov == "exa":
                    items = await search_exa(client, query, exa_key)
                    budget.exa_queries_used += 1
                else:
                    items = await search_serper(client, query, serper_key)
                    budget.serper_queries_used += 1

                results.extend(items)
                break
            except Exception as exc:  # noqa: BLE001
                errors.append(f"[Tier2:{prov}] {tag} failed -> {exc}")

    # Monthly projection assuming 4 weekly runs/month (Tavily: 1000/mo, Exa: 2500/mo)
    budget.tavily_monthly_pct_projected = round((budget.tavily_credits_used * 4 / 1000.0) * 100.0, 2)
    budget.exa_monthly_pct_projected = round((budget.exa_queries_used * 4 / 2500.0) * 100.0, 2)
    return results, budget, errors


# ---------------------------------------------------------------------------
# Tier 3: Deduplication, Conditional HTTP Check & R2 Manifest Persistence
# ---------------------------------------------------------------------------


def deduplicate_and_rank(
    raw_candidates: list[DiscoveredCandidate],
    min_score: float = 0.25,
) -> tuple[list[DiscoveredCandidate], int]:
    """Merge duplicate canonical URLs across tiers, compute scores, and sort descending."""
    merged: dict[str, DiscoveredCandidate] = {}
    filtered_noise = 0

    for item in raw_candidates:
        canon = canonicalize_url(item.canonical_url or item.raw_url)
        if not canon or is_noise_url(canon, item.title, item.snippet):
            filtered_noise += 1
            continue

        if canon not in merged:
            merged[canon] = item.model_copy(update={"canonical_url": canon})
            continue

        existing = merged[canon]
        combined_sources = sorted(set(existing.sources) | set(item.sources))
        best_title = existing.title if len(existing.title) >= len(item.title) else item.title
        best_snippet = existing.snippet if len(existing.snippet) >= len(item.snippet) else item.snippet
        best_tier = (
            "seed_baseline"
            if "seed_baseline" in {existing.discovery_tier, item.discovery_tier}
            else existing.discovery_tier
        )
        merged[canon] = existing.model_copy(
            update={
                "sources": combined_sources,
                "title": best_title,
                "snippet": best_snippet,
                "discovery_tier": best_tier,
                "published_at": existing.published_at or item.published_at,
                "lastmod": existing.lastmod or item.lastmod,
            }
        )

    scored: list[DiscoveredCandidate] = []
    for candidate in merged.values():
        score = compute_relevance_score(
            url=candidate.canonical_url,
            title=candidate.title,
            snippet=candidate.snippet,
            source_count=len(candidate.sources),
            discovery_tier=candidate.discovery_tier,
        )
        if score >= min_score or candidate.discovery_tier == "seed_baseline":
            scored.append(candidate.model_copy(update={"relevance_score": score}))

    scored.sort(key=lambda c: (c.relevance_score, len(c.sources)), reverse=True)
    return scored, filtered_noise


async def apply_conditional_http_checks(
    client: httpx.AsyncClient,
    candidates: list[DiscoveredCandidate],
    http_cache: dict[str, dict[str, str]],
    max_checks: int = 30,
) -> tuple[list[DiscoveredCandidate], list[str]]:
    """Run HTTP HEAD with ETag / If-Modified-Since to skip unchanged pages (304)."""
    errors: list[str] = []
    semaphore = asyncio.Semaphore(6)

    async def _check_one(idx: int, cand: DiscoveredCandidate) -> DiscoveredCandidate:
        if idx >= max_checks:
            return cand
        cached = http_cache.get(cand.canonical_url, {})
        headers: dict[str, str] = {}
        if cached.get("etag"):
            headers["If-None-Match"] = cached["etag"]
        if cached.get("last_modified"):
            headers["If-Modified-Since"] = cached["last_modified"]

        async with semaphore:
            try:
                resp = await client.head(cand.canonical_url, headers=headers, timeout=10.0)
                etag = resp.headers.get("etag") or cached.get("etag")
                last_mod = resp.headers.get("last-modified") or cached.get("last_modified")
                if etag or last_mod:
                    http_cache[cand.canonical_url] = {
                        "etag": etag or "",
                        "last_modified": last_mod or "",
                    }
                return cand.model_copy(
                    update={
                        "http_status": resp.status_code,
                        "etag": etag,
                        "last_modified_header": last_mod,
                        "needs_crawl": resp.status_code != 304 and resp.status_code < 400,
                    }
                )
            except Exception as exc:  # noqa: BLE001
                errors.append(f"[Tier3:HEAD] {cand.canonical_url} -> {exc}")
                return cand

    updated = await asyncio.gather(*(_check_one(i, c) for i, c in enumerate(candidates)))
    return list(updated), errors


def load_http_cache_from_r2() -> dict[str, dict[str, str]]:
    """Load persisted ETag / Last-Modified cache from Cloudflare R2, if present."""
    try:
        s3 = settings.create_r2_client()
        obj = s3.get_object(Bucket=settings.bucket_name, Key=R2_DISCOVERY_HTTP_CACHE_KEY)
        return json.loads(obj["Body"].read().decode("utf-8"))
    except Exception:  # noqa: BLE001
        return {}


def upload_manifest_to_r2(
    manifest: DiscoveryManifest,
    http_cache: dict[str, dict[str, str]] | None = None,
) -> tuple[str, str]:
    """Upload DiscoveryManifest JSON (latest + daily snapshot) directly to Cloudflare R2."""
    s3 = settings.create_r2_client()
    now = datetime.now(UTC)
    ts = int(now.timestamp())
    snapshot_key = (
        f"bronze/_discovery/year={now.year}/month={now.strftime('%m')}/day={now.strftime('%d')}/"
        f"manifest_{ts}.json"
    )
    payload_bytes = manifest.model_dump_json(indent=2).encode("utf-8")

    for key in (R2_DISCOVERY_LATEST_KEY, snapshot_key):
        s3.put_object(
            Bucket=settings.bucket_name,
            Key=key,
            Body=payload_bytes,
            ContentType="application/json; charset=utf-8",
            Metadata={"layer": "bronze", "component": "discovery_v2"},
        )

    if http_cache is not None:
        s3.put_object(
            Bucket=settings.bucket_name,
            Key=R2_DISCOVERY_HTTP_CACHE_KEY,
            Body=json.dumps(http_cache, indent=2, ensure_ascii=False).encode("utf-8"),
            ContentType="application/json; charset=utf-8",
            Metadata={"layer": "bronze", "component": "discovery_http_cache"},
        )

    return R2_DISCOVERY_LATEST_KEY, snapshot_key


# ---------------------------------------------------------------------------
# Helpers & Orchestration
# ---------------------------------------------------------------------------


def _find_xml_text(parent: object, local_name: str) -> str | None:
    target = local_name.lower()
    for child in parent:  # type: ignore[attr-defined]
        if child.tag.rsplit("}", 1)[-1].lower() == target and child.text:
            return child.text.strip()
    return None


def _is_recent_iso_date(raw_date: str, cutoff: datetime) -> bool:
    cleaned = raw_date.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(cleaned[:19])
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=UTC)
        return parsed >= cutoff
    except ValueError:
        return True


def build_seed_candidates() -> list[DiscoveredCandidate]:
    """Return baseline curated URLs used in Phase 1 TLCN."""
    items: list[DiscoveredCandidate] = []
    for url in CURATED_SEED_URLS:
        canon = canonicalize_url(url)
        if canon:
            items.append(
                DiscoveredCandidate(
                    canonical_url=canon,
                    raw_url=url,
                    domain=urlparse(canon).netloc,
                    discovery_tier="seed_baseline",
                    sources=["curated_seed"],
                )
            )
    return items


async def run_discovery_pipeline(
    tier1_only: bool = False,
    tier2_provider: Literal["auto", "tavily", "exa", "serper", "none"] = "auto",
    max_queries: int | None = None,
    include_pdf_queries: bool = False,
    include_seeds: bool = False,
    check_http: bool = False,
    min_score: float = 0.25,
    limit: int = 50,
    dry_run: bool = False,
) -> DiscoveryManifest:
    """Orchestrate 3-tier URL discovery and persist manifest to Cloudflare R2."""
    cap = max_queries if max_queries is not None else settings.discovery_max_queries_per_run
    all_raw: list[DiscoveredCandidate] = []
    all_errors: list[str] = []

    if include_seeds:
        all_raw.extend(build_seed_candidates())

    async with httpx.AsyncClient(headers=DEFAULT_HTTP_HEADERS, follow_redirects=True) as client:
        tier1_items, tier1_errors = await run_tier1_discovery(client)
        all_raw.extend(tier1_items)
        all_errors.extend(tier1_errors)

        mode: Literal["auto", "tavily", "exa", "serper", "none"] = "none" if tier1_only else tier2_provider
        tier2_items, budget, tier2_errors = await run_tier2_discovery(
            client=client,
            provider_mode=mode,
            max_queries=cap,
            include_pdf_queries=include_pdf_queries,
            tavily_key=settings.tavily_api_key,
            exa_key=settings.exa_api_key,
            serper_key=settings.serper_api_key,
        )
        all_raw.extend(tier2_items)
        all_errors.extend(tier2_errors)

        deduped, filtered_noise = deduplicate_and_rank(all_raw, min_score=min_score)
        if limit > 0:
            deduped = deduped[:limit]

        http_cache: dict[str, dict[str, str]] | None = None
        if check_http and deduped:
            http_cache = {} if dry_run else load_http_cache_from_r2()
            deduped, head_errors = await apply_conditional_http_checks(client, deduped, http_cache)
            all_errors.extend(head_errors)

    manifest = DiscoveryManifest(
        budget=budget,
        total_raw=len(all_raw),
        total_filtered_noise=filtered_noise,
        total_deduplicated=len(deduped),
        errors=all_errors,
        candidates=deduped,
    )

    if not dry_run:
        latest_key, snapshot_key = upload_manifest_to_r2(manifest, http_cache=http_cache)
        print(f"[R2] Uploaded discovery manifest -> s3://{settings.bucket_name}/{latest_key}")
        print(f"[R2] Snapshot saved -> s3://{settings.bucket_name}/{snapshot_key}")

    return manifest


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="ACDP v2 3-Tier Academic Competition URL Discovery")
    parser.add_argument("--tier1-only", action="store_true", help="Run only Tier 1 zero-quota sources")
    parser.add_argument(
        "--tier2-provider",
        choices=["auto", "tavily", "exa", "serper", "none"],
        default="auto",
        help="Tier 2 Search API provider selection",
    )
    parser.add_argument("--max-queries", type=int, default=None, help="Max Tier 2 queries per run (default: 12)")
    parser.add_argument("--include-pdf", action="store_true", help="Include Group D PDF rulebook search queries")
    parser.add_argument("--include-seeds", action="store_true", help="Merge curated Phase 1 TLCN seed URLs")
    parser.add_argument("--check-http", action="store_true", help="Run HTTP HEAD ETag/If-Modified-Since checks")
    parser.add_argument("--min-score", type=float, default=0.25, help="Minimum relevance score [0.0-1.0]")
    parser.add_argument("--limit", type=int, default=50, help="Max candidates to keep in manifest")
    parser.add_argument("--dry-run", action="store_true", help="Print manifest summary without uploading to R2")
    return parser.parse_args(argv)


def main() -> None:
    args = _parse_args()
    manifest = asyncio.run(
        run_discovery_pipeline(
            tier1_only=args.tier1_only,
            tier2_provider=args.tier2_provider,
            max_queries=args.max_queries,
            include_pdf_queries=args.include_pdf,
            include_seeds=args.include_seeds,
            check_http=args.check_http,
            min_score=args.min_score,
            limit=args.limit,
            dry_run=args.dry_run,
        )
    )
    print(
        f"[DISCOVERY] raw={manifest.total_raw} noise_filtered={manifest.total_filtered_noise} "
        f"deduplicated={manifest.total_deduplicated} errors={len(manifest.errors)}"
    )
    print(
        f"[BUDGET] tavily={manifest.budget.tavily_queries_used} ({manifest.budget.tavily_monthly_pct_projected}%/mo) | "
        f"exa={manifest.budget.exa_queries_used} ({manifest.budget.exa_monthly_pct_projected}%/mo) | "
        f"serper={manifest.budget.serper_queries_used}"
    )
    for err in manifest.errors:
        print(f"  [WARN] {err}")
    for idx, cand in enumerate(manifest.candidates[:15], 1):
        print(f"  {idx:02d}. [{cand.relevance_score:.2f}] ({','.join(cand.sources)}) {cand.canonical_url}")


if __name__ == "__main__":
    main()
