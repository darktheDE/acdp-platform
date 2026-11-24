# Example Drift Audit & Decision Propagation Run (`DIR-016`)

This example demonstrates how `doc-decision-sync` identifies and resolves multi-document drift after adopting `DIR-016` (PostgreSQL 18 OLTP, FastAPI Serving Gateway, Next.js 16 Frontend, DuckDB Gold OLAP, Qdrant Vector Store).

---

## 1. Pre-Edit Blast Radius Discovery

Run the impact analyzer before propagating a decision across the repository:

```powershell
uv run python .agents/skills/doc-decision-sync/scripts/audit_doc_drift.py --impact "Next.js 15"
```

Sample output before synchronization:

```text
[IMPACT SCAN] Query: "Next.js 15"
Tier 1 (Agent Contracts & Harness):
  - AGENTS.md:33 -> | **Mode 6: Frontend & UI/UX** | ... Next.js 15 components |
  - .agents/skills/README.md:22 -> | **`frontend-designer`** | ... Next.js 15, ... |
  - docs/frameworks/PROMPT_EXECUTION_FRAMEWORK.md:75 -> - *Option 2 (Production Component)*: E.g., Next.js 15 App Router component ...
```

---

## 2. Strict Drift & Internal Link Audit Output (Before Remediation)

```powershell
uv run python .agents/skills/doc-decision-sync/scripts/audit_doc_drift.py --strict
```

Sample failing report:

```text
================================================================================
ACDP DOCUMENTATION DRIFT & DECISION SYNC AUDIT
================================================================================
[FAIL] DIRECTIVE-SYNC: DIR-016 missing in AGENTS.md
[FAIL] DIRECTIVE-SYNC: DIR-016 missing in GEMINI.md
[FAIL] SKILL-REGISTRY-PARITY: 'visual-dossier-reporter' missing in CLAUDE.md
[FAIL] CANONICAL-FACT-DRIFT [DRIFT-002]: AGENTS.md:33 matched 'Next.js 15'
[FAIL] CANONICAL-FACT-DRIFT [DRIFT-003]: docs/specs/0001-system-foundation-spec.md:22 matched excluded PostgreSQL claim
[FAIL] INTERNAL-LINK-INTEGRITY: docs/specs/0002-data-ingestion-and-schema-spec.md:52 -> '../../src/acdp/lakehouse/schema.py' does not exist
--------------------------------------------------------------------------------
Summary: 6 violation(s) found. Exit code: 1
```

---

## 3. Strict Drift Audit Output (After Atomic Synchronization)

After updating Tiers 0, 1, 2, and 3 and re-running the strict audit:

```powershell
uv run python .agents/skills/doc-decision-sync/scripts/audit_doc_drift.py --strict
```

Expected passing output:

```text
================================================================================
ACDP DOCUMENTATION DRIFT & DECISION SYNC AUDIT
================================================================================
[PASS] DIRECTIVE-SYNC: All 17 directives accounted for; 9/9 universal directives synced in AGENTS.md & GEMINI.md
[PASS] SKILL-REGISTRY-PARITY: 11/11 skills registered across AGENTS.md, GEMINI.md, CLAUDE.md, .agents/skills/README.md
[PASS] CANONICAL-FACT-DRIFT: 0 stale facts detected across active rules
[PASS] INTERNAL-LINK-INTEGRITY: All relative Markdown links resolve to existing files
--------------------------------------------------------------------------------
Summary: 0 violations found. Status: CLEAN (Exit code: 0)
```
