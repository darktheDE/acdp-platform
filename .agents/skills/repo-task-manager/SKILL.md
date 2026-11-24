---
name: repo-task-manager
description: >-
  Manage technical, architectural, and R&D tasks directly inside the repository
  using docs/tasks/tasks-data.json, docs/tasks/task-registry.md, and the interactive
  portal docs/tasks/index.html.
  Trigger on: add task, update task, task status, task management, sprint backlog,
  cycle planning, deliverables link, tasks-data.json, task-registry.md, DIR-018,
  thêm task, cập nhật task, quản lý task.
  DO NOT use for: external HTTP URL reachability checks (use url-link-verifier),
  writing FastAPI/Next.js application code, or running pytest on src/acdp/.
compatibility: Python 3.10+, Standard Library only, HTML5/Tailwind/Vanilla JS
---

# In-Repo Task Management & Deliverables Sync (`repo-task-manager`)

This skill enforces **DIR-018 (In-Repo Task Management & Notion Decommissioning)**. All code, Medallion architecture, R&D, and academic engineering tasks in `acdp-platform` live in `docs/tasks/tasks-data.json`, render to `docs/tasks/task-registry.md`, and are interactively browsed/edited in `docs/tasks/index.html`.

---

## 1. Trigger Conditions & Boundaries

- **Activate when**:
  - Adding, editing, or completing a task or sprint/cycle in `docs/tasks/`.
  - Linking a newly created deliverable (`docs/deliverables/`), spec (`docs/specs/`), or code module (`src/acdp/`) to its task ID.
  - Synchronizing `docs/tasks/tasks-data.json`, `docs/tasks/task-registry.md`, and `docs/tasks/index.html`.
- **Do not activate when**:
  - Checking external HTTP URLs (`url-link-verifier`).
  - Auditing cross-tier directive drift (`doc-decision-sync`).
  - Implementing application code in `src/acdp/` or `apps/web/`.

---

## 2. Invariant Project Standards

1. **Single Source of Truth**: `docs/tasks/tasks-data.json` is the canonical task database. Never hand-edit `docs/tasks/task-registry.md` without regenerating it via `scripts/sync_tasks.py --sync`.
2. **Scope Demarcation**: Every task must explicitly declare `TLCN (Phase 1)` or `KLTN (Phase 2)` (or `TLCN -> KLTN`).
3. **No-Code Flagging**: Tasks that rely on external platforms (e.g., Google Forms, Plane, Fanpage) without custom codebase implementation must set `"is_no_code": true` and `"task_type": "No-Code / External Integration"`.
4. **In-Repo Only**: Keep all task titles, descriptions, and deliverables strictly within the in-repo registry (`tasks-data.json`, `task-registry.md`, `index.html`).

---

## 3. Step-by-Step Execution Protocol

### Step 1: Update `docs/tasks/tasks-data.json`
Consult [`references/task_schema.md`](./references/task_schema.md) and [`examples/sample_task_entry.json`](./examples/sample_task_entry.json) when adding or updating a task entry.

### Step 2: Synchronize Registry & Interactive Portal
Run the deterministic sync script to validate schema, regenerate `docs/tasks/task-registry.md`, and embed the latest JSON into `docs/tasks/index.html`:

```powershell
uv run python .agents/skills/repo-task-manager/scripts/sync_tasks.py --sync
```

### Step 3: Verify Integrity
Run both the unit tests and the strict validation gate:

```powershell
uv run python .agents/skills/repo-task-manager/scripts/test_sync_tasks.py
uv run python .agents/skills/repo-task-manager/scripts/sync_tasks.py --validate
```

---

## 4. Edge Cases & Gotchas

| Scenario / Failure Mode | Root Cause | Remediation |
| :--- | :--- | :--- |
| `index.html` shows stale tasks when opened via `file:///` | Browsers block `fetch('tasks-data.json')` on `file:///` due to CORS | `sync_tasks.py --sync` embeds `window.__ACDP_TASKS_DATA__` directly inside `index.html` |
| `sync_tasks.py --validate` fails on `done` task | A file path listed in `deliverables` does not exist on disk | Fix the relative path or create the deliverable before marking `status: "done"` |
| `detect_ai_slop.py` flags `task-registry.md` | Title Case headings or banned slop words in task titles | Keep headings in Sentence case and use concise, technical phrasing |

---

## 5. Reference Links

- Task JSON Schema: [`references/task_schema.md`](./references/task_schema.md)
- Sample Task Entry: [`examples/sample_task_entry.json`](./examples/sample_task_entry.json)
- Deterministic Sync Script: [`scripts/sync_tasks.py`](./scripts/sync_tasks.py)
- Unit Test Suite: [`scripts/test_sync_tasks.py`](./scripts/test_sync_tasks.py)
