# AGENTS.md: Universal AI Agent Operating Contract & Harness
> **Repository**: `acdp-platform` (Academic Competition Discovery Platform)  
> **Authors**: Do Kien Hung (`darktheDE`) & Nguyen Van Quang Duy (`QuangDuyReal`)  
> **Scientific Advisor**: M.Sc. Tran Quang Khai  
> **Institution**: Faculty of Information Technology, Ho Chi Minh City University of Technology and Engineering (HCM-UTE) / Trường Đại học Công nghệ Kỹ thuật TP.HCM (HCM-UTE)

---

## 1. Master Operating Framework & Prompt Execution Protocol

All AI agents working in this repository (Google Antigravity, Claude Code, Cursor, Codex, Windsurf) must process every prompt through the official framework:
👉 **[`docs/frameworks/PROMPT_EXECUTION_FRAMEWORK.md`](./docs/frameworks/PROMPT_EXECUTION_FRAMEWORK.md)**

### The 4 Adaptive Execution Pathways
- **Pathway A (Full 6-Step Cycle)**: Used for formal research, thesis chapters, production pipelines, RAG API, and benchmarks.
- **Pathway B (Rapid Prototyping & Spikes)**: Used for UI mockups, visual previews, and tool spikes. Generates mock contract data stubs; never waits for missing backend layers.
- **Pathway C (Direct Knowledge / Q&A)**: Used for quick conceptual inquiries, technical comparisons, and codebase navigation. Delivers punchy 2–3 paragraph answers.
- **Pathway D (Disambiguation)**: Used for ambiguous prompts. Never guess; propose 2–3 concrete options and await user selection.

---

## 2. Specialized Skills Suite (`.agents/skills/`)

Detect user intent and activate the corresponding modular skill playbook:

| Mode / Domain | Specialized Skill Path | Key Output |
| :--- | :--- | :--- |
| **Mode 1: Academic Research** | [`.agents/skills/academic-researcher/SKILL.md`](./.agents/skills/academic-researcher/SKILL.md) | Literature matrix, BibTeX library |
| **Mode 2: Strategy & Competitors**| [`.agents/skills/competitor-benchmark/SKILL.md`](./.agents/skills/competitor-benchmark/SKILL.md) | Competitor teardowns, SWOT matrix |
| **Mode 3: Engineering & Code** | **Spec-Driven Protocol** (`docs/specs/`) | Production data pipelines, FastAPI |
| **Mode 4: Experiments & Metrics** | [`.agents/skills/experiment-evaluator/SKILL.md`](./.agents/skills/experiment-evaluator/SKILL.md) | Ragas scorecards, latency benchmarks |
| **Mode 5: Thesis & Presentation** | [`.agents/skills/thesis-writer/SKILL.md`](./.agents/skills/thesis-writer/SKILL.md)<br>[`.agents/skills/defense-pitch-builder/SKILL.md`](./.agents/skills/defense-pitch-builder/SKILL.md) | HCMUTE thesis chapters, defense slides |
| **Mode 6: Frontend & UI/UX** | [`.agents/skills/frontend-designer/SKILL.md`](./.agents/skills/frontend-designer/SKILL.md) | Visual UI mockups, Next.js 15 components |

*JIT Skill Inception*: If a recurring domain lacks a skill, complete the task using core capabilities, then instantiate a new specialized skill following the strict engineering specification in [`docs/frameworks/AGENT_SKILL_ENGINEERING_SPEC.md`](./docs/frameworks/AGENT_SKILL_ENGINEERING_SPEC.md). Skills must never be mere conversational prompts; they require structured frontmatter with negative triggers, deterministic scripts in `scripts/`, reference manuals in `references/`, and verification tests.

---

## 3. Notion Task Deliverables Protocol

The team coordinates daily work on **Notion**.
1. Inspect [`docs/tasks/notion-task-mapping.md`](./docs/tasks/notion-task-mapping.md) for active task IDs (`NT-XXXX`).
2. Record research outputs, spikes, and UI previews under `docs/deliverables/` using [`docs/deliverables/0000-deliverable-template.md`](./docs/deliverables/0000-deliverable-template.md).
3. Keep the master mapping ledger synchronized.

---

## 4. Universal Guardrails (Non-Negotiable)

1. ⚠️ **Git Operations Policy (Read-Only Inspection Allowed)**:
   - ❌ **Prohibited (Mutating)**: Never execute `git add`, `git commit`, `git push`, or create/delete branches.
   - ✅ **Permitted (Read-Only)**: Inspecting repository state via `git status`, `git log`, `git diff`, `git show` is fully allowed.
2. ❌ **NO Empty Directory Skeletons**: Folders (`apps/`, `pipelines/`) are created strictly Just-In-Time (JIT) when implementing active specifications.
3. ❌ **NO Database Dumps or Secrets in Git**: Never commit `.parquet`, `.duckdb`, `.db`, or `.env` files.
4. ❌ **NO RAG Hallucinations**: Contest regulation responses must strictly cite official source clauses and URLs.
5. ❌ **NO Silent Architectural Drift**: Altering foundational tech stack choices requires an approved RFC in `docs/rfc/`.

---

## 5. Technology Stack Standards

- **Python**: `3.13+` (Typed, Pydantic v2.10+, Ruff)
- **FastAPI**: `v0.115+` (Async REST endpoints)
- **Next.js**: `v15+` (App Router, React 19, TypeScript 5.6+, Tailwind CSS v4.0)
- **Lakehouse**: DuckDB `v1.2+`, Apache Parquet, dbt-core `v1.9+`, PostgreSQL `v17+`
- **Vector DB**: Qdrant `v1.19+` (Hybrid search: BM25 + dense vectors, Cross-Encoder re-ranking)
- **Ingestion**: Crawl4AI `v0.9+`, Playwright `v1.48+`, Scrapy `v2.12+`
- **Containers**: Docker Compose `v2.30+`

---

## 6. Team Standing Directives & Continuous Memory Protocol

All agents operating in this repository must strictly adhere to the continuous directives established by **Đỗ Kiến Hưng** and **Nguyễn Văn Quang Duy** in:
👉 **[`docs/frameworks/TEAM_DIRECTIVES.md`](./docs/frameworks/TEAM_DIRECTIVES.md)**

### Non-Negotiable Directives:
1. 🔍 **Zero Blind Trust & Verification-First Protocol**:
   - **Never trust model pre-trained weights blindly**: Pre-trained knowledge may be outdated, inaccurate, or hallucinated regarding Vietnamese university regulations, contest rules, and modern library APIs.
   - **MANDATORY FIRST ACTION**: Whenever handling user queries, verifying claims, checking library features, or extracting contest info, the agent **MUST FIRST search Google, the internet, or Google Scholar** via tools (`search_web`, `read_url_content`) to verify and ground facts before responding.
2. 🏛️ **Institutional Entity Standards**:
   - Official University Name: **Trường Đại học Công nghệ Kỹ thuật TP.HCM (HCM-UTE)**.
   - Faculty: Khoa Công nghệ Thông tin (FIT).
   - Major: Kỹ thuật Dữ liệu (Data Engineering).
3. 🧠 **Dynamic Rule Ingestion & Memory Persistence**:
   - Whenever the user specifies a new operational rule or working constraint during conversation, the agent must immediately apply it AND permanently record it in [`docs/frameworks/TEAM_DIRECTIVES.md`](./docs/frameworks/TEAM_DIRECTIVES.md) (and update `AGENTS.md` / `GEMINI.md` if universally applicable).

