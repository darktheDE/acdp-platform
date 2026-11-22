# Task Schema Specification (`docs/tasks/tasks-data.json`)

## Top-Level Structure

```json
{
  "version": "1.0.0",
  "project": "ACDP (Academic Competition Discovery Platform)",
  "last_updated": "2026-11-22",
  "cycles": [
    {
      "id": "Cycle 06",
      "name": "Medallion Theory & Audit",
      "scope": "TLCN (Phase 1)",
      "goal": "..."
    }
  ],
  "tasks": [ ... ]
}
```

## Task Object Fields

| Field | Type | Required | Allowed Values / Format |
| :--- | :--- | :---: | :--- |
| `id` | `string` | Yes | Unique ID: `NT-001..NT-029` (historical) or `TASK-<LAYER>-<NN>` (`ING`, `BRZ`, `SLV`, `GLD`, `CLD`, `SRV`, `OPS`) |
| `title` | `string` | Yes | Concise task title |
| `cycle` | `string` | Yes | e.g., `Cycle 01` .. `Cycle 10` |
| `scope` | `string` | Yes | `TLCN (Phase 1)` \| `KLTN (Phase 2)` \| `TLCN -> KLTN` |
| `layer` | `string` | Yes | `Discovery` \| `Bronze` \| `Silver` \| `Gold` \| `Serving & Web` \| `Cloud & Infra` \| `Academic & Ops` |
| `task_type` | `string` | Yes | `Research & Theory` \| `Engineering` \| `Architecture` \| `No-Code / External Integration` \| `Academic` |
| `is_no_code` | `boolean` | Yes | `true` for external/no-code tasks (e.g., `TASK-OPS-02`), `false` otherwise |
| `owner` | `string` | Yes | `Hung` \| `Duy` \| `Hung & Duy` |
| `status` | `string` | Yes | `todo` \| `in_progress` \| `review` \| `done` |
| `priority` | `string` | Yes | `high` \| `medium` \| `low` |
| `problem_statement` | `string` | Yes | Why this task exists / what dilemma it resolves |
| `research_questions` | `string[]` | No | List of specific questions to answer |
| `acceptance_criteria` | `string[]` | No | Definition of Done |
| `deliverables` | `string[]` | Yes | Relative repo paths (e.g., `docs/deliverables/...`, `src/acdp/...`) |
| `notes` | `string` | No | Optional Markdown notes edited in `index.html` |
| `updated_at` | `string` | Yes | ISO date `YYYY-MM-DD` |
