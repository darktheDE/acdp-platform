import asyncio
from crawl4ai import (
    AsyncWebCrawler,
    AdaptiveConfig,
    AdaptiveCrawler,
    LLMConfig
)
from dotenv import load_dotenv
import os
import boto3
from datetime import datetime
from urllib.parse import urlparse

# TẢI BIẾN MÔI TRƯỜNG
load_dotenv()

bucket_name = os.getenv("BUCKET_NAME")
endpoint = os.getenv("AWS_ENDPOINT_URL")
access_key_id = os.getenv ("AWS_ACCESS_KEY_ID")
sec_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")

s3_client = boto3.client(
    service_name="s3",
    endpoint_url=endpoint,
    aws_access_key_id=access_key_id,
    aws_secret_access_key=sec_access_key,
    region_name="auto"
)

###

def upload_to_bronze(md_content, dm_name: str):
    now = datetime.now()
    dm_name = urlparse(dm_name).netloc

    bronze_key = (
        f"bronze/{dm_name}"
        f"/year={now.year}/month={now.strftime('%m')}/day={now.strftime('%d')}/"
        f"{int(now.timestamp())}"
    )

    s3_client.put_object(
        Bucket=bucket_name,
        Key=bronze_key,
        Body=md_content.encode("utf-8"),
        ContentType="text/markdown; charset=utf-8",
        Metadata={"source": dm_name, "layer": "bronze"},
    )
    print(f"Upload {dm_name} content to bronze layer sucessfully !")

async def main():
    urls = [
        "https://codetour.org/"
        "https://aichallenge.hochiminhcity.gov.vn/",
        "https://www.vietnamaichallenge.com/",
        "https://datadna.onyxdata.co.uk/challenges/",
        "https://itconsultantchallenge.org/vi",
        "https://rmit-hackathon.com",
        "https://hackaithon.vsds.vn/"
    ]

    async with AsyncWebCrawler() as crawler:
        config = AdaptiveConfig(
            strategy='embedding',
            embedding_model=None,
            embedding_llm_config=LLMConfig(
                provider='ollama/qwen3-embedding:0.6b'
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
            embedding_quality_max_confidence=1  # Max displayed confidence
        )

        for url in urls:
            adaptive = AdaptiveCrawler(crawler, config)
            
            result = await adaptive.digest(
                start_url=url,
                query="upcoming competition including description, policy/regulation, prize, timeline/registry deadline, and challenge"
            )
            adaptive.print_stats()
            md_content = "\n\n".join(
                r.markdown.raw_markdown for r in result.knowledge_base
                if r.markdown and r.markdown.raw_markdown
            )

            upload_to_bronze(md_content, url)

            # adaptive.print_stats()
            # relevant_pages = adaptive.get_relevant_content(top_k=5)
            # for page in relevant_pages:
            #     print(f"- {page['url']} (score: {page['score']:.2f})")

if __name__ == '__main__':
    asyncio.run(main())