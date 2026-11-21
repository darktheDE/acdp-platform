import asyncio
import json
import os
import random
import re
import sys
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
from crawl4ai.adaptive_crawler import EmbeddingStrategy, LinkPreviewConfig
from crawl4ai.utils import perform_completion_with_backoff
from dotenv import find_dotenv, load_dotenv

from acdp.config import settings

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# TẢI BIẾN MÔI TRƯỜNG
load_dotenv(find_dotenv(usecwd=True))

BUCKET_NAME = os.getenv("BUCKET_NAME")
ENDPOINT_URL = os.getenv("AWS_ENDPOINT_URL")
ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")

CLOUDFLARE_API_TOKEN = os.getenv("CLOUDFLARE_API_TOKEN")
CLOUDFLARE_ACCOUNT_ID = os.getenv("CLOUDFLARE_ACCOUNT_ID") or (
    urlparse(ENDPOINT_URL).netloc.split(".", 1)[0] if ENDPOINT_URL else ""
)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

_raw_embed_model = (
    os.getenv("CRAWLER_EMBED_MODEL")
    or os.getenv("CLOUDFLARE_EMBEDDING_MODEL")
    or "@cf/baai/bge-m3"
)
if any(old in _raw_embed_model.lower() for old in ("qwen", "ollama")):
    _raw_embed_model = "@cf/baai/bge-m3"
# Crawl4AI get_text_embeddings() yêu cầu prefix 'openai/' khi dùng custom OpenAI-compatible base_url
EMBEDDING_PROVIDER = (
    _raw_embed_model if _raw_embed_model.startswith("openai/") else f"openai/{_raw_embed_model}"
)

_raw_query_model = os.getenv("CRAWLER_QUERY_MODEL") or "gemini/gemini-3.5-flash"
if any(old in _raw_query_model.lower() for old in ("qwen", "ollama")):
    _raw_query_model = "gemini/gemini-3.5-flash"
QUERY_PROVIDER = _raw_query_model if "/" in _raw_query_model else f"gemini/{_raw_query_model}"

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
        local_dir = (
            Path(settings.bronze_storage_uri)
            / domain
            / f"year={now.year}"
            / f"month={now.strftime('%m')}"
            / f"day={now.strftime('%d')}"
        )
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

def _extract_query_list(raw_content: str) -> list[str]:
    """Chuẩn hóa JSON trả về từ LLM khi sinh biến thể câu hỏi (list hoặc dict)."""
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


def _attach_crawler_patches(adaptive: AdaptiveCrawler) -> None:
    """Gắn các patch an toàn cho AdaptiveCrawler:

    1. Inject delay_before_return_html=5.0 + wait_until='networkidle' cho SPA.
    2. Chuẩn hóa JSON trả về của map_query_semantic_space khi LLM trả list thay vì {'queries': [...]}.
    """
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
            if hasattr(result, "_results") and result._results:
                result = result._results[0]
            if hasattr(result, "links") and result.links:
                result.links["internal"] = [
                    link for link in result.links["internal"]
                    if link.get("head_data")
                ]
            return result
        except Exception as e:  # noqa: BLE001 - Không làm sập vòng crawl khi 1 link con lỗi
            print(f"Error crawling {url_inner}: {e}")
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
            provider = llm_cfg.get("provider", QUERY_PROVIDER)
            api_token = llm_cfg.get("api_token", GEMINI_API_KEY)
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
            except Exception as exc:  # noqa: BLE001 - Fallback nếu mở rộng truy vấn lỗi
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


async def main():
    if not CLOUDFLARE_ACCOUNT_ID or not CLOUDFLARE_API_TOKEN:
        raise RuntimeError(
            "Thiếu CLOUDFLARE_API_TOKEN hoặc CLOUDFLARE_ACCOUNT_ID (không trích được từ AWS_ENDPOINT_URL). "
            "Vui lòng kiểm tra file .env."
        )
    if not GEMINI_API_KEY:
        raise RuntimeError("Thiếu GEMINI_API_KEY (hoặc GOOGLE_API_KEY) trong file .env.")

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
        #"https://vnquantum.org/events/quantum-hackathon-qc4sg/",
        "https://www.vjaihackathon.com/",
        "https://qvic.vn/",
        "https://vbic.vn/",
        #"https://web3hackfest.org/",
        "https://marketingarena.vn/",
        "https://challenge.zalo.ai/",
        "https://event.navercorp.vn/event/naver-vietnam-ai-hackathon-2025/"
        #"https://hackaithon.vsds.vn/"
    ]

    cloudflare_ai_base_url = f"https://api.cloudflare.com/client/v4/accounts/{CLOUDFLARE_ACCOUNT_ID}/ai/v1"
    print(f">> Crawler Embedding: {EMBEDDING_PROVIDER} (Cloudflare Workers AI)")
    print(f">> Crawler Query LLM: {QUERY_PROVIDER}")

    # delay_before_return_html=5.0 được inject qua _attach_crawler_patches()
    # BrowserConfig đảm bảo JS được bật để render SPA (React/Next.js/Vue).
    browser_config = BrowserConfig(
        java_script_enabled=True,
        headless=True,
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        config = AdaptiveConfig(
            strategy="embedding",
            embedding_model=None,
            embedding_llm_config=LLMConfig(
                provider=EMBEDDING_PROVIDER,
                api_token=CLOUDFLARE_API_TOKEN,
                base_url=cloudflare_ai_base_url,
            ),
            query_llm_config=LLMConfig(
                provider=QUERY_PROVIDER,
                api_token=GEMINI_API_KEY,
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

        for idx, url in enumerate(urls, 1):
            print(f"\n>> [{idx}/{len(urls)}] Crawling: {url}")
            try:
                adaptive = AdaptiveCrawler(crawler, config)
                _attach_crawler_patches(adaptive)

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
            except Exception as exc:  # noqa: BLE001 - Cô lập lỗi từng URL để tiếp tục batch
                print(f"[ERROR] Thất bại khi crawl {url}: {exc}")

if __name__ == "__main__":
    asyncio.run(main())
