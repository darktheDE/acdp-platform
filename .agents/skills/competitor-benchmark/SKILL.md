---
name: competitor-benchmark
description: >-
  Conduct rigorous competitive benchmarking against global and domestic competition platforms,
  formulate SWOT matrices, and identify Unique Value Propositions (UVP) for ACDP.
  Use when the user asks for: competitor analysis, Devpost/Unstop comparisons, SWOT matrix, UVP formulation, or strategic positioning.
  DO NOT use for: Writing application source code, running database migrations, or designing slide deck animations.
compatibility: Markdown, Mermaid, SWOT Framework
---

# Competitor Benchmark & Strategic Analysis Skill

This skill guides the AI agent in evaluating existing academic competition platforms, hackathon aggregators, and education technology portals to benchmark ACDP's technical novelty and strategic positioning.

---

## 1. Trigger Conditions & Boundaries

- **Activate when**:
  - Benchmarking platforms like Devpost, Unstop (Dare2Compete), Kaggle Community, StudentCompetitions, VietChallenge.
  - Formulating or updating the 5-dimensional feature matrix in [`docs/research/competitor-benchmarks.md`](../../docs/research/competitor-benchmarks.md).
  - Writing the SWOT analysis for project proposals, thesis chapters, or defense slides.
  - Defining ACDP's Unique Value Proposition (UVP) against Vietnamese status-quo social media channels.
- **DO NOT activate when**:
  - Writing code implementations (FastAPI, Next.js, crawlers).
  - Parsing rulebook PDFs using Python.
  - Designing UI color palettes or CSS styles.

---

## 2. Invariant Strategic Standards

1. **Five Core Dimensions**: Every competitive assessment must compare platforms across all 5 dimensions:
   - *Data Ingestion Method* (Manual vs. Automated multi-source crawl).
   - *Rulebook Discovery & Q&A* (Static PDF vs. Grounded RAG Copilot).
   - *Teammate Matchmaking* (Ad-hoc forum vs. Vector skill complementarity).
   - *Faculty / Advisor Connection* (None vs. Research interest alignment).
   - *Institutional Analytics* (Enterprise paywall vs. Open faculty BI dashboard).
2. **Fact-Checked Platform Profiles**: Base claims on verified platform features as cataloged in [`references/competitor_profiles.md`](./references/competitor_profiles.md). Never invent pricing or feature capabilities.
3. **Actionable SWOT Quadrants**: Avoid generic filler (e.g. *"Good team"*). Every point in the SWOT matrix must be tied to a concrete engineering constraint or institutional dynamic at HCMUTE.

---

## 3. Step-by-Step Execution Protocol

### Step 1: Feature Matrix Comparison
Construct the 5-dimensional comparative matrix against Devpost, Unstop, and the Vietnamese Status Quo (Facebook groups) following [`examples/uvp_differentiation_matrix.md`](./examples/uvp_differentiation_matrix.md).

### Step 2: SWOT Formulation & Strategic Synthesis
Analyze the 4 quadrants:
- **Strengths**: Automated headless ingestion, native Vietnamese LLM parsing, tailored to academic credit workflows.
- **Weaknesses**: Dependency on dynamic social DOMs, API token budget constraints.
- **Opportunities**: Institutional adoption across Ho Chi Minh City university clusters, integration with student activity points.
- **Threats**: Source platform anti-bot measures, LLM extraction rate limits.

### Step 3: Format & Rigor Verification Gate
Always execute the automated benchmark format validator:
```bash
python .agents/skills/competitor-benchmark/scripts/validate_swot_format.py --file docs/research/competitor-benchmarks.md
```

---

## 4. Edge Cases & Gotchas Catalog

| Gotcha / Common Failure Mode | Root Cause | Enforced Solution |
| :--- | :--- | :--- |
| **Confusing Hackathon vs. Contest Platforms** | Treating Kaggle (ML-only) the same as Devpost (hackathon-wide) | Clearly distinguish domain-specific platforms from general academic aggregators. |
| **Outdated Pricing / Feature Claims** | Assuming features are free when behind enterprise paywalls | Check [`references/competitor_profiles.md`](./references/competitor_profiles.md) for verified enterprise tier details. |
| **Vague SWOT Quadrants** | Listing generic points like "Competitors are strong" | Quantify: "Devpost covers < 5% of Vietnamese academic competitions". |

---

## 5. Verification Checklist

- [ ] Execute `python .agents/skills/competitor-benchmark/scripts/validate_swot_format.py --file docs/research/competitor-benchmarks.md`.
- [ ] Confirm all 5 dimensions are evaluated with concrete technical criteria.
- [ ] Ensure UVP highlights ACDP's local Vietnamese university focus.
