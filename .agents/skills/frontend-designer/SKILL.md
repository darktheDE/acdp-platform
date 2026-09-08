---
name: frontend-designer
description: Design and build modern, responsive web interfaces, interactive UI mockups, and client-side components for the student portal and faculty dashboard using Next.js 15, React 19, and Tailwind CSS.
---

# Frontend Designer & UI/UX Prototyper Skill

This skill equips the AI agent to act as a Senior Frontend Engineer & UI/UX Designer, creating clean, modern, and accessible interfaces for the ACDP Student Competition Explorer and Faculty BI Analytics Dashboard.

---

## 1. When to Activate This Skill
Activate this skill whenever the user prompts for:
- Designing UI/UX mockups, wireframes, or visual prototypes for competition search, contest detail views, or dashboard charts.
- Building interactive, self-contained HTML/Tailwind preview files for rapid human evaluation.
- Writing Next.js 15 (App Router), React 19, TypeScript, and Tailwind CSS components.
- Designing responsive layouts, search filters, modal dialogues, or data visualization widgets (Recharts).
- Stubbing mock competition datasets for frontend testing prior to backend API readiness.

---

## 2. Design System & Aesthetic Standards

### Core Aesthetic Guidelines
- **Modern Academic & Professional**: Clean, minimal, high contrast, avoiding cluttered gradients or distracting animations.
- **Color Palette**:
  - Primary Base: `#FAF8F5` (Warm paper tone) or `#0F172A` (Slate dark mode).
  - Surface: `#FFFFFF` / `#1E293B`.
  - Brand Navy: `#1E3A8A` (Academic authority).
  - Accent Rust / Coral: `#C2410C` (Call-to-action, deadline urgency).
  - Success Olive: `#15803D` (Eligible, open registration, verified).
- **Typography**: Clean system sans-serif (`Inter`, `Plus Jakarta Sans`) paired with monospace (`JetBrains Mono`) for dates, codes, and IDs.
- **Icons**: Lucide React icons (`Calendar`, `Trophy`, `Users`, `Search`, `ExternalLink`, `ShieldCheck`).

---

## 3. Rapid Prototyping Protocol (No-Blocker Workflow)

When the user requests a frontend mockup or preview:

### Step 1: Generate Mock Contract Data Stubs
Do not wait for backend APIs. Immediately synthesize realistic mock JSON adhering to the Pydantic competition schema:

```json
[
  {
    "id": "comp-2026-icpc-vietnam",
    "name": "Kỳ thi Lập trình Sinh viên Quốc tế ICPC Việt Nam 2026",
    "organizer": "Hội Tin học Việt Nam (VAIP) & Bộ GD&ĐT",
    "category": "Competitive Programming",
    "registration_deadline": "2026-10-15T23:59:59+07:00",
    "tier": "National",
    "team_size": "3 sinh viên",
    "prize_pool": "150.000.000 VND",
    "tags": ["ICPC", "Thuật toán", "C++", "Python"],
    "status": "OPEN_FOR_REGISTRATION",
    "is_verified": true
  }
]
```

### Step 2: Deliver Self-Contained Visual Preview
For fast human review, generate a self-contained HTML prototype utilizing Tailwind CSS CDN, interactive search input filtering, and responsive mobile-first cards under:
`docs/deliverables/ui-mockups/[page-name]-preview.html`

### Step 3: Transition to Production Component
When transitioning to production code:
- Place components under `apps/web/components/`.
- Use React 19 server/client component boundaries (`'use client'`).
- Ensure full accessibility (ARIA labels, keyboard navigation).
