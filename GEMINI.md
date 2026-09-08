# GEMINI.md: Antigravity & Gemini CLI Workspace Rules

This file is automatically discovered and loaded by Google Antigravity and Gemini CLI agents working in the `acdp-platform` workspace.

---

## 1. Master Agent Contract

All agents operating in this workspace must strictly abide by the rules, operational modes, and procedures documented in:
👉 **[`AGENTS.md`](./AGENTS.md)**

---

## 2. Antigravity-Specific Operational Directives

1. **Direction & Prompting**: Read [`docs/HOW_TO_USE.md`](./docs/HOW_TO_USE.md) to understand project context, user workflows, and prompting templates.
2. **Specialized Skills Activation**: When prompted for academic research, thesis drafting, slides, competitor benchmarking, or experiments, inspect and activate the modular skills located in:
   - `.agents/skills/academic-researcher/SKILL.md`
   - `.agents/skills/thesis-writer/SKILL.md`
   - `.agents/skills/defense-pitch-builder/SKILL.md`
   - `.agents/skills/competitor-benchmark/SKILL.md`
   - `.agents/skills/experiment-evaluator/SKILL.md`
3. **Notion Deliverables**: When completing research or technical spikes corresponding to Notion tasks, log deliverables under `docs/deliverables/` and update [`docs/tasks/notion-task-mapping.md`](./docs/tasks/notion-task-mapping.md).
4. **Spec-Driven Implementation**: Before generating pipeline or application code, verify the corresponding specification in [`docs/specs/`](./docs/specs/).
5. **No Empty Directory Trees**: Do not create placeholder skeletons. Code folders are created Just-In-Time (JIT) during active coding.
6. **No Git Commands**: Do NOT run `git add`, `git commit`, or `git push`. Leave all git operations to the user.
