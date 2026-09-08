# CLAUDE.md: Claude Code Configuration & Standing Brief

## Behavioral Contract
All operations in this repository are governed by the master specification:
👉 **Read [`AGENTS.md`](./AGENTS.md) for full role definition, 5 operational modes, and Notion workflows.**

---

## Operational Modes & Modular Skills
Claude Code must inspect the relevant skill in `.agents/skills/` before executing tasks:
- **Literature Review & BibTeX**: `.agents/skills/academic-researcher/SKILL.md`
- **Thesis Writing (FIT-HCMUTE)**: `.agents/skills/thesis-writer/SKILL.md`
- **Defense Slides & Pitching**: `.agents/skills/defense-pitch-builder/SKILL.md`
- **Competitor Benchmarking**: `.agents/skills/competitor-benchmark/SKILL.md`
- **Experiment Evaluation (Ragas)**: `.agents/skills/experiment-evaluator/SKILL.md`

---

## Key Development Commands
- **Linting & Formatting**: `ruff check .` and `ruff format .`
- **Testing**: `pytest -v`
- **Type Checking**: `mypy --config-file pyproject.toml`
- **Docker Orchestration**: `docker-compose up -d --build`

---

## Core Rules & Guardrails
1. **Direction & Prompt Cookbook**: See `docs/HOW_TO_USE.md` for project capabilities and prompt recipes.
2. **Notion Task Sync**: Save research outputs to `docs/deliverables/NT-XXXX-[slug].md` and update `docs/tasks/notion-task-mapping.md`.
3. **Spec-Driven Code**: Never write production code without an approved spec in `docs/specs/`.
4. **No Empty Directory Skeletons**: Folders (`pipelines/`, `apps/`) are created strictly Just-In-Time.
5. **No Git Execution**: Do not run `git commit`, `git add`, or `git push`. Leave git commands to the user.
