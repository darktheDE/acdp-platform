---
name: experiment-evaluator
description: >-
  Design empirical experiments, measure quantitative evaluation metrics (Ragas for RAG evaluation,
  query latency benchmarks, crawler throughput, schema extraction accuracy), and generate scientific scorecards.
  Use when the user asks for: Ragas evaluation, latency benchmarks, experiment scorecards, ablation studies, or empirical testing.
  DO NOT use for: Writing frontend CSS styling, drafting general thesis introduction prose, or configuring docker containers.
compatibility: Python 3.13+, Ragas, DuckDB, Qdrant, Markdown
---

# Experiment Evaluator Skill

This skill guides the AI agent in designing, executing, and analyzing empirical experiments for the ACDP project, ensuring rigorous scientific evaluation for the thesis report and defense committee under FIT-HCMUTE standards.

---

## 1. Trigger Conditions & Boundaries

- **Activate when**:
  - Designing evaluation frameworks for the RAG competition regulation assistant.
  - Benchmarking query throughput and latency across DuckDB (Silver tier) vs. PostgreSQL (Gold tier).
  - Measuring crawler extraction resilience and schema parsing error rates across different LLM backends.
  - Generating evaluation scorecards and ablation study logs in [`docs/experiments/`](../../docs/experiments/).
- **DO NOT activate when**:
  - Building Next.js 15 frontend components (`apps/web/`).
  - Writing thesis narrative chapters without numerical data.
  - Designing presentation slide animations.

---

## 2. Invariant Empirical Standards

1. **Ragas Metrics Quad**: Every RAG assessment must measure and report all 4 standard Ragas metrics:
   - *Faithfulness* ($> 0.90$ target).
   - *Answer Relevance* ($> 0.85$ target).
   - *Context Precision* ($> 0.85$ target).
   - *Context Recall* ($> 0.80$ target).
   Detailed formulas are defined in [`references/ragas_metric_definitions.md`](./references/ragas_metric_definitions.md).
2. **Deterministic Metric Computation**: Never ask the LLM to invent summary numbers. Calculate mean, P95, and standard deviation using the deterministic scorecard script.
3. **Statistical Soundness**: Latency benchmarks must run a minimum of 5 warm-up iterations and report P50, P95, and P99 latency percentiles rather than simple arithmetic averages.

---

## 3. Step-by-Step Execution Protocol

### Step 1: Benchmark Dataset & Ground Truth Preparation
Prepare a synthetic or curated evaluation set containing at least 20 question-context-ground_truth triples covering diverse contest rule types (eligibility, dates, prizes, team constraints).

### Step 2: Metric Computation via Script
Execute the deterministic scorecard generator script:
```bash
python .agents/skills/experiment-evaluator/scripts/compute_ragas_scorecard.py --input <path-to-json-results>
```

### Step 3: Synthesis into Experiment Deliverable
Record findings under `docs/experiments/XXXX-[experiment-name].md` adhering to the reference format in [`examples/sample_evaluation_scorecard.md`](./examples/sample_evaluation_scorecard.md).

---

## 4. Edge Cases & Gotchas Catalog

| Gotcha / Common Failure Mode | Root Cause | Enforced Solution |
| :--- | :--- | :--- |
| **Evaluating RAG without Ground Truth** | Relying purely on LLM subjective impressions | Always curate a verified ground-truth answer set from official PDF rulebooks before scoring. |
| **Cold-Start Bias in Latency Tests** | Measuring initial database connection or model loading time | Execute 5 unmeasured "warm-up" queries before beginning latency metric capture. |
| **Data Leakage in Ablation Tests** | Exposing evaluation test queries to the retrieval index during chunking | Keep the test query bank completely isolated from index creation. |

---

## 5. Verification Checklist

- [ ] Execute `python .agents/skills/experiment-evaluator/scripts/compute_ragas_scorecard.py --input <data.json>`.
- [ ] Verify that Faithfulness, Answer Relevance, Context Precision, and Context Recall all exceed their target thresholds.
- [ ] Confirm P50, P95, P99 latency percentiles are documented in milliseconds.
