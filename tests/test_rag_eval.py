"""Offline unit tests for NT-012 Gold pre-filtering and Ragas evaluation harness."""

from __future__ import annotations

from pathlib import Path

from acdp.api.services.rag_service import RetrievedChunk, build_gold_filter, infer_gold_filters
from acdp.v2.rag_eval import (
    DEFAULT_DATASET_PATH,
    BM25CorpusRetriever,
    load_golden_dataset,
    summarize_system_scores,
)


def test_infer_gold_filters_extracts_structured_intents() -> None:
    filters = infer_gold_filters("Tìm cuộc thi AI miễn phí đang mở đăng ký thi online")
    assert filters["is_free"] is True
    assert filters["mode_canonical"] == "Online"
    assert filters["registration_status"] == "open"
    assert filters["domain_slugs"] == "ai-data-science"


def test_build_gold_filter_constructs_qdrant_must_conditions() -> None:
    q_filter = build_gold_filter(
        domain_filter="challenge.zalo.ai",
        gold_filters={"mode_canonical": "Online", "is_free": True, "registration_status": "open"},
    )
    assert q_filter is not None
    keys = {cond.key for cond in q_filter.must}
    assert keys == {"metadata.domain", "metadata.mode_canonical", "metadata.registration_status", "metadata.is_free"}


def test_bm25_corpus_retriever_ranks_relevant_chunk_first() -> None:
    chunks = [
        RetrievedChunk(text="Zalo AI Challenge 2026 giải thưởng 304 triệu đồng", domain="challenge.zalo.ai", source_url="https://challenge.zalo.ai", crawl_date="2026-11-23"),
        RetrievedChunk(text="Code Tour 2026 thi lập trình cá nhân", domain="codetour.org", source_url="https://codetour.org", crawl_date="2026-11-23"),
        RetrievedChunk(text="RMIT Hackathon 2026 tổ chức tại cơ sở Nam Sài Gòn", domain="rmit-hackathon.com", source_url="https://rmit-hackathon.com", crawl_date="2026-11-23"),
        RetrievedChunk(text="LotusHacks 2026 cuộc thi công nghệ dành cho sinh viên", domain="lotushack.org", source_url="https://lotushack.org", crawl_date="2026-11-23"),
    ]
    bm25 = BM25CorpusRetriever(chunks)
    hits = bm25.retrieve("giải thưởng Zalo AI Challenge", top_k=1)
    assert len(hits) == 1
    assert hits[0].domain == "challenge.zalo.ai"


def test_golden_dataset_has_20_valid_queries() -> None:
    rows = load_golden_dataset(Path(DEFAULT_DATASET_PATH))
    assert len(rows) == 20
    categories = {r["category"] for r in rows}
    assert categories == {"deadline", "team_size", "domain_mode", "prize"}
    for row in rows:
        assert row["question"].strip()
        assert row["reference"].strip()
        assert row["expected_urls"]


def test_summarize_system_scores_aggregates_metrics_and_percentiles() -> None:
    rows = [
        {"system": "A", "faithfulness": 0.8, "answer_relevancy": 0.7, "context_precision": 0.6, "context_recall": 0.5, "latency_ms": 1000},
        {"system": "A", "faithfulness": 1.0, "answer_relevancy": 0.9, "context_precision": 0.8, "context_recall": 0.7, "latency_ms": 2000},
    ]
    summary = summarize_system_scores(rows)
    assert summary["A"]["count"] == 2
    assert summary["A"]["faithfulness"] == 0.9
    assert summary["A"]["latency_p50_ms"] == 1500.0
    assert summary["A"]["latency_p95_ms"] == 1950.0


def test_percentile_semantic_chunker_splits_on_topic_shift_without_deprecation() -> None:
    """Verify PercentileSemanticChunker splits semantically distant topics cleanly (RFC-0001 R6)."""
    from langchain_core.documents import Document
    from langchain_core.embeddings import Embeddings

    from acdp.v2.rag_ingest import build_chunker, chunk_single_document

    class _TopicEmbeddings(Embeddings):
        def embed_documents(self, texts: list[str]) -> list[list[float]]:
            vecs = []
            for text in texts:
                if "giải thưởng" in text.lower() or "tiền" in text.lower():
                    vecs.append([1.0, 0.0, 0.0])
                else:
                    vecs.append([0.0, 1.0, 0.0])
            return vecs

        def embed_query(self, text: str) -> list[float]:
            return self.embed_documents([text])[0]

    chunker = build_chunker(_TopicEmbeddings())
    chunker.min_chunk_size = 40
    doc = Document(
        page_content=(
            "Giải thưởng cuộc thi AI Challenge 2026 lên tới 300 triệu đồng tiền mặt. "
            "Giải nhất nhận tiền thưởng trực tiếp và cúp lưu niệm từ ban tổ chức. "
            "Thể lệ đăng ký yêu cầu đội thi gồm hai đến bốn sinh viên chính quy tại trường đại học."
        ),
        metadata={"domain": "aichallenge.vn", "source_url": "https://aichallenge.vn"},
    )
    parts = chunk_single_document(chunker, doc)
    assert len(parts) >= 2
    assert all("[Nguồn: aichallenge.vn | URL: https://aichallenge.vn]" in p.page_content for p in parts)
    assert [p.metadata["chunk_index"] for p in parts] == list(range(len(parts)))
