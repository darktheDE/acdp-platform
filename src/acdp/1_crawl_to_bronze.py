import asyncio
from crawl4ai import (
    AsyncWebCrawler,
    AdaptiveConfig,
    AdaptiveCrawler,
    BrowserConfig,
    CrawlerRunConfig,
    LLMConfig,
)
from crawl4ai.adaptive_crawler import LinkPreviewConfig
from dotenv import load_dotenv
import os
import boto3
from datetime import datetime
from urllib.parse import urlparse

# TẢI BIẾN MÔI TRƯỜNG
load_dotenv()

BUCKET_NAME = os.getenv("BUCKET_NAME")
ENDPOINT_URL = os.getenv("AWS_ENDPOINT_URL")
ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")

s3_client = boto3.client(
    service_name="s3",
    endpoint_url=ENDPOINT_URL,
    aws_access_key_id=ACCESS_KEY_ID,
    aws_secret_access_key=SECRET_ACCESS_KEY,
    region_name="auto"
)

###

def upload_to_bronze(md_content: str, dm_name: str) -> None:
    """Upload nội dung Markdown lên tầng Bronze trên R2.

    FIX: Chặn upload file rỗng — nếu nội dung trống (crawl thất bại / bị anti-bot),
    in cảnh báo và thoát ngay; không tạo object 0-byte trên bucket.
    """
    if not md_content or not md_content.strip():
        domain = urlparse(dm_name).netloc or dm_name
        print(f"[SKIP] {domain}: Nội dung rỗng sau crawl (có thể bị anti-bot hoặc lỗi fetch). Bỏ qua upload lên Bronze.")
        return

    now = datetime.now()
    dm_name = urlparse(dm_name).netloc

    bronze_key = (
        f"bronze/{dm_name}"
        f"/year={now.year}/month={now.strftime('%m')}/day={now.strftime('%d')}/"
        f"{int(now.timestamp())}"
    )

    s3_client.put_object(
        Bucket=BUCKET_NAME,
        Key=bronze_key,
        Body=md_content.encode("utf-8"),
        ContentType="text/markdown; charset=utf-8",
        Metadata={"source": dm_name, "layer": "bronze"},
    )
    print(f"Upload {dm_name} content to bronze layer successfully! ({len(md_content):,} chars -> {bronze_key})")

async def main():
    urls = [
        "https://codetour.org/",
        #"https://aichallenge.hochiminhcity.gov.vn/",
        "https://www.vietnamaichallenge.com/",
        "https://datadna.onyxdata.co.uk/challenges/",
        "https://itconsultantchallenge.org/vi",
        "https://rmit-hackathon.com",
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
