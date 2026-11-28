---
name: standard-delivery-gate
description: >-
  Enforce the 7-Pillar Standard Task Delivery Package (DIR-024) for completed engineering
  and research tasks: Markdown deliverable, quantitative benchmarks, single-file HTML visual
  dossier, verified Search Provenance URLs, automated pytest suite, manual test & advisor
  demo runbook with captured outputs, and zero-drift closure.
  Trigger on: standard delivery, wrapup html, manual test, demo runbook, delivery gate,
  DIR-024, bàn giao chuẩn, hướng dẫn demo, chuẩn hóa bàn giao.
  DO NOT use for: quick conceptual Q&A (Pathway C), raw code-only bugfixes without
  task deliverables, or external HTTP URL verification alone (use url-link-verifier).
compatibility: Python 3.11+, Standard Library only (Zero external pip dependencies), Markdown, HTML
---

# Standard Delivery & Demo-Ready Gate (`standard-delivery-gate`)

This skill enforces **DIR-024 (Standard Task Delivery Package & Demo-Ready Verification)** across `acdp-platform`. Every completed engineering or research task must ship a self-contained, verifiable, and advisor-demo-ready delivery package rather than isolated markdown notes or untested code.

---

## 1. Trigger Conditions & Boundaries

Activate this skill when:
1. A task in `docs/tasks/tasks-data.json` is being finalized as `done` (`TASK-*`, `NT-*`).
2. The user requests a complete task wrap-up with benchmarks, interactive HTML visual summary, automated tests, and step-by-step manual test / demo commands with captured real outputs.
3. Preparing technical evidence and live demo scripts for advisor review (ThS. Trần Quang Khải) or defense committees.

Do not activate this skill for:
1. Quick conceptual questions or codebase navigation answers (Pathway C).
2. Minor typo fixes or formatting edits that do not close a task deliverable.
3. Standalone external link scans (`url-link-verifier`) or standalone prose linting (`anti-slop-scientific-writer`).

---

## 2. The 7-Pillar Standard Delivery Package (`DIR-024`)

Every completed task deliverable package must satisfy all seven pillars before closing the task:

| Pillar | Required Artifact / Section | Deterministic Verification Gate |
| :---: | :--- | :--- |
| **1. Primary Deliverable & Registry** | `docs/deliverables/[TASK_ID]-[slug].md` + synced `tasks-data.json`, `task-registry.md`, `index.html` | `sync_tasks.py --sync --validate` |
| **2. Quantitative Benchmarks** | Real measured table (RAM, latency, test counts, coverage, or pass rates — never unmeasured claims) | `check_delivery_package.py` |
| **3. Visual Dossier HTML** | `docs/deliverables/[TASK_ID]-[slug]-visual-dossier.html` (Tailwind + Mermaid + Chart.js, 3-Tier layout) | `validate_visual_report.py` |
| **4. Verified External References** | Search Provenance (`DIR-020`) listing exact search queries + live canonical `https://` URLs/DOIs | `verify_links.py` (`0 BROKEN`) |
| **5. Automated Test Suite** | Dedicated unit/integration tests (`tests/test_*.py`) executed after final edits | `uv run pytest` + `ruff check` |
| **6. Manual Test & Demo Runbook** | Copy-pasteable PowerShell/CLI commands + verbatim captured outputs + advisor demo flow | `check_delivery_package.py` |
| **7. Zero-Drift Closure** | Clean scientific prose and synchronized 4-tier docs/links (`DIR-007`, `DIR-017`) | `detect_ai_slop.py --strict` + `audit_doc_drift.py --strict` |

---

## 3. Step-by-Step Execution Protocol

### Step 1: Gather Real Measurements & Verify External Sources
- Execute live benchmark and test collection commands first (`pytest`, `docker compose config`, timing measurements) so every number reported in Pillar 2 is directly observed.
- Record every `search_web` query and canonical URL/DOI in the **Search Provenance & References** table (`DIR-020`). Never embed search-proxy redirect URLs.

### Step 2: Author Deliverable, Visual Dossier & Tests
- Follow [`docs/deliverables/0000-deliverable-template.md`](../../../docs/deliverables/0000-deliverable-template.md) and [`references/delivery_checklist.md`](./references/delivery_checklist.md).
- Include the **Manual Test, CLI Deployment & Advisor Demo Runbook** section using [`examples/sample_delivery_section.md`](./examples/sample_delivery_section.md) as a structural baseline: every command must be copy-pasteable and paired with actual captured terminal output.
- Build the companion `*-visual-dossier.html` following `visual-dossier-reporter` (`DIR-014`) without legacy external tracker badges (`DRIFT-006`).

### Step 3: Run the Deterministic 7-Pillar Gate
Run the automated gate script before reporting completion:

```powershell
uv run python .agents/skills/standard-delivery-gate/scripts/test_check_delivery_package.py
uv run python .agents/skills/standard-delivery-gate/scripts/check_delivery_package.py --task-id <TASK_ID>
```

---

## 4. Gotchas Catalog (Common Agent Failure Modes)

| Failure Mode | Root Cause | Remediation |
| :--- | :--- | :--- |
| **Vertex redirect URLs written into docs** | Copying grounding redirect links instead of canonical resolved URLs | Resolve or search canonical domain URLs and run `verify_links.py` (`0 BROKEN`). |
| **Contiguous bold-bullet lists trip anti-slop** | Using 5+ consecutive `- **Key**: value` lines in runbooks or summaries | Format multi-item specs as Markdown tables or plain prose (`detect_ai_slop.py --strict`). |
| **Placeholder outputs left in Manual Test** | Writing `[insert output here]` or `TBD` instead of running commands | Execute every documented command and paste verbatim observed terminal output. |
| **Template legacy tracker badge copied into HTML** | Copying older HTML boilerplate triggers `DRIFT-006` | Replace with `Task ID: <TASK_ID>` and run `audit_doc_drift.py --strict`. |

---

## 5. Reference Links

1. 7-Pillar Rubric & Advisor Demo Guide: [`references/delivery_checklist.md`](./references/delivery_checklist.md)
2. Canonical Manual Test & Output Example: [`examples/sample_delivery_section.md`](./examples/sample_delivery_section.md)
3. Delivery Gate CLI Validator: [`scripts/check_delivery_package.py`](./scripts/check_delivery_package.py)
4. Unit Tests for Delivery Gate: [`scripts/test_check_delivery_package.py`](./scripts/test_check_delivery_package.py)
