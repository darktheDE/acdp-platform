# CLAUDE.md: Claude Code Configuration & Standing Brief

## Behavioral Contract
All operations in this repository are governed by the master specifications:
👉 **Read [`AGENTS.md`](./AGENTS.md) and [`docs/frameworks/PROMPT_EXECUTION_FRAMEWORK.md`](./docs/frameworks/PROMPT_EXECUTION_FRAMEWORK.md)**.

---

## The 4 Adaptive Execution Pathways
1. **Full Pipeline (Pathway A)**: Research, thesis drafting, core Lakehouse/RAG development.
2. **Rapid Prototyping (Pathway B)**: UI mockups, visual HTML previews with mock data stubs.
3. **Direct Knowledge (Pathway C)**: Concise 2–3 paragraph answers for quick inquiries.
4. **Disambiguation (Pathway D)**: Offer 2–3 actionable choices when instructions are underspecified.

---

## Specialized Skills (`.agents/skills/`)
- Literature Review & BibTeX: `.agents/skills/academic-researcher/SKILL.md`
- Thesis Writing (FIT-HCMUTE): `.agents/skills/thesis-writer/SKILL.md`
- Presentation & Defense: `.agents/skills/defense-pitch-builder/SKILL.md`
- Competitor Benchmarks: `.agents/skills/competitor-benchmark/SKILL.md`
- Experiment Evaluation: `.agents/skills/experiment-evaluator/SKILL.md`
- Frontend UI/UX: `.agents/skills/frontend-designer/SKILL.md`

---

## Invariant Guardrails
- **Git Policy**: Never execute mutating git commands (`git add`, `git commit`, `git push`). Read-only inspection (`git status`, `git log`, `git diff`, `git show`) is allowed.
- **No Empty Directories**: Folders are created strictly Just-In-Time.
- **Notion Sync**: Log deliverables to `docs/deliverables/NT-XXXX-[slug].md` and update `docs/tasks/notion-task-mapping.md`.
- **Zero Parametric Trust**: Never trust pre-trained model weights blindly. Always search Google/internet/scholar first to ground and verify claims.
- **Institutional Naming**: Always use **Trường Đại học Công nghệ Kỹ thuật TP.HCM (HCM-UTE)**.
- **Team Directives & Memory**: Strictly follow [`docs/frameworks/TEAM_DIRECTIVES.md`](./docs/frameworks/TEAM_DIRECTIVES.md) and persist newly given user rules immediately.

