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

## 4. Execution Plan & Results Logging
Results will be generated via Python test scripts invoking `ragas` against `src/acdp/api/services/rag_service.py` and logged in a comparative table here upon completion.
