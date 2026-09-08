# CLAUDE.md: Claude Code Configuration & Standing Brief

## Behavioral Contract
All operations in this repository are governed by the master specification:
👉 **Read [`AGENTS.md`](./AGENTS.md) for full role definition, constraints, and SOPs.**

---

## Key Development Commands
- **Linting & Formatting**: `ruff check .` and `ruff format .`
- **Testing**: `pytest -v` (when test suite is instantiated)
- **Type Checking**: `mypy --config-file pyproject.toml`
- **Docker Orchestration**: `docker-compose up -d --build`

---

## Core Architecture & Rules
1. **Medallion Lakehouse**:
   - `Bronze`: Raw payloads and HTML dumps.
   - `Silver`: Cleaned & deduplicated via DuckDB and dbt-core.
   - `Gold`: Curated dimensional data marts loaded into PostgreSQL.
2. **Spec-Driven Development**:
   - Never write production code without an approved spec in `docs/specs/`.
   - Before implementing, inspect `docs/tasks/active-sprint.md`.
3. **No Empty Directory Skeletons**:
   - Create directories (`pipelines/`, `apps/`) strictly Just-In-Time (JIT) when implementing active specifications.
4. **Change Management**:
   - Follow `docs/rfc/PROCESS.md` for any tech stack or architectural change.
5. **No Hallucinations in RAG**:
   - Competition regulation Q&A must cite official rulebook links and sections.

---

## Context Pointers
- **Documentation Portal**: `docs/README.md`
- **Active Task Context**: `docs/tasks/active-sprint.md`
- **Architectural Baseline**: `docs/adr/0001-medallion-lakehouse-and-rag-stack.md`
- **System Standards**: `docs/specs/0001-system-foundation-spec.md`
