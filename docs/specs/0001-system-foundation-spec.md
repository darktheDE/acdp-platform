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

To match the 5–10 competition dataset scale ($\sim 1\text{ MB}$) without infrastructure bloat (`DIR-015`, `DIR-021`, `DIR-022`, `RFC-0001`):
- **Ingestion**: 3-Tier Discovery (`src/acdp/v2/discovery.py`) + `Crawl4AI` + `Playwright` executed on-demand via [`src/acdp/v2/bronze_crawl.py`](../../src/acdp/v2/bronze_crawl.py) (preserving legacy `1_crawl_to_bronze.py` untouched).
- **Storage**: Raw Rendered HTML (`.html`), Clean Markdown, Silver Parquet, and Gold Parquet stored exclusively on **Cloudflare R2 (`boto3` / S3 API)** with zero local disk persistence (`DIR-021`). Unnecessary intermediate binary compression (`zstandard`) and heavy ETL daemons (`SeaweedFS`, `dbt-core`) are excluded from the mandatory TLCN Bronze-to-Gold execution path.
- **Structured Extraction**: Hybrid Deterministic Sandwich (`JSON-LD`, `og:*`, Scope Gate `DIR-022`) + `Instructor` constrained by `Pydantic v2` (`Competition` and `CompetitionExtractionResult` in [`src/acdp/v2/schemas.py`](../../src/acdp/v2/schemas.py) via [`src/acdp/v2/silver_transform.py`](../../src/acdp/v2/silver_transform.py)).
- **Analytical Engine**: `DuckDB 1.5.6` querying Gold Star Schema Parquet directly on Cloudflare R2 via `httpfs` (`4 dim_*`, `3 fact_*`, `2 bridge_*`, `6 mart_*` per [`SPEC-0003`](./0003-gold-dimensional-modeling-spec.md) and [`src/acdp/v2/gold_star_schema.py`](../../src/acdp/v2/gold_star_schema.py)).
- **Serving & Web Portal (`DIR-016` / `ADR-0002` / `SPEC-0004`–`0006`)**: **FastAPI** serving gateway + **PostgreSQL 17+/18** (Supabase Cloud Free / Docker `postgres:18.7-alpine3.23` OLTP App DB) + **Qdrant `v1.20.x`** (`@cf/baai/bge-m3` RAG vector store) + **Next.js 16** (App Router, Tailwind CSS v4, Recharts).

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
