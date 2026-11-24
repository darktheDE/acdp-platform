# Sample RAG Baseline Evaluation Scorecard (Gold Standard)

- **Experiment ID**: `EXP-0001`
- **Model Pipeline**: Hybrid Search (BM25 + Qdrant Dense Vector) + Cross-Encoder Re-ranking
- **Target Knowledge Base**: 10 Official University Competition Rulebooks (2025–2026)

---

## 1. Quantitative Scorecard Summary

| Evaluation Metric | Target Threshold | Baseline (Dense Only) | ACDP Hybrid (BM25 + Dense) | Delta Improvement | Status |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Faithfulness** | $> 0.90$ | 0.8120 | **0.9467** | $+13.47\%$ | **PASS [OK]** |
| **Answer Relevance** | $> 0.85$ | 0.7850 | **0.9167** | $+13.17\%$ | **PASS [OK]** |
| **Context Precision** | $> 0.85$ | 0.7420 | **0.8967** | $+15.47\%$ | **PASS [OK]** |
| **Context Recall** | $> 0.80$ | 0.7100 | **0.8567** | $+14.67\%$ | **PASS [OK]** |

---

## 2. Latency & Resource Utilization

- **Retrieval P50 Latency**: $45\text{ ms}$
- **Retrieval P95 Latency**: $82\text{ ms}$
- **End-to-End Synthesis Latency (Gemini Flash)**: $383\text{ ms}$
- **Overall Result**: System satisfies real-time student chat requirements with zero hallucinated dates.
