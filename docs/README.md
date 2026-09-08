# ACDP Documentation Portal

Welcome to the central documentation index for the **Academic Competition Discovery Platform (ACDP)**.

This repository strictly adheres to **Spec-Driven Development** and an **Agentic Engineering Harness**. All architectural decisions, feature specifications, active tasks, and change proposals are version-controlled alongside code.

---

## Documentation Taxonomy

| Directory | Purpose | Status & Description |
| :--- | :--- | :--- |
| **[`academic/`](./academic/)** | University Deliverables | Thesis registration, scientific research proposal (NCKH), LaTeX files, defense slides, and academic prompt. |
| **[`adr/`](./adr/)** | Architecture Decision Records | Immutable log of major architectural, database, and infrastructure choices. |
| **[`specs/`](./specs/)** | Feature & Schema Specifications | Formal data schemas (Pydantic), API contracts, crawler definitions, and acceptance criteria. |
| **[`tasks/`](./tasks/)** | Task State & Memory | Long-term roadmap, active sprint context, and task execution progress. |
| **[`rfc/`](./rfc/)** | Change Management & Proposals | Formal Request for Comments (RFC) protocol for adding, modifying, or deprecating features or tech stack dependencies. |

---

## Quick Links

- **Academic Registration**: [`docs/academic/DangKy_DeTai_TLCN.md`](./academic/DangKy_DeTai_TLCN.md)
- **Scientific Research Proposal**: [`docs/academic/Proposal_NCKH_TLCN.md`](./academic/Proposal_NCKH_TLCN.md)
- **Baseline Architecture Decision**: [`docs/adr/0001-medallion-lakehouse-and-rag-stack.md`](./adr/0001-medallion-lakehouse-and-rag-stack.md)
- **Active Sprint & Next Steps**: [`docs/tasks/active-sprint.md`](./tasks/active-sprint.md)
- **Change Management Protocol**: [`docs/rfc/PROCESS.md`](./rfc/PROCESS.md)

---

## Operating Protocol for AI Agents and Developers

Before implementing any code or modifying the repository:
1. **Consult the Active Sprint**: Read [`docs/tasks/active-sprint.md`](./tasks/active-sprint.md) to understand current priorities.
2. **Review the Relevant Spec**: Locate and read the corresponding spec in [`docs/specs/`](./specs/). If no spec exists for a new feature, draft one using [`docs/specs/0000-spec-template.md`](./specs/0000-spec-template.md) first.
3. **Respect Architectural Decisions**: Never alter established patterns in [`docs/adr/`](./adr/) without going through the [`docs/rfc/PROCESS.md`](./rfc/PROCESS.md) change workflow.
4. **Just-In-Time Inception**: Only create code directories (`apps/`, `pipelines/`, `lakehouse/`) when actively writing verified code specified in a task.
