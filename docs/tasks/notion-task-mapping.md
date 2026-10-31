# Notion Task Mapping & Master Deliverables Ledger

This document establishes the bidirectional mapping between tasks managed on the team's **Notion Board** and the deliverables, research files, specifications, and code artifacts committed in this repository.

---

## Active Task Mapping Ledger

| Notion Task ID | Task Description | Owner | Target Phase | Linked Repo Deliverable / Artifact | Status |
| :---: | :--- | :---: | :---: | :--- | :---: |
| **NT-001** | Thesis Registration Form & Topic Proposal Formulation | Hung & Duy | Phase 1 (W1–W3) | [`docs/academic/DangKy_DeTai_TLCN.md`](../academic/DangKy_DeTai_TLCN.md) | ✅ Complete |
| **NT-002** | Scientific Research Proposal (NCKH) Manuscript Drafting | Hung & Duy | Phase 1 (W1–W3) | [`docs/academic/Proposal_NCKH_TLCN.md`](../academic/Proposal_NCKH_TLCN.md) | ✅ Complete |
| **NT-003** | Proposal Defense Presentation Deck Construction | Hung & Duy | Phase 1 (W1–W3) | [`docs/academic/Slide_Proposal_TLCN.html`](../academic/Slide_Proposal_TLCN.html) | ✅ Complete |
| **NT-004** | Literature Review & SOTA Matrix Synthesis | Hung | Phase 1 (W1–W3) | [`docs/academic/literature-review.md`](../academic/literature-review.md) | ✅ Complete |
| **NT-005** | BibTeX Citation Library Setup | Duy | Phase 1 (W1–W3) | [`docs/academic/references.bib`](../academic/references.bib) | ✅ Complete |
| **NT-006** | Platform Competitor Benchmarking (Devpost, Unstop) | Hung | Phase 1 (W1–W3) | [`docs/research/competitor-benchmarks.md`](../research/competitor-benchmarks.md) | ✅ Complete |
| **NT-007** | Foundational Architecture Decision Formulation (ADR-0001) | Hung & Duy | Phase 1 (W1–W3) | [`docs/adr/0001-medallion-lakehouse-and-rag-stack.md`](../adr/0001-medallion-lakehouse-and-rag-stack.md) | ✅ Complete |
| **NT-008** | Multi-Agent Harness & Skills Suite Deployment | Hung & Duy | Phase 1 (W1–W3) | [`AGENTS.md`](../../AGENTS.md), [`.agents/skills/`](../../.agents/skills/) | ✅ Complete |
| **NT-009** | On-Demand Crawl4AI Feasibility Spike on 7 Curated Competitions & R2 Upload | Duy & Hung | Phase 1 (W4–W9) | [`src/acdp/1_crawl_to_bronze.py`](../../src/acdp/1_crawl_to_bronze.py), [`data/raw/markdown/`](../../data/raw/markdown/) | ✅ Complete |
| **NT-010** | Pydantic Event Schema & Lean Extraction Spec (SPEC-0002) | Duy & Hung | Phase 1 (W6–W9) | [`docs/specs/0002-data-ingestion-and-schema-spec.md`](../specs/0002-data-ingestion-and-schema-spec.md) | ✅ Complete |
| **NT-011** | Bronze-to-Silver LLM Extraction (`instructor` + `litellm`) & DuckDB Querying | Duy & Hung | Phase 1 (W9–W10) | [`src/acdp/2_instruction.py`](../../src/acdp/2_instruction.py) | 🔄 In Progress |
| **NT-012** | Hybrid Search (BM25 + Qdrant) RAG Prototype & Ragas Scorecard | Duy | Phase 1 (W11–W12) | [`docs/experiments/0001-rag-baseline-evaluation.md`](../experiments/0001-rag-baseline-evaluation.md) | ⏳ Planned |
| **NT-013** | Business Requirements, Technical Feasibility & Architectural Review ([`T01`](../rd-tasks/T01.md)) | Hung & Duy | Phase 1 (W1–W3) | [`docs/deliverables/NT-013-business-technical-feasibility-review.md`](../deliverables/NT-013-business-technical-feasibility-review.md) | ✅ Complete |
| **NT-014** | Academic Competition Landscape Survey & Ingestion Scaling Roadmap ([`T02`](../rd-tasks/T02.md)) | Hung & Duy | Phase 1 (W1–W3) | [`docs/deliverables/NT-014-competition-landscape-survey.md`](../deliverables/NT-014-competition-landscape-survey.md) | ✅ Complete |
| **NT-017** | Problem Formulation & Thesis Introduction Drafting ([`T08_v2`](../rd-tasks/T08_v2.md)) | Duy & Hung | Phase 1 (W3–W4) | [`docs/rd-tasks/T08_v2.md`](../rd-tasks/T08_v2.md) | ✅ Complete |
| **NT-018** | Bronze Layer Storage & Open Table Format Tech Stack Evaluation ([`T13`](../rd-tasks/T13.md)) | Duy & Hung | Phase 1 (W4–W5) | [`docs/deliverables/NT-018-bronze-storage-and-table-format-evaluation.md`](../deliverables/NT-018-bronze-storage-and-table-format-evaluation.md) | ✅ Complete |
| **NT-019** | Bronze Lakehouse Engine Implementation & Lean Refactoring TODO (Remove `zstandard`) | Duy & Hung | Phase 1 (W6–W10) | [`src/acdp/lakehouse/bronze.py`](../../src/acdp/lakehouse/bronze.py), [`src/acdp/1_crawl_to_bronze.py`](../../src/acdp/1_crawl_to_bronze.py) | 🔄 TODO Refactor |
| **NT-020** | Silver Layer Competition Schema & Data Contracts Implementation | Hung & Duy | Phase 1 (W7–W8) | [`src/acdp/lakehouse/schema.py`](../../src/acdp/lakehouse/schema.py), [`tests/test_silver_schema.py`](../../tests/test_silver_schema.py) | ✅ Complete |
| **NT-021** | Comprehensive FIT-HCMUTE Specialized Topic Project Report Manuscript | Hung & Duy | Phase 1 (W7–W15) | [`docs/academic/BaoCao_TieuLuan_ChuyenNganh_KTDL.md`](../academic/BaoCao_TieuLuan_ChuyenNganh_KTDL.md) | 🔄 In Progress |
| **NT-022** | Lakehouse Cloudflare R2 Sync Technical Guide (Lean 5–10 Competition Scale) | Hung & Duy | Phase 1 (W8–W9) | [`docs/deliverables/HUONG_DAN_MIGRATE_R2_LAKEHOUSE.md`](../deliverables/HUONG_DAN_MIGRATE_R2_LAKEHOUSE.md) | ✅ Complete |

---

## Instructions for Team Members
1. Whenever a new task is started on Notion, add a corresponding row to the table above.
2. When the task produces research notes, code prototypes, or meeting outcomes, summarize them in `docs/deliverables/NT-XXX-[slug].md` using the template.
3. Update the status column to `✅ Complete` when verified.
