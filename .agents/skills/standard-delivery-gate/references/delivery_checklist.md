# Standard Delivery Package Checklist (`DIR-024`)

## 1. Seven-Pillar Acceptance Rubric

| Pillar | Verification Item | Pass Condition |
| :---: | :--- | :--- |
| **1** | Deliverable & Registry Sync | Primary `docs/deliverables/[TASK_ID]-[slug].md` registered in `tasks-data.json`, `task-registry.md`, and `index.html`. |
| **2** | Quantitative Benchmarks | At least one structured table containing directly measured values (latency, RAM, pass counts, or resource limits). |
| **3** | Interactive Visual Dossier | Companion `*-visual-dossier.html` with Tailwind CSS, Mermaid.js architecture diagram, and Chart.js metrics passing `validate_visual_report.py`. |
| **4** | Search Provenance (`DIR-020`) | Exact search queries executed plus verified canonical `https://` URLs/DOIs passing `verify_links.py` (`0 BROKEN`). |
| **5** | Automated Test Suite | Dedicated `tests/test_*.py` file passing `uv run pytest` and `ruff check` after final edits. |
| **6** | Manual Test & Advisor Demo Runbook | Step-by-step copy-pasteable CLI commands paired with verbatim captured outputs and a 5-to-15 minute demo flow. |
| **7** | Zero-Drift Governance Closure | Passes `detect_ai_slop.py --strict`, `audit_doc_drift.py --strict`, and `check_delivery_package.py` with zero placeholders. |

---

## 2. Advisor Demo Structure (5-Minute vs. 15-Minute Walkthrough)

When presenting any completed task to the scientific advisor or defense committee:

1. **Minute 0–2 (Architecture & Visual Scan)**: Open `docs/deliverables/[TASK_ID]-[slug]-visual-dossier.html` in a browser to show Tier 1 KPI cards and the Tier 2 Mermaid diagram.
2. **Minute 2–5 (Quantitative Evidence & Verification)**: Run the automated test command and governance checks directly in PowerShell so the committee observes live deterministic passes.
3. **Minute 5–15 (Deep Inspection & Q&A)**: Walk through individual decision rows, spec-vs-code drift logs, RFC triggers, and committee Q&A points in the primary `.md` deliverable.
