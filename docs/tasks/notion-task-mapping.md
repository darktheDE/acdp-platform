# Notion Task Mapping & Master Deliverables Ledger

This document establishes the bidirectional mapping between tasks managed on the team's **Notion Board** and the deliverables, research files, specifications, and code artifacts committed in this repository.

---

## Active Task Mapping Ledger

| Notion Task ID | Task Description | Owner | Target Phase | Linked Repo Deliverable / Artifact | Status |
| :---: | :--- | :---: | :---: | :--- | :---: |
| **NT-001** | Thesis Registration Form & Topic Proposal Formulation | Hung & Duy | Phase 1 (W1–W3) | [`docs/academic/DangKy_DeTai_TLCN.md`](../academic/DangKy_DeTai_TLCN.md) | ✅ Complete |
| **NT-002** | Scientific Research Proposal (NCKH) Manuscript Drafting | Hung & Duy | Phase 1 (W1–W3) | [`docs/academic/Proposal_NCKH_TLCN.md`](../academic/Proposal_NCKH_TLCN.md) | ✅ Complete |
| **NT-003** | Proposal Defense Presentation Deck Construction | Hung & Duy | Phase 1 (W1–W3) | [`docs/academic/Slide_Proposal_TLCN.html`](../academic/Slide_Proposal_TLCN.html) | ✅ Complete |
| **NT-004** | Literature Review & SOTA Matrix Synthesis | Hung | Phase 1 (W1–W3) | [`docs/academic/literature-review.md`](../academic/literature-review.md) | 🔄 In Progress |
| **NT-005** | BibTeX Citation Library Setup | Duy | Phase 1 (W1–W3) | [`docs/academic/references.bib`](../academic/references.bib) | ✅ Complete |
| **NT-006** | Platform Competitor Benchmarking (Devpost, Unstop) | Hung | Phase 1 (W1–W3) | [`docs/research/competitor-benchmarks.md`](../research/competitor-benchmarks.md) | 🔄 In Progress |
| **NT-007** | Foundational Architecture Decision Formulation (ADR-0001) | Hung & Duy | Phase 1 (W1–W3) | [`docs/adr/0001-medallion-lakehouse-and-rag-stack.md`](../adr/0001-medallion-lakehouse-and-rag-stack.md) | ✅ Complete |
| **NT-008** | Multi-Agent Harness & Skills Suite Deployment | Hung & Duy | Phase 1 (W1–W3) | [`AGENTS.md`](../../AGENTS.md), [`.agents/skills/`](../../.agents/skills/) | ✅ Complete |
| **NT-009** | Crawl4AI & Playwright Feasibility Spike on Social Fanpages | Hung | Phase 1 (W4–W5) | `docs/deliverables/NT-009-crawler-feasibility-spike.md` | ⏳ Planned |
| **NT-010** | Pydantic Event Schema & Extraction Prompt Design (SPEC-0002) | Duy | Phase 1 (W4–W5) | `docs/specs/0002-data-ingestion-and-schema-spec.md` | ⏳ Planned |
| **NT-011** | DuckDB Lakehouse Bronze-to-Silver Ingestion Pipeline | Hung | Phase 1 (W6–W7) | `pipelines/lakehouse/` | ⏳ Planned |
| **NT-012** | Hybrid Search (BM25 + Qdrant) RAG Prototype & Ragas Scorecard | Duy | Phase 1 (W8–W10) | `docs/experiments/0001-rag-baseline-evaluation.md` | ⏳ Planned |

---

## Instructions for Team Members
1. Whenever a new task is started on Notion, add a corresponding row to the table above.
2. When the task produces research notes, code prototypes, or meeting outcomes, summarize them in `docs/deliverables/NT-XXX-[slug].md` using the template.
3. Update the status column to `✅ Complete` when verified.
