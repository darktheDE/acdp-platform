---
name: defense-pitch-builder
description: >-
  Generate academic defense slide decks (HTML/CSS and Marp), formulate pitching scripts,
  and build adversarial committee Q&A defense preparation banks for academic presentations.
  Use when the user asks for: proposal defense slides, presentation decks, pitch scripts, or adversarial committee Q&A practice.
  DO NOT use for: Writing production backend API code, building large database dbt models, or drafting 50-page thesis text.
compatibility: HTML5, CSS3, Marp, Markdown
---

# Defense & Pitch Builder Skill

This skill equips the AI agent to build compelling presentation decks, pitch narratives, and adversarial Q&A defense preparation banks for academic thesis defense and competition pitching under FIT-HCMUTE standards.

---

## 1. Trigger Conditions & Boundaries

- **Activate when**:
  - Creating or updating slide decks for project proposals, milestone reviews, or final thesis defense.
  - Generating self-contained HTML/CSS presentation decks or Marp Markdown slides.
  - Formulating speaking scripts and timing strategies (5-minute pitch, 10-minute proposal, 15-minute defense).
  - Simulating tough reviewer questions from thesis committee members (GVPB / Hội đồng) and formulating technical answers.
- **DO NOT activate when**:
  - Writing Next.js production web components (`apps/web/`).
  - Setting up Lakehouse storage infrastructure or dbt SQL models.
  - Writing formal thesis chapters (`docs/academic/`).

---

## 2. Invariant Presentation Standards

1. **Self-Contained Offline Independence**: Presentation HTML files must work completely offline without relying on external CDNs for CSS/JS, ensuring failure-proof delivery in university lecture halls.
2. **Keyboard Navigation Support**: Must include standard keyboard listeners for `ArrowRight`, `ArrowLeft`, and `Space`.
3. **Pacing & Timing Constraint**:
   - 10-Slide Deck $\rightarrow$ 10–12 minutes total presentation time (~60–75 seconds per slide).
   - See pacing guidelines in [`references/committee_defense_rubric.md`](./references/committee_defense_rubric.md).
4. **Structured Defense Q&A Formula**: Every committee answer must follow the 4-part formula:
   `[Direct Answer Claim] -> [Architecture Reference (ADR/Spec)] -> [Empirical Metric / Evidence] -> [Known Trade-off / Mitigation]`.

---

## 3. Step-by-Step Execution Protocol

### Step 1: Slide Deck Architecture Selection
- **Option A (HTML5 Presentation Engine - Recommended)**: Clean academic paper texture (`#FAF8F5`), top progress bar, responsive card grid layout. See reference: [`examples/sample_defense_slide.html`](./examples/sample_defense_slide.html).
- **Option B (Marp Markdown)**: Standard Marp format for export to PDF/PPTX.

### Step 2: 10-Slide Canonical Defense Structure
1. Title & Team Identity (HCMUTE, Major: Data Engineering).
2. Background & 4 Real-World Bottlenecks.
3. Research Questions & Concrete Objectives.
4. End-to-End System Architecture (4 Phased Layers).
5. Data Ingestion & Medallion Lakehouse Flow.
6. Semantic AI & Regulation RAG Copilot.
7. Teammate Recommendation & Faculty BI Dashboard.
8. Implementation Walkthrough & Live Demo.
9. Empirical Evaluation Metrics (Ragas & Latency).
10. Conclusion, Limitations & Phase 2 Outlook.

### Step 3: Deck Quality Verification Gate
Execute the automated slide deck validator before delivery:
```bash
python .agents/skills/defense-pitch-builder/scripts/validate_slides_html.py --file docs/academic/Slide_Proposal_TLCN.html
```

---

## 4. Edge Cases & Gotchas Catalog

| Gotcha / Common Failure Mode | Root Cause | Enforced Solution |
| :--- | :--- | :--- |
| **Slides Wall-of-Text** | Copy-pasting thesis text directly onto slides | Strictly enforce maximum 4 bullet points per slide, max 15 words per bullet. Use visual cards. |
| **Broken Offline Presentation** | Linking fonts or Tailwind scripts to remote CDNs | Embed critical styles in `<style>` tags directly inside the HTML deck. |
| **Defensive Hesitation in Q&A** | Hedging or apologizing to the committee | State the direct engineering choice immediately: "Nhóm đã lựa chọn giải pháp X vì lý do kỹ thuật Y...". |

---

## 5. Verification Checklist

- [ ] Execute `python .agents/skills/defense-pitch-builder/scripts/validate_slides_html.py --file <path>`.
- [ ] Test presentation keyboard navigation (`ArrowRight` / `ArrowLeft`).
- [ ] Verify timing adheres to 10–12 minute defense limit.
