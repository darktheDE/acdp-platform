# ACDP: Academic Competition Discovery Platform
> **Building a Data Pipeline and Platform for Academic Competition Discovery, Knowledge Management, and Teammate Recommendation**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.13+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-15+-black?logo=next.js&logoColor=white)](https://nextjs.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-17+-4169E1?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![DuckDB](https://img.shields.io/badge/DuckDB-1.2+-FFF000?logo=duckdb&logoColor=black)](https://duckdb.org/)
[![Qdrant](https://img.shields.io/badge/Qdrant-1.19+-DC2626?logo=qdrant&logoColor=white)](https://qdrant.tech/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)

An end-to-end data platform that automates academic competition ingestion, provides RAG-powered regulation query assistants, enables intelligent teammate matchmaking, and delivers faculty-level analytical dashboards.

---

[Overview](#overview) • [Key Features](#key-features) • [Architecture](#system-architecture) • [Tech Stack](#tech-stack) • [Documentation](docs/README.md) • [User & AI Guide](docs/HOW_TO_USE.md) • [Getting Started](#getting-started) • [Contributors & Advisor](#contributors--advisor)

---

## Overview

Academic competitions, hackathons, and high-impact talent programs (e.g., ICPC, National Student Olympiad in Informatics, Euréka, Student Scientific Research, Samsung Innovation Campus, VinUni AI) are vital for students to gain hands-on technical experience. However, students and academic institutions face core challenges:

- **Scattered Information**: Announcements are fragmented across external portals and social media fanpages, causing missed registration deadlines.
- **Rule Navigation & Knowledge Gap**: Complex rulebooks and the absence of centralized historical repositories (past prompts, solutions, guidelines) hinder preparation.
- **Team Formation & Mentorship Friction**: Difficulties in identifying cross-functional peers (e.g., pairing Frontend with Data/AI engineers) and connecting with faculty advisors whose research matches the competition theme.
- **Lack of Institutional Visibility**: Faculty leadership lacks consolidated analytics on student engagement, domain trends, and award tracking.

**ACDP** solves these challenges with a modern Data Engineering stack: automated multi-source web ingestion, Medallion Lakehouse storage, a Hybrid-Search RAG regulation assistant, vector-based teammate recommendation, and an interactive student web portal with administrative analytics.

---

## Key Features

- **Automated Multi-Source Data Ingestion**: Headless dynamic crawlers (Playwright, Crawl4AI) collect announcements across academic portals and social media; LLMs enforce structured JSON schemas via Pydantic.
- **Medallion Lakehouse Architecture**: Tiered data processing (`Bronze` raw payload $\rightarrow$ `Silver` cleaned & deduplicated $\rightarrow$ `Gold` curated data marts) using DuckDB, Parquet, and dbt.
- **AI-Powered Regulation Copilot**: Hybrid Search (BM25 lexical + dense vector retrieval in Qdrant) with Cross-Encoder re-ranking, strictly grounded in official contest regulations.
- **Intelligent Teammate & Advisor Matchmaking**: Vector similarity and heuristic constraints match students with complementary skills and align student teams with faculty research interests.
- **Interactive Student Portal & BI Dashboard**: Fast web application built with Next.js 15, asynchronous REST APIs with FastAPI, and administrative dashboards tracking competition trends.

---

## System Architecture

```mermaid
flowchart TD
    subgraph Ingestion["1. Data Ingestion Layer"]
        A1["Social Fanpages & Academic Portals"] --> B1["Playwright / Crawl4AI Crawlers"]
        B1 --> B2["LLM Schema Parser (Pydantic Structured Output)"]
    end

    subgraph Lakehouse["2. Storage & Lakehouse Layer (Medallion)"]
        B2 --> C1["Bronze Layer: Raw Payloads"]
        C1 --> C2["Silver Layer: Cleaned & Deduplicated (DuckDB / dbt)"]
        C2 --> C3["Gold Layer: Curated Data Marts & PostgreSQL"]
    end

    subgraph Intelligence["3. Semantic & Intelligence Layer"]
        C2 --> D1["Document Chunking & Vector Embeddings"]
        D1 --> D2["Vector Store: Qdrant / pgvector"]
        D2 --> D3["Hybrid Search (BM25 + Dense Vectors) & Re-ranking"]
        D3 --> D4["Regulation RAG Copilot & Teammate Matchmaker"]
    end

    subgraph Serving["4. Serving & Presentation Layer"]
        C3 --> E1["FastAPI Backend REST Services"]
        D4 --> E1
        E1 --> F1["Next.js Web Portal (Student Experience)"]
        E1 --> F2["Faculty Analytics & BI Dashboard"]
    end
```

---

## Tech Stack

All components use current production-ready stable releases:

| Domain | Technology & Version | Purpose |
| :--- | :--- | :--- |
| **Ingestion & Crawling** | Python 3.13+, Crawl4AI (v0.9+), Playwright (v1.48+), Scrapy (v2.12+), Pydantic (v2.10+) | Web extraction & structured schema validation |
| **Data Lakehouse & Storage** | PostgreSQL (v17+), DuckDB (v1.2+), Apache Parquet, dbt-core (v1.9+) | Medallion storage, deduplication & transformation |
| **Workflow Orchestration** | Apache Airflow (v2.10+) / Prefect (v3.0+) | Scheduled pipelines and ingestion monitoring |
| **Vector DB & Retrieval** | Qdrant (v1.19+) / pgvector (v0.8+), Sentence-Transformers (v3.1+), BM25, Cross-Encoder | Semantic search, vector embeddings & re-ranking |
| **LLM & Semantic AI** | Gemini API / OpenAI API, LangChain (v0.3+) / LlamaIndex (v0.12+) | RAG pipeline, parsing & question answering |
| **Backend REST API** | FastAPI (v0.115+), SQLAlchemy (v2.0+) / SQLModel, Uvicorn | High-performance asynchronous API endpoints |
| **Frontend & Analytics** | Next.js 15+ (App Router), React 19, TypeScript 5.6+, Tailwind CSS v4.0, Recharts | Responsive web portal & analytics dashboard |
| **DevOps & Infrastructure** | Docker, Docker Compose (v2.30+), GitHub Actions | Containerization & continuous integration |

---

## Roadmap & Project Scope

The project is conducted within the **Major in Data Engineering**, Faculty of Information Technology at Ho Chi Minh City University of Technology and Engineering (HCMUTE), structured across two consecutive phases:

### Phase 1: Special Topic Project (Tiểu luận chuyên ngành - 15-Week MVP)
- [x] Problem formulation, data schema design, and architectural modeling.
- [ ] Multi-source ingestion pipeline covering 5–10 key competition sources.
- [ ] Medallion Lakehouse implementation with event deduplication and validation rules.
- [ ] Core RAG copilot for contest rules and guideline Q&A.
- [ ] MVP web portal for contest exploration and assistant queries.
- [ ] Faculty analytics dashboard displaying contest distributions by domain.

### Phase 2: Graduation Thesis (Khóa luận tốt nghiệp - 15-Week Full System)
- [ ] Real-time streaming ingestion via webhooks and live event feeds.
- [ ] Production teammate recommendation algorithm and faculty research matchmaking.
- [ ] Historical knowledge repository with past winning solutions and project playbooks.
- [ ] Automated commendation proposals and student activity credit integration.
- [ ] Departmental administrative portal and multi-channel notification bots (Telegram/Discord).

---

## Getting Started

### Prerequisites
- [Docker](https://docs.docker.com/get-docker/) & [Docker Compose v2.30+](https://docs.docker.com/compose/)
- [Python 3.13+](https://www.python.org/downloads/)
- [Node.js 22 LTS](https://nodejs.org/) & [pnpm](https://pnpm.io/) or `npm`

### Environment Configuration
Create a `.env` file in the project root:
```bash
cp .env.example .env
```
Configure necessary credentials:
```env
# Database & Vector DB
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=acdp_db
QDRANT_URL=http://localhost:6333

# LLM Providers
OPENAI_API_KEY=your_openai_api_key
# or GEMINI_API_KEY=your_gemini_api_key

# Services
API_HOST=0.0.0.0
API_PORT=8000
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Running with Docker Compose
Start all database, vector store, backend, and frontend services:
```bash
docker-compose up -d --build
```
- **Web Application**: `http://localhost:3000`
- **FastAPI OpenAPI Documentation**: `http://localhost:8000/docs`
- **Qdrant Dashboard**: `http://localhost:6333/dashboard`

---

## Contributors & Advisor

### Core Authors
- **Do Kien Hung (Đỗ Kiến Hưng)**  
  Student ID: `23133030`  
  Major in Data Engineering, Faculty of Information Technology  
  Ho Chi Minh City University of Technology and Engineering (HCMUTE)  
  GitHub: [@darktheDE](https://github.com/darktheDE)

- **Nguyen Van Quang Duy (Nguyễn Văn Quang Duy)**  
  Student ID: `23110086`  
  Major in Data Engineering, Faculty of Information Technology  
  Ho Chi Minh City University of Technology and Engineering (HCMUTE)  
  GitHub: [@QuangDuyReal](https://github.com/QuangDuyReal)

### Scientific Advisor
- **M.Sc. Tran Quang Khai (ThS. Trần Quang Khải)**  
  Lecturer, Faculty of Information Technology  
  Ho Chi Minh City University of Technology and Engineering (HCMUTE)

---

## License

This project is licensed under the [MIT License](LICENSE).
