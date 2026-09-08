---
name: experiment-evaluator
description: Design empirical experiments, measure quantitative metrics (Ragas for RAG evaluation, query latency, crawler throughput), and track scientific benchmarks.
---

# Experiment Evaluator Skill

This skill guides the AI agent in designing, executing, and analyzing empirical experiments for the ACDP project, ensuring rigorous scientific evaluation for the thesis report and defense committee.

---

## 1. When to Activate This Skill
Activate this skill whenever the user prompts for:
- Designing evaluation frameworks for the RAG regulation assistant.
- Measuring and comparing query latency across storage layers (DuckDB vs. PostgreSQL).
- Benchmarking crawler extraction resilience and schema parsing error rates.
- Generating evaluation scorecards and ablation study logs in `docs/experiments/`.

---

## 2. Core Evaluation Frameworks

### 2.1. RAG Intelligence Evaluation (Ragas Framework Methodology)
Evaluate the competition rulebook question-answering assistant across four standard metrics:

| Metric | Scientific Question | Target Threshold |
| :--- | :--- | :---: |
| **Faithfulness** | Is the answer grounded exclusively in the retrieved rulebook context, with zero hallucinations? | $> 0.90$ |
| **Answer Relevance** | Does the answer directly address the student's question without extraneous filler? | $> 0.85$ |
| **Context Precision** | Are the top-ranked retrieved chunks truly relevant to the query? | $> 0.85$ |
| **Context Recall** | Did the retriever fetch all clauses necessary to form the complete answer? | $> 0.80$ |

### 2.2. Ingestion & Extraction Performance
Measure the robustness and efficiency of the Crawl4AI + Playwright + LLM Parser pipeline:
- **Crawl Success Rate**: Percentage of target URLs successfully rendered without timeouts (`Target: > 95%`).
- **Schema Extraction Accuracy**: Ratio of JSON outputs strictly passing Pydantic validation on first attempt (`Target: > 90%`).
- **Extraction Latency**: Mean time (seconds) to crawl, parse, and store one competition event (`Target: < 5s / event`).
- **Deduplication Precision / Recall**: Accuracy of fuzzy string matching in identifying duplicate cross-posted events (`Target: > 95%`).

### 2.3. Lakehouse Storage & Query Latency
Benchmark analytical query throughput comparing DuckDB (Silver tier) vs. PostgreSQL (Gold tier):
- Aggregation query speed (e.g. counting competitions by domain, calculating participant metrics).
- Vector indexing and retrieval latency in Qdrant (P50, P95, P99 query latency in milliseconds).

---

## 3. Experiment Documentation Protocol
All benchmark designs, synthetic test sets, and quantitative scorecards must be recorded under [`docs/experiments/`](../../docs/experiments/) using the format:
- `docs/experiments/XXXX-<experiment-name>.md`
- Documenting: *Hypothesis, Test Environment, Benchmark Dataset, Results Table, Visual Chart, Conclusion*.
