# SPEC-0001: System Foundation, Coding Standards, and Lean Configuration

- **Status**: Approved & Active (Updated for Lean TLCN Scope - DIR-015)
- **Author(s)**: Do Kien Hung, Nguyen Van Quang Duy
- **Scientific Advisor**: M.Sc. Tran Quang Khai
- **Target Phase**: Phase 1: TLCN MVP (5–10 Competitions Feasibility Scale)

---

## 1. Objective & Scope

This specification establishes the engineering conventions, strict typing practices, configuration management, and directory inception rules for the ACDP repository at **Trường Đại học Công nghệ Kỹ thuật TP.HCM (HCM-UTE)**.

In accordance with **DIR-015**, Phase 1 (Tiểu luận chuyên ngành - TLCN) simulates the end-to-end data pipeline over a curated set of **5–10 competition sources** crawled on-demand. High-volume ingestion and automated batch/realtime scheduling are deferred to Phase 2 (Khóa luận tốt nghiệp - KLTN).

---

## 2. Minimalist Tech Stack Baseline (Phase 1 TLCN)

To match the 5–10 competition dataset scale ($\sim 1\text{ MB}$) without infrastructure bloat:
- **Ingestion**: `Crawl4AI` + `Playwright` executed on-demand via Python scripts (`src/acdp/1_crawl_to_bronze.py`).
- **Storage**: Raw UTF-8 Markdown/HTML objects stored on **Local Files (`data/raw/`)** and **Cloudflare R2 (`boto3` / S3 API)**. Unnecessary intermediate binary compression (`zstandard`) and heavy ETL daemons (`SeaweedFS`, `dbt-core`) are excluded from the mandatory TLCN Bronze-to-Gold execution path.
- **Structured Extraction**: `Instructor` + `LiteLLM` constrained by `Pydantic v2` (`Competition` and `CompetitionExtractionResult` in [`src/acdp/schemas.py`](../../src/acdp/schemas.py)).
- **Analytical Engine**: `DuckDB` in-process SQL engine querying Gold Star Schema Parquet/JSON (`4 dim_*`, `3 fact_*`, `2 bridge_*`, `6 mart_*` per [`SPEC-0003`](./0003-gold-dimensional-modeling-spec.md)).
- **Serving & Web Portal (`DIR-016` / `SPEC-0004`–`0006`)**: **FastAPI** serving gateway + **PostgreSQL 18** (OLTP App DB for accounts, bookmarks, and chat history) + **Qdrant** (RAG vector store) + **Next.js 16** (App Router, Tailwind CSS v4, Recharts).

---

## 3. Configuration Management

Runtime configurations are managed via `pydantic-settings` in [`src/acdp/config.py`](../../src/acdp/config.py), reading environment variables from `.env` with fallback to `.env.example`.

---

## 4. Python & Code Quality Standards

- **Package & Environment Manager**: `uv` (`pyproject.toml` and `uv.lock`).
- **Language Version**: Python `3.11+` / `3.13+`.
- **Typing**: Strict type annotations for function signatures and data contracts.
- **Linter & Formatter**: `ruff` for linting and formatting.
- **Data Models**: `Pydantic v2` for all schema enforcement, serialization, and validation.

---

## 5. Verification & Pending Refactoring TODOs

- [x] Configuration model validates `.env.example` without exceptions.
- [x] `uv run pytest` passes 100% of unit tests (Bronze, Silver, and Gold Star Schema).
- [x] **TODO-CODE-01**: Pruned deprecated `src/acdp/lakehouse/` in favor of clean `src/acdp/schemas.py` and removed legacy `zstandard` dependency in alignment with `DIR-015`.
- [x] **TODO-CODE-02**: Synchronized `BUCKET_NAME`, `SILVER_STORAGE_URI`, `GOLD_STORAGE_URI`, and PostgreSQL/JWT config in `src/acdp/config.py` and `.env.example`.
