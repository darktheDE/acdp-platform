# In-repo task registry & deliverables ledger

This ledger is auto-generated from [`tasks-data.json`](./tasks-data.json) and synchronized with the interactive portal [`index.html`](./index.html) per **DIR-018**.

- **Total tasks**: `44` (`26` completed)
- **Scope distribution**: `40` TLCN (Phase 1) | `6` KLTN (Phase 2)
- **Last updated**: `2026-11-22`

---

## Master task registry

| Task ID | Cycle | Scope | Layer | Title | Owner | Deliverables | Status |
| :---: | :---: | :---: | :---: | :--- | :---: | :--- | :---: |
| **NT-001** | Cycle 01 | TLCN (Phase 1) | Academic & Ops | Thesis Registration Form & Topic Proposal Formulation | Hung & Duy | [`DangKy_DeTai_TLCN.md`](../../docs/academic/DangKy_DeTai_TLCN.md) | ✅ Done |
| **NT-002** | Cycle 01 | TLCN (Phase 1) | Academic & Ops | Scientific Research Proposal (NCKH) Manuscript Drafting | Hung & Duy | [`Proposal_NCKH_TLCN.md`](../../docs/academic/Proposal_NCKH_TLCN.md) | ✅ Done |
| **NT-003** | Cycle 01 | TLCN (Phase 1) | Academic & Ops | Proposal Defense Presentation Deck Construction | Hung & Duy | [`Slide_Proposal_TLCN.html`](../../docs/academic/Slide_Proposal_TLCN.html) | ✅ Done |
| **NT-004** | Cycle 01 | TLCN (Phase 1) | Academic & Ops | Literature Review & SOTA Matrix Synthesis | Hung | [`literature-review.md`](../../docs/academic/literature-review.md) | ✅ Done |
| **NT-005** | Cycle 01 | TLCN (Phase 1) | Academic & Ops | BibTeX Citation Library Setup | Duy | [`references.bib`](../../docs/academic/references.bib) | ✅ Done |
| **NT-006** | Cycle 01 | TLCN (Phase 1) | Academic & Ops | Platform Competitor Benchmarking (Devpost, Unstop) | Hung | [`competitor-benchmarks.md`](../../docs/research/competitor-benchmarks.md) | ✅ Done |
| **NT-007** | Cycle 01 | TLCN (Phase 1) | Cloud & Infra | Foundational Architecture Decision Formulation (ADR-0001) | Hung & Duy | [`0001-medallion-lakehouse-and-rag-stack.md`](../../docs/adr/0001-medallion-lakehouse-and-rag-stack.md) | ✅ Done |
| **NT-008** | Cycle 01 | TLCN (Phase 1) | Academic & Ops | Multi-Agent Harness & Skills Suite Deployment | Hung & Duy | [`AGENTS.md`](../../AGENTS.md), [`README.md`](../../.agents/skills/README.md) | ✅ Done |
| **NT-009** | Cycle 02 | TLCN (Phase 1) | Bronze | On-Demand Crawl4AI Feasibility Spike on Curated Competitions & R2 Upload | Hung & Duy | [`1_crawl_to_bronze.py`](../../src/acdp/1_crawl_to_bronze.py), [`markdown`](../../data/raw/markdown) | ✅ Done |
| **NT-010** | Cycle 02 | TLCN (Phase 1) | Silver | Pydantic Event Schema & Lean Extraction Spec (SPEC-0002) | Hung & Duy | [`0002-data-ingestion-and-schema-spec.md`](../../docs/specs/0002-data-ingestion-and-schema-spec.md), [`schemas.py`](../../src/acdp/schemas.py) | ✅ Done |
| **NT-011** | Cycle 03 | TLCN (Phase 1) | Silver | Bronze-to-Silver LLM Extraction & DuckDB Gold OLAP Querying | Hung & Duy | [`2_instruction.py`](../../src/acdp/2_instruction.py), [`4_analytics_gold.py`](../../src/acdp/4_analytics_gold.py) | ✅ Done |
| **NT-012** | Cycle 03 | TLCN (Phase 1) | Serving & Web | Hybrid Search (BM25 + Qdrant) RAG Prototype & Ragas Scorecard | Hung & Duy | [`3_chatbot_mvp.py`](../../src/acdp/3_chatbot_mvp.py), [`0001-rag-baseline-evaluation.md`](../../docs/experiments/0001-rag-baseline-evaluation.md) | 🔄 In Progress |
| **NT-013** | Cycle 01 | TLCN (Phase 1) | Discovery | Business Requirements, Technical Feasibility & Architectural Review (T01) | Hung & Duy | [`NT-013-business-technical-feasibility-review.md`](../../docs/deliverables/NT-013-business-technical-feasibility-review.md) | ✅ Done |
| **NT-014** | Cycle 01 | TLCN (Phase 1) | Discovery | Academic Competition Landscape Survey & Ingestion Scaling Roadmap (T02) | Hung & Duy | [`NT-014-competition-landscape-survey.md`](../../docs/deliverables/NT-014-competition-landscape-survey.md) | ✅ Done |
| **NT-017** | Cycle 01 | TLCN (Phase 1) | Academic & Ops | Problem Formulation & Thesis Introduction Drafting (T08_v2) | Hung & Duy | [`T08_v2.md`](../../docs/rd-tasks/T08_v2.md) | ✅ Done |
| **NT-018** | Cycle 02 | TLCN (Phase 1) | Bronze | Bronze Layer Storage & Open Table Format Tech Stack Evaluation (T13) | Hung & Duy | [`NT-018-bronze-storage-and-table-format-evaluation.md`](../../docs/deliverables/NT-018-bronze-storage-and-table-format-evaluation.md) | ✅ Done |
| **NT-019** | Cycle 02 | TLCN (Phase 1) | Bronze | Bronze Lakehouse Engine Implementation & Lean Refactoring | Hung & Duy | [`1_crawl_to_bronze.py`](../../src/acdp/1_crawl_to_bronze.py) | ✅ Done |
| **NT-020** | Cycle 02 | TLCN (Phase 1) | Silver | Silver Layer Competition Schema & Data Contracts Implementation | Hung & Duy | [`schemas.py`](../../src/acdp/schemas.py) | ✅ Done |
| **NT-021** | Cycle 03 | TLCN (Phase 1) | Academic & Ops | Comprehensive FIT-HCMUTE Specialized Topic Project Report Manuscript | Hung & Duy | [`BaoCao_TieuLuan_ChuyenNganh_KTDL.md`](../../docs/academic/BaoCao_TieuLuan_ChuyenNganh_KTDL.md) | 🔄 In Progress |
| **NT-022** | Cycle 02 | TLCN (Phase 1) | Bronze | Lakehouse Cloudflare R2 Sync Technical Guide | Hung & Duy | [`HUONG_DAN_MIGRATE_R2_LAKEHOUSE.md`](../../docs/deliverables/HUONG_DAN_MIGRATE_R2_LAKEHOUSE.md) | ✅ Done |
| **NT-023** | Cycle 04 | TLCN (Phase 1) | Serving & Web | Web & Gold Tech Stack Benchmarking (2026-2027 LTS Matrix) | Hung & Duy | [`T14_web_and_gold_stack_evaluation.md`](../../docs/rd-tasks/T14_web_and_gold_stack_evaluation.md) | ✅ Done |
| **NT-024** | Cycle 04 | TLCN (Phase 1) | Gold | Gold Layer Kimball Star Schema & Analytical Data Marts Design | Hung & Duy | [`0003-gold-dimensional-modeling-spec.md`](../../docs/specs/0003-gold-dimensional-modeling-spec.md) | ✅ Done |
| **NT-025** | Cycle 04 | TLCN (Phase 1) | Serving & Web | FastAPI Serving Gateway, PostgreSQL 18 OLTP & Spec-Driven OpenAPI Contract | Hung & Duy | [`0004-serving-api-and-oltp-spec.md`](../../docs/specs/0004-serving-api-and-oltp-spec.md) | ✅ Done |
| **NT-026** | Cycle 04 | TLCN (Phase 1) | Serving & Web | Frontend Brand Identity (SVG Logo), WCAG 2.2 Color Tokens & UI/UX Spec | Hung & Duy | [`0005-frontend-design-system-and-ux-spec.md`](../../docs/specs/0005-frontend-design-system-and-ux-spec.md) | ✅ Done |
| **NT-027** | Cycle 04 | TLCN (Phase 1) | Cloud & Infra | Docker Infrastructure, Version Pinning & 16GB RAM Resource Budget | Hung & Duy | [`0006-docker-infrastructure-and-resource-spec.md`](../../docs/specs/0006-docker-infrastructure-and-resource-spec.md) | ✅ Done |
| **NT-028** | Cycle 04 | TLCN (Phase 1) | Serving & Web | 4-Tier Testing Strategy, 8 Edge Cases & Manual Test / CLI Playbook | Hung & Duy | [`sprint-web-01-research-plan.md`](../../docs/tasks/sprint-web-01-research-plan.md) | ✅ Done |
| **NT-029** | Cycle 05 | TLCN (Phase 1) | Serving & Web | Web Sprint 02 Full-Stack Implementation (Docker, FastAPI + PG18, Next.js 16) | Hung | [`api`](../../src/acdp/api), [`web`](../../apps/web), [`docker-compose.yml`](../../docker-compose.yml) | ✅ Done |
| **TASK-ING-01** | Cycle 06 | TLCN (Phase 1) | Discovery | Nghiên cứu Search Pattern & Kỹ thuật Cào Tối ưu trên Free Tier (Scale nhỏ) | Hung & Duy | [`TASK-ING-01-search-pattern-and-crawling-tradeoffs.md`](../../docs/deliverables/TASK-ING-01-search-pattern-and-crawling-tradeoffs.md), [`TASK-ING-01-search-pattern-and-crawling-tradeoffs-visual-dossier.html`](../../docs/deliverables/TASK-ING-01-search-pattern-and-crawling-tradeoffs-visual-dossier.html) | ✅ Done |
| **TASK-BRZ-01** | Cycle 06 | TLCN (Phase 1) | Bronze | Kiểm định Lý thuyết Lớp Đồng (Bronze Purity: Raw HTML vs Pre-processed Markdown) | Hung & Duy | `docs/deliverables/TASK-BRZ-01-bronze-raw-vs-markdown-justification.md` | ⏳ Todo |
| **TASK-SLV-01** | Cycle 06 | TLCN (Phase 1) | Silver | Bảo vệ Tính chất Data Engineering & Tối ưu Tỷ lệ Sử dụng LLM ở Lớp Bạc | Hung & Duy | `docs/deliverables/TASK-SLV-01-hybrid-de-vs-llm-extraction-study.md` | ⏳ Todo |
| **TASK-SLV-02** | Cycle 06 | TLCN (Phase 1) | Silver | Kiểm chứng Schema Lớp Bạc (Competition + PrizeTier) & Lưu trữ Parquet | Hung & Duy | `docs/deliverables/TASK-SLV-02-silver-schema-and-parquet-validation.md` | ⏳ Todo |
| **TASK-GLD-01** | Cycle 06 | TLCN (Phase 1) | Gold | Phản biện & Bảo vệ Mô hình Lớp Vàng (Kimball Star Schema vs OBT / Alternatives) | Hung & Duy | `docs/deliverables/TASK-GLD-01-kimball-star-schema-audit-and-alternatives.md` | ⏳ Todo |
| **TASK-CLD-01** | Cycle 07 | TLCN (Phase 1) | Cloud & Infra | Đồng nhất Qdrant Cloud & Xác định Vai trò Qdrant Docker Local | Hung & Duy | [`docker-compose.yml`](../../docker-compose.yml), [`config.py`](../../src/acdp/config.py) | ⏳ Todo |
| **TASK-CLD-02** | Cycle 07 | TLCN (Phase 1) | Cloud & Infra | Phân định Ranh giới Vai trò giữa Web Dashboard và Metabase | Hung & Duy | [`T15_metabase_and_prefect_lightweight_architecture.md`](../../docs/rd-tasks/T15_metabase_and_prefect_lightweight_architecture.md) | ⏳ Todo |
| **TASK-CLD-03** | Cycle 07 | TLCN -> KLTN | Cloud & Infra | Kiến trúc Đồng bộ Full Cloud Free-Tier (Giải quyết Hybrid Local vs Cloud) | Hung & Duy | `docs/deliverables/TASK-CLD-03-full-cloud-free-tier-architecture.md` | ⏳ Todo |
| **TASK-CLD-04** | Cycle 07 | TLCN -> KLTN | Cloud & Infra | Triển khai Kết nối Supabase OLTP & DuckDB Direct-on-R2 (s3://) | Hung | [`config.py`](../../src/acdp/config.py), [`api`](../../src/acdp/api) | ⏳ Todo |
| **TASK-SRV-01** | Cycle 08 | TLCN (Phase 1) | Serving & Web | Xây dựng Trang Hồ sơ Cá nhân Sinh viên (/profile — Định dạng Mini-CV) | Hung | `apps/web/app/profile/page.tsx`, [`api`](../../src/acdp/api) | ⏳ Todo |
| **TASK-SRV-02** | Cycle 08 | TLCN (Phase 1) | Serving & Web | Hệ thống Tạo Đội & Xin Tham Gia Đội trên từng Cuộc thi (Thuần OLTP — Không AI) | Hung | [`competitions`](../../apps/web/app/competitions), [`api`](../../src/acdp/api) | ⏳ Todo |
| **TASK-SRV-03** | Cycle 08 | TLCN (Phase 1) | Serving & Web | Màn hình Tổng hợp Thông tin Cuộc thi & Đội thi (Team Summary để gửi Giảng viên) | Hung | `apps/web/app/teams` | ⏳ Todo |
| **TASK-SRV-04** | Cycle 08 | TLCN (Phase 1) | Serving & Web | Nâng cấp RAG Chatbot Tư vấn Cuộc thi Phù hợp theo Hồ sơ Sinh viên | Duy & Hung | [`rag_service.py`](../../src/acdp/api/services/rag_service.py) | ⏳ Todo |
| **TASK-ING-02** | Cycle 09 | KLTN (Phase 2) | Discovery | Tự động hóa Khám phá & Cào Cuộc thi Định kỳ bằng GitHub Actions | Hung & Duy | `.github/workflows` | ⏳ Todo |
| **TASK-SRV-05** | Cycle 09 | KLTN (Phase 2) | Serving & Web | Hệ thống Thông báo & Mail Service Tự động khi có Cuộc thi Mới | Hung | [`services`](../../src/acdp/api/services) | ⏳ Todo |
| **TASK-OPS-01** | Cycle 10 | KLTN (Phase 2) | Academic & Ops | Triển khai Truyền thông Bài bản, Bộ Nhận diện Thương hiệu & Fanpage *(No-Code)* | Duy & Hung | [`task-registry.md`](../../docs/tasks/task-registry.md) | ⏳ Todo |
| **TASK-OPS-02** | Cycle 10 | KLTN (Phase 2) | Academic & Ops | Nền tảng Quản lý Ticket & Phản hồi Người dùng (External No-Code Platform) *(No-Code)* | Hung & Duy | [`task-registry.md`](../../docs/tasks/task-registry.md) | ⏳ Todo |

---

## Synchronization commands

```powershell
uv run python .agents/skills/repo-task-manager/scripts/sync_tasks.py --sync
uv run python .agents/skills/repo-task-manager/scripts/sync_tasks.py --validate
```
