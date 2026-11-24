"""TASK-BRZ-02: Bronze Layer Raw Rendered HTML Crawler (ACDP v2).

Implements the Bronze Purity decision from TASK-BRZ-01:
- Renders JS/SPA competition pages via Playwright + AdaptiveCrawler.
- Preserves 100% Raw Rendered HTML (result.html) including <head>, JSON-LD,
  og:* metadata, and Next.js state payloads.
- Packages multi-page AdaptiveCrawler results with `ACDP_PAGE_BOUNDARY` markers.
- Uploads directly to Cloudflare R2 `bronze/` as `.html` objects
  (`text/html; charset=utf-8`) with zero local disk persistence (DIR-021).
"""

from __future__ import annotations

import argparse
import asyncio
import html
import json
import os
import random
import re
import sys
from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any
from urllib.parse import urlparse

from crawl4ai import (
    AdaptiveConfig,
    AdaptiveCrawler,
    AsyncWebCrawler,
    BrowserConfig,
    CrawlerRunConfig,
    LLMConfig,
)
from crawl4ai.adaptive_crawler import EmbeddingStrategy, LinkPreviewConfig
from crawl4ai.utils import perform_completion_with_backoff
from dotenv import find_dotenv, load_dotenv

from acdp.config import settings

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv(find_dotenv(usecwd=True))

PAGE_BOUNDARY_PATTERN = re.compile(r"<!--\s*ACDP_PAGE_BOUNDARY\s+url=\"[^\"]*\"\s*-->")

DEFAULT_URLS: list[str] = [
    "https://codetour.org/",
    "https://www.vietnamaichallenge.com/",
    "https://datadna.onyxdata.co.uk/challenges/",
    "https://itconsultantchallenge.org/vi",
    "https://rmit-hackathon.com",
    "https://thucchien.ai/",
    "https://www.lotushack.org/",
    "https://dataforlife.vn/",
    "https://vietnamdatathon.com/",
    "https://www.datathon.site/",
    "https://httt.uit.edu.vn/aisc/",
    "https://www.rmithackaventure.com/",
    "https://www.vjaihackathon.com/",
    "https://qvic.vn/",
    "https://vbic.vn/",
    "https://marketingarena.vn/",
    "https://challenge.zalo.ai/",
    "https://event.navercorp.vn/event/naver-vietnam-ai-hackathon-2025/",
]


def _resolve_embedding_provider() -> str:
    raw = settings.get_embedding_model()
    return raw if raw.startswith("openai/") else f"openai/{raw}"


def _resolve_query_provider() -> str:
    raw = os.getenv("CRAWLER_QUERY_MODEL") or "gemini/gemini-3.5-flash"
    if any(old in raw.lower() for old in ("qwen", "ollama")):
        raw = "gemini/gemini-3.5-flash"
    return raw if "/" in raw else f"gemini/{raw}"


def package_bronze_html(
    knowledge_base: Sequence[Any],
    fallback_url: str = "",
) -> tuple[str, int]:
    """Package rendered HTML pages from AdaptiveCrawler into a single Bronze payload.

    Each valid page is prefixed with `<!-- ACDP_PAGE_BOUNDARY url="..." -->` so
    downstream Silver processing (`2_instruction.py`) can split multi-page
    captures deterministically without re-opening Playwright.
    """
    sections: list[str] = []
    for record in knowledge_base:
        if getattr(record, "success", True) is False:
            continue
        raw_html = getattr(record, "html", None)
        if not isinstance(raw_html, str) or not raw_html.strip():
            continue
        page_url = str(getattr(record, "url", "") or fallback_url).strip()
        escaped_url = html.escape(page_url, quote=True)
        sections.append(
            f'<!-- ACDP_PAGE_BOUNDARY url="{escaped_url}" -->\n{raw_html.strip()}'
        )

    if not sections:
        return "", 0
    return "\n\n".join(sections), len(sections)


def upload_to_bronze(
    html_content: str,
    dm_name: str,
    page_count: int | None = None,
) -> str | None:
    """Upload Raw Rendered HTML to Cloudflare R2 Bronze layer (`*.html`).

    Blocks 0-byte or whitespace-only uploads when crawl fails or is blocked.
    Returns the uploaded R2 object key, or None if skipped.
    """
    domain = urlparse(dm_name).netloc or dm_name
    if not html_content or not html_content.strip():
        print(
            f"[SKIP] {domain}: Nội dung HTML rỗng sau crawl (anti-bot hoặc lỗi fetch). Bỏ qua upload Bronze."
        )
        return None

    now = datetime.now(UTC)
    ts = int(now.timestamp())
    resolved_pages = (
        page_count
        if page_count is not None
        else max(1, len(PAGE_BOUNDARY_PATTERN.findall(html_content)))
    )

    bronze_key = (
        f"bronze/{domain}"
        f"/year={now.year}/month={now.strftime('%m')}/day={now.strftime('%d')}/"
        f"{ts}.html"
    )
    s3_client = settings.create_r2_client()
    s3_client.put_object(
        Bucket=settings.bucket_name,
        Key=bronze_key,
        Body=html_content.encode("utf-8"),
        ContentType="text/html; charset=utf-8",
        Metadata={
            "source": domain,
            "layer": "bronze",
            "format": "raw_html",
            "page_count": str(resolved_pages),
        },
    )
    print(
        f"Upload {domain} raw HTML to bronze layer successfully! "
        f"({len(html_content):,} chars, {resolved_pages} page(s) -> {bronze_key})"
    )
    return bronze_key


def _extract_query_list(raw_content: str) -> list[str]:
    """Normalize LLM JSON output for query expansion (supports list or dict)."""
    cleaned = raw_content.strip()
    fence_match = re.search(r"```(?:json)?\s*(.*?)\s*```", cleaned, re.DOTALL)
    if fence_match:
        cleaned = fence_match.group(1)
    parsed = json.loads(cleaned)
    if isinstance(parsed, list):
        return [str(q).strip() for q in parsed if str(q).strip()]
    if isinstance(parsed, dict):
        if "queries" in parsed and isinstance(parsed["queries"], list):
            return [str(q).strip() for q in parsed["queries"] if str(q).strip()]
        for val in parsed.values():
            if isinstance(val, list):
                return [str(q).strip() for q in val if str(q).strip()]
    return []


def _attach_crawler_patches(
    adaptive: AdaptiveCrawler,
    query_provider: str,
    gemini_api_key: str,
) -> None:
    """Attach SPA rendering wait config and resilient query-expansion fallback."""

    async def _patched_crawl_with_preview(url_inner: str, query_inner: str):
        config_with_delay = CrawlerRunConfig(
            delay_before_return_html=5.0,
            page_timeout=35000,
            wait_until="networkidle",
            link_preview_config=LinkPreviewConfig(
                include_internal=True,
                include_external=False,
                query=query_inner,
                concurrency=5,
                timeout=adaptive.config.link_preview_timeout,
                max_links=50,
                verbose=False,
            ),
            score_links=True,
        )
        try:
            result = await adaptive.crawler.arun(url=url_inner, config=config_with_delay)
            if hasattr(result, "_results") and result._results:
                result = result._results[0]
            if hasattr(result, "links") and result.links:
                result.links["internal"] = [
                    link for link in result.links["internal"] if link.get("head_data")
                ]
            return result
        except Exception as exc:  # noqa: BLE001 - Isolate per-link crawl failure
            print(f"[WARN] Error crawling {url_inner}: {exc}")
            return None

    adaptive._crawl_with_preview = _patched_crawl_with_preview

    if isinstance(adaptive.strategy, EmbeddingStrategy):
        strategy = adaptive.strategy

        async def _resilient_map_query_semantic_space(query: str, n_synthetic: int = 10):
            n_total = max(3, int(n_synthetic * 1.3))
            prompt = (
                f"Generate {n_total} variations of this query that explore different aspects: '{query}'. "
                "Return ONLY a JSON object with a single key 'queries' containing an array of strings, "
                'e.g. {"queries": ["variation 1", "variation 2"]}.'
            )
            llm_cfg = strategy._get_query_llm_config_dict() or {}
            provider = llm_cfg.get("provider", query_provider)
            api_token = llm_cfg.get("api_token", gemini_api_key)
            base_url = llm_cfg.get("base_url")

            other_queries: list[str] = []
            try:
                response = perform_completion_with_backoff(
                    provider=provider,
                    prompt_with_variables=prompt,
                    api_token=api_token,
                    json_response=True,
                    base_url=base_url,
                    base_delay=llm_cfg.get("backoff_base_delay", 2),
                    max_attempts=llm_cfg.get("backoff_max_attempts", 3),
                    exponential_factor=llm_cfg.get("backoff_exponential_factor", 2),
                )
                content = response.choices[0].message.content
                other_queries = _extract_query_list(content)
            except Exception as exc:  # noqa: BLE001 - Fallback if query expansion fails
                print(f"[WARN] Query expansion fallback ({provider}): {exc}")

            if len(other_queries) < 3:
                other_queries = [query] * 3

            random.shuffle(other_queries)
            n_validation = max(2, int(len(other_queries) * 0.2))
            val_queries = other_queries[-n_validation:]
            train_queries = [query] + (other_queries[:-n_validation] or [query])

            train_embeddings = await strategy._get_embeddings(train_queries)
            strategy._validation_queries = val_queries
            return train_embeddings, train_queries

        strategy.map_query_semantic_space = _resilient_map_query_semantic_space


async def _single_page_fallback(crawler: AsyncWebCrawler, url: str) -> tuple[str, int]:
    """Fallback to single-page Playwright fetch if AdaptiveCrawler fails or yields 0 pages."""
    fallback_cfg = CrawlerRunConfig(
        delay_before_return_html=5.0,
        page_timeout=35000,
        wait_until="networkidle",
    )
    single_res = await crawler.arun(url=url, config=fallback_cfg)
    if hasattr(single_res, "_results") and single_res._results:
        single_res = single_res._results[0]
    return package_bronze_html([single_res], fallback_url=url)


def _load_urls_from_r2_discovery() -> list[str]:
    """Load candidate URLs from R2 `bronze/_discovery/latest_manifest.json`."""
    s3_client = settings.create_r2_client()
    obj = s3_client.get_object(
        Bucket=settings.bucket_name,
        Key="bronze/_discovery/latest_manifest.json",
    )
    manifest = json.loads(obj["Body"].read().decode("utf-8"))
    candidates = manifest.get("candidates") or []
    urls: list[str] = []
    for c in candidates:
        if not isinstance(c, dict):
            continue
        if c.get("needs_crawl") is False:
            continue
        target = c.get("canonical_url") or c.get("raw_url") or c.get("url")
        if isinstance(target, str) and target.strip():
            urls.append(target.strip())
    return urls


def _merge_unique_urls(*url_lists: list[str]) -> list[str]:
    """Merge URL lists preserving order and deduplicating by normalized URL."""
    seen: set[str] = set()
    merged: list[str] = []
    for group in url_lists:
        for u in group:
            norm = u.strip().rstrip("/")
            if norm and norm not in seen:
                seen.add(norm)
                merged.append(u.strip())
    return merged


def _upload_benchmark_report(report: dict[str, Any]) -> str:
    """Upload Bronze crawl benchmark telemetry JSON to Cloudflare R2."""
    now = datetime.now(UTC)
    ts = int(now.timestamp())
    key = f"bronze/_benchmarks/crawl_bronze_{ts}.json"
    s3_client = settings.create_r2_client()
    s3_client.put_object(
        Bucket=settings.bucket_name,
        Key=key,
        Body=json.dumps(report, ensure_ascii=False, indent=2).encode("utf-8"),
        ContentType="application/json; charset=utf-8",
        Metadata={"layer": "bronze", "type": "benchmark"},
    )
    return key


async def crawl_urls_to_bronze(urls: list[str]) -> list[str]:
    """Crawl given URLs, upload Raw Rendered HTML to R2 Bronze, and record benchmark metrics."""
    import time

    account_id = settings.get_cloudflare_account_id()
    cf_token = settings.cloudflare_api_token or os.getenv("CLOUDFLARE_API_TOKEN", "")
    gemini_key = (
        settings.gemini_api_key
        or settings.google_api_key
        or os.getenv("GEMINI_API_KEY")
        or os.getenv("GOOGLE_API_KEY", "")
    )

    if not account_id or not cf_token:
        raise RuntimeError(
            "Thiếu CLOUDFLARE_API_TOKEN hoặc CLOUDFLARE_ACCOUNT_ID (không trích được từ AWS_ENDPOINT_URL). "
            "Vui lòng kiểm tra file .env."
        )
    if not gemini_key:
        raise RuntimeError("Thiếu GEMINI_API_KEY (hoặc GOOGLE_API_KEY) trong file .env.")
    if not settings.aws_endpoint_url or not settings.aws_access_key_id or not settings.aws_secret_access_key:
        raise RuntimeError(
            "Thiếu thông tin kết nối Cloudflare R2 (AWS_ENDPOINT_URL / AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY) trong .env."
        )

    embedding_provider = _resolve_embedding_provider()
    query_provider = _resolve_query_provider()
    cloudflare_ai_base_url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/v1"

    print(f">> Crawler Embedding: {embedding_provider} (Cloudflare Workers AI)")
    print(f">> Crawler Query LLM: {query_provider}")
    print(f">> Target R2 Bucket: s3://{settings.bucket_name}/bronze/")
    print(f">> Total URLs queued: {len(urls)}")

    browser_config = BrowserConfig(java_script_enabled=True, headless=True)
    uploaded_keys: list[str] = []
    per_url_metrics: list[dict[str, Any]] = []
    batch_start = time.perf_counter()

    async with AsyncWebCrawler(config=browser_config) as crawler:
        config = AdaptiveConfig(
            strategy="embedding",
            embedding_model=None,
            embedding_llm_config=LLMConfig(
                provider=embedding_provider,
                api_token=cf_token,
                base_url=cloudflare_ai_base_url,
            ),
            query_llm_config=LLMConfig(
                provider=query_provider,
                api_token=gemini_key,
            ),
            confidence_threshold=0.6,
            min_gain_threshold=0.1,
            n_query_variations=10,
            embedding_coverage_radius=0.2,
            embedding_k_exp=1.2,
            embedding_min_relative_improvement=0.1,
            embedding_validation_min_score=0.3,
            embedding_min_confidence_threshold=0.1,
            embedding_overlap_threshold=0.4,
            embedding_quality_min_confidence=0,
            embedding_quality_max_confidence=1,
        )

        for idx, url in enumerate(urls, 1):
            print(f"\n>> [{idx}/{len(urls)}] Crawling Raw HTML: {url}")
            url_start = time.perf_counter()
            domain = urlparse(url).netloc or url
            html_content = ""
            page_count = 0
            crawl_mode = "adaptive"
            error_msg = ""

            try:
                adaptive = AdaptiveCrawler(crawler, config)
                _attach_crawler_patches(adaptive, query_provider, gemini_key)
                result = await adaptive.digest(
                    start_url=url,
                    query="upcoming competition including description, policy/regulation, prize, timeline/registry deadline, and challenge",
                )
                adaptive.print_stats()
                html_content, page_count = package_bronze_html(
                    result.knowledge_base, fallback_url=url
                )
            except Exception as exc:  # noqa: BLE001 - Fall back to single-page fetch on AdaptiveCrawler failure
                error_msg = str(exc)
                print(f"[WARN] AdaptiveCrawler lỗi tại {url}: {exc}. Chuyển sang fallback 1 trang...")

            if not html_content:
                crawl_mode = "fallback_single_page"
                try:
                    html_content, page_count = await _single_page_fallback(crawler, url)
                except Exception as fallback_exc:  # noqa: BLE001
                    elapsed_s = round(time.perf_counter() - url_start, 2)
                    err_detail = f"{error_msg} | fallback: {fallback_exc}" if error_msg else str(fallback_exc)
                    print(f"[ERROR] Fallback crawl thất bại tại {url}: {fallback_exc}")
                    per_url_metrics.append(
                        {
                            "url": url,
                            "domain": domain,
                            "status": "error",
                            "mode": crawl_mode,
                            "elapsed_s": elapsed_s,
                            "page_count": 0,
                            "raw_html_chars": 0,
                            "raw_html_bytes": 0,
                            "r2_key": None,
                            "error": err_detail[:300],
                        }
                    )
                    continue

            uploaded_key = upload_to_bronze(html_content, url, page_count=page_count)
            elapsed_s = round(time.perf_counter() - url_start, 2)
            raw_bytes = len(html_content.encode("utf-8")) if html_content else 0
            if uploaded_key:
                uploaded_keys.append(uploaded_key)
                status = f"ok_{crawl_mode}"
            else:
                status = "skipped_empty"

            per_url_metrics.append(
                {
                    "url": url,
                    "domain": domain,
                    "status": status,
                    "mode": crawl_mode,
                    "elapsed_s": elapsed_s,
                    "page_count": page_count,
                    "raw_html_chars": len(html_content),
                    "raw_html_bytes": raw_bytes,
                    "r2_key": uploaded_key,
                    "error": error_msg[:300] if error_msg else None,
                }
            )

    total_elapsed_s = round(time.perf_counter() - batch_start, 2)
    succeeded = [m for m in per_url_metrics if m["r2_key"]]
    total_bytes = sum(m["raw_html_bytes"] for m in succeeded)
    total_pages = sum(m["page_count"] for m in succeeded)

    summary = {
        "timestamp_utc": datetime.now(UTC).isoformat(),
        "total_urls": len(urls),
        "succeeded_urls": len(succeeded),
        "adaptive_succeeded": sum(1 for m in succeeded if m["mode"] == "adaptive"),
        "fallback_succeeded": sum(1 for m in succeeded if m["mode"] == "fallback_single_page"),
        "failed_or_skipped": len(urls) - len(succeeded),
        "total_pages_captured": total_pages,
        "total_raw_html_bytes": total_bytes,
        "total_raw_html_mb": round(total_bytes / (1024 * 1024), 3),
        "total_elapsed_s": total_elapsed_s,
        "avg_elapsed_per_url_s": round(total_elapsed_s / len(urls), 2) if urls else 0.0,
        "avg_bytes_per_succeeded_url": round(total_bytes / len(succeeded)) if succeeded else 0,
        "results": per_url_metrics,
    }
    bench_key = _upload_benchmark_report(summary)
    print("\n================ BRONZE CRAWL BENCHMARK ================")
    print(f"Total URLs      : {summary['total_urls']} (OK: {summary['succeeded_urls']} | Adaptive: {summary['adaptive_succeeded']} | Fallback: {summary['fallback_succeeded']} | Fail/Skip: {summary['failed_or_skipped']})")
    print(f"Total Pages     : {summary['total_pages_captured']}")
    print(f"Total Raw HTML  : {summary['total_raw_html_bytes']:,} B ({summary['total_raw_html_mb']} MB)")
    print(f"Total Time      : {summary['total_elapsed_s']}s (Avg: {summary['avg_elapsed_per_url_s']}s / URL)")
    print(f"Benchmark JSON  : s3://{settings.bucket_name}/{bench_key}")
    print("========================================================")

    return uploaded_keys


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="ACDP v2 Bronze Crawler (Raw Rendered HTML -> Cloudflare R2)"
    )
    parser.add_argument(
        "--url",
        action="append",
        dest="urls",
        help="Target URL to crawl (repeatable). Defaults to curated competition list.",
    )
    parser.add_argument(
        "--from-discovery",
        action="store_true",
        help="Load URLs from R2 bronze/_discovery/latest_manifest.json",
    )
    parser.add_argument(
        "--all-sources",
        action="store_true",
        help="Merge curated DEFAULT_URLS with R2 discovery manifest (deduplicated).",
    )
    parser.add_argument(
        "--max-urls",
        type=int,
        default=0,
        help="Optional cap on number of URLs to crawl (0 = all).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)
    if args.urls:
        urls = args.urls
    elif args.all_sources:
        discovery_urls = _load_urls_from_r2_discovery()
        urls = _merge_unique_urls(DEFAULT_URLS, discovery_urls)
    elif args.from_discovery:
        urls = _load_urls_from_r2_discovery()
    else:
        urls = list(DEFAULT_URLS)

    if args.max_urls > 0:
        urls = urls[: args.max_urls]

    asyncio.run(crawl_urls_to_bronze(urls))


if __name__ == "__main__":
    main()
