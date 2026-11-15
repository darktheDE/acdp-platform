import asyncio
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

from crawl4ai import (
    AdaptiveConfig,
    AdaptiveCrawler,
    AsyncWebCrawler,
    BrowserConfig,
    CrawlerRunConfig,
    LLMConfig,
)
from crawl4ai.adaptive_crawler import LinkPreviewConfig

from acdp.config import settings


def upload_to_bronze(md_content: str, dm_name: str) -> None:
    """Upload nội dung Markdown lên tầng Bronze trên R2 hoặc lưu cục bộ theo cấu hình.

    FIX: Chặn upload file rỗng — nếu nội dung trống (crawl thất bại / bị anti-bot),
    in cảnh báo và thoát ngay; không tạo object 0-byte trên bucket.
    """
    domain = urlparse(dm_name).netloc or dm_name
    if not md_content or not md_content.strip():
        print(f"[SKIP] {domain}: Nội dung rỗng sau crawl (có thể bị anti-bot hoặc lỗi fetch). Bỏ qua upload lên Bronze.")
        return

    now = datetime.now()
    ts = int(now.timestamp())

    if settings.bronze_storage_backend == "local" and not settings.bronze_storage_uri.startswith(("s3://", "r2://")):
        local_dir = Path(settings.bronze_storage_uri) / domain / f"year={now.year}" / f"month={now.strftime('%m')}" / f"day={now.strftime('%d')}"
        local_dir.mkdir(parents=True, exist_ok=True)
        local_path = local_dir / f"{ts}.md"
        local_path.write_text(md_content, encoding="utf-8")
        print(f"Saved {domain} content to local bronze layer! ({len(md_content):,} chars -> {local_path})")
        return

    bronze_key = (
        f"bronze/{domain}"
        f"/year={now.year}/month={now.strftime('%m')}/day={now.strftime('%d')}/"
        f"{ts}"
    )
    s3_client = settings.create_r2_client()
    s3_client.put_object(
        Bucket=settings.bucket_name,
        Key=bronze_key,
        Body=md_content.encode("utf-8"),
        ContentType="text/markdown; charset=utf-8",
        Metadata={"source": domain, "layer": "bronze"},
    )
    print(f"Upload {domain} content to bronze layer successfully! ({len(md_content):,} chars -> {bronze_key})")

async def main():
    urls = [
        "https://codetour.org/",
        #"https://aichallenge.hochiminhcity.gov.vn/",
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
        "https://web3hackfest.org/",
        "https://marketingarena.vn/",
        "https://challenge.zalo.ai/",
        "https://event.navercorp.vn/event/naver-vietnam-ai-hackathon-2025/"
        #"https://hackaithon.vsds.vn/"
    ]

    # delay_before_return_html=5.0 được inject qua monkey-patch _crawl_with_preview
    # (xem bên dưới trong vòng lặp for url in urls).
    # BrowserConfig đảm bảo JS được bật để render SPA (React/Next.js/Vue).
    browser_config = BrowserConfig(
        java_script_enabled=True,
        headless=True,
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        config = AdaptiveConfig(
            strategy='embedding',
            embedding_model=None,
            embedding_llm_config=LLMConfig(
                provider='ollama/qwen3-embedding:4b'
            ),
            query_llm_config=LLMConfig(
                provider='ollama/qwen2.5:7b'
            ),
            confidence_threshold=0.6,
            min_gain_threshold=0.1,
            # Query expansion
            n_query_variations=10,  # Number of query variations to generate

            # Coverage parameters
            embedding_coverage_radius=0.2,  # Distance threshold for coverage
            embedding_k_exp=1.2,  # Exponential decay factor (higher = stricter)

            # Stopping criteria
            embedding_min_relative_improvement=0.1,  # Min improvement to continue
            embedding_validation_min_score=0.3,  # Min validation score
            embedding_min_confidence_threshold=0.1,  # Below this = irrelevant

            # Link selection
            embedding_overlap_threshold=0.4,  # Similarity for deduplication

            # Display confidence mapping
            embedding_quality_min_confidence=0,  # Min displayed confidence
            embedding_quality_max_confidence=1   # Max displayed confidence
        )

        for url in urls:
            adaptive = AdaptiveCrawler(crawler, config)

            # FIX: AdaptiveCrawler.digest() không nhận crawler_config. Để inject
            # delay_before_return_html=5.0, ta monkey-patch _crawl_with_preview để
            # ghi đè CrawlerRunConfig mà nó tự tạo, thêm delay cho JS render (SPA).
            _original_crawl_with_preview = adaptive._crawl_with_preview

            async def _patched_crawl_with_preview(url_inner: str, query_inner: str):
                config_with_delay = CrawlerRunConfig(
                    delay_before_return_html=5.0,   # Chờ 5s để JS render hoàn chỉnh
                    page_timeout=35000,             # Timeout tổng thể 35s (5s buffer trên delay)
                    wait_until="networkidle",       # Chờ network idle trước khi lấy HTML
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
                    if hasattr(result, '_results') and result._results:
                        result = result._results[0]
                    if hasattr(result, 'links') and result.links:
                        result.links['internal'] = [
                            link for link in result.links['internal']
                            if link.get('head_data')
                        ]
                    return result
                except Exception as e:
                    print(f"Error crawling {url_inner}: {e}")
                    return None

            adaptive._crawl_with_preview = _patched_crawl_with_preview

            result = await adaptive.digest(
                start_url=url,
                query="upcoming competition including description, policy/regulation, prize, timeline/registry deadline, and challenge",
            )
            adaptive.print_stats()
            md_content = "\n\n".join(
                r.markdown.raw_markdown for r in result.knowledge_base
                if r.markdown and r.markdown.raw_markdown
            )

            upload_to_bronze(md_content, url)

if __name__ == '__main__':
    asyncio.run(main())
