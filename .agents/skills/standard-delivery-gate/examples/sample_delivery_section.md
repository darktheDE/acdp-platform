# Sample Manual Test & Advisor Demo Runbook Section

## Manual Test, CLI Deployment & Advisor Demo Runbook

### Step 1: Verify Architecture Invariants & Automated Tests

```powershell
uv run pytest tests/test_infra_spec0006.py -q
```

Captured Output:

```text
5 passed in 0.42s
```

### Step 2: Verify Documentation Drift & External Link Integrity

```powershell
uv run python .agents/skills/doc-decision-sync/scripts/audit_doc_drift.py --strict
```

Captured Output:

```text
Summary: 0 violation(s) found. Status: CLEAN
```
