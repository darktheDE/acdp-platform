# ACDP Change Management Protocol (RFC Process)

This document establishes the official protocol for proposing, reviewing, and applying changes to:
1. **Functional Requirements**: Adding, altering, or removing application features.
2. **Architecture & Data Flows**: Changing storage layers, schemas, or pipelines.
3. **Tech Stack & Dependencies**: Upgrading, adding, or removing libraries and external services.

Both human contributors and AI agents must follow this process to maintain consistency and prevent breaking changes.

---

## The 4-Step Change Governance Lifecycle

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ 1. DRAFT RFC │ ──> │  2. CONSENSUS│ ──> │ 3. PROMOTE   │ ──> │ 4. CODE &    │
│ (Problem &   │     │ (Review with │     │    TO ADR /  │     │    TEST      │
│ Alternatives)│     │  Team/Advisor│     │    SPEC      │     │ (Refactor)   │
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
```

### Step 1: Draft an RFC
When a non-trivial change or pivot is proposed:
1. Copy [`docs/rfc/0000-rfc-template.md`](./0000-rfc-template.md) to `docs/rfc/RFC-XXXX-<short-title>.md`.
2. Clearly articulate:
   - **The Problem / Driver**: Why the existing solution is inadequate.
   - **Proposed Modification**: What is being added, modified, or removed.
   - **Alternatives Explored**: Other tools or approaches evaluated.
   - **Impact Analysis**: Which components (`pipelines/`, `lakehouse/`, `apps/`) will be affected.
   - **Migration / Deprecation Strategy**: How existing data and code will transition safely without data loss.

### Step 2: Review and Consensus
- Discuss the RFC with the team (Do Kien Hung & Nguyen Van Quang Duy) and advisor (M.Sc. Tran Quang Khai).
- Update the RFC status: `Draft` $\rightarrow$ `Under Review` $\rightarrow$ `Approved` (or `Rejected`).

### Step 3: Promote to ADR & Spec
- If the change affects architecture or foundational dependencies, create a new ADR in `docs/adr/` (or update an existing ADR status to `Superseded by ADR-XXXX`).
- Update or draft corresponding specifications in `docs/specs/`.
- Log the actionable migration tasks in `docs/tasks/active-sprint.md`.

### Step 4: Implementation and Verification
- Only after Step 3 is completed does code implementation begin.
- Verify through automated tests and schema validation before merging the PR.
- Mark the RFC as `Implemented`.

---

## Fast-Track Changes (Exempt from Full RFC)
The following minor changes do not require a full RFC and can be handled via direct PR:
- Minor non-breaking dependency patch bumps (e.g. `pydantic 2.10.1` $\rightarrow$ `2.10.2`).
- Bug fixes that do not alter public API signatures or database schemas.
- Documentation grammar, typo, or markdown formatting corrections.
