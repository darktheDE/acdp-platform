# Active Sprint & Context Memory

This document maintains the immediate context, active tasks, and session state for the ACDP project at **Trường Đại học Công nghệ Kỹ thuật TP.HCM (HCM-UTE)**. **AI agents must review this document at the start of every session and update it upon task completion.**

---

## Current Sprint: Web Sprint 01 / Sprint 05 (Weeks 11–12) - Research, Gold Star Schema & Web Architecture Inception
- **Sprint Goal**: Research and document 2026–2027 tech benchmarks, Kimball Star Schema for Gold Layer (18 competitions), FastAPI + PostgreSQL 18 (OLTP) Spec-Driven Architecture, Next.js 16 + Tailwind v4 UI/UX design system, Docker resource budget (`<= 2.0 GB` core profile), and 4-tier testing procedures before coding the Web application.
- **Master Playbook**: [`docs/tasks/sprint-web-01-research-plan.md`](./sprint-web-01-research-plan.md)
- **Master Product Spec**: [`docs/specs/SPEC.md`](../specs/SPEC.md) (Business value, user personas, dashboard ROI, and end-to-end user flows)

### Web Sprint 01 Task Board (Research & Architecture Only)
- [x] **TASK-W101 (`NT-023`)**: Nghiên cứu đối sánh & bảo vệ lựa chọn Tech Stack 2026–2027 (`Next.js 16`, `Recharts`, `FastAPI`, `PostgreSQL 18`, `DuckDB`) $\rightarrow$ [`docs/rd-tasks/T14_web_and_gold_stack_evaluation.md`](../rd-tasks/T14_web_and_gold_stack_evaluation.md).
- [x] **TASK-W102 (`NT-024`)**: Thiết kế chuẩn hóa Kimball Star Schema Lớp Vàng (`4 dim_*`, `3 fact_*`, `2 bridge_*`, `6 mart_*`) khắc phục 5 lỗi của `4_analytics_gold.py` $\rightarrow$ [`docs/specs/0003-gold-dimensional-modeling-spec.md`](../specs/0003-gold-dimensional-modeling-spec.md).
- [x] **TASK-W103 (`NT-025`)**: Đặc tả Backend FastAPI, PostgreSQL 18 OLTP schema và luồng Spec-Driven Development (`OpenAPI 3.1` $\rightarrow$ `openapi-typescript`) $\rightarrow$ [`docs/specs/0004-serving-api-and-oltp-spec.md`](../specs/0004-serving-api-and-oltp-spec.md).
- [x] **TASK-W104 (`NT-026`)**: Nghiên cứu Logo SVG (3 biến thể), bảng màu Tailwind CSS v4 WCAG 2.2 AA, bố cục 3 phân hệ UI/UX và bộ Skills Frontend $\rightarrow$ [`docs/specs/0005-frontend-design-system-and-ux-spec.md`](../specs/0005-frontend-design-system-and-ux-spec.md).
- [x] **TASK-W105 (`NT-027`)**: Thiết kế Hạ tầng Docker (khóa tag phiên bản, Docker Compose profiles `core`/`bi`/`pipeline`, giới hạn RAM/CPU cho máy 16GB RAM) $\rightarrow$ [`docs/specs/0006-docker-infrastructure-and-resource-spec.md`](../specs/0006-docker-infrastructure-and-resource-spec.md).
- [x] **TASK-W106 (`NT-028`)**: Chuẩn hóa quy trình kiểm thử tự động 4 tầng, 8 edge cases bắt buộc, hướng dẫn Manual Test & sổ tay lệnh CLI $\rightarrow$ [`docs/tasks/sprint-web-01-research-plan.md`](./sprint-web-01-research-plan.md).

---

## Previous Sprint: Sprint 04 (Weeks 9–10) - Lean MVP Scope Alignment & Bronze-to-Silver Extraction
- **Sprint Goal**: Verify end-to-end feasibility on the curated 5–10 competition dataset (7 sample competitions) using the minimalist tech stack (`Crawl4AI` $\rightarrow$ `Cloudflare R2 / Local` raw Markdown $\rightarrow$ `Instructor + LiteLLM` + `Pydantic v2 SilverCompetitionRecord` $\rightarrow$ `DuckDB`).
- **Target Completion**: Week 10 (November 8, 2026)

---

## Task Board

### Completed & Code Refactoring Updates (Đợt 1 - DIR-015 / SPEC-0003)
- [x] **TODO-CODE-02 (Unify R2 Storage Config)**: Synchronized `BUCKET_NAME`, `BRONZE_STORAGE_URI`, `SILVER_STORAGE_URI`, `GOLD_STORAGE_URI`, and app/JWT/DB config across `.env.example`, `src/acdp/config.py`, `src/acdp/1_crawl_to_bronze.py`, and `src/acdp/2_instruction.py`.
- [x] **TODO-CODE-03 & Gold Star Schema (SPEC-0003)**: Added Silver Parquet export (`--save-parquet`) to `src/acdp/2_instruction.py`, removed deprecated `src/acdp/2-1_instruction.py` and `zstandard`/`deltalake` packages, and refactored `src/acdp/4_analytics_gold.py` to Kimball Star Schema + 6 `mart_*` marts (`tests/test_gold_star_schema.py`).

### Next Up (Backlog for Upcoming Weeks)
- [ ] **TASK-0502**: Run formal Ragas evaluation over `src/acdp/3_chatbot_mvp.py` (faithfulness, answer relevancy, context precision) and document results in `docs/experiments/0001-rag-baseline-evaluation.md`.
- [ ] **TASK-0601**: Expose FastAPI endpoints (with PostgreSQL 18 OLTP app DB + DuckDB Gold OLAP) and Next.js 16 (Active LTS) student portal MVP for final TLCN defense.

### Completed
- [x] **TASK-0001**: Initialize GitHub repository (`acdp-platform`) with `.gitignore`, `LICENSE` (MIT), and `.env.example`.
- [x] **TASK-0002**: Relocate thesis proposal and registration documents into `docs/academic/`.
- [x] **TASK-0003**: Formulate ADR-0001 and SPEC-0001 (System Foundation and Lean Configuration Standards).
- [x] **TASK-0101**: Finalize multi-agent harness (`AGENTS.md`, `GEMINI.md`, `CLAUDE.md`, `.cursorrules`, and 9 skills in `.agents/skills/`).
- [x] **TASK-0102**: Organize `docs/` taxonomy (`academic/`, `adr/`, `specs/`, `tasks/`, `rd-tasks/`, `deliverables/`).
- [x] **TASK-0103**: Author `docs/specs/0002-data-ingestion-and-schema-spec.md` for the 5–10 competition Lean MVP pipeline.
- [x] **TASK-0104**: Setup Python environment management (`pyproject.toml` and `uv.lock`) with `crawl4ai`, `instructor`, `litellm`, `duckdb`, `pydantic`.
- [x] **TASK-0105**: Resolve business dilemmas & technical feasibility review for [`docs/rd-tasks/T01.md`](../rd-tasks/T01.md) (Deliverable `NT-013`).
- [x] **TASK-0106**: Complete academic competition survey for [`docs/rd-tasks/T02.md`](../rd-tasks/T02.md) (Deliverable `NT-014`).
- [x] **TASK-0107**: Implement Silver Layer Competition Schema & Data Contracts (Pydantic v2 `src/acdp/schemas.py`, Deliverable `NT-020`).
- [x] **TASK-0108**: Author & update FIT-HCMUTE Specialized Topic Project Report Manuscript (`BaoCao_TieuLuan_ChuyenNganh_KTDL.md`, Deliverable `NT-021`).
- [x] **TASK-0400**: Implement `src/acdp/1_crawl_to_bronze.py` (`Crawl4AI AdaptiveCrawler` uploading raw UTF-8 Markdown of 7 competitions to Cloudflare R2).
- [x] **TODO-CODE-01**: Remove `zstandard` overhead and prune deprecated `src/acdp/lakehouse/` folder in favor of clean `src/acdp/schemas.py`.
- [x] **TASK-0401**: Implement `src/acdp/2_instruction.py` using `instructor` + Pydantic v2 `CompetitionExtractionResult` with few-shot extraction and offline fallback.
- [x] **TASK-0403**: Implement `src/acdp/3_chatbot_mvp.py` featuring RAG Chatbot MVP with Gradio ChatInterface, Qdrant vector store, `SemanticChunker`, Ollama embeddings, and Gemini generation.
- [x] **TASK-0404**: Realign unit test suite (`tests/test_silver_schema.py` and `tests/test_bronze_storage.py`) with `src/acdp/schemas.py` and Lean Bronze storage (14/14 tests passed, 100% ruff clean).
- [x] **TASK-0402**: Implement Gold Layer DuckDB Analytics & Parquet persistence (`src/acdp/4_analytics_gold.py`) materializing analytical views (`gold_category_summary`, `gold_mode_distribution`, `gold_seasonality`, `gold_top_prizes`).
- [x] **TASK-0501**: Implement Prefect 3.x Medallion workflow pipeline (`src/acdp/flows/medallion_pipeline.py`) and configure Metabase with MotherDuck DuckDB driver in `docker-compose.yml`.

---

## Session Memory & Context Notes
- **Lean TLCN Scope (`DIR-015`)**: Phase 1 (TLCN) strictly uses **5–10 curated competition links** crawled on-demand to simulate the data system and verify feasibility. High-volume crawling and automated batch/realtime scheduling belong to Phase 2 (Khóa luận tốt nghiệp - KLTN).
- **Minimalist Stack**: `Crawl4AI` $\rightarrow$ raw UTF-8 Markdown on `Cloudflare R2` / `Local` $\rightarrow$ `Instructor` + `Pydantic v2` $\rightarrow$ `Parquet/JSON` queried by `DuckDB`. Code cleanup tasks (`TODO-CODE-01`, `TODO-CODE-02`) are tracked above to remove legacy `zstandard` compression from `src/acdp/lakehouse/`.
