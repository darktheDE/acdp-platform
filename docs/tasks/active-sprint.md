# Active Sprint & Context Memory

This document maintains the immediate context, active tasks, and session state for the ACDP project at **Trường Đại học Công nghệ Kỹ thuật TP.HCM (HCM-UTE)**. **AI agents must review this document at the start of every session and update it upon task completion.**

---

## Current Sprint: Sprint 04 (Weeks 9–10) - Lean MVP Scope Alignment & Bronze-to-Silver Extraction
- **Sprint Goal**: Verify end-to-end feasibility on the curated 5–10 competition dataset (7 sample competitions) using the minimalist tech stack (`Crawl4AI` $\rightarrow$ `Cloudflare R2 / Local` raw Markdown $\rightarrow$ `Instructor + LiteLLM` + `Pydantic v2 SilverCompetitionRecord` $\rightarrow$ `DuckDB`).
- **Target Completion**: Week 10 (November 8, 2026)

---

## Task Board

### In Progress & Code Refactoring TODOs (Lean MVP Alignment - DIR-015)
- [ ] **TODO-CODE-01 (Remove Zstandard Overhead)**: Remove `zstandard` dependency from `pyproject.toml`, `src/acdp/lakehouse/bronze.py`, `src/acdp/lakehouse/schema.py`, and `tests/test_bronze_storage.py`; switch `BronzeRecord` to store raw UTF-8 Markdown (`raw_content: str`) consistent with `src/acdp/1_crawl_to_bronze.py`.
- [ ] **TODO-CODE-02 (Unify R2 Storage Config)**: Synchronize `BUCKET_NAME`, `BRONZE_STORAGE_URI`, `SILVER_STORAGE_URI`, and `GOLD_STORAGE_URI` across `.env.example`, `src/acdp/config.py`, and `src/acdp/1_crawl_to_bronze.py`.
- [ ] **TASK-0401 (Silver LLM Extraction)**: Implement `src/acdp/2_instruction.py` using `instructor` and `litellm` to extract the 7 Markdown competition files from Bronze (`data/raw/markdown/` & R2) into validated `SilverCompetitionRecord` objects.
- [ ] **TASK-0402 (Silver Persistence & DuckDB Querying)**: Persist extracted Silver records as Parquet/JSON to Local and Cloudflare R2 (`silver/competitions.parquet`) and verify direct analytical SQL queries via `DuckDB`.

### Next Up (Backlog for Upcoming Weeks)
- [ ] **TASK-0501**: Design Gold Layer analytical queries (`Fact_Competitions` & dimensional views) directly on `DuckDB` over the 5–10 competition dataset.
- [ ] **TASK-0502**: Build RAG prototype over the 7 competition rulebooks (clause chunking + hybrid retrieval) and evaluate with Ragas (`NT-012`).
- [ ] **TASK-0601**: Expose FastAPI endpoints and Next.js 15 student portal MVP for final TLCN defense.

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
- [x] **TASK-0107**: Implement Silver Layer Competition Schema & Data Contracts (Pydantic v2 `SilverCompetitionRecord`, Deliverable `NT-020`).
- [x] **TASK-0108**: Author & update FIT-HCMUTE Specialized Topic Project Report Manuscript (`BaoCao_TieuLuan_ChuyenNganh_KTDL.md`, Deliverable `NT-021`).
- [x] **TASK-0400**: Implement `src/acdp/1_crawl_to_bronze.py` (`Crawl4AI AdaptiveCrawler` uploading raw UTF-8 Markdown of 7 competitions to Cloudflare R2).

---

## Session Memory & Context Notes
- **Lean TLCN Scope (`DIR-015`)**: Phase 1 (TLCN) strictly uses **5–10 curated competition links** crawled on-demand to simulate the data system and verify feasibility. High-volume crawling and automated batch/realtime scheduling belong to Phase 2 (Khóa luận tốt nghiệp - KLTN).
- **Minimalist Stack**: `Crawl4AI` $\rightarrow$ raw UTF-8 Markdown on `Cloudflare R2` / `Local` $\rightarrow$ `Instructor` + `Pydantic v2` $\rightarrow$ `Parquet/JSON` queried by `DuckDB`. Code cleanup tasks (`TODO-CODE-01`, `TODO-CODE-02`) are tracked above to remove legacy `zstandard` compression from `src/acdp/lakehouse/`.
