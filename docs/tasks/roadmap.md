# ACDP Implementation Roadmap: 15-Week Special Topic Project (TLCN Lean MVP)

This roadmap outlines the milestones for the **Special Topic Project (Tiểu luận chuyên ngành - TLCN)** at **Trường Đại học Công nghệ Kỹ thuật TP.HCM (HCM-UTE)**, leading up to the final defense in December 2026.

In accordance with **DIR-015**, Phase 1 (TLCN) focuses on simulating the end-to-end data platform and validating technical feasibility over a curated dataset of **5–10 academic competitions** crawled on-demand. Large-scale ingestion and automated batch/realtime scheduling are scheduled for Phase 2 (Khóa luận tốt nghiệp - KLTN).

---

## Milestone Schedule (Phase 1: TLCN 15-Week MVP)

| Phase | Duration | Focus Area | Key Deliverables | Status |
| :--- | :---: | :--- | :--- | :---: |
| **M1: Foundation & Governance** | Weeks 1–3 | Architecture, R&D feasibility (`T01`, `T02`, `T08_v2`), and repository harness | Proposal, Thesis Registration, SPEC-0001, Agent Harness | ✅ Completed |
| **M2: On-Demand Ingestion & Bronze R2** | Weeks 4–6 | Crawling 5–10 curated sources (`7 sample competitions`) via `Crawl4AI` to Local & Cloudflare R2 | `data/raw/` fixtures, `src/acdp/1_crawl_to_bronze.py`, Bronze R2 sync (`NT-009`, `NT-019`) | ✅ Completed |
| **M3: Silver Extraction & DuckDB Marts** | Weeks 7–10 | Pydantic v2 `SilverCompetitionRecord`, `instructor` + `litellm` extraction, and DuckDB OLAP queries | `src/acdp/lakehouse/schema.py`, `SPEC-0002`, `src/acdp/2_instruction.py`, Silver Parquet on R2 | 🔄 In Progress (Week 9) |
| **M4: RAG Regulation Engine** | Weeks 11–12 | Qdrant vector storage, BM25 Hybrid Search, Cross-Encoder over sample competition rulebooks | Rulebook clause chunking, RAG evaluation scorecard (Ragas) | ⏳ Planned |
| **M5: Serving & Web Portal** | Weeks 13–14 | FastAPI backend endpoints and Next.js 15 student portal & faculty dashboard | Interactive competition explorer, RAG chat assistant, DuckDB analytics charts | ⏳ Planned |
| **M6: Testing & Final Defense** | Week 15 | End-to-end integration, full academic report, defense slide deck | Final TLCN manuscript (`BaoCao_TieuLuan_ChuyenNganh_KTDL.md`), committee defense | ⏳ Planned |

---

## Phase 2 Outlook: Graduation Thesis (Khóa luận tốt nghiệp - KLTN)
- Automated large-scale ingestion (periodic batch jobs, seasonality scheduler, HTTP `ETag` polling, and realtime webhooks) across nationwide university portals and fanpages.
- High-volume small-file optimization (`zstandard` payload compression, `delta-rs` bin-packing `OPTIMIZE`, and self-hosted `SeaweedFS` object storage) and multi-channel fuzzy entity deduplication.
- Production teammate recommendation engine and faculty advisor research alignment.
- Historical repository of winning solutions and automated student activity credit (*điểm rèn luyện*) reporting.
