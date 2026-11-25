# DELIVERABLE: Task Gap Audit & Correctness Assurance Plan (TLCN + KLTN)

- **Task ID**: `TASK-QA-00` (Audit Baseline)
- **Related Sprint**: Cycle 07–10 Planning
- **Primary Owner**: Do Kien Hung & Nguyen Van Quang Duy
- **Date Completed**: 2026-11-25
- **Deliverable Type**: Governance Audit & Task Planning
- **Status**: Complete

---

## 1. Executive Summary & Objective

Rà soát toàn bộ `61` task nền tảng ban đầu trong [`docs/tasks/tasks-data.json`](../tasks/tasks-data.json) (`53` TLCN, `12` KLTN; `44` đã hoàn thành) nhằm đảm bảo mọi layer và quyết định kỹ thuật đều được kiểm chứng theo 3 trục: **đúng lý thuyết**, **đúng thực tiễn doanh nghiệp/OSS**, và **cho ra output đúng với nhu cầu người dùng**.

Sau hai đợt rà soát và tinh chỉnh theo định hướng thực tế (`DIR-023`), hệ thống quản lý task được bổ sung tổng cộng **24 task mới** (nâng tổng số lên **85 task**), đồng thời hiệu chỉnh chiến lược triển khai giữa hai giai đoạn:
- **TLCN (Phase 1 — Cycle 07–08, +15 task mới)**: Tập trung hoàn thiện kiểm chứng dữ liệu (`TASK-DQ-01..06`), audit lý thuyết/thực tiễn (`TASK-QA-01`), xác thực theo Persona + Đối chuẩn + GVHD (`TASK-QA-03`, thay cho khảo sát rộng chưa khả thi ở TLCN), CI/CD Data Validation tách biệt với `keep-alive.yml` (`TASK-QA-08`), FE tối giản dễ demo (`TASK-FE-01`), tối ưu BE API + AI (`TASK-BE-01`), và trọn bộ sơ đồ BA/CNPM/System/BE/FE/Data Pipeline cho báo cáo (`TASK-DOC-01`).
- **KLTN (Phase 2 — Cycle 09–10, +9 task mới)**: Mở rộng sang vận hành Production gồm Orchestration/Backfill (`TASK-DQ-11`), Incremental & Schema Evolution (`TASK-DQ-12`), Observability (`TASK-DQ-13`), Golden Eval & LLM Drift (`TASK-DQ-14`), Re-audit Kiến trúc (`TASK-QA-15`), **Multi-Provider Free AI Gateway** không nghẽn giới hạn Gemini (`TASK-AI-01`), **FE Production chuẩn Design System & UI/UX Rules** (`TASK-FE-02`), **Triển khai Cộng đồng/CLB & Khảo sát SUS Thực tế** (`TASK-USR-01`), và **Mở rộng Hệ thống Sơ đồ & Luận văn KLTN** (`TASK-DOC-02`).

---

## 2. Lỗ hổng phát hiện & Chiến lược Khắc phục

| # | Lỗ hổng | Bằng chứng từ registry cũ | Task mới khắc phục |
| :---: | :--- | :--- | :--- |
| 1 | Chưa có golden dataset hay độ chính xác trích xuất theo từng field cho Silver | `TASK-SLV-01..04` dừng ở thiết kế, phản biện và triển khai code | `TASK-DQ-02`, `TASK-DQ-14` |
| 2 | Chưa có Data Contract hay Quality Gate chạy tự động giữa các layer | Chưa có task kiểm soát chất lượng dữ liệu tự động | `TASK-DQ-03` |
| 3 | Chưa kiểm chứng grain, khóa thay thế, toàn vẹn tham chiếu của Gold và đối soát số liệu với Silver | `TASK-GLD-01/02` dừng ở phản biện mô hình và hiệu chỉnh schema | `TASK-DQ-05` |
| 4 | Chưa có ma trận truy vết Yêu cầu → Schema → API → UI | `NT-013` có yêu cầu nhưng không ánh xạ 1-1 tới field/bảng/màn hình | `TASK-QA-02` |
| 5 | Xác thực người dùng chưa tách rõ tính khả thi giữa TLCN và KLTN | TLCN khó khảo sát sinh viên diện rộng khi chưa ready-for-prod; thiếu kênh cộng đồng/CLB | `TASK-QA-03` (TLCN: Persona + GVHD), `TASK-USR-01` (KLTN: CLB + SUS) |
| 6 | Chưa có kiểm định tính bất biến, provenance và idempotent re-crawl ở Bronze | `TASK-BRZ-01/02` chưa có bộ test xác nhận re-crawl không sinh trùng | `TASK-DQ-01` |
| 7 | Chưa có Entity Resolution / khử trùng cuộc thi đa nguồn, đa mùa giải | `TASK-ING-03` discovery 3 tầng trả về nhiều nguồn cho cùng một sự kiện | `TASK-DQ-04` |
| 8 | Chưa có Lineage, Run Manifest và kiểm thử Idempotency end-to-end | Pipeline chạy on-demand chưa có cơ chế kiểm chứng chạy lại cho kết quả đồng nhất | `TASK-DQ-06` |
| 9 | Chưa rà soát chéo toàn bộ ADR/tech stack theo 3 trục (Lý thuyết × Thực tiễn × Scope) | `ADR-0001/0002` đã ban hành nhưng chưa có audit đối chiếu case doanh nghiệp/OSS | `TASK-QA-01`, `TASK-QA-15` |
| 10 | Chưa có Golden QA set chuẩn hóa và kiểm định trích dẫn URL 100% | `NT-012` mới dừng ở Ragas baseline tự tạo (`in_progress`) | `TASK-QA-07` |
| 11 | `.github/workflows/` mới chỉ có `keep-alive.yml` (cron), thiếu CI/CD Data Validation | Chưa có workflow kiểm định Bronze/Silver/Gold + API + FE khi push/PR | `TASK-QA-08` |
| 12 | Chưa có quy trình triage lỗi, RCA và regression test bắt buộc | Chưa có sổ theo dõi lỗi và quy tắc gắn regression test | `TASK-QA-09` |
| 13 | Thiếu tách tầng FE (Demo TLCN vs Design System KLTN), tối ưu BE & Multi-Provider Free AI Gateway | Fallback sơ bộ ở `TASK-CLD-06` chưa giải quyết quota-aware routing & Silver/RAG scale lớn; FE thiếu lộ trình tối giản -> production | `TASK-FE-01`, `TASK-BE-01`, `TASK-AI-01`, `TASK-FE-02` |
| 14 | Thiếu bộ sơ đồ chuẩn BA, CNPM, System, BE, FE & Data/AI Pipeline cho báo cáo | Báo cáo `NT-021` & `TASK-KLT-01` chưa có task gom trọn hệ thống sơ đồ đồng bộ | `TASK-DOC-01`, `TASK-DOC-02` |
| 15 | KLTN thiếu orchestration + backfill, incremental/schema evolution và data observability | `TASK-ING-02` và `TASK-GLD-03` chưa bao phủ đầy đủ 3 năng lực vận hành này | `TASK-DQ-11`, `TASK-DQ-12`, `TASK-DQ-13` |

---

## 3. Danh mục 24 task bổ sung & Lý do thiết kế

### 3.1. Phạm vi TLCN (Phase 1 & Cầu nối `TLCN -> KLTN` — Cycle 07–08, 15 task)

| Task ID | Cycle | Scope | Layer | Mục tiêu & Lý do bổ sung | Deliverable dự kiến |
| :--- | :---: | :---: | :---: | :--- | :--- |
| **TASK-QA-01** | Cycle 07 | TLCN (Phase 1) | Academic & Ops | Audit toàn bộ quyết định kỹ thuật theo 3 trục: nguồn học thuật/chuẩn chính thức, case doanh nghiệp/OSS thực tế, và mức độ hợp lý với scope 5–10 cuộc thi. | `docs/deliverables/TASK-QA-01-tech-decision-theory-practice-audit.md` |
| **TASK-QA-02** | Cycle 08 | TLCN (Phase 1) | Discovery | Ma trận truy vết (RTM) Yêu cầu từ Persona/GVHD → Silver → Gold → API → UI để phát hiện field thừa hoặc thiếu. | `docs/deliverables/TASK-QA-02-requirements-traceability-matrix.md` |
| **TASK-QA-03** | Cycle 08 | TLCN (Phase 1) | Discovery | Xác thực nhu cầu & schema qua 3 Persona chuẩn, đối chuẩn Devpost/Unstop/YBox và tham vấn GVHD (khả thi cho TLCN; khảo sát thật dời sang `TASK-USR-01`). | `docs/deliverables/TASK-QA-03-persona-competitor-advisor-validation.md` |
| **TASK-DQ-01** | Cycle 07 | TLCN (Phase 1) | Bronze | Kiểm định Bronze: content hash, URL gốc, timestamp, UTF-8 và tính idempotent khi re-crawl. | `docs/deliverables/TASK-DQ-01-bronze-validation-report.md` |
| **TASK-DQ-02** | Cycle 07 | TLCN (Phase 1) | Silver | Gán nhãn tay 5–10 cuộc thi thành Golden Dataset; đo Precision/Recall/Exact-Match theo từng field và phân loại lỗi. | `docs/deliverables/TASK-DQ-02-silver-golden-dataset-accuracy.md` |
| **TASK-DQ-03** | Cycle 07 | TLCN (Phase 1) | Silver | Data Contract & Quality Gate tự động (Pydantic v2 + DuckDB checks) chặn dữ liệu lỗi, kiểm tra URL chính thức theo DIR-022. | `docs/deliverables/TASK-DQ-03-data-contracts-and-quality-gates.md` |
| **TASK-DQ-04** | Cycle 07 | TLCN (Phase 1) | Silver | Entity Resolution & khử trùng cuộc thi theo khóa tự nhiên (tên chuẩn hóa + đơn vị tổ chức + năm). | `docs/deliverables/TASK-DQ-04-entity-resolution-and-dedup.md` |
| **TASK-DQ-05** | Cycle 07 | TLCN (Phase 1) | Gold | Kiểm chứng Gold: không trùng grain, không FK mồ côi, đối soát 100% với Silver và giải được toàn bộ câu hỏi từ `TASK-QA-02`. | `docs/deliverables/TASK-DQ-05-gold-integrity-and-reconciliation.md` |
| **TASK-DQ-06** | Cycle 07 | TLCN (Phase 1) | Cloud & Infra | Ghi Run Manifest (input hash → output) và kiểm thử chạy lại end-to-end 2 lần cho kết quả đồng nhất. | `docs/deliverables/TASK-DQ-06-lineage-manifest-and-idempotency.md` |
| **TASK-QA-07** | Cycle 08 | TLCN (Phase 1) | Serving & Web | Golden QA Set >= 30 câu bám sát Persona/GVHD (`TASK-QA-03`), đạt ngưỡng Faithfulness & Context Precision và 100% trích dẫn URL. | `docs/deliverables/TASK-QA-07-rag-golden-qa-and-citation-gate.md` |
| **TASK-QA-08** | Cycle 08 | TLCN (Phase 1) | Cloud & Infra | Thiết lập `.github/workflows/ci-validation.yml` tách biệt với `keep-alive.yml`: chạy Ruff, Pytest, Data Validation Gate (Bronze/Silver/Gold) và Next.js build. | `.github/workflows/ci-validation.yml`, `docs/deliverables/TASK-QA-08-ci-pipeline-and-dq-tests.md` |
| **TASK-QA-09** | Cycle 08 | TLCN (Phase 1) | Academic & Ops | Quy trình Bug Ledger, phân tích nguyên nhân gốc (RCA) và regression test bắt buộc cho mọi bug đã sửa. | `docs/deliverables/TASK-QA-09-bug-triage-rca-and-regression.md` |
| **TASK-FE-01** | Cycle 08 | TLCN (Phase 1) | Serving & Web | Hoàn thiện FE Tiểu luận tối giản, ít thao tác thừa, đủ loading/empty/error states để Demo bảo vệ 15 phút mượt mà. | `apps/web/app`, `docs/deliverables/TASK-FE-01-tlcn-clean-demo-ui.md` |
| **TASK-BE-01** | Cycle 08 | TLCN -> KLTN | Serving & Web | Tối ưu Backend toàn diện: async Supabase pooler, DuckDB-on-R2 projection/predicate pushdown + cache, xóa N+1, nén ngữ cảnh RAG, SSE streaming & benchmark p50/p95. | `src/acdp/api`, `docs/deliverables/TASK-BE-01-backend-api-and-ai-optimization.md` |
| **TASK-DOC-01** | Cycle 08 | TLCN (Phase 1) | Academic & Ops | Xây dựng trọn bộ sơ đồ BA, System/CNPM (C4, Sequence, Deployment), BE (OLTP ERD), FE (Sitemap/Components), Data/AI Pipeline & tối ưu `BaoCao_TieuLuan_ChuyenNganh_KTDL.md`. | `docs/academic/BaoCao_TieuLuan_ChuyenNganh_KTDL.md`, `docs/deliverables/TASK-DOC-01-tlcn-complete-diagrams-and-report-polish.md` |

### 3.2. Phạm vi KLTN (Phase 2 — Cycle 09–10, 9 task)

| Task ID | Cycle | Layer | Mục tiêu & Lý do bổ sung | Deliverable dự kiến |
| :--- | :---: | :---: | :--- | :--- |
| **TASK-DQ-11** | Cycle 09 | Cloud & Infra | Đối chiếu Orchestrator (GitHub Actions / Prefect / Dagster) ở quy mô 100–500 cuộc thi, kèm retry & backfill. | `docs/deliverables/TASK-DQ-11-kltn-orchestration-retry-backfill.md` |
| **TASK-DQ-12** | Cycle 09 | Silver | Incremental load theo content hash & Schema Evolution (versioning schema, migration Parquet). | `docs/deliverables/TASK-DQ-12-incremental-load-and-schema-evolution.md` |
| **TASK-DQ-13** | Cycle 09 | Cloud & Infra | Data Observability: giám sát Freshness, Volume, Null/Schema Drift và cảnh báo tự động. | `docs/deliverables/TASK-DQ-13-data-observability-and-alerting.md` |
| **TASK-DQ-14** | Cycle 09 | Silver | Mở rộng Golden Dataset bằng lấy mẫu phân tầng ở quy mô 100–500 cuộc thi và theo dõi LLM drift giữa các phiên bản model. | `docs/deliverables/TASK-DQ-14-kltn-scaled-golden-eval-and-llm-drift.md` |
| **TASK-QA-15** | Cycle 10 | Academic & Ops | Audit lại toàn bộ kiến trúc ở quy mô KLTN dựa trên số liệu thực nghiệm và cập nhật ADR qua peer defense (DIR-011). | `docs/deliverables/TASK-QA-15-kltn-architecture-reaudit-and-adr.md` |
| **TASK-AI-01** | Cycle 09 | Serving & Web | Kiến trúc Multi-Provider Free AI Gateway (Groq, OpenRouter `:free`, Cloudflare Workers AI, Gemini/Gemma, GitHub Models/Ollama) dùng chung Silver & RAG, quota-aware routing & Semantic Cache. | `src/acdp/v2`, `src/acdp/api/services/rag_service.py`, `docs/deliverables/TASK-AI-01-multi-provider-free-ai-gateway.md` |
| **TASK-FE-02** | Cycle 09 | Serving & Web | Nghiên cứu UI/UX Rules, Agent Design Skills, System Color Tokens (WCAG 2.2 AA), Mobile-First & xây dựng FE hoàn chỉnh chuẩn Production (Lighthouse >= 90). | `apps/web`, `docs/specs/0005-frontend-design-system-and-ux-spec.md`, `docs/deliverables/TASK-FE-02-kltn-production-design-system-and-fe.md` |
| **TASK-USR-01** | Cycle 10 | Discovery | Triển khai thực tế cho Cộng đồng / CLB Sinh viên sau khi ready-for-prod & phát hành form khảo sát SUS + mức độ hữu ích ($N \ge 30\text{--}50$). | `docs/deliverables/TASK-USR-01-club-community-rollout-and-survey.md` |
| **TASK-DOC-02** | Cycle 10 | Academic & Ops | Mở rộng bộ sơ đồ BA/CNPM/System/BE/FE/Data Pipeline sang quy mô KLTN Production & hoàn thiện Luận văn `KhoaLuan_TotNghiep_KTDL.md`. | `docs/academic/KhoaLuan_TotNghiep_KTDL.md`, `docs/deliverables/TASK-DOC-02-kltn-architecture-diagrams-and-thesis-polish.md` |

---

## 4. Thứ tự phụ thuộc & Ảnh hưởng tới Registry

```text
TLCN (Phase 1 — Cycle 07 & 08):
TASK-QA-03 (Persona + Competitor + GVHD)
   └──> TASK-QA-02 (Traceability Matrix)
           ├──> TASK-DQ-02 (Silver Golden Eval)
           ├──> TASK-DQ-05 (Gold Integrity) ──> TASK-DQ-06 (Lineage & Idempotency)
           └──> TASK-QA-07 (RAG Golden QA)

TASK-BRZ-02 ──> TASK-DQ-01 (Bronze Validation) ──> TASK-DQ-06
TASK-SLV-04 ──> TASK-DQ-03 (Data Contracts)    ──> TASK-QA-08 (CI/CD Data Gate) ──> TASK-QA-09 (RCA & Regression)
TASK-ING-03 + TASK-SLV-04 ──> TASK-DQ-04 (Entity Resolution)

TASK-FE-01 + TASK-BE-01 + TASK-QA-08 ──> TASK-TST-01 (Demo Day E2E)
TASK-QA-01..09 + TASK-FE-01 + TASK-BE-01 ──> TASK-DOC-01 (Full Diagrams & Report) ──> NT-021 & TASK-ACD-01

KLTN (Phase 2 — Cycle 09 & 10):
TASK-BE-01 + TASK-CLD-06 ──> TASK-AI-01 (Multi-Provider Free AI Gateway) ──┐
TASK-FE-01               ──> TASK-FE-02 (Design System & Prod FE)       ──┼──> TASK-USR-01 (CLB Rollout & SUS Survey)
TASK-DQ-11..14 + TASK-QA-15 + TASK-USR-01 ──> TASK-DOC-02 (KLTN Diagrams & Thesis) ──> TASK-KLT-01
```

---

## 5. Associated Artifacts & Code Links

- **Task Data JSON**: [`docs/tasks/tasks-data.json`](../tasks/tasks-data.json)
- **Task Registry Markdown**: [`docs/tasks/task-registry.md`](../tasks/task-registry.md)
- **Interactive Portal**: [`docs/tasks/index.html`](../tasks/index.html)
- **Team Directives**: [`docs/frameworks/TEAM_DIRECTIVES.md`](../frameworks/TEAM_DIRECTIVES.md) (`DIR-023`)

---

## 6. Search Provenance & References (DIR-020)

| Search Query Executed | Reference Source | Direct Verified URL |
| :--- | :--- | :--- |
| `"Kimball Group" "Dimensional Modeling" techniques OR "Data Warehouse Toolkit" official url` | Kimball Group — Dimensional Modeling Techniques & Toolkit Hub | https://www.kimballgroup.com |
| `site:docs.databricks.com "medallion architecture" url` | Databricks Official Documentation — What is the medallion lakehouse architecture? | https://docs.databricks.com/aws/en/lakehouse/medallion |
| `site:docs.ragas.io "faithfulness" "context precision" url` | Ragas Official Documentation — Faithfulness & Context Precision Metrics | https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/faithfulness/ ; https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/context_precision/ |
| `"Data Contracts" "Andrew Jones" OR "Bitol" "Open Data Contract Standard" official url` | Bitol (Linux Foundation AI & Data) — Open Data Contract Standard (ODCS) & Andrew Jones Data Contracts | https://bitol-io.github.io/open-data-contract-standard/ ; https://github.com/bitol-io/open-data-contract-standard ; https://andrew-jones.com |
| `site:c4model.com official documentation context container component` | Simon Brown — The C4 Model for Visualising Software Architecture | https://c4model.com |
| `"System Usability Scale" "John Brooke" OR site:usability.gov OR site:digital.gov SUS official url` | John Brooke (1996) SUS Paper & US Digital.gov Usability Guidelines | https://www.researchgate.net/publication/228593520_SUS_A_quick_and_dirty_usability_scale ; https://digital.gov/resources/usability/ |
| `free LLM API providers 2026 rate limits Groq Cerebras OpenRouter Cloudflare Workers AI LiteLLM fallback` | OpenRouter Free Models & Rate Limits / Groq / Cloudflare Workers AI (2026 verified via search) | https://openrouter.ai ; https://www.groq.com ; https://developers.cloudflare.com/workers-ai/ |
