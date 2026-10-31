# ACDP Direction & AI Prompting Guide
> **A Handbook for Humans & AI Agents Working in the ACDP Workspace**

This document serves as the primary onboarding manual for the **Academic Competition Discovery Platform (ACDP)** at **Trường Đại học Công nghệ Kỹ thuật TP.HCM (HCM-UTE)**. It outlines the repository structure, clarifies the **Phase 1 (TLCN Lean MVP: 5–10 competitions)** vs. **Phase 2 (KLTN Full Scale)** boundaries, and provides a Prompt Cookbook for AI agents.

---

## 1. What is ACDP? (Repository Overview & Scope Boundary)

The **Academic Competition Discovery Platform (ACDP)** is an end-to-end data engineering and AI system built for the Faculty of Information Technology (FIT-HCMUTE).

### Phase 1: TLCN Lean MVP Scope (`DIR-015` — Current Active Phase)
During the 15-week Special Topic Project (*Tiểu luận chuyên ngành*), the team focuses on simulating the data architecture and validating technical feasibility over a small, curated set of **5–10 competition links** (currently 7 competitions in `data/raw/`):
1. **On-Demand Event Ingestion**: Crawls 5–10 selected academic contests on-demand using `Crawl4AI` (`src/acdp/1_crawl_to_bronze.py`) and stores clean UTF-8 Markdown directly on **Local Files** and **Cloudflare R2** (without unnecessary intermediate `zstandard` binary compression).
2. **Bronze-to-Silver LLM Extraction**: Uses `Instructor` + `LiteLLM` constrained by `Pydantic v2` (`SilverCompetitionRecord` in `src/acdp/lakehouse/schema.py`) to extract structured competition records (`src/acdp/2_instruction.py`) saved as Parquet/JSON.
3. **In-Process OLAP Analytics**: Queries Silver/Gold Parquet datasets directly via **DuckDB** without requiring heavy container daemons (`PostgreSQL`, `dbt-core`, or `SeaweedFS`).
4. **RAG Regulation Copilot**: Hybrid Search (`BM25` + `Qdrant` dense embeddings) with Cross-Encoder re-ranking grounded in official contest rulebooks.
5. **Student Portal & Faculty Dashboard MVP**: FastAPI backend and Next.js 15 web interface.

### Phase 2: KLTN Full-Scale Scope (Graduation Thesis)
High-volume automated crawling (periodic batch jobs, seasonality scheduler, HTTP `ETag` polling, realtime webhooks), multi-channel fuzzy entity deduplication, teammate matchmaking, and faculty advisor alignment are scheduled for Phase 2 (*Khóa luận tốt nghiệp*).

---

## 2. Directory Navigation Map

```text
acdp-platform/
├── AGENTS.md               <-- Master operating contract for all AI agents
├── GEMINI.md / CLAUDE.md   <-- Tool-specific configuration loaders
├── .cursorrules            <-- Cursor IDE & Windsurf directives
├── pyproject.toml          <-- Python dependencies managed via uv
├── .agents/skills/         <-- 9 specialized skills (Research, Thesis, Anti-Slop, Visual Dossier, etc.)
├── data/                   <-- Data storage (README.md, data/raw/ 7 sample contests, data/lakehouse/)
├── src/acdp/               <-- Core application codebase
│   ├── config.py           <-- Pydantic v2 settings (Local & Cloudflare R2)
│   ├── 1_crawl_to_bronze.py<-- On-demand Crawl4AI AdaptiveCrawler to R2 Bronze
│   ├── 2_instruction.py    <-- Instructor + LiteLLM Bronze-to-Silver extraction
│   └── lakehouse/          <-- Bronze/Silver schemas (schema.py), storage (bronze.py), seed.py
├── tests/                  <-- Pytest suites for Bronze storage and Silver schema contracts
└── docs/
    ├── README.md           <-- Central documentation index
    ├── HOW_TO_USE.md       <-- THIS FILE: Direction & prompt cookbook
    ├── frameworks/         <-- Prompt Execution Framework, TEAM_DIRECTIVES.md (DIR-001 to DIR-015)
    ├── academic/           <-- TLCN report manuscript, GVHD progress report, BibTeX, proposal
    ├── research/           <-- Competitor analysis (Devpost, Unstop, Ybox)
    ├── experiments/        <-- Empirical benchmarks (Ragas scorecards, query latency)
    ├── deliverables/       <-- Notion task outputs & Cloudflare R2 technical guide
    ├── adr/                <-- Architecture Decision Records
    ├── specs/              <-- SPEC-0001 (Foundation) & SPEC-0002 (Lean Ingestion & Schema)
    ├── rd-tasks/           <-- R&D research dossiers (T01, T02, T08_v2, T13)
    ├── tasks/              <-- Notion task mapping, 15-week roadmap, and active sprint (with Code TODOs)
    └── rfc/                <-- Change management protocol (RFC process)
```

---

## 3. Notion Task Synchronization & Quality Verification

- **Notion Task Mapping**: Consult [`docs/tasks/notion-task-mapping.md`](./tasks/notion-task-mapping.md) and [`docs/tasks/active-sprint.md`](./tasks/active-sprint.md) before starting work.
- **Automated Verification Commands**:
  ```bash
  # 1. Run unit tests for Bronze and Silver schemas
  uv run pytest -v

  # 2. Run Anti-Slop scientific writing linter on documentation
  uv run python .agents/skills/anti-slop-scientific-writer/scripts/detect_ai_slop.py <path-to-doc> --strict

  # 3. Verify external URL reachability
  uv run python .agents/skills/url-link-verifier/scripts/verify_links.py <path-to-doc>
  ```

---

## 4. AI Agent Prompt Cookbook (Copy & Paste)

### Mode 1: Academic Literature & SOTA Research
```text
@AGENTS.md Hãy tìm kiếm và tổng hợp các bài báo khoa học gần đây (2023 - 2026) về chủ đề "LLM Information Extraction from Unstructured Web Data" và "Hybrid Search in Administrative RAG". 
Trích xuất: Phương pháp cốt lõi, tập dữ liệu kiểm thử, hạn chế còn tồn đọng và điểm khác biệt của đề tài ACDP. 
Sau đó tạo mục trích dẫn BibTeX chuẩn và cập nhật vào docs/academic/references.bib.
```

### Mode 2: Competitor & Strategic Analysis
```text
@AGENTS.md Hãy tiến hành phân tích và so sánh đối thủ giữa ACDP với nền tảng Devpost và Unstop.
Lập ma trận so sánh 5 chiều: Cơ chế thu thập dữ liệu, Khả năng tra cứu thể lệ, Thuật toán ghép đội, Kênh kết nối giảng viên, và Bảng điều khiển phân tích cho trường đại học. 
Lưu kết quả phân tích vào docs/research/competitor-benchmarks.md.
```

### Mode 3: Drafting Thesis Chapters (FIT-HCMUTE Standard)
```text
@AGENTS.md Dựa trên SPEC-0002 và tài liệu trong docs/academic/, hãy viết hoặc cập nhật bản thảo trong docs/academic/BaoCao_TieuLuan_ChuyenNganh_KTDL.md bằng văn phong học thuật tiếng Việt tự nhiên chuẩn Khoa CNTT - Trường Đại học Công nghệ Kỹ thuật TP.HCM (HCM-UTE), tuân thủ DIR-009, DIR-010 và giới hạn quy mô 5-10 cuộc thi của TLCN (DIR-015).
```

### Mode 4: Slide Decks & Visual Dossiers
```text
@AGENTS.md Hãy tạo một báo cáo trực quan Single-File HTML (Tailwind CSS + Mermaid.js + Chart.js) tổng hợp tiến độ thực hiện tầng Bronze và Silver trên bộ 7 cuộc thi mẫu để nhóm báo cáo với GVHD ThS. Trần Quang Khải.
```
