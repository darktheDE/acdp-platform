---
name: frontend-designer
description: >-
  Design and build accessible, responsive UI/UX mockups, Tailwind CSS components,
  and Next.js 15 pages for the student competition portal and faculty analytics dashboard.
  Use when the user asks for: UI previews, wireframes, Next.js components, Tailwind styling, Recharts widgets, or frontend prototypes.
  DO NOT use for: Backend FastAPI REST routes, database migrations, lakehouse dbt transformations, or crawler pipeline implementation.
compatibility: Next.js 15+, React 19, Tailwind CSS v4, TypeScript 5.6+
---

# Frontend Designer & UI/UX Prototyper Skill

This skill equips the AI agent to operate as a Senior Frontend Engineer & UI/UX Architect, building high-performance, accessible, and aesthetically cohesive web applications for the ACDP platform.

---

## 1. Trigger Conditions & Boundaries

- **Activate when**:
  - Designing visual wireframes, prototypes, or user flows for competition discovery.
  - Generating self-contained preview prototypes in `docs/deliverables/ui-mockups/`.
  - Writing production Next.js 15 (App Router), React 19, TypeScript, and Tailwind CSS components.
  - Designing data visualization widgets with Recharts for faculty analytics.
- **DO NOT activate when**:
  - Writing FastAPI REST endpoints (`apps/api/`).
  - Developing crawler scripts or parsing logic (`pipelines/ingestion/`).
  - Formulating thesis text or literature matrices (`docs/academic/`).

---

## 2. Invariant Project Standards

All frontend code must adhere to:
1. **Tech Stack Baseline**: Next.js 15+ (App Router), React 19, TypeScript 5.6+ (Strict mode), Tailwind CSS v4.0.
2. **Design Tokens**: Follow the official palette defined in [`references/design_tokens.md`](./references/design_tokens.md):
   - Primary: Slate dark mode (`#0F172A`) or Paper white (`#FAF8F5`).
   - Authority Navy: `#1E3A8A` | Accent Coral: `#C2410C` | Success Olive: `#15803D`.
3. **Architecture Boundary**:
   - Client interactivity (`useState`, `useEffect`, `onClick`) requires explicit `'use client'` directive at line 1.
   - Server components are the default for data fetching and layout structure.
4. **Accessibility (a11y)**: Every button, icon-only element, and input must have descriptive `aria-label` or associated `<label>`.

---

## 3. Step-by-Step Execution Protocol

### Step 1: Zero-Blocker Data Stubbing
Do not wait for backend APIs. When designing a component, construct a typed mock data contract matching the expected Pydantic schema:
- See reference implementation: [`examples/competition_card.tsx`](./examples/competition_card.tsx).

### Step 2: Prototyping Pathway Selection
- **Pathway B (Fast-Track Preview)**: If the user requests a quick mockup, generate a self-contained HTML/Tailwind preview under `docs/deliverables/ui-mockups/[name]-preview.html`.
- **Pathway A (Production Component)**: When building active codebase files, place components in `apps/web/components/` and routes in `apps/web/app/`.

### Step 3: Quality Verification Gate
Always execute the automated component validator before delivering code:
```bash
python .agents/skills/frontend-designer/scripts/validate_ui_component.py --file <path-to-file>
```

---

## 4. Edge Cases & Gotchas Catalog

| Gotcha / Common Failure Mode | Root Cause | Enforced Solution |
| :--- | :--- | :--- |
| **Missing `'use client'` Error** | Using React hooks (`useState`, `usePathname`) in a Server Component | Add `'use client'` as the very first line of the file. |
| **Tailwind v4 `@theme` mismatch** | Using deprecated Tailwind v3 `tailwind.config.js` syntax | Use CSS-first `@theme` variables in `globals.css` as detailed in [`references/design_tokens.md`](./references/design_tokens.md). |
| **Hydration Mismatch on Dates** | Formatting dates using local timezone on server vs. client | Use static ISO formatting or render dates inside a `useEffect` / mounted-state gate. |
| **Broken Lucide Icon Imports** | Importing non-existent icon names or importing full bundle | Import individual named icons from `lucide-react` (e.g. `import { Trophy, Calendar } from 'lucide-react'`). |

---

## 5. Verification Checklist

- [ ] Run `python .agents/skills/frontend-designer/scripts/validate_ui_component.py --file <path>`.
- [ ] Verify responsive layout across mobile (`375px`), tablet (`768px`), and desktop (`1280px`).
- [ ] Confirm dark mode / light mode semantic token alignment.
- [ ] Ensure all interactive elements have focus rings and keyboard accessibility.
