---
name: visual-dossier-reporter
description: Generate self-contained, interactive single-file HTML reports and living visual dossiers combining Tailwind CSS, Mermaid.js architecture diagrams, and Chart.js benchmarks. Use whenever the user asks for: visual reports, living dossiers, HTML summaries, interactive reports, báo cáo trực quan, tóm tắt trực quan, visual deliverable, or architecture dashboards. DO NOT use for: simple 1-paragraph Q&A, raw database migrations, or backend algorithmic code.
compatibility: Antigravity, Claude Code, Gemini CLI, Cursor, Windsurf
metadata:
  version: "1.0.0"
  author: "Do Kien Hung & Nguyen Van Quang Duy"
  institution: "FIT-HCMUTE"
  directive: "DIR-014"
---

# Visual Dossier Reporter: Interactive Single-File HTML Living Reports

> **Standing Team Directive**: Conforms strictly to **DIR-014 (Living Visual Dossier & Interactive HTML Reporting Protocol)**.  
> **Institution**: Faculty of Information Technology, Ho Chi Minh City University of Technology and Engineering (FIT-HCMUTE).

---

## 1. Trigger Matrix & Context Boundary

### Positive Triggers (Auto-Activate)
- User asks to summarize a complex milestone, tech evaluation, or deliverable visually:
  - *"tóm tắt trực quan"*, *"báo cáo trực quan"*, *"visual report"*, *"living dossier"*, *"tổng hợp tiến độ dạng html"*, *"làm dashboard báo cáo"*.
- User asks to present architectural trade-offs, benchmarks, or pipeline steps in an easy-to-digest format rather than a massive wall of markdown text.
- User requests deliverables under `docs/deliverables/` or personal memos under `.scratchpad/` with diagrams and graphs.

### Negative Triggers (DO NOT Activate)
- Quick conceptual Q&A (Pathway C: DuckDB vs SQLite) $\rightarrow$ Deliver concise 2–3 paragraphs in chat.
- Writing production Python backend code, Pydantic schemas, or SQL pipelines $\rightarrow$ Use Spec-driven engineering.
- Writing formal thesis LaTeX/Markdown manuscripts intended strictly for PDF print submission $\rightarrow$ Use `thesis-writer`.

---

## 2. Core Philosophy: Ending Markdown Visual Fatigue

Markdown files (`.md`) are optimal for Git diffs, CI/CD, and machine parsing, but impose severe cognitive overload on human readers (advisors, co-authors, committee members) when documenting multi-layered distributed systems.

The **Living Visual Dossier** approach solves this by compiling research findings and deliverables into a **100% self-contained, zero-install Single-File HTML document**:
1. **Zero Runtime Overhead**: Opens instantly by double-clicking in Chrome, Edge, Safari, or Firefox without running Node.js, Vite, or a local web server.
2. **Multi-CDN Integration**:
   - **Tailwind CSS CDN**: Modern, refined design system with card layouts, high-contrast dark/light mode palette, and responsive typography.
   - **Mermaid.js CDN**: Interactive, vector-rendered data flow, sequence, and system architecture diagrams.
   - **Chart.js CDN**: Clean, animated bar, radar, and doughnut charts for latency, RAM, and compression benchmarks.
3. **Progressive Disclosure**: Information is organized into 3 distinct cognitive tiers so readers can absorb value according to their time constraints.

---

## 3. The 3-Tier Progressive Disclosure Architecture

Every visual dossier must structure content into 3 progressive tiers:

```
┌────────────────────────────────────────────────────────────────────────┐
│ TIER 1: EXECUTIVE SUMMARY & METRIC SCORECARDS (1-Minute Scan)          │
│ - Target task ID, Notion mapping link, status badge                    │
│ - 3 to 4 prominent KPI metric cards (RAM, Storage Savings, Latency)   │
│ - TL;DR conclusion in 2-3 concise sentences                            │
├────────────────────────────────────────────────────────────────────────┤
│ TIER 2: INTERACTIVE DIAGRAMS & BENCHMARK CHARTS (3-Minute Visual Dive) │
│ - Mermaid.js pipeline & architecture diagrams                          │
│ - Chart.js side-by-side benchmark comparison (RAM, I/O, Cost)          │
│ - Trade-off scorecard matrix                                           │
├────────────────────────────────────────────────────────────────────────┤
│ TIER 3: DEEP TECHNICAL SPECIFICATIONS & CODE DIFFS (Deep Audit)        │
│ - Collapsible accordions with schema contracts & Pydantic models       │
│ - Step-by-step implementation guide                                    │
│ - Direct clickable file links (file:///) and verification audit logs   │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 4. File Output Routing Protocol

1. **Personal Workspace / Author Inquiry (`.scratchpad/`)**:
   - When the user asks for a visual summary to answer a personal question, debug, or explore ideas:
   - Output to: `.scratchpad/<task-id>-<topic>-visual-report.html`.
   - *Example*: `.scratchpad/NT-018-019-bronze-lakehouse-report.html`.
   - *Rule*: Never commit `.scratchpad/` to git (enforced by `.gitignore`).

2. **Official Repository Deliverables (`docs/deliverables/`)**:
   - When the visual report serves as an official project milestone deliverable accompanying a Notion Task:
   - Output to: `docs/deliverables/<task-id>-<slug>-visual-dossier.html`.
   - Update `docs/tasks/notion-task-mapping.md` with the link.

---

## 5. Technical Template Reference

Always base reports on the canonical template in `resources/template.html`:
- Includes responsive navbar with dark/light mode toggle.
- Automatically initializes Mermaid.js with `mermaid.initialize({ startOnLoad: true, theme: 'dark' })`.
- Sets up Chart.js canvas elements with clean data structures.
- Provides interactive tab-switching logic for multi-tab dossiers.

---

## 6. Verification & Quality Assurance

After generating any `.html` report:
1. Run the deterministic validator:
   ```bash
   python .agents/skills/visual-dossier-reporter/scripts/validate_visual_report.py <path_to_html_file>
   ```
2. Verify that:
   - All CDN scripts load securely over HTTPS.
   - All local file links use standard clickable file paths.
   - Mermaid diagrams parse without syntax errors.
   - No broken HTML tags or unclosed layout divs exist.
