# ACDP Implementation Roadmap: 15-Week Special Topic Project (TLCN Lean MVP)

This roadmap outlines the milestones for the **Special Topic Project (Tiểu luận chuyên ngành - TLCN)** at **Trường Đại học Công nghệ Kỹ thuật TP.HCM (HCM-UTE)**, leading up to the final defense in December 2026.

In accordance with **DIR-015**, Phase 1 (TLCN) focuses on simulating the end-to-end data platform and validating technical feasibility over a curated dataset of **5–10 academic competitions** crawled on-demand. Large-scale ingestion and automated batch/realtime scheduling are scheduled for Phase 2 (Khóa luận tốt nghiệp - KLTN).

---

## Milestone Schedule (Phase 1: TLCN 15-Week MVP)

| Phase | Duration | Focus Area | Key Deliverables | Status |
| :--- | :---: | :--- | :--- | :---: |
| **M1: Foundation & Governance** | Weeks 1–3 | Architecture, R&D feasibility (`T01`, `T02`, `T08_v2`), and repository harness | Proposal, Thesis Registration, SPEC-0001, Agent Harness | ✅ Completed |
| **M2: On-Demand Ingestion & Bronze R2** | Weeks 4–6 | Crawling 5–10 curated sources (`7 sample competitions`) via `Crawl4AI` to Local & Cloudflare R2 | `data/raw/` fixtures, `src/acdp/1_crawl_to_bronze.py`, Bronze R2 sync (`NT-009`, `NT-019`) | ✅ Completed |
| **M3: Silver Extraction & DuckDB Marts** | Weeks 7–10 | Pydantic v2 `src/acdp/schemas.py`, `instructor` extraction (`src/acdp/2_instruction.py`), and DuckDB OLAP queries | `src/acdp/schemas.py`, `src/acdp/2_instruction.py`, Silver Parquet, DuckDB Kimball Star Schema (`4_analytics_gold.py`) | ✅ Completed |
| **M4: RAG Regulation Engine** | Weeks 11–12 | Qdrant vector storage, Semantic chunking, Gradio ChatInterface, and Ragas evaluation | `src/acdp/3_chatbot_mvp.py`, RAG evaluation scorecard (Ragas) | 🔄 In Progress (MVP Deployed) |
| **M5: Serving & Web Portal** | Weeks 13–14 | FastAPI backend endpoints (PostgreSQL 18 OLTP + DuckDB Gold OLAP) and Next.js 16 student portal & faculty dashboard | `src/acdp/api/`, `apps/web/`, `docker-compose.yml` (`core` profile), `tests/api/` | ✅ Completed |
| **M6: Testing & Final Defense** | Week 15 | End-to-end integration, full academic report, defense slide deck | Final TLCN manuscript (`BaoCao_TieuLuan_ChuyenNganh_KTDL.md`), committee defense | ⏳ Planned |

---

## Phase 2 Outlook: Graduation Thesis (Khóa luận tốt nghiệp - KLTN)
- Automated large-scale ingestion via GitHub Actions cron (`TASK-ING-02`) and new-contest email notifications (`TASK-SRV-05`).
- Full Cloud Free-Tier unification (`TASK-CLD-03`, `TASK-CLD-04`: Supabase OLTP, Cloudflare R2, Cloudflare Workers AI, Qdrant Cloud).
- Media branding, Fanpage (`TASK-OPS-01`), and external No-Code user feedback/ticketing platform (`TASK-OPS-02`).
- Interactive task tracking across all cycles: [`docs/tasks/index.html`](./index.html) and [`docs/tasks/task-registry.md`](./task-registry.md).
