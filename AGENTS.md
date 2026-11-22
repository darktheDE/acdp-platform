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
| **Mode 3: Engineering & Code** | **Spec-Driven Protocol** (`docs/specs/`) | Production data pipelines, REST APIs |
| **Mode 4: Experiments & Metrics** | [`.agents/skills/experiment-evaluator/SKILL.md`](./.agents/skills/experiment-evaluator/SKILL.md) | Ragas scorecards, latency benchmarks |
| **Mode 5: Thesis & Presentation** | [`.agents/skills/thesis-writer/SKILL.md`](./.agents/skills/thesis-writer/SKILL.md)<br>[`.agents/skills/defense-pitch-builder/SKILL.md`](./.agents/skills/defense-pitch-builder/SKILL.md) | HCMUTE thesis chapters, defense slides |
| **Mode 6: Frontend & UI/UX** | [`.agents/skills/frontend-designer/SKILL.md`](./.agents/skills/frontend-designer/SKILL.md) | Visual UI mockups, Next.js 16 components |
| **Mode 7: Quality & Link Verification** | [`.agents/skills/url-link-verifier/SKILL.md`](./.agents/skills/url-link-verifier/SKILL.md) | Reachability audit, dead link detection |
| **Mode 8: Scientific Prose & Anti-Slop** | [`.agents/skills/anti-slop-scientific-writer/SKILL.md`](./.agents/skills/anti-slop-scientific-writer/SKILL.md) | Concise responses, zero AI slop/tropes, doc audit |
| **Mode 9: Visual Dossiers & HTML Reports** | [`.agents/skills/visual-dossier-reporter/SKILL.md`](./.agents/skills/visual-dossier-reporter/SKILL.md) | Single-File HTML reports, Tailwind/Mermaid/Chart dashboards |
| **Mode 10: Open Models & Ollama** | [`.agents/skills/ollama-bridge/SKILL.md`](./.agents/skills/ollama-bridge/SKILL.md) | Ollama orchestration, local SLM/embedding, Cloud API bridge |
| **Mode 11: Decision Sync & Doc Governance** | [`.agents/skills/doc-decision-sync/SKILL.md`](./.agents/skills/doc-decision-sync/SKILL.md) | 4-Tier decision propagation, drift & internal link audit |
| **Mode 12: In-Repo Task Management** | [`.agents/skills/repo-task-manager/SKILL.md`](./.agents/skills/repo-task-manager/SKILL.md) | `tasks-data.json`, `task-registry.md`, `index.html` sync |


*Implicit Intent & Auto-Activation*: Every skill in this repository must automatically activate based on the user's intent and prompt context. Never demand or expect the user to explicitly call skills by name.


---

## 3. In-Repo Task & Deliverables Management Protocol (`DIR-018`)

All code, Medallion architecture, and R&D tasks are managed directly inside the repository.
1. Inspect [`docs/tasks/task-registry.md`](./docs/tasks/task-registry.md) or open [`docs/tasks/index.html`](./docs/tasks/index.html) for active task IDs (`TASK-*`, `NT-*`).
2. Record research outputs, spikes, and UI previews under `docs/deliverables/` using [`docs/deliverables/0000-deliverable-template.md`](./docs/deliverables/0000-deliverable-template.md).
3. Keep `docs/tasks/tasks-data.json`, `docs/tasks/task-registry.md`, and `docs/tasks/index.html` synchronized via `uv run python .agents/skills/repo-task-manager/scripts/sync_tasks.py --sync`.

---

## 4. Universal Guardrails (Non-Negotiable)

1. ⚠️ **Git Operations Policy (Read-Only Inspection Allowed)**:
   - ❌ **Prohibited (Mutating)**: Never execute `git add`, `git commit`, `git push`, or create/delete branches.
   - ✅ **Permitted (Read-Only)**: Inspecting repository state via `git status`, `git log`, `git diff`, `git show` is fully allowed.
2. ❌ **NO Empty Directory Skeletons**: Folders (`apps/`, `pipelines/`) are created strictly Just-In-Time (JIT) when implementing active specifications. Preserved storage hierarchies must maintain `.gitkeep` as documented in [`data/README.md`](data/README.md).
3. ❌ **NO Database Dumps or Secrets in Git**: Never commit runtime `.parquet`, `.duckdb`, `.db`, or `.env` files. Local Lakehouse tiers under [`data/lakehouse/`](data/README.md) are strictly uncommitted. Only test fixtures under [`data/raw/`](data/README.md) and `.gitkeep` files are tracked.
4. ❌ **NO RAG Hallucinations**: Contest regulation responses must strictly cite official source clauses and URLs.
5. ❌ **NO Silent Architectural Drift**: Altering foundational tech stack choices requires an approved RFC in `docs/rfc/`.

---

## 5. Technology Governance & Active R&D Phase

In accordance with **DIR-011 (Tabula Rasa in Tech Research)**, the project is currently in the active R&D evaluation phase. Specific technologies across storage, ingestion, table formats, vector search, and serving are being benchmarked objectively under [`docs/rd-tasks/`](./docs/rd-tasks/).
- **Core Languages & Tooling Baseline**: Python `3.13+` (Typed, Pydantic v2.10+, Ruff), Docker Compose `v2.30+`.
- **No Premature Lock-in**: All layer-specific technologies are adopted only after empirical benchmark dossiers and formal mutual peer defense between Hưng and Duy, finalized via approved ADRs in `docs/adr/` and specifications in `docs/specs/`.

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
4. 🎯 **Concise Scientific Communication & Anti-Slop (DIR-007)**:
   - **Answer-First**: Lead immediately with the direct technical solution; never open with conversational throat-clearing, prompt restatements, or sycophancy.
   - **Zero AI Slop & Tropes**: Banished across all replies and documents (.md, .html) using `.agents/skills/anti-slop-scientific-writer/`.
5. ⚡ **Implicit Intent & Automatic Skill Activation (DIR-008)**:
   - All modular skills in `.agents/skills/` must automatically trigger based on user intent analysis; never wait for the user to explicitly call a skill by name.
6. 🛡️ **Tabula Rasa in Tech Research & Peer Defense Before ADR (DIR-011)**:
   - **Clean Slate for Research**: When executing technology research tasks (storage, table formats, ingestion, architecture), disregard pre-existing tech mentions in READMEs or starter templates. Treat prior setup as unverified draft placeholders; research objectively from first principles without bias toward boilerplate.
   - **Peer Defense Before ADR**: Research outputs serve as defense and debate dossiers for internal cross-examination between co-authors (Hưng & Duy). Never prematurely draft or enforce formal ADRs; ADRs are written strictly after peer defense and explicit mutual approval.
7. 📅 **Temporal Grounding (Project Anchor: September 2026 - DIR-012)**:
   - **Active Timeline**: The active project execution timestamp is permanently anchored to **September 2026 (Tháng 9/2026)**.
   - **Modern SOTA Search & Research**: When conducting technical research, verifying library APIs, assessing software licensing, or finding scientific literature, agents **MUST** anchor all internet queries and knowledge lookups to the **September 2026** reality (covering 2024–2026 advances, releases, and papers), strictly avoiding outdated, legacy information.
8. 📝 **Personal Scratchpad Governance (`.scratchpad/` - DIR-013)**:
   - `.scratchpad/` is git-ignored and strictly reserved for author drafts, long prompts, and on-demand visual reports.
   - Agents **NEVER** write to `.scratchpad/` autonomously; write operations occur strictly when explicitly instructed by the author.
9. 📊 **Living Visual Dossier & Interactive HTML Reporting (DIR-014)**:
   - Whenever the user requests research reports, deliverables, architecture deep-dives, or benchmarks, PROACTIVELY PROPOSE or GENERATE a **Single-File Interactive HTML Dossier** (Tailwind CSS CDN + Mermaid.js CDN + Chart.js CDN) alongside markdown to avoid text-heavy visual fatigue.
   - Structure in 3 tiers: (1) 1-Minute Executive Summary KPI cards, (2) Interactive Mermaid Architecture Diagrams & Chart.js Benchmark Charts, (3) Collapsible deep technical specs & code diffs.
   - Route output to `.scratchpad/<name>.html` (on-demand personal analysis) or `docs/deliverables/<name>.html` (formal project deliverable).
10. ⚡ **Lean TLCN Scope (5–10 Competitions) & Minimalist Tech Stack (DIR-015)**:
   - Phase 1 (TLCN) strictly targets a small, curated set of **5–10 competition links** executed on-demand to simulate the data pipeline and validate technical feasibility. Large-scale crawling and automated batch/realtime scheduling are deferred to Phase 2 (KLTN).
   - Maintain the leanest possible stack matching this scale: raw UTF-8 Markdown/HTML objects on Local/Cloudflare R2 (`Crawl4AI` + `boto3`), structured extraction via `Instructor` + `LiteLLM` + `Pydantic v2`, and direct analytical querying via `DuckDB` over Parquet/JSON (eliminating unnecessary `zstandard` binary payload compression, `SeaweedFS`, or `dbt` overhead in the Bronze-to-Gold ETL path).
11. 🌐 **Final Web & OLTP/OLAP Split Stack (DIR-016)**:
   - Separate transactional and analytical workloads cleanly: **PostgreSQL 18** (`postgres:18-alpine`, 17+ min) for Web OLTP App DB (user accounts, auth sessions, bookmarks, chat history), **DuckDB** (`read_only=True`) for Gold Star Schema OLAP, and **Qdrant** for RAG vector search.
   - Serving & Frontend baseline: **FastAPI** (`fastapi[standard]`, Python 3.11+/3.13+, Pydantic v2) and **Next.js 16** (Active LTS `16.4.x`, or `15.5.x` Maintenance LTS) + TypeScript + Tailwind CSS v4 + Recharts.
12. 🔄 **Atomic Decision Propagation & Zero Doc Drift (DIR-017)**:
   - Whenever any directive (`DIR-XXX`), `ADR`, `SPEC`, tech version, or file path changes, scan blast radius via `audit_doc_drift.py --impact <keyword>`, propagate edits across Tiers 0–3 in the same turn, and verify `python .agents/skills/doc-decision-sync/scripts/audit_doc_drift.py --strict` returns `0` violations.
13. 💬 **Reader-First Conciseness & Untrusted Skill Ban (DIR-019)**:
   - Keep chat responses short, plain, and reader-friendly without jargon overload. Never mention internal skills or announce anti-slop/semantic checks. Never download or execute external untrusted skills, scripts, or binaries.
14. 🔗 **Search Provenance & Verifiable References (DIR-020)**:
   - Every research report and deliverable (`docs/deliverables/`, `docs/rd-tasks/`) must include a **Search Provenance & References** section listing the exact search queries executed and direct source URLs/DOIs for human verification.



