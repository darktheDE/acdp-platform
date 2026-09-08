# GEMINI.md: Antigravity & Gemini CLI Workspace Rules

This file is automatically loaded by Google Antigravity and Gemini CLI agents working in the `acdp-platform` workspace.

---

## 1. Master Agent Contract

All agents operating in this workspace must strictly abide by the rules, architectural tenets, and operating procedures documented in:
👉 **[`AGENTS.md`](./AGENTS.md)**

---

## 2. Antigravity-Specific Operational Directives

1. **Active Context Memory**: Always inspect [`docs/tasks/active-sprint.md`](./docs/tasks/active-sprint.md) before starting any task to review current sprint status and priorities.
2. **Spec-Driven Implementation**: Before generating or modifying pipeline or application code, verify the corresponding specification in [`docs/specs/`](./docs/specs/). If a new feature is requested, draft a spec first.
3. **No Empty Directory Trees**: Do not create empty placeholder skeletons (`apps/`, `pipelines/`). Create directory structures only when actively populating them with tested implementation code (JIT inception).
4. **Change Management**: Any modification to technology choices, storage layers, or core features must follow the 4-step RFC process outlined in [`docs/rfc/PROCESS.md`](./docs/rfc/PROCESS.md).
5. **Clean Workspace Verification**: Always run linting (`ruff check`), type checks, and unit tests before declaring any task complete.
