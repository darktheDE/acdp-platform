# ACDP Design Tokens & Design System Reference

This document serves as the authoritative specification for all UI/UX components in the ACDP web portal and admin dashboards.

---

## 1. Color Palette (Semantic Tokens)

### Light Mode (Academic Minimalist)
- **Canvas / Background**: `#FAF8F5` (Warm off-white, paper texture)
- **Surface / Card**: `#FFFFFF` (Pure white)
- **Border**: `#E2E8F0` (Slate-200)
- **Text Primary**: `#0F172A` (Slate-900)
- **Text Muted**: `#64748B` (Slate-500)

### Dark Mode (Slate Authority)
- **Canvas / Background**: `#0F172A` (Slate-900)
- **Surface / Card**: `#1E293B` (Slate-800)
- **Border**: `#334155` (Slate-700)
- **Text Primary**: `#F8FAFC` (Slate-50)
- **Text Muted**: `#94A3B8` (Slate-400)

### Functional Accents
- **Academic Authority Navy**: `#1E3A8A` (`blue-900`) - Headers, verified badges.
- **Urgency / Deadline Coral**: `#C2410C` (`orange-700`) - Registration countdown, action buttons.
- **Success / Verified Olive**: `#15803D` (`green-700`) - Status OPEN, eligible criteria met.
- **Warning Amber**: `#B45309` (`amber-700`) - Approaching deadline (< 3 days).

---

## 2. Typography Scale

- **Display Headings**: `font-serif` (*Plus Jakarta Sans* or *Newsreader* for academic authority).
- **Body Text**: `font-sans` (*Inter*, *system-ui*).
- **Metadata / Monospace**: `font-mono` (*JetBrains Mono*) for dates, IDs, registration codes, prize numbers.

| Token | Class | Size / Line Height | Usage |
| :--- | :--- | :--- | :--- |
| `text-display` | `text-3xl font-bold font-serif` | 30px / 36px | Page Titles, Hero Banner |
| `text-heading` | `text-xl font-semibold` | 20px / 28px | Card Titles, Modal Headers |
| `text-subheading`| `text-base font-medium` | 16px / 24px | Section Dividers |
| `text-body` | `text-sm font-normal` | 14px / 20px | Standard descriptions, rules |
| `text-caption` | `text-xs font-mono` | 12px / 16px | Badges, deadlines, tags |

---

## 3. Standard Breakpoints & Layouts

- **Mobile**: `< 640px` (Single column, full width cards, bottom sticky actions).
- **Tablet**: `640px - 1024px` (2-column card grid, collapsible sidebar).
- **Desktop**: `> 1024px` (3-column grid, persistent filter rail on left, analytics on right).
