# ACDP Direction & AI Prompting Guide
> **A Comprehensive Handbook for Humans & AI Agents Working in the ACDP Workspace**

This document serves as the primary onboarding manual. It explains the purpose and capabilities of the repository, guides human reviewers on navigating its assets, and provides a ready-to-use **Prompt Cookbook** for interacting with any AI agent (Google Antigravity, Claude Code, Cursor, etc.) across every phase of the project.

---

## 1. What is ACDP? (Repository Overview)

The **Academic Competition Discovery Platform (ACDP)** is an end-to-end data-centric system built for the Faculty of Information Technology at Ho Chi Minh City University of Technology and Engineering (FIT-HCMUTE).

### Core Capabilities
1. **Automated Event Ingestion**: Scrapes and normalizes academic contests and hackathons across dynamic websites and social media using Crawl4AI, Playwright, and LLM Schema Enforcement (Pydantic).
2. **Medallion Lakehouse**: Tiered data processing (`Bronze` raw payload $\rightarrow$ `Silver` cleaned DuckDB $\rightarrow$ `Gold` PostgreSQL analytical data mart) managed with dbt-core.
3. **RAG Regulation Copilot**: Hybrid Search (BM25 + Qdrant Dense Embeddings) with Cross-Encoder re-ranking, strictly grounded in official rulebooks to eliminate hallucinations.
4. **Teammate & Advisor Matchmaking**: Vector similarity and heuristic constraints to recommend cross-functional peers (e.g. frontend + data/AI) and match projects with faculty research domains.
5. **Faculty BI & Student Portal**: Next.js 15 web application and high-performance FastAPI backend.

---

## 2. Directory Navigation Map

```text
acdp-platform/
├── AGENTS.md               <-- Master operating contract for all AI agents
├── GEMINI.md / CLAUDE.md   <-- Tool-specific configuration loaders
├── .cursorrules            <-- Cursor IDE & Windsurf directives
├── .agents/skills/         <-- On-demand skills (Research, Writing, Slides, Benchmark, Experiments)
└── docs/
    ├── README.md           <-- Central documentation index
    ├── HOW_TO_USE.md       <-- THIS FILE: Direction & prompt cookbook
    ├── academic/           <-- Thesis proposals, BibTeX library, literature review
    ├── research/           <-- Competitor analysis (Devpost, Unstop, etc.)
    ├── experiments/        <-- Empirical benchmarks (Ragas scorecards, query latency)
    ├── deliverables/       <-- Research outputs & spikes mapped to NOTION tasks
    ├── adr/                <-- Architecture Decision Records
    ├── specs/              <-- Technical specifications & Pydantic data contracts
    ├── tasks/              <-- Notion task mapping, roadmap, and active sprint
    └── rfc/                <-- Change management protocol (RFC process)
```

---

## 3. Notion Task Synchronization

The research and development team (Do Kien Hung & Nguyen Van Quang Duy) coordinates development milestones via **Notion**. 
- To see the master task list and corresponding repository artifacts, consult [`docs/tasks/notion-task-mapping.md`](./tasks/notion-task-mapping.md).
- To log research outputs, technical spikes, or evaluation reports corresponding to a Notion task, write them under [`docs/deliverables/`](./deliverables/) using [`docs/deliverables/0000-deliverable-template.md`](./deliverables/0000-deliverable-template.md).

---

## 4. AI Agent Prompt Cookbook (Copy & Paste)

When opening this workspace with any AI agent, use the prompts below to trigger the specialized skills and achieve production-grade results:

### Mode 1: Academic Literature & SOTA Research
```text
@AGENTS.md Kích hoạt skill academic-researcher:
Hãy tìm kiếm và tổng hợp các bài báo khoa học gần đây nhất (từ 2023 - 2026) về chủ đề "LLM Information Extraction from Unstructured Web Data" và "Hybrid Search in Administrative RAG". 
Trích xuất: Phương pháp cốt lõi, tập dữ liệu kiểm thử, hạn chế còn tồn đọng và điểm khác biệt của đề tài ACDP. 
Sau đó tạo mục trích dẫn BibTeX chuẩn và cập nhật vào docs/academic/references.bib.
```

### Mode 2: Competitor & Strategic Analysis
```text
@AGENTS.md Kích hoạt skill competitor-benchmark:
Hãy tiến hành phân tích và so sánh đối thủ giữa ACDP với nền tảng Devpost và Unstop.
Lập ma trận so sánh 5 chiều: Cơ chế thu thập dữ liệu, Khả năng tra cứu thể lệ, Thuật toán ghép đội, Kênh kết nối giảng viên, và Bảng điều khiển phân tích cho trường đại học. 
Lưu kết quả phân tích vào docs/research/competitor-benchmarks.md.
```

### Mode 3: Drafting Thesis Chapters (FIT-HCMUTE Standard)
```text
@AGENTS.md Kích hoạt skill thesis-writer:
Dựa trên ADR-0001 và tài liệu trong docs/academic/, hãy viết bản thảo Chương 3: "Thiết kế kiến trúc và Hệ thống" (Mục 3.1 và 3.2) bằng văn phong học thuật tiếng Việt trang trọng chuẩn Khoa CNTT - ĐH Công nghệ Kỹ thuật TP.HCM (FIT-HCMUTE). 
Bao gồm sơ đồ luồng dữ liệu 4 tầng, định nghĩa schema Pydantic cho Ingestion Layer, và các trích dẫn \cite{} tương ứng.
```

### Mode 4: Slide Decks & Presentation Pitching
```text
@AGENTS.md Kích hoạt skill defense-pitch-builder:
Hãy tạo một slide deck hoàn chỉnh bằng HTML/CSS tự đóng gói (self-contained) chuẩn phong cách học thuật để nhóm báo cáo đề cương trước GVHD ThS. Trần Quang Khải.
Bố cục 10 slide: Đặt vấn đề, 4 nút thắt thực tế, kiến trúc Medallion Lakehouse, Hybrid RAG, phân định phạm vi TLCN 15 tuần vs KLTN, và demo kế hoạch triển khai.
```

### Mode 5: Adversarial Committee Defense Q&A
```text
@AGENTS.md Kích hoạt skill defense-pitch-builder:
Đóng vai Giảng viên phản biện (GVPB) khó tính tại Hội đồng bảo vệ Tiểu luận chuyên ngành Khoa CNTT HCMUTE.
Hãy đặt ra 5 câu hỏi phản biện hóc búa nhất nhằm chất vấn nhóm về:
1. Tính chất chuyên ngành Kỹ thuật Dữ liệu trong đề tài.
2. Phương pháp kiểm soát ảo giác (hallucination) trong RAG thể lệ.
3. Độ bền bỉ của crawler khi website nguồn chặn IP hoặc đổi DOM.
Sau đó, hãy soạn câu trả lời mẫu có tính thuyết phục cao dựa trên các ADR và Spec hiện có.
```

### Mode 6: Experiment Design & Evaluation
```text
@AGENTS.md Kích hoạt skill experiment-evaluator:
Hãy thiết kế khung thực nghiệm đo lường chất lượng của RAG engine theo tiêu chuẩn Ragas (Faithfulness, Answer Relevance, Context Precision). 
Định nghĩa bộ câu hỏi kiểm thử giả lập (synthetic test dataset) gồm 20 câu hỏi thể lệ thi và tạo scorecard ghi nhận kết quả vào docs/experiments/.
```

### Mode 7: Logging Deliverables from Notion Tasks
```text
@AGENTS.md Chúng tôi vừa hoàn thành task trên Notion: "NT-012: Nghiên cứu công nghệ Crawl4AI và thiết kế schema Pydantic cho fanpage Facebook". 
Hãy giúp nhóm tổng hợp bản báo cáo kết quả nghiên cứu (deliverable) theo mẫu docs/deliverables/0000-deliverable-template.md và lưu vào docs/deliverables/NT-012-crawl4ai-schema-spike.md, đồng thời cập nhật docs/tasks/notion-task-mapping.md.
```
