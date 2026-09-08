# ADR-0001: Core Architecture, Medallion Lakehouse, and Hybrid RAG Stack

- **Status**: Accepted
- **Date**: 2026-09-08
- **Deciders**: Do Kien Hung, Nguyen Van Quang Duy, M.Sc. Tran Quang Khai
- **Consulted**: Faculty of Information Technology, HCMUTE

---

## Context and Problem Statement

The Academic Competition Discovery Platform (ACDP) must solve three disparate technical challenges:
1. Ingesting volatile, semi-structured event announcements from disparate web portals and social media channels.
2. Providing analytical aggregations for university administrators (OLAP) while supporting fast, low-latency relational queries for the student application (OLTP).
3. Answering intricate natural language queries about contest regulations with zero hallucination.

We need to establish the foundational tech stack, storage architecture, and intelligence retrieval strategy for the Special Topic Project (15-week MVP) with seamless extensibility into the Graduation Thesis.

---

## Decision Drivers

- **Domain Relevance**: The project is under the Major in Data Engineering; modern data architecture (Lakehouse, dbt, Parquet) must be central.
- **Resilience Against DOM Drift**: Traditional CSS/XPath scraping breaks frequently. The ingestion mechanism must be anti-fragile.
- **Accuracy & Grounding**: In academic rules, hallucinating an eligibility requirement or submission deadline is unacceptable.
- **Resource Efficiency**: Must run cost-effectively on local workstations (Docker/WSL2) or lightweight cloud VMs without requiring multi-node Spark clusters.

---

## Considered Options

### Storage & Lakehouse
1. **Option A (Traditional Warehouse)**: Store everything directly in a monolithic PostgreSQL database.
2. **Option B (Heavyweight Big Data)**: Deploy Apache Spark + Delta Lake on a multi-node cluster.
3. **Option C (Embedded Medallion Lakehouse - Chosen)**: Tiered storage using Parquet files and DuckDB for in-process OLAP, paired with PostgreSQL for operational serving and dbt for transformations.

### Ingestion & Information Extraction
1. **Option A (Static Regex/BeautifulSoup)**: Traditional static HTML parsers.
2. **Option B (Headless Browser + LLM Schema Parser - Chosen)**: Crawl4AI and Playwright for dynamic SPA rendering, followed by LLM-guided extraction constrained by Pydantic schemas.

### AI & Retrieval Engine
1. **Option A (Pure Dense Vector Search)**: Embed rulebooks and query vector similarity directly.
2. **Option B (Hybrid Search with Re-ranking - Chosen)**: Combine BM25 lexical keyword search and dense vector retrieval in Qdrant, followed by Cross-Encoder re-ranking.

---

## Decision Outcome

**Chosen Architecture**:
1. **Lakehouse Tiering**:
   - `Bronze`: Raw, immutable web payloads, HTML dumps, and crawl metadata stored as JSON/Parquet.
   - `Silver`: Cleaned, validated, and deduplicated records managed via DuckDB and transformed with dbt-core.
   - `Gold`: Curated dimensional data marts, loaded into PostgreSQL for consumption by web consumers and faculty analytics.
2. **Anti-fragile Ingestion**:
   - Playwright & Crawl4AI for headless dynamic rendering.
   - Pydantic models enforcing strict typing on competition entities.
3. **Hybrid RAG Engine**:
   - Qdrant for vector embeddings, BM25 for precise keyword/date matching, and a Cross-Encoder for context re-ranking before LLM synthesis.
4. **Decoupled Serving**:
   - FastAPI for high-throughput asynchronous REST APIs.
   - Next.js 15 (React 19) for student and administrative web interfaces.
5. **Just-In-Time Codebase Growth**:
   - The repository will not contain empty placeholder directories. Directories (`apps/`, `pipelines/`) are instantiated only upon executing an approved feature specification.

---

## Consequences

### Positive
- High analytical performance using DuckDB without cluster overhead.
- Ingestion pipelines remain operational even when source websites alter HTML classes or layouts.
- Regulation queries achieve high precision by combining exact keyword matching (BM25) with semantic embeddings.
- Clean separation of concerns between data engineering (Python/dbt) and web presentation (Next.js).

### Negative / Trade-offs
- Multiple storage formats (Parquet, DuckDB, PostgreSQL) require clear sync pipelines and orchestration (Airflow/Prefect).
- LLM schema extraction incurs API latency and token cost, mitigated by caching raw payloads in the Bronze tier.
