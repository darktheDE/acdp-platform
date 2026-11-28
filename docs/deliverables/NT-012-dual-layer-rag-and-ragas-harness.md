# Deliverable NT-012: Dual-Layer RAG (v2) & Ragas Baseline Harness

- **Task ID**: `NT-012`
- **Cycle / Scope**: `Cycle 03` | `TLCN (Phase 1)` | `Serving & Web`
- **Status**: `In Progress` (Harness, Gold Pre-Filter, Qdrant Indexes & Unit Tests Complete; Live 20-Query Ragas Scoring Pending Quota Reset)
- **Date**: `2026-11-24`

---

## 1. Summary of Implemented Changes

### 1.1. Gold OBT Pre-Filtering in Serving RAG (`src/acdp/api/services/rag_service.py`)
- Added `RetrievalConfig` and `RetrievedChunk` dataclasses to decouple retrieval from generation/caching for both production serving and Ragas ablation.
- Added rule-based `infer_gold_filters(message)` (0 extra LLM tokens) extracting structured intents (`is_free`, `mode_canonical`, `registration_status`, `domain_slugs`) and `build_gold_filter()` constructing Qdrant `Filter(must=...)` conditions.
- Added automatic relaxation: if a strict Gold pre-filter returns 0 points, `retrieve_contexts()` falls back to unfiltered vector search (retaining `domain_filter` if set).

### 1.2. Qdrant Cloud Payload Indexes & Fallback Chain Hardening (`src/acdp/config.py`)
- Created all 7 payload indexes (`metadata.domain`, `metadata.canonical_url`, `metadata.competition_key`, `metadata.domain_slugs`, `metadata.mode_canonical`, `metadata.registration_status`, `metadata.is_free`) on the live Qdrant Cloud collection `acdp_competitions_bge_m3` (778 points).
- Replaced deprecated Tier-2/Tier-3 fallback models in `src/acdp/config.py`:
  - **Groq**: `llama-3.3-70b-versatile` (404) → `qwen/qwen3.8-27b`
  - **OpenRouter**: `meta-llama/llama-3.3-70b-instruct:free` (404) → `google/gemma-4-31b-it:free`

### 1.3. Ragas Evaluation Harness & Golden Dataset
- **`src/acdp/v2/rag_eval.py`**: Compares **System A** (Naive Dense), **System B** (Lexical BM25 via `rank_bm25` over Qdrant chunks), and **System C** (Dual-Layer + Gold Pre-Filter) using Ragas (`Faithfulness`, `AnswerRelevancy(strictness=1)`, `LLMContextPrecisionWithReference`, `LLMContextRecall`), latency p50/p95, generation checkpointing (`--from-checkpoint`), and `--judge groq|gemini`.
- **`docs/experiments/data/0001-golden-queries.jsonl`**: 20 grounded queries across `deadline`, `team_size`, `domain_mode`, and `prize` derived from the 24 Gold records on R2.
- **`tests/test_rag_eval.py`**: Offline unit tests for filter inference, Qdrant filter construction, BM25 ranking, dataset validation, and metric aggregation.

---

## 2. Verification & Next Run Command
- Offline unit & API regression tests (`pytest tests/test_rag_eval.py tests/api/test_rag_and_openapi.py`) and `ruff check` verified.
- Live 20-query Ragas run paused after exhausting Free Tier daily/rate quotas across Gemini (`500 RPD`), Groq (`429`), and OpenRouter (`429`). Once quotas reset, run:
  ```powershell
  uv run python -u -m acdp.v2.rag_eval --systems A B C --sleep 4.2 --judge groq
  ```
