# Active Sprint & Context Memory

This document maintains the immediate context, active tasks, and session state for the ACDP project. **AI agents must review this document at the start of every session and update it upon task completion.**

---

## Current Sprint: Sprint 01 - Foundation, Harness & Ingestion Design
- **Sprint Goal**: Establish a robust multi-agent harness, documentation taxonomy, and prepare the first ingestion specification (SPEC-0002).
- **Target Completion**: Week 3

---

## Task Board

### In Progress
- [ ] **TASK-0101**: Finalize multi-agent harness (`AGENTS.md`, `GEMINI.md`, `CLAUDE.md`, `.cursorrules`).
- [ ] **TASK-0102**: Organize `docs/` taxonomy (`academic/`, `adr/`, `specs/`, `tasks/`, `rfc/`).

### Next Up (Backlog for Current Sprint)
- [ ] **TASK-0103**: Draft `docs/specs/0002-data-ingestion-and-schema-spec.md` for multi-source competition scraping.
- [ ] **TASK-0104**: Setup Python environment management (`pyproject.toml` or `uv.lock`) with latest production versions.

### Completed
- [x] **TASK-0001**: Initialize GitHub repository (`acdp-platform`) with professional `.gitignore`, `LICENSE` (MIT), `.env.example`, and issue templates.
- [x] **TASK-0002**: Relocate thesis proposal and registration documents into `docs/academic/`.
- [x] **TASK-0003**: Formulate ADR-0001 (Architecture, Medallion Lakehouse, Hybrid RAG).
- [x] **TASK-0004**: Formulate SPEC-0001 (System Foundation and Configuration Standards).
- [x] **TASK-0105**: Resolve business dilemmas & technical feasibility review for [`docs/rd-tasks/T01.md`](../rd-tasks/T01.md) (Deliverable NT-013).
- [x] **TASK-0106**: Complete academic competition survey and phased ingestion scaling roadmap for [`docs/rd-tasks/T02.md`](../rd-tasks/T02.md) (Deliverable NT-014).

---

## Session Memory & Context Notes
- **Codebase Rule**: Do not create empty folder skeletons. Follow the Just-in-Time (JIT) inception rule specified in `SPEC-0001`.
- **Tech Stack Baseline**: Python 3.13+, Next.js 15+, FastAPI 0.115+, DuckDB 1.2+, PostgreSQL 17+, Qdrant 1.19+, Crawl4AI 0.9+, Playwright 1.48+, dbt-core 1.9+.
