# DELIVERABLE: Frontend UI/UX cleanup, student use-case upgrades & root docs synchronization

| Metadata | Value |
| :--- | :--- |
| Task ID | `TASK-HF-01` |
| Related Sprint | Hotfix (Cycle 08 — TLCN Phase 1) |
| Primary Owner | Do Kien Hung |
| Date Completed | `2026-11-25` |
| Deliverable Type | Hotfix Engineering & Documentation Sync |
| Status | Integrated into Codebase |

---

## 1. Executive Summary & Objective

Public-facing routes in `apps/web/` exposed internal architecture identifiers (`Medallion Lakehouse`, `DuckDB Kimball Star Schema`, `PostgreSQL 18`, `saved_competitions`, `mart_competition_explorer`, `bridge_competition_organizer`, `allocation_weight`, `Qdrant Filter`, `OWASP LLM10:2025`, `DIR-004`, `Gate G5/G6`, `ADMIN_EMAILS`) and lacked core student discovery workflows (instant search, status/sort controls, challenge brief, contextual rulebook Q&A links). At the root level, `README.md`, `openapi.json`, `.env.example`, `.env.dev`, and `docker-compose.yml` drifted behind the Cycle 06–07 `acdp.v2` pipeline and RBAC `/admin` API.

`TASK-HF-01` removes all internal engineering jargon from end-user views, upgrades the student UX based on competition-portal benchmarks (Devpost, Unstop, Kaggle), and synchronizes all root artifacts with automated regression tests.

---

## 2. Technical Changes & Audit Matrix

### 2.1. Frontend UI/UX Cleanup & Use-Case Upgrades (`apps/web/`)

| Surface / File | Issue Fixed | Student Use-Case Upgrade |
| :--- | :--- | :--- |
| `components/brand/AcdpLogo.tsx`, `TopNav.tsx`, `AppShell.tsx` | Removed `HCM-UTE Data Lakehouse`, `Medallion Lakehouse · DuckDB + PostgreSQL 18 + Qdrant`, `RAG Copilot` | Renamed nav labels to `Thống kê` and `Trợ lý Thể lệ`; added quick footer links |
| `app/page.tsx` | Removed `Medallion Lakehouse (DuckDB Star Schema)`, `Dashboard OLAP`, `RAG Copilot` | Added instant search bar (`action="/competitions"`), 5 quick filter chips, 3-step student workflow, and live featured competitions grid |
| `app/competitions/page.tsx`, `FilterSidebar.tsx`, `CompetitionCard.tsx` | Removed `DuckDB mart_competition_explorer` and `Academic Competition Explorer` | Activated `status` (`open`/`upcoming`/`closed`) & `sort` (`prize_desc`, `deadline_asc`, `name_asc`, `prize_asc`) controls, active filter chips, and `Miễn phí` card badge |
| `app/competitions/[key]/page.tsx` | Missing `target_audience` and `challenge_overview`; static link to `/copilot` | Rendered `Đối tượng`, `Lệ phí`, `Nội dung & Đề bài Thử thách`, and deep-link `/copilot?domain=...&q=...` |
| `app/dashboard/page.tsx`, `components/charts/*` | Removed `DuckDB Kimball Star Schema (read_only=True)`, `allocation_weight`, `bridge_competition_organizer`, hardcoded `5 nhóm ngành` | Replaced with student/advisor trend copy and dynamic `{kpi.unique_domains}` count |
| `app/copilot/page.tsx`, `CopilotWorkspace.tsx` | Removed `Qdrant`, `PostgreSQL 18`, `OWASP LLM10:2025`, `DIR-004`, hardcoded `17 nguồn` | Dynamically loads competition scopes from `/api/v1/competitions?page_size=100`, pre-fills `domain`/`q`, adds 4 sample prompts and loading status indicator |
| `app/bookmarks/page.tsx`, `BookmarkButton.tsx`, `login/page.tsx`, `layout.tsx`, `error.tsx` | Removed `PostgreSQL 18`, `saved_competitions`, `DuckDB Gold`, `Gold Star Schema`, `FastAPI Gateway` | Plain Vietnamese copy focused on deadlines, team notes, and saved rulebook sessions |
| `app/admin/page.tsx` | Exposed `ADMIN_EMAILS`, `Gate G5/G6`, and opened broken `/docs` URL | Removed internal labels; fixed Swagger UI action to fetch `/api/v1/admin/docs` with Bearer token |

### 2.2. Root Artifacts Synchronization

| Root File | Drift Detected | Resolution Applied |
| :--- | :--- | :--- |
| [`README.md`](../../README.md) | Referenced only `v1` scripts (`1..4_*.py`), omitted `src/acdp/v2/`, `scripts/seed_local_users.py`, and `.github/workflows/keep-alive.yml` | Updated architecture, `v2` pipeline table, repo layout, and CLI Quickstart |
| [`openapi.json`](../../openapi.json) | Missing 4 `/api/v1/admin/*` endpoints compared to `src/acdp/api/main.py` | Re-exported deterministically via `uv run python -m acdp.api.export_openapi` |
| [`.env.example`](../../.env.example), [`.env.dev`](../../.env.dev) | `GROQ_CHAT_MODEL` and `OPENROUTER_CHAT_MODEL` differed from `config.py`; missing `MOTHERDUCK_*`, `RAG_MAX_OUTPUT_TOKENS`, `RATE_LIMIT_ENABLED` | Aligned model IDs (`qwen/qwen3.8-27b`, `google/gemma-4-31b-it:free`) and documented missing keys |
| [`docker-compose.yml`](../../docker-compose.yml) | `api` service omitted `GROQ_*`, `OPENROUTER_*`, `ADMIN_EMAILS`, `SUPABASE_DIRECT_URL` passthroughs | Added passthrough env mappings while keeping `core` RAM cap (`1408M`) unchanged |

---

## 3. Verification & Automated Tests

New deterministic test suite [`tests/test_frontend_ux_and_root_sync.py`](../../tests/test_frontend_ux_and_root_sync.py) enforces:
1. Regex scan across 20 public UI files confirming zero internal database, pipeline, or directive leaks.
2. Admin page hygiene and authenticated `/api/v1/admin/docs` handler verification.
3. Presence of student discovery UX controls (`action="/competitions"`, `status`/`sort` filters, `challenge_overview`, `/copilot?` deep-linking, dynamic scope builder).
4. Exact path parity between `openapi.json` and `app.openapi()`, `.env.*` vs `AppConfig` fallback models, `docker-compose.yml` env keys, and `README.md` `v2` module references.

---

## 4. Associated Artifacts & Search Provenance

| Artifact | Path |
| :--- | :--- |
| Frontend Portal | [`apps/web/`](../../apps/web) |
| Root Documentation & Contracts | [`README.md`](../../README.md), [`openapi.json`](../../openapi.json), [`.env.example`](../../.env.example), [`.env.dev`](../../.env.dev), [`docker-compose.yml`](../../docker-compose.yml) |
| Automated Tests | [`tests/test_frontend_ux_and_root_sync.py`](../../tests/test_frontend_ux_and_root_sync.py) |
| Visual Dossier (HTML) | [`TASK-HF-01-fe-ux-cleanup-and-root-sync-visual-dossier.html`](./TASK-HF-01-fe-ux-cleanup-and-root-sync-visual-dossier.html) |
| Task Registry | [`docs/tasks/task-registry.md`](../tasks/task-registry.md) |

### Search Provenance & References
1. Web search query `hackathon competition discovery platform UX best practices Devpost Unstop Kaggle student portal 2025 2026` validated frictionless discovery patterns: smart faceted filters, urgency badges, contextual team/rulebook workflows, and mobile-first status visibility.
2. Internal project baselines [`docs/specs/0005-frontend-design-system-and-ux-spec.md`](../specs/0005-frontend-design-system-and-ux-spec.md) and [`docs/research/competitor-benchmarks.md`](../research/competitor-benchmarks.md).
