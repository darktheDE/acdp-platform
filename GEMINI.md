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
   - URL & Link Verifier: `.agents/skills/url-link-verifier/SKILL.md`
   - Scientific Prose & Anti-Slop: `.agents/skills/anti-slop-scientific-writer/SKILL.md`
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
9. **Concise Scientific Communication & Anti-Slop (DIR-007)**:
   - Always lead with the direct technical answer (Answer-First). Never use throat-clearing, preambles, reasoning leaks, or sycophancy.
   - Author `.md` and `.html` documentation strictly adhering to `.agents/skills/anti-slop-scientific-writer/`.
10. **Implicit Intent & Auto-Activation (DIR-008)**:
    - Never demand or wait for the user to explicitly call skills by name. Automatically infer user intent and activate the relevant skill playbooks immediately.
11. **Tabula Rasa in Tech Research & Peer Defense Before ADR (DIR-011)**:
    - Treat all existing tech mentions in READMEs and starter templates as unverified placeholders during research tasks; research candidates objectively from first principles.
    - Research findings must be structured as defense dossiers for internal debate between Hưng and Duy; never draft or adopt formal ADRs until both partners review and reach explicit consensus.
12. **Temporal Grounding (Project Anchor: September 2026 - DIR-012)**:
    - Active project execution timestamp is permanently anchored to **September 2026 (Tháng 9/2026)**.
    - When conducting technical research, verifying library APIs, assessing software licensing, or finding scientific literature, agents MUST anchor all internet queries and knowledge lookups to the **September 2026** reality (covering 2024–2026 advances, releases, and papers), strictly avoiding outdated, legacy information.


