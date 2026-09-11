# ACDP Documentation Portal

Welcome to the central documentation index for the **Academic Competition Discovery Platform (ACDP)**.

This repository strictly adheres to **Spec-Driven Development** and an **End-to-End Academic Research & Engineering Harness**. All academic research, architectural decisions, feature specifications, empirical benchmarks, Notion deliverables, and change proposals are version-controlled alongside code.

---

## 🌟 Quick Start & AI Direction
👉 **[Read `docs/HOW_TO_USE.md`](./HOW_TO_USE.md)** for human developer onboarding and the **AI Prompt Cookbook** containing copy-paste prompts for all 5 project modes.

---

## Documentation Taxonomy

| Directory | Purpose | Status & Description |
| :--- | :--- | :--- |
| **[`frameworks/`](./frameworks/)** | Operational Frameworks | Unified Multi-Agent Framework ([`PROMPT_EXECUTION_FRAMEWORK.md`](./frameworks/PROMPT_EXECUTION_FRAMEWORK.md)), Standing Directives ([`TEAM_DIRECTIVES.md`](./frameworks/TEAM_DIRECTIVES.md)), Skill Engineering Spec ([`AGENT_SKILL_ENGINEERING_SPEC.md`](./frameworks/AGENT_SKILL_ENGINEERING_SPEC.md)). |
| **[`academic/`](./academic/)** | University Deliverables | Registration form, NCKH proposal, defense slides, BibTeX library ([`references.bib`](./academic/references.bib)), and literature review matrix ([`literature-review.md`](./academic/literature-review.md)). |
| **[`research/`](./research/)** | Strategic & Market Research | Competitor teardowns ([`competitor-benchmarks.md`](./research/competitor-benchmarks.md)) comparing Devpost, Unstop, and domestic Vietnamese channels. |
| **[`experiments/`](./experiments/)** | Empirical Benchmarks | Scientific experiment designs, RAG evaluation scorecards (Ragas framework), and latency profiles. |
| **[`deliverables/`](./deliverables/)** | Notion Task Outputs | Structured research outputs, technical spikes, and meeting minutes directly mapped to Notion task boards. |
| **[`adr/`](./adr/)** | Architecture Decision Records | Immutable log of major architectural, database, and infrastructure choices. |
| **[`specs/`](./specs/)** | Feature & Schema Specifications | Formal data schemas (Pydantic), API contracts, crawler definitions, and acceptance criteria. |
| **[`tasks/`](./tasks/)** | Task State & Notion Mapping | Notion task mapping ledger ([`notion-task-mapping.md`](./tasks/notion-task-mapping.md)), 15-week roadmap, and active sprint context. |
| **[`rd-tasks/`](./rd-tasks/)** | R&D Research Spikes | Exploratory R&D tasks authored by Duy (@QuangDuyReal) for problem formulation, scientific grounding, and cross-review ([`README.md`](./rd-tasks/README.md)). |
| **[`rfc/`](./rfc/)** | Change Management & Proposals | Formal Request for Comments (RFC) protocol for adding, modifying, or deprecating features or tech stack dependencies. |

---

## Operating Protocol for AI Agents and Developers

Before implementing any code or modifying the repository:
1. **Consult the Active Sprint**: Read [`docs/tasks/active-sprint.md`](./tasks/active-sprint.md) to understand current priorities.
2. **Review Notion Mapping**: Check [`docs/tasks/notion-task-mapping.md`](./tasks/notion-task-mapping.md) for linked deliverables.
3. **Review the Relevant Spec**: Locate and read the corresponding spec in [`docs/specs/`](./specs/). If no spec exists for a new feature, draft one using [`docs/specs/0000-spec-template.md`](./specs/0000-spec-template.md) first.
4. **Respect Architectural Decisions**: Never alter established patterns in [`docs/adr/`](./adr/) without going through the [`docs/rfc/PROCESS.md`](./rfc/PROCESS.md) change workflow.
5. **Just-In-Time Inception**: Only create code directories (`apps/`, `pipelines/`, `lakehouse/`) when actively writing verified code specified in a task.
