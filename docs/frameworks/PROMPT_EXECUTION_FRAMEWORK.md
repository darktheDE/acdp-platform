# ACDP Unified Multi-Agent Prompt Execution Framework (A-PEF)
> **Standard Operating Procedure for All AI Agents (Google Antigravity, Claude Code, Cursor, Codex, Windsurf)**

This document establishes the mandatory operational framework for **any AI agent** working in the `acdp-platform` repository. Regardless of which model (Claude, Gemini, GPT) or tool interface is used by the developers (**Đỗ Kiến Hưng** and **Nguyễn Văn Quang Duy**), the agent must process every prompt through this adaptive protocol to ensure unwavering architectural integrity and academic rigor.

---

## 1. Core Philosophy: Anti-Fragile Agentic Engineering

1. **Framework as Guardrail, Not Bottleneck**: The framework exists to protect project quality and prevent architectural drift. It must never freeze, deadlock, or refuse to work when given ad-hoc, informal, or incomplete prompts.
2. **Adaptive Execution (Multi-Pathway Dispatching)**: Prompts vary from quick queries and visual spikes to formal thesis chapters. Agents must dispatch prompts into the appropriate execution pathway instead of forcing every trivial request through an elaborate academic cycle.
3. **Just-In-Time (JIT) Skill Inception**: Skills in `.agents/skills/` are specialized procedural accelerators. If an agent receives a task for which no skill exists (e.g. *Frontend UI/UX*, *Cloud Deployment*), the agent must execute using core engineering capabilities, then formalize a new skill in `.agents/skills/` to retain memory for future turns.

---

## 2. The 4 Adaptive Execution Pathways

```
                      [ USER PROMPT INGESTION ]
                                  │
                                  ▼
                    [ INTENT & COMPLEXITY CHECK ]
                                  │
         ┌────────────────────────┼────────────────────────┐
         │                        │                        │
         ▼                        ▼                        ▼
  [ PATHWAY A ]            [ PATHWAY B ]            [ PATHWAY C ]
Full Academic & Spec     Rapid Prototyping        Direct Knowledge
(Research, Thesis, Code)     & UI Spikes              & Quick Q&A
         │                        │                        │
         ▼                        ▼                        ▼
(6-Step DSRM Cycle)      (Mock Stubs & JIT)       (Direct Concise Answer)
```

---

### Pathway A: Full Academic & Core Engineering (Standard 6-Step Cycle)
*Used for*: Literature reviews, thesis chapter drafting, production crawler development, Lakehouse dbt pipelines, RAG API endpoints, and scientific experiments.

1. **Classify**: Identify the active Mode (1 to 5) and associated Notion Task ID (`NT-XXXX`).
2. **Ground**: Read `docs/tasks/active-sprint.md`, `docs/adr/0001-medallion-lakehouse-and-rag-stack.md`, and relevant specs in `docs/specs/`.
3. **Safety Gate (RFC Check)**: If the prompt alters the tech stack or storage architecture, pause and initiate `docs/rfc/PROCESS.md`.
4. **Execute**: Activate the specialized skill from `.agents/skills/` (e.g. `thesis-writer`, `academic-researcher`, `experiment-evaluator`).
5. **Verify**: Run tests (`pytest`), linter (`ruff check`), citation checks, and anti-hallucination validation.
6. **Deliver & Sync**: Log outcomes in `docs/deliverables/NT-XXXX-[slug].md` and update `docs/tasks/notion-task-mapping.md`.

---

### Pathway B: Rapid Prototyping & Exploratory Spikes (Fast-Track)
*Used for*: UI/UX mockups, visual previews, testing candidate APIs, proof-of-concept crawler scripts.

1. **Zero-Blocker Inception (Mock Contract)**: If downstream layers (backend, database) do not exist yet, **do not wait**. Generate mock data stubs matching the expected Pydantic schema.
2. **Direct Visual Deliverable**: Produce immediately verifiable artifacts (e.g., self-contained HTML/Tailwind preview files under `docs/deliverables/ui-mockups/` or isolated script spikes under `docs/research/spikes/`).
3. **Adherence to Core Baseline**: Even in fast-track prototypes, respect the baseline tech stack from `ADR-0001` (Next.js 15, Tailwind CSS v4, React 19).
4. **JIT Skill Synthesis**: If the task revealed a recurring domain gap, propose or instantiate a new `.agents/skills/<skill-name>/SKILL.md`.

---

### Pathway C: Direct Knowledge & Quick Lookups
*Used for*: Conceptual comparisons (*"DuckDB vs. SQLite"*), codebase navigation, file explanation, or quick syntax questions.

1. **Bypass Bureaucracy**: Do not create RFCs, deliverables, or update sprint logs.
2. **Concise & Grounded Response**: Provide direct, punchy technical answers in 2–4 paragraphs.
3. **Contextual Tie-in**: Relate the general concept back to ACDP's specific architecture (e.g. *"In ACDP, DuckDB was chosen for the Silver tier because..."*).

---

### Pathway D: Disambiguation & Decision Support
*Used for*: Ambiguous, underspecified, or conflicting prompts (*"Build the frontend"*, *"Fix the crawl"*).

1. **Never Guess or Assume**: Do not blindly execute high-impact code changes based on vague instructions.
2. **Propose 2–3 Actionable Options**:
   - *Option 1 (Minimal / MVP)*: E.g., standalone HTML visual prototype.
   - *Option 2 (Production Component)*: E.g., Next.js 15 App Router component with mock state.
   - *Option 3 (Full Integration)*: E.g., complete frontend hooked into FastAPI endpoints.
3. **Awaiting User Selection**: Proceed only after the user indicates their preferred trajectory.

---

## 3. Universal Guardrails (Non-Negotiable)

Every AI agent must strictly enforce these invariants across all interactions:

1. ❌ **NO Git Execution**: **Never run `git add`, `git commit`, `git push`, or branch commands**. All Git version control is strictly executed by the human developers.
2. ❌ **NO Empty Directory Skeletons**: Only create folders when populating them with tested, active implementation files (Just-In-Time inception).
3. ❌ **NO Database Dumps or Secrets in Git**: Never generate or commit `.parquet`, `.duckdb`, `.db`, `.env`, or API credentials.
4. ❌ **NO RAG Hallucinations**: When answering contest rules or eligibility questions, strictly cite official source clauses and URLs.
5. ❌ **NO Silent Architectural Drift**: Never change foundational databases, frameworks, or languages without an approved RFC in `docs/rfc/`.

---

## 4. JIT Skill Inception Protocol

When an AI agent identifies that a requested domain lacks a specialized skill:
1. Verify if the task falls outside the existing 5 skills (`academic-researcher`, `thesis-writer`, `defense-pitch-builder`, `competitor-benchmark`, `experiment-evaluator`).
2. Complete the immediate user prompt first using general engineering expertise.
3. Once the output is delivered, formalize the workflow into a new file:
   `.agents/skills/<domain-name>/SKILL.md`
   conforming to the standard YAML frontmatter specification:
   ```markdown
   ---
   name: [skill-name]
   description: [Concise 1-sentence description of capabilities]
   ---
   # [Skill Title]
   ## 1. When to Activate This Skill
   ## 2. Standard Operational Protocol
   ## 3. Best Practices & Output Templates
   ```
4. Register the new skill in `AGENTS.md` and `docs/HOW_TO_USE.md`.
