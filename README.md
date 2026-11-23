# ACDP: Academic Competition Discovery Platform

An end-to-end data engineering platform that automates competition discovery, provides a RAG-powered regulation query copilot, and delivers analytical OLAP marts.

---

## 1. Overview & Problem Statement

Academic hackathons, coding contests, and research challenges are crucial for student development. However, notices and rulebooks are fragmented across dynamic websites and social media, leading to missed deadlines and information asymmetry.

---

## 2. System Architecture

![ACDP System Architecture Pipeline](docs/assets/arch.png)

---

## 3. Medallion Pipeline & Tech Stack

| Lakehouse Tier | Processing Scope & Target | Core Technology | Source Module |
| :--- | :--- | :--- | :--- |
| **Bronze Layer** | Raw, lossless Markdown capture from dynamic web pages | `Crawl4AI` (`AdaptiveCrawler`) + `Cloudflare R2` (S3) | [`src/acdp/1_crawl_to_bronze.py`](src/acdp/1_crawl_to_bronze.py) |
| **Silver Layer** | Pydantic v2 structured extraction with few-shot prompting | `Instructor` + `LiteLLM` + `Pydantic v2` | [`src/acdp/2_instruction.py`](src/acdp/2_instruction.py), [`schemas.py`](src/acdp/schemas.py) |
| **Gold Layer (OLAP)** | Kimball Star Schema (`4 dim`, `3 fact`, `2 bridge`, `6 mart`) | **DuckDB** (`httpfs` over Cloudflare R2 Parquet) | [`src/acdp/4_analytics_gold.py`](src/acdp/4_analytics_gold.py), [`SPEC-0003`](docs/specs/0003-gold-dimensional-modeling-spec.md) |
| **Semantic RAG Ingestion** | Regulation clause chunking & vector indexing | `Qdrant` + `Cloudflare Workers AI (@cf/baai/bge-m3)` | [`src/acdp/3_ingest_to_qdrant.py`](src/acdp/3_ingest_to_qdrant.py) |
| **Serving & Web (OLTP + UI)** | Transactional app DB, OpenAPI 3.1 gateway, RAG Copilot & portal | `FastAPI` + `PostgreSQL 18` + `Next.js 16` + `Gemini 3.5 Flash Lite` | [`SPEC.md`](docs/specs/SPEC.md), [`SPEC-0004`](docs/specs/0004-serving-api-and-oltp-spec.md), [`SPEC-0005`](docs/specs/0005-frontend-design-system-and-ux-spec.md) |

---

## 4. Repository Layout

```text
acdp-platform/
├── apps/web/                 # Next.js 16 + Tailwind v4 + Recharts web portal (includes RAG Copilot UI)
├── src/acdp/                 # Core data pipeline and serving API modules
│   ├── api/                  # FastAPI gateway (PostgreSQL 18 OLTP + DuckDB R2 httpfs + Qdrant RAG)
│   ├── flows/                # Prefect 3.x Medallion orchestration flows (Cloudflare R2 Exclusive)
│   ├── 1_crawl_to_bronze.py  # Crawl4AI ingestion to Cloudflare R2 Bronze
│   ├── 2_instruction.py      # Instructor few-shot extraction directly to R2 Silver JSON
│   ├── 3_ingest_to_qdrant.py # Bronze-to-Qdrant BGE-M3 semantic chunking & vector ingestion
│   ├── 4_analytics_gold.py   # In-memory DuckDB Kimball Star Schema & R2 Gold Parquet materialization
│   ├── config.py             # Application & Cloudflare R2 / Workers AI configuration (AppConfig)
│   └── schemas.py            # Pydantic v2 data contracts (Competition, PrizeTier)
├── tests/                    # Unit & API integration test suites
├── docs/                     # Academic manuscripts, architecture specs, ADRs, roadmap
│   ├── assets/               # Architecture diagrams, figures, and static media
│   ├── academic/             # TLCN report draft, registration & NCKH proposal
│   ├── specs/                # Master SPEC.md & technical specs (SPEC-0001..0006)
│   └── tasks/                # Active sprint context, Notion mapping & 15-week roadmap
├── docker-compose.yml        # Docker profiles: core (Web+API+PG18+Qdrant), bi (Metabase R2), pipeline
├── Dockerfile.api            # Slim FastAPI production image with pre-installed DuckDB httpfs
├── openapi.json              # Exported OpenAPI 3.1 contract for Frontend codegen
├── pyproject.toml            # Python dependencies & optional extras (uv)
└── README.md
```

---

## 5. Quickstart

### Step 1: Install Dependencies
```bash
# Full host environment (API + Crawl4AI + Vector Ingestion + Prefect)
uv sync --all-extras
```

### Step 2: Configure Environment
Copy the template and provide your API keys:
```bash
cp .env.example .env
```
*(Required for Cloudflare R2 & Workers AI: `BUCKET_NAME`, `AWS_ENDPOINT_URL`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `CLOUDFLARE_API_TOKEN`; for LLM extraction & RAG Copilot: `GEMINI_API_KEY`; for Qdrant Cloud: `QDRANT_CLUSTER_ENDPOINT`, `QDRANT_API_KEY`).*

### Step 3: Run Verification & Pure-R2 Pipeline
```bash
# 1. Run unit tests
uv run pytest -v

# 2. Ingest competition pages to Bronze (Cloudflare R2)
uv run python src/acdp/1_crawl_to_bronze.py

# 3. Extract structured Silver schema directly to Cloudflare R2 (silver/extractions/)
uv run python src/acdp/2_instruction.py --extract

# 4. Ingest Bronze snapshots into Qdrant Vector DB (@cf/baai/bge-m3)
uv run python src/acdp/3_ingest_to_qdrant.py

# 5. Build Gold Star Schema Parquet directly on Cloudflare R2 & verify via DuckDB httpfs
uv run python -m src.acdp.4_analytics_gold --build --verify

# 6. Launch Full-Stack Web Portal & API (Docker core profile: :3000 & :8000)
docker compose --profile core up -d --build

# 7. (Optional) Launch Metabase BI (:3001) & generate DuckDB httpfs R2 init SQL
docker compose --profile bi up -d
uv run python -m src.acdp.4_analytics_gold --print-metabase-sql
```

---

## 6. Contributors & Scientific Advisor

### Core Authors
- **Đỗ Kiến Hưng** (MSSV: `23133030`) — Data Engineering, FIT, HCM-UTE — [@darktheDE](https://github.com/darktheDE)
- **Nguyễn Văn Quang Duy** (MSSV: `23110086`) — Data Engineering, FIT, HCM-UTE — [@QuangDuyReal](https://github.com/QuangDuyReal)

### Scientific Advisor
- **ThS. Trần Quang Khải** — Giảng viên Khoa Công nghệ Thông tin, Trường Đại học Công nghệ Kỹ thuật TP.HCM (HCM-UTE)

---

## 7. License

This repository is licensed under the [MIT License](LICENSE).
