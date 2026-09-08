# GEMINI.md: Antigravity & Gemini CLI Workspace Rules

This file is automatically discovered and loaded by Google Antigravity and Gemini CLI agents working in the `acdp-platform` workspace.

---

## 1. Master Agent Contract & Prompt Framework

All agents operating in this workspace must strictly abide by the rules and adaptive execution pathways documented in:
👉 **[`AGENTS.md`](./AGENTS.md)**  
👉 **[`docs/frameworks/PROMPT_EXECUTION_FRAMEWORK.md`](./docs/frameworks/PROMPT_EXECUTION_FRAMEWORK.md)**

---

## 2. Antigravity-Specific Operational Directives

1. **Adaptive Pathways**:
   - For research/thesis/core code $\rightarrow$ Run standard full cycle.
   - For UI mockups / visual previews $\rightarrow$ Run **Pathway B (Fast-Track)** using mock data stubs.
   - For quick queries $\rightarrow$ Answer directly in 2–3 paragraphs.
   - For ambiguous prompts $\rightarrow$ Propose 2–3 concrete options; never guess.
2. **Specialized Skills Activation**:
   - Academic Research: `.agents/skills/academic-researcher/SKILL.md`
   - Thesis Writing (FIT-HCMUTE): `.agents/skills/thesis-writer/SKILL.md`
   - Presentation & Defense: `.agents/skills/defense-pitch-builder/SKILL.md`
   - Competitor Analysis: `.agents/skills/competitor-benchmark/SKILL.md`
   - Experiment Evaluation: `.agents/skills/experiment-evaluator/SKILL.md`
   - Frontend UI/UX: `.agents/skills/frontend-designer/SKILL.md`
3. **Notion Synchronization**: Record deliverables in `docs/deliverables/` and maintain `docs/tasks/notion-task-mapping.md`.
4. **No Git Execution**: Do NOT execute any `git` commands (`git add`, `git commit`, `git push`).
