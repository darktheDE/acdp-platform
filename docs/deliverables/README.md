# Notion Deliverables & Research Results Repository

This directory serves as the centralized repository for **deliverables, research findings, technical spikes, and experiment results** produced by the team (Do Kien Hung & Nguyen Van Quang Duy), corresponding directly to task boards maintained on **Notion**.

---

## Workflow: Connecting Notion to Repository Deliverables

```
┌─────────────────────────┐          ┌───────────────────────────────────┐
│   NOTION TASK BOARD     │          │    GIT REPOSITORY DELIVERABLES    │
│  Task ID: NT-012        │ ───────> │  File: docs/deliverables/         │
│  Title: Crawl4AI Spike  │          │        NT-012-crawl4ai-spike.md   │
│  Owner: Hung / Duy      │          │  Status: Verified & Versioned     │
└─────────────────────────┘          └───────────────────────────────────┘
```

1. **Task Execution on Notion**: When a research or engineering task is executed on Notion (e.g. *Literature analysis*, *Tech stack benchmarking*, *UI prototype review*, *Prompt engineering experiments*), record findings using [`0000-deliverable-template.md`](./0000-deliverable-template.md).
2. **File Naming Standard**: Name deliverable files with their corresponding Notion Task ID:
   `docs/deliverables/[NOTION_TASK_ID]-[short-kebab-slug].md`
   *(Example: `NT-001-crawling-feasibility-study.md`)*.
3. **Master Ledger Update**: Add an entry into the master tracking table in [`docs/tasks/notion-task-mapping.md`](../tasks/notion-task-mapping.md).

---

## Deliverable Types Stored Here
- **Research Spikes & Studies**: Technology feasibility analyses, API evaluation notes, tool trade-offs.
- **Data Schemas & Sample Payloads**: Real-world parsed competition payloads, JSON validation dumps.
- **Benchmark & Metric Reports**: Crawler speed tests, vector retrieval latency reports, RAG precision assessments.
- **Meeting Minutes & Advisor Notes**: Feedback and action items from weekly meetings with M.Sc. Tran Quang Khai.
