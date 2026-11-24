# Project Deliverables & Research Results Repository

This directory serves as the centralized repository for **deliverables, research findings, technical spikes, and experiment results** produced by the team (Do Kien Hung & Nguyen Van Quang Duy), linked directly to the **In-Repo Task Registry** (`DIR-018`).

---

## Workflow: Connecting In-Repo Tasks to Deliverables

```
┌─────────────────────────┐          ┌───────────────────────────────────┐
│  IN-REPO TASK REGISTRY  │          │    GIT REPOSITORY DELIVERABLES    │
│  Task ID: TASK-ING-01   │ ───────> │  File: docs/deliverables/         │
│  Portal: index.html     │          │        TASK-ING-01-[slug].md      │
│  Owner: Hung / Duy      │          │  Status: Verified & Versioned     │
└─────────────────────────┘          └───────────────────────────────────┘
```

1. **Task Execution**: When a research or engineering task is executed, record findings using [`0000-deliverable-template.md`](./0000-deliverable-template.md).
2. **File Naming Standard**: Name deliverable files with their corresponding Task ID:
   `docs/deliverables/[TASK_ID]-[short-kebab-slug].md`
   *(Example: `TASK-ING-01-search-pattern-and-crawling-tradeoffs.md`)*.
3. **Master Ledger Update**: Add or update the entry in [`docs/tasks/tasks-data.json`](../tasks/tasks-data.json) and run `uv run python .agents/skills/repo-task-manager/scripts/sync_tasks.py --sync` to update [`docs/tasks/task-registry.md`](../tasks/task-registry.md) and [`docs/tasks/index.html`](../tasks/index.html).

---

## Deliverable Types Stored Here
- **Research Spikes & Studies**: Technology feasibility analyses, API evaluation notes, tool trade-offs.
- **Data Schemas & Sample Payloads**: Real-world parsed competition payloads, JSON validation dumps.
- **Benchmark & Metric Reports**: Crawler speed tests, vector retrieval latency reports, RAG precision assessments.
- **Meeting Minutes & Advisor Notes**: Feedback and action items from weekly meetings with M.Sc. Tran Quang Khai.
