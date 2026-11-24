"""NT-012 / EXP-0001: Dual-Layer RAG (v2) Evaluation Harness using Ragas.

Compares three retrieval architectures on the same chunk corpus and generator:
  - System A: Naive Dense Vector Search (Qdrant @cf/baai/bge-m3, no Gold pre-filtering)
  - System B: Lexical BM25 (rank_bm25 over Qdrant Silver chunks)
  - System C: ACDP v2 Dual-Layer RAG (Qdrant @cf/baai/bge-m3 + Gold OBT Metadata Pre-Filtering)
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import statistics
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from qdrant_client import QdrantClient

from acdp.api.services.rag_service import (
    RetrievalConfig,
    RetrievedChunk,
    answer_with_contexts,
    retrieve_contexts,
)
from acdp.config import settings
from acdp.v2.rag_ingest import CloudflareWorkersAIEmbeddings

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

DEFAULT_DATASET_PATH = Path("docs/experiments/data/0001-golden-queries.jsonl")
DEFAULT_CHECKPOINT_PATH = Path("docs/experiments/data/0001-generations-checkpoint.json")
DEFAULT_OUT_PATH = Path("docs/experiments/data/0001-results.json")


@dataclass
class QueryEvalRecord:
    """Single evaluated query record for one retrieval system."""

    id: str
    category: str
    system: str
    question: str
    reference: str
    answer: str
    retrieved_contexts: list[str]
    retrieved_urls: list[str]
    latency_ms: int
    provider: str


def _tokenize_bm25(text: str) -> list[str]:
    return re.findall(r"\w+", (text or "").lower(), flags=re.UNICODE)


class BM25CorpusRetriever:
    """In-memory BM25 retriever over Qdrant Silver chunks for fair Baseline B ablation."""

    def __init__(self, chunks: list[RetrievedChunk]) -> None:
        from rank_bm25 import BM25Okapi  # type: ignore[import-not-found]

        self.chunks = chunks
        self._corpus_tokens = [_tokenize_bm25(c.text) for c in chunks]
        self._bm25 = BM25Okapi(self._corpus_tokens) if chunks else None

    @classmethod
    def from_qdrant(
        cls,
        qdrant_client: QdrantClient,
        collection_name: str,
        batch_size: int = 256,
    ) -> BM25CorpusRetriever:
        chunks: list[RetrievedChunk] = []
        offset = None
        while True:
            points, next_offset = qdrant_client.scroll(
                collection_name=collection_name,
                limit=batch_size,
                offset=offset,
                with_payload=True,
                with_vectors=False,
            )
            for pt in points:
                payload = pt.payload or {}
                meta = payload.get("metadata") or {}
                domain = str(meta.get("domain") or "unknown")
                chunks.append(
                    RetrievedChunk(
                        text=str(payload.get("page_content") or ""),
                        domain=domain,
                        source_url=str(meta.get("source_url") or f"https://{domain}"),
                        crawl_date=str(meta.get("crawl_date") or ""),
                        metadata=meta,
                    )
                )
            if next_offset is None:
                break
            offset = next_offset
        return cls(chunks)

    def retrieve(self, query: str, top_k: int = 6) -> list[RetrievedChunk]:
        if not self.chunks or self._bm25 is None:
            return []
        q_tokens = _tokenize_bm25(query)
        if not q_tokens:
            return []
        scores = self._bm25.get_scores(q_tokens)
        ranked = sorted(range(len(scores)), key=lambda idx: scores[idx], reverse=True)
        out: list[RetrievedChunk] = []
        for idx in ranked[:top_k]:
            if scores[idx] <= 0:
                continue
            c = self.chunks[idx]
            out.append(
                RetrievedChunk(
                    text=c.text,
                    domain=c.domain,
                    source_url=c.source_url,
                    crawl_date=c.crawl_date,
                    score=float(scores[idx]),
                    metadata=c.metadata,
                )
            )
        return out


def load_golden_dataset(path: Path, limit: int = 0) -> list[dict[str, Any]]:
    """Load JSONL golden evaluation queries."""
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            raw = line.strip()
            if not raw:
                continue
            rows.append(json.loads(raw))
    return rows[:limit] if limit > 0 else rows


def _percentile(values: list[int], pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    k = (len(ordered) - 1) * pct
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return float(ordered[int(k)])
    return float(ordered[f] * (c - k) + ordered[c] * (k - f))


def _safe_mean(values: list[float]) -> float:
    valid = [float(v) for v in values if v is not None and not math.isnan(float(v))]
    return round(statistics.mean(valid), 4) if valid else 0.0


def _build_ragas_evaluators(judge: str = "groq") -> tuple[Any, Any]:
    """Initialize LangChain-wrapped LLM judge (Groq LPU default or Gemini) & Cloudflare BGE-M3 embeddings."""
    from ragas.embeddings import LangchainEmbeddingsWrapper
    from ragas.llms import LangchainLLMWrapper

    if judge == "groq":
        from langchain_openai import ChatOpenAI  # type: ignore[import-not-found]

        groq_key = settings.groq_api_key.strip()
        if not groq_key:
            raise RuntimeError("GROQ_API_KEY is required when --judge groq is selected.")
        groq_model = settings.groq_chat_model.strip() or "qwen/qwen3.8-27b"
        if groq_model == "llama-3.3-70b-versatile":
            groq_model = "qwen/qwen3.8-27b"
        llm = ChatOpenAI(
            model=groq_model,
            api_key=groq_key,
            base_url="https://api.groq.com/openai/v1",
            temperature=0.0,
            max_retries=4,
            timeout=60,
        )
    else:
        from langchain_google_genai import ChatGoogleGenerativeAI  # type: ignore[import-not-found]

        api_key = (settings.gemini_api_key or settings.google_api_key or os.getenv("GOOGLE_API_KEY") or "").strip()
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY or GOOGLE_API_KEY is required for Gemini judge.")
        llm = ChatGoogleGenerativeAI(
            model=settings.get_chat_model(),
            google_api_key=api_key,
            temperature=0.0,
        )
    return LangchainLLMWrapper(llm), LangchainEmbeddingsWrapper(CloudflareWorkersAIEmbeddings())


def score_records_with_ragas(records: list[QueryEvalRecord], judge: str = "groq") -> list[dict[str, Any]]:
    """Run Ragas evaluation on collected records and return per-row metric dicts."""
    from datasets import Dataset
    from ragas import evaluate
    from ragas.metrics import (
        AnswerRelevancy,
        Faithfulness,
        LLMContextPrecisionWithReference,
        LLMContextRecall,
    )
    from ragas.run_config import RunConfig

    eval_llm, eval_embeddings = _build_ragas_evaluators(judge=judge)
    metrics = [
        Faithfulness(llm=eval_llm),
        AnswerRelevancy(llm=eval_llm, embeddings=eval_embeddings, strictness=1),
        LLMContextPrecisionWithReference(llm=eval_llm),
        LLMContextRecall(llm=eval_llm),
    ]
    ds = Dataset.from_dict(
        {
            "user_input": [r.question for r in records],
            "response": [r.answer for r in records],
            "retrieved_contexts": [r.retrieved_contexts or [""] for r in records],
            "reference": [r.reference for r in records],
        }
    )
    workers = 4 if judge == "groq" else 1
    result = evaluate(
        dataset=ds,
        metrics=metrics,
        run_config=RunConfig(timeout=90, max_retries=5, max_wait=20, max_workers=workers),
        raise_exceptions=False,
    )
    df = result.to_pandas()
    scored_rows: list[dict[str, Any]] = []
    for idx, rec in enumerate(records):
        row_dict = asdict(rec)
        for col in ("faithfulness", "answer_relevancy", "llm_context_precision_with_reference", "context_recall"):
            if col in df.columns:
                val = df.iloc[idx][col]
                norm_key = "context_precision" if col == "llm_context_precision_with_reference" else col
                row_dict[norm_key] = None if val is None or (isinstance(val, float) and math.isnan(val)) else round(float(val), 4)
        scored_rows.append(row_dict)
    return scored_rows


def summarize_system_scores(scored_rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Aggregate mean Ragas metrics and latency percentiles per retrieval system."""
    by_sys: dict[str, list[dict[str, Any]]] = {}
    for row in scored_rows:
        by_sys.setdefault(row["system"], []).append(row)

    summary: dict[str, dict[str, Any]] = {}
    for sys_name, rows in sorted(by_sys.items()):
        latencies = [int(r["latency_ms"]) for r in rows]
        summary[sys_name] = {
            "count": len(rows),
            "faithfulness": _safe_mean([r.get("faithfulness") for r in rows if r.get("faithfulness") is not None]),
            "answer_relevancy": _safe_mean([r.get("answer_relevancy") for r in rows if r.get("answer_relevancy") is not None]),
            "context_precision": _safe_mean([r.get("context_precision") for r in rows if r.get("context_precision") is not None]),
            "context_recall": _safe_mean([r.get("context_recall") for r in rows if r.get("context_recall") is not None]),
            "latency_p50_ms": round(_percentile(latencies, 0.50), 1),
            "latency_p95_ms": round(_percentile(latencies, 0.95), 1),
        }
    return summary


def run_evaluation(
    dataset_path: Path = DEFAULT_DATASET_PATH,
    out_path: Path = DEFAULT_OUT_PATH,
    checkpoint_path: Path = DEFAULT_CHECKPOINT_PATH,
    systems: list[str] | None = None,
    limit: int = 0,
    top_k: int = 6,
    sleep_seconds: float = 4.2,
    judge: str = "groq",
    from_checkpoint: bool = False,
) -> dict[str, Any]:
    """Execute end-to-end retrieval + generation + Ragas evaluation across requested systems."""
    selected_systems = [s.upper() for s in (systems or ["A", "B", "C"])]
    queries = load_golden_dataset(dataset_path, limit=limit)
    if not queries:
        raise RuntimeError(f"Empty golden dataset: {dataset_path}")

    if from_checkpoint and checkpoint_path.exists():
        raw_records = json.loads(checkpoint_path.read_text(encoding="utf-8"))
        records = [QueryEvalRecord(**r) for r in raw_records]
        print(f">> Loaded {len(records)} generated records from checkpoint: {checkpoint_path}")
    else:
        prev_cache_flag = settings.rag_cache_enabled
        settings.rag_cache_enabled = False
        bm25: BM25CorpusRetriever | None = None
        try:
            if "B" in selected_systems:
                qc = QdrantClient(url=settings.get_qdrant_url(), api_key=settings.get_qdrant_api_key(), timeout=20)
                bm25 = BM25CorpusRetriever.from_qdrant(qc, settings.get_qdrant_collection())

            records = []
            for sys_name in selected_systems:
                for idx, item in enumerate(queries, 1):
                    question = item["question"]
                    t0 = time.perf_counter()
                    if sys_name == "A":
                        chunks = retrieve_contexts(
                            question,
                            RetrievalConfig(use_gold_filter=False, limit=top_k, score_threshold=0.35),
                        )
                    elif sys_name == "B":
                        assert bm25 is not None
                        chunks = bm25.retrieve(question, top_k=top_k)
                    elif sys_name == "C":
                        chunks = retrieve_contexts(
                            question,
                            RetrievalConfig(use_gold_filter=True, limit=top_k, score_threshold=0.35),
                        )
                    else:
                        raise ValueError(f"Unsupported system '{sys_name}'. Expected A, B, or C.")

                    answer, citations, provider = ("", [], "none")
                    for attempt in range(1, 4):
                        try:
                            answer, citations, provider = answer_with_contexts(question, chunks)
                            break
                        except Exception as exc:
                            if attempt == 3:
                                raise
                            wait_s = 20 * attempt
                            print(f"[{sys_name}] {item['id']} rate-limited/failed (attempt {attempt}), sleeping {wait_s}s: {exc}")
                            time.sleep(wait_s)
                    elapsed_ms = int((time.perf_counter() - t0) * 1000)
                    records.append(
                        QueryEvalRecord(
                            id=item["id"],
                            category=item.get("category", "general"),
                            system=sys_name,
                            question=question,
                            reference=item["reference"],
                            answer=answer,
                            retrieved_contexts=[c.text for c in chunks],
                            retrieved_urls=[c.url for c in citations],
                            latency_ms=elapsed_ms,
                            provider=provider,
                        )
                    )
                    print(f"[{sys_name}] {idx}/{len(queries)} {item['id']} | {len(chunks)} chunks | {elapsed_ms}ms | {provider}")
                    if sleep_seconds > 0 and idx < len(queries):
                        time.sleep(sleep_seconds)
        finally:
            settings.rag_cache_enabled = prev_cache_flag

        checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
        checkpoint_path.write_text(
            json.dumps([asdict(r) for r in records], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f">> Saved {len(records)} generated answers checkpoint to {checkpoint_path}")

    print(f">> Running Ragas judge scoring (judge={judge})...")
    scored_rows = score_records_with_ragas(records, judge=judge)
    summary = summarize_system_scores(scored_rows)

    payload = {
        "dataset": str(dataset_path),
        "query_count": len(queries),
        "systems": selected_systems,
        "judge": judge,
        "summary": summary,
        "records": scored_rows,
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f">> Saved evaluation results to {out_path}")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return payload


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="ACDP v2 Dual-Layer RAG Ragas Evaluator (NT-012)")
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET_PATH)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT_PATH)
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT_PATH)
    parser.add_argument("--from-checkpoint", action="store_true", help="Skip generation and score from saved checkpoint")
    parser.add_argument("--judge", choices=["groq", "gemini"], default="groq", help="Ragas LLM judge provider")
    parser.add_argument("--systems", nargs="+", default=["A", "B", "C"], choices=["A", "B", "C"])
    parser.add_argument("--limit", type=int, default=0, help="Limit number of queries for smoke testing")
    parser.add_argument("--top-k", type=int, default=6)
    parser.add_argument("--sleep", type=float, default=4.2, help="Delay between queries (seconds, 4.2s respects 15 RPM)")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)
    run_evaluation(
        dataset_path=args.dataset,
        out_path=args.out,
        checkpoint_path=args.checkpoint,
        systems=args.systems,
        limit=args.limit,
        top_k=args.top_k,
        sleep_seconds=args.sleep,
        judge=args.judge,
        from_checkpoint=args.from_checkpoint,
    )


if __name__ == "__main__":
    main()
