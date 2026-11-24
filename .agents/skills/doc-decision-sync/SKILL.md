---
name: doc-decision-sync
description: >-
  Propagate architectural decisions, team directives (DIR-XXX), ADR/RFC outcomes, and schema or tech-stack changes
  atomically across all dependent documentation, agent contracts, and specs while auditing for documentation drift
  and broken internal links.
  Trigger on: decision sync, update related docs, doc drift, propagate decision, single source of truth,
  đồng bộ tài liệu, cập nhật quyết định, trôi dạt tài liệu, cập nhật docs liên quan, kiểm tra đồng bộ.
  DO NOT use for: external HTTP URL reachability checks (use url-link-verifier), running SQL/Alembic database
  migrations, or implementing Python/TypeScript application business logic.
compatibility: Python 3.10+, Standard Library only (Zero external pip dependencies), Markdown
---

# Documentation Decision Sync & Drift Governance (`doc-decision-sync`)

This skill enforces **DIR-017 (Atomic Decision Propagation & Zero Doc Drift)** across `acdp-platform`. Whenever a directive, tech stack choice, spec contract, skill, or file path changes, the agent must trace the blast radius across all four documentation tiers, update every affected file in the same change set, and pass deterministic verification via `scripts/audit_doc_drift.py --strict`.

---

## 1. Trigger Conditions & Boundaries

Activate this skill when:
1. A new Team Directive (`DIR-XXX`), ADR (`docs/adr/`), or RFC (`docs/rfc/`) is created or amended.
2. Any technology version, database role, file path, or schema contract changes (for example upgrading a web framework major version or adopting `PostgreSQL 18`).
3. A skill in `.agents/skills/` is added, renamed, or retired.
4. The user asks how to keep related docs up to date or requests a cross-document consistency audit.

Do not activate this skill for:
1. Checking external HTTP/HTTPS URLs or paper DOIs (`url-link-verifier`).
2. Running Python unit tests on data pipelines without documentation changes.
3. Writing raw frontend components or FastAPI route handlers unrelated to specification updates.

---

## 2. Invariant Project Standards

1. Single Source of Truth Manifest. Canonical directives, skill registry targets, and banned drift patterns live in [`references/decision_rules.json`](./references/decision_rules.json).
2. Deterministic Verification Gate. Never manually guess whether related files are synchronized; run [`scripts/audit_doc_drift.py`](./scripts/audit_doc_drift.py) with `--strict` before closing any decision task.
3. Internal vs. External Link Separation. `doc-decision-sync` validates relative repository Markdown links (`./`, `../`), whereas `url-link-verifier` validates external `http://` and `https://` URLs.
4. Read-Only Git Policy. Inspect repository status via `git status` or `git diff` only; never execute `git add`, `git commit`, or `git push`.

---

## 3. Step-by-Step Execution Protocol

### Step 1: Compute Blast Radius (`--impact`)
Before editing files after a new decision, inspect the dependency topology in [`references/decision_dependency_graph.md`](./references/decision_dependency_graph.md) and scan all Markdown documents for affected references:

```powershell
uv run python .agents/skills/doc-decision-sync/scripts/audit_doc_drift.py --impact "<keyword_or_DIR_or_path>"
```

### Step 2: Update Tier 0 Origin & Machine Rules
1. Record or update the authoritative decision in `docs/frameworks/TEAM_DIRECTIVES.md` (for standing rules), `docs/adr/`, or `docs/rfc/`.
2. Update [`references/decision_rules.json`](./references/decision_rules.json) if the decision introduces a new universal `DIR-XXX`, deprecates an old file path, or supersedes a framework version.

### Step 3: Propagate Across Tiers 1–3 Atomically
Update every affected file identified in Step 1 and in the Blast-Radius Matrix:
1. Tier 1 (Agent Contracts). Sync `AGENTS.md`, `GEMINI.md`, `CLAUDE.md`, `.cursorrules`, `docs/frameworks/PROMPT_EXECUTION_FRAMEWORK.md`, and `.agents/skills/README.md`.
2. Tier 2 (Specs & Task Ledgers). Sync `docs/specs/SPEC.md`, `docs/specs/0001..0006-*.md`, `docs/tasks/active-sprint.md`, `docs/tasks/task-registry.md`, and `README.md`.
3. Tier 3 (Skills & Academic Outputs). Sync affected `.agents/skills/*/SKILL.md` files and active deliverables.

### Step 4: Run Deterministic Audit & Anti-Slop Gate
Execute the strict drift audit and unit test suite:

```powershell
uv run python .agents/skills/doc-decision-sync/scripts/test_audit_doc_drift.py
uv run python .agents/skills/doc-decision-sync/scripts/audit_doc_drift.py --strict
```

If any newly authored or edited Markdown document contains narrative prose, run the scientific prose check:

```powershell
uv run python .agents/skills/anti-slop-scientific-writer/scripts/detect_ai_slop.py <modified_file.md> --strict
```

---

## 4. Edge Cases & Gotchas

| Scenario / Failure Mode | Root Cause | Remediation |
| :--- | :--- | :--- |
| Placeholder links inside fenced code blocks trigger false positives | Skill templates and docs show sample paths like `[Name](./sample.md)` inside triple-backtick blocks | Strip fenced code blocks and inline code spans before extracting relative Markdown links |
| Historical rename notes trigger institutional name drift | `TEAM_DIRECTIVES.md` documents the historical name `Trường ĐH Sư phạm Kỹ thuật TP.HCM` inside a `tên cũ` note | Configure `exclude_if_line_contains` markers (`tên cũ`, `đổi tên`, `Decision`, `Quyết định`) in `decision_rules.json` |
| New directive added to `TEAM_DIRECTIVES.md` but forgotten in `AGENTS.md` | Agent writes only to Section 6 changelog without updating `<user_rules>` contracts | `check_directive_sync()` parses every `DIR-\d{3}` from `TEAM_DIRECTIVES.md` and fails if any ID is missing from both `required_directives_in_agent_contracts` and `scoped_directives` |
| Windows paths or URL fragments fail file-existence checks | Relative link includes `#anchor` suffix (`./spec.md#section-2`) or query string | Strip `#...` fragment and `?` query before resolving the target path relative to the source file directory |

---

## 5. Reference Links

1. Canonical drift rules manifest: [`references/decision_rules.json`](./references/decision_rules.json)
2. 4-Tier propagation DAG & matrix: [`references/decision_dependency_graph.md`](./references/decision_dependency_graph.md)
3. Drift audit script: [`scripts/audit_doc_drift.py`](./scripts/audit_doc_drift.py)
4. Unit test suite: [`scripts/test_audit_doc_drift.py`](./scripts/test_audit_doc_drift.py)
5. Reference audit output: [`examples/sample_drift_audit_report.md`](./examples/sample_drift_audit_report.md)
