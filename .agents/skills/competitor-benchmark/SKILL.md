---
name: competitor-benchmark
description: Conduct comprehensive competitive benchmarking against global and domestic competition platforms, formulate SWOT matrices, and identify Unique Value Propositions (UVP).
---

# Competitor Benchmark & Strategic Analysis Skill

This skill guides the AI agent in evaluating existing academic competition platforms, hackathon aggregators, and education technology portals to benchmark ACDP's technical novelty and strategic positioning.

---

## 1. When to Activate This Skill
Activate this skill whenever the user prompts for:
- Benchmarking platforms like Devpost, Unstop (Dare2Compete), Kaggle Community Competitions, StudentCompetitions, VietChallenge.
- Conducting SWOT (Strengths, Weaknesses, Opportunities, Threats) analysis for academic proposals or thesis defense.
- Formulating the Unique Value Proposition (UVP) or product differentiation matrix.
- Updating `docs/research/competitor-benchmarks.md`.

---

## 2. Standard Competitor Analysis Protocol

### Step 1: Feature Matrix Comparison
Compare target platforms across five technical dimensions:

| Dimension | Devpost / Unstop | Traditional University Web / Fanpage | ACDP Solution |
| :--- | :--- | :--- | :--- |
| **Data Ingestion** | Manual submission by organizers | Manual admin post; scattered across social channels | **Automated multi-source crawling** (Crawl4AI + Playwright) with LLM Schema extraction |
| **Rulebook Search** | Static PDF / web text reading | Unindexed, buried in social post captions or attachments | **RAG Copilot** combining Hybrid Search (BM25 + Qdrant) with verified citations |
| **Teammate Matching** | Basic forum / self-advertisement threads | Word of mouth; informal student groups | **Vector skill similarity** & cross-functional constraint satisfaction matching |
| **Faculty Involvement** | None | Manual email / direct contact | **Faculty research interest alignment** and advisor suggestion |
| **University Analytics** | B2B enterprise dashboards only | No consolidated tracking | **Real-time Faculty BI** for student engagement, domain trends, and commendations |

### Step 2: SWOT Analysis Framework
When conducting SWOT analysis for ACDP:
- **Strengths**: Automated data ingestion eliminating manual submission barriers; localized knowledge retrieval in Vietnamese; tight alignment with university administrative needs.
- **Weaknesses**: Dependency on dynamic social media scrapers; API token costs for LLM parsing (mitigated by Bronze payload caching).
- **Opportunities**: Expansion to inter-university competition sharing across Ho Chi Minh City; integration with university credit recognition systems.
- **Threats**: Anti-scraping defenses from target websites; LLM schema parsing failures on malformed text.

### Step 3: Synthesis into Research Documentation
Store all competitive analyses and platform teardowns directly under [`docs/research/`](../../docs/research/).
