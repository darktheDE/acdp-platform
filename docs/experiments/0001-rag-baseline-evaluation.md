# EXP-0001: RAG Baseline Evaluation Protocol (Ragas Framework)

- **Experiment ID**: `EXP-0001`
- **Related Spec**: `docs/specs/0003-rag-regulation-assistant-spec.md`
- **Target Phase**: Phase 1: TLCN MVP
- **Responsible**: Nguyen Van Quang Duy

---

## 1. Hypothesis & Objective

We hypothesize that combining **BM25 Lexical Search with Qdrant Dense Embeddings (Hybrid Search) followed by Cross-Encoder Re-ranking** will outperform pure vector search in answering academic competition rules, achieving a **Faithfulness score $> 0.90$** and an **Answer Relevance score $> 0.85$** evaluated via the Ragas framework.

---

## 2. Experimental Setup

### Retrieval Architectures Compared
1. **Baseline A**: Pure Dense Vector Search (cosine similarity on `sentence-transformers/paraphrase-multilingual-mpnet-base-v2`).
2. **Baseline B**: Pure BM25 Lexical Keyword Search.
3. **Proposed System (ACDP)**: Reciprocal Rank Fusion (RRF) combining BM25 and Dense Vectors, followed by a Cross-Encoder Re-ranker (`BAAI/bge-reranker-large`).

### Benchmark Dataset
- 20 synthetic and human-annotated test queries covering:
  - Registration deadlines and date constraints.
  - Team composition restrictions (e.g. max members per team, inter-university rules).
  - Programming language and framework requirements.
  - Prize distribution and award criteria.

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
Results will be generated via Python test scripts invoking `ragas` and logged in a comparative table here upon completion.
