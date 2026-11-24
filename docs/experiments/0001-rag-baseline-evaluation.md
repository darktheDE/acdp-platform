# EXP-0001: Dual-Layer RAG (v2) Baseline Evaluation Protocol (Ragas Framework)

- **Experiment ID**: `EXP-0001`
- **Related Task**: `NT-012`
- **Related Code**: `src/acdp/v2/rag_ingest.py`, `src/acdp/api/services/rag_service.py`
- **Target Phase**: Phase 1: TLCN MVP
- **Responsible**: Nguyen Van Quang Duy & Do Kien Hung

---

## 1. Hypothesis & Objective

We hypothesize that **Dual-Layer RAG** — combining **Silver Clean Markdown** chunks (`SemanticChunker` + Cloudflare Workers AI `@cf/baai/bge-m3`, 1024 dims) with **Gold OBT Metadata Pre-Filtering** (`gold/mart_competition_explorer.parquet` fields such as `domain_groups`, `mode_canonical`, `is_free`, `registration_status`, `team_size_max`) on Qdrant Cloud, synthesized by `gemini-3.5-flash-lite` — will outperform naive dense vector search in answering academic competition rules, achieving a **Faithfulness score $\ge 0.90$** and an **Answer Relevance score $\ge 0.85$** evaluated via the Ragas framework.

---

## 2. Experimental Setup

### Retrieval Architectures Compared
1. **Baseline A (Naive Dense)**: Pure Dense Vector Search on Qdrant Cloud (`@cf/baai/bge-m3`, cosine similarity) without metadata pre-filtering.
2. **Baseline B (Lexical BM25)**: Pure BM25 Lexical Keyword Search over Silver Clean Markdown chunks.
3. **Proposed System (ACDP v2 Dual-Layer RAG)**: Qdrant Cloud Dense Vector Search (`@cf/baai/bge-m3`) with **Gold Mart Payload Pre-Filtering** (`competition_key`, `domain_groups`, `mode_canonical`, `is_free`, `registration_status`, `team_size_min`, `team_size_max`) + `gemini-3.5-flash-lite` citation-grounded synthesis.

### Benchmark Dataset
- 20 synthetic and human-annotated test queries covering:
  - Registration deadlines and date constraints.
  - Team composition restrictions (e.g. max members per team, inter-university rules).
  - Domain eligibility (`AI/Data`, `Cybersecurity`, `Programming`, etc.) and participation mode (`online`, `offline`, `hybrid`).
  - Prize distribution, scholarships, and award criteria.

---

## 3. Evaluation Metrics & Target Scorecard

| Metric | Scientific Question | Target Score |
| :--- | :--- | :---: |
| **Faithfulness** | Does the answer contain only facts supported by the retrieved context? | $\ge 0.90$ |
| **Answer Relevance** | Is the response directly addressing the user's specific query? | $\ge 0.85$ |
| **Context Precision** | Are the truly relevant rule clauses ranked in the top 3 positions? | $\ge 0.85$ |
| **Context Recall** | Were all necessary conditions retrieved from the rulebook? | $\ge 0.80$ |
| **End-to-End Latency** | Time elapsed from query submission to complete synthesized response | $\le 2.5\text{ seconds}$ |

---

## 4. Execution Plan, Engineering Findings & Results Status

### 4.1. Implemented Evaluation Harness & Pipeline Fixes
- **Gold Pre-Filtering in Serving (`src/acdp/api/services/rag_service.py`)**: Added rule-based `infer_gold_filters()` and `build_gold_filter()` (`mode_canonical`, `registration_status`, `domain_slugs`, `is_free`) with zero extra LLM tokens and automatic unfiltered fallback when strict filters return 0 chunks.
- **Qdrant Cloud Payload Indexes**: Created all 7 payload indexes (`metadata.domain`, `metadata.canonical_url`, `metadata.competition_key`, `metadata.domain_slugs`, `metadata.mode_canonical`, `metadata.registration_status`, `metadata.is_free`) on `acdp_competitions_bge_m3` (778 points) after observing HTTP 400 index-missing errors on filtered queries.
- **Fallback Chain Hardening (`src/acdp/config.py`)**: Replaced deprecated fallback models (`llama-3.3-70b-versatile` on Groq → `qwen/qwen3.8-27b`; `meta-llama/llama-3.3-70b-instruct:free` on OpenRouter → `google/gemma-4-31b-it:free`).
- **Evaluation Harness & Dataset**: Implemented `src/acdp/v2/rag_eval.py` (with generation checkpointing and `--judge groq|gemini`) and `docs/experiments/data/0001-golden-queries.jsonl` (20 grounded queries across `deadline`, `team_size`, `domain_mode`, `prize`).

### 4.2. Execution Status (Pending Quota Reset)
- **Unit & API Regression Tests**: `uv run pytest tests/test_rag_eval.py tests/api/test_rag_and_openapi.py -q` and `ruff check` passed.
- **Live Ragas Benchmark**: Paused due to Free Tier quota exhaustion across all 3 LLM providers (`gemini-3.5-flash-lite` 500 RPD limit, Groq `qwen/qwen3.8-27b` and OpenRouter `google/gemma-4-31b-it:free` 429 rate limits during 60-query generation + 240-task Ragas judging).
- **Re-run Command (after quota reset)**:
  ```powershell
  uv run python -u -m acdp.v2.rag_eval --systems A B C --sleep 4.2 --judge groq
  # If scoring is interrupted after generation checkpoint:
  uv run python -u -m acdp.v2.rag_eval --from-checkpoint --judge groq
  ```

| System | Faithfulness | Answer Relevance | Context Precision | Context Recall | Latency p50 / p95 |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Baseline A (Naive Dense)** | *Pending* | *Pending* | *Pending* | *Pending* | *Pending* |
| **Baseline B (BM25)** | *Pending* | *Pending* | *Pending* | *Pending* | *Pending* |
| **Proposed C (Dual-Layer + Gold Filter)** | *Pending* | *Pending* | *Pending* | *Pending* | *Pending* |

---

## 5. Search Provenance & References (DIR-020)
- **Query**: `Ragas 0.4 evaluate faithfulness context_precision context_recall answer_relevancy custom LLM embeddings LangchainLLMWrapper 2026`
- **References**:
  - Ragas Evaluation Framework Documentation: <https://docs.ragas.io/>
  - Qdrant Payload Indexing & Filtering Documentation: <https://qdrant.tech/documentation/concepts/indexing/>
