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
4. **Skill Engineering Specification**: When creating or upgrading any skill, strictly adhere to [`docs/frameworks/AGENT_SKILL_ENGINEERING_SPEC.md`](./docs/frameworks/AGENT_SKILL_ENGINEERING_SPEC.md). Never create cosmetic or prompt-only skills; always provide structured frontmatter with negative triggers, deterministic scripts (`scripts/`), deep references (`references/`), and verification suites.
5. **Git Policy (Read-Only Inspection Allowed)**:
   - Never execute mutating git commands (`git add`, `git commit`, `git push`, branch creation).
   - Read-only inspection (`git status`, `git log`, `git diff`, `git show`) is allowed.
6. **Zero Parametric Trust & Verification-First**:
   - **Never trust model pre-trained weights blindly**: Model pre-trained data can be outdated, inaccurate, or hallucinated.
   - **MANDATORY FIRST ACTION**: When answering technical questions, contest rules, university facts, or research claims, **FIRST search Google, internet, and Google Scholar** (`search_web`, `read_url_content`) to verify and confirm reality before concluding.
7. **Institutional Entity Standards**:
   - University Name: **Trường Đại học Công nghệ Kỹ thuật TP.HCM (HCM-UTE)**.
   - Faculty: Khoa Công nghệ Thông tin (FIT-HCM-UTE).
   - Major: Kỹ thuật Dữ liệu (Data Engineering).
8. **Continuous Directives & Active Memory**:
   - Consult and respect all standing directives in [`docs/frameworks/TEAM_DIRECTIVES.md`](./docs/frameworks/TEAM_DIRECTIVES.md).
   - When the user issues any new constraint or preference during chat, immediately apply it AND persist it to [`docs/frameworks/TEAM_DIRECTIVES.md`](./docs/frameworks/TEAM_DIRECTIVES.md).

