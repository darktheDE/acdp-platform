# Deliverable: Triển khai Hybrid Deterministic Sandwich & Clean Markdown ở Lớp Bạc (`v2/silver_transform.py` & `v2/rag_ingest.py`)

- **Task ID**: `TASK-SLV-03`
- **Related Cycle**: Cycle 06 (TLCN Phase 1)
- **Primary Owner**: Do Kien Hung (`@darktheDE`) & Nguyen Van Quang Duy (`@QuangDuyReal`)
- **Institution**: Khoa Công nghệ Thông tin, Trường Đại học Công nghệ Kỹ thuật TP.HCM (HCM-UTE)
- **Date Completed**: 2026-11-23
- **Deliverable Type**: Silver Layer Engineering Implementation, RAG Migration & Live R2/Qdrant Benchmark
- **Status**: Complete

---

## 1. Tóm tắt điều hành

Hiện thực hóa quyết định kiến trúc từ [`TASK-BRZ-01`](./TASK-BRZ-01-bronze-raw-vs-markdown-justification.md), [`TASK-SLV-01`](./TASK-SLV-01-hybrid-de-vs-llm-extraction-study.md) và chỉ thị `DIR-022` trên nhánh mã nguồn `src/acdp/v2/` (giữ nguyên mã nguồn cũ):

1. **[`src/acdp/v2/silver_transform.py`](../../src/acdp/v2/silver_transform.py)**: Đọc Raw Rendered HTML (`*.html` kèm thẻ `ACDP_PAGE_BOUNDARY`) và tương thích ngược với tệp `.md` lịch sử trên Cloudflare R2 `bronze/`. Chạy `DefaultMarkdownGenerator()` của `Crawl4AI` trực tiếp trong RAM (`0 ms` mở lại trình duyệt) để xuất Clean Markdown lên `silver/markdown/`, kết hợp mô hình **Hybrid Deterministic Sandwich** (`JSON-LD`, `og:*`, `canonical`, link trang chính thức, thể lệ `.pdf`/`.docx`, Regex + lọc scope `DIR-022`) trước khi gọi Bounded LLM (`Instructor`).
2. **[`src/acdp/v2/rag_ingest.py`](../../src/acdp/v2/rag_ingest.py)**: Chấm dứt hoàn toàn việc đọc tắt từ `bronze/`. Đọc Clean Markdown thuần túy từ `silver/markdown/`, làm giàu metadata (`canonical_url`, `competition_name`, `category`, `mode`, `registration_status`) từ `silver/extractions/` và nạp vector `@cf/baai/bge-m3` (`1024` chiều) vào Qdrant Cloud.

---

## 2. Kiến trúc & Cơ chế kỹ thuật đã triển khai

### 2.1. Gom nhóm theo `(domain, source_url)` & Tương thích ngược
- Kiểm tra thực tế trên R2 ngày `2026-11-23` phát hiện cùng domain tổng hợp `ybox.vn` có `2` cuộc thi khác nhau trong cùng một ngày (`1795418230.html` và `1795418261.html`), còn `codetour.org` có `2` bản cào trùng URL.
- `silver_transform.py` phân tích URL gốc từ thẻ `ACDP_PAGE_BOUNDARY` đầu tiên và gom nhóm theo `(domain, source_url)`, giữ bản có `timestamp` cao nhất cho mỗi URL duy nhất (ưu tiên `.html` hơn `.md` lịch sử).

### 2.2. Luồng 4 bước Hybrid Deterministic Sandwich
1. **Deterministic Extract (`0` token LLM)**:
   - Tách đa trang qua `ACDP_PAGE_BOUNDARY`, chuyển HTML sang Clean Markdown trong RAM bằng `DefaultMarkdownGenerator(options={"ignore_images": True, "body_width": 0})` (`citations=False`), loại bỏ ảnh, SVG/base64, link neo điều hướng và dòng trùng lặp.
   - Bóc tách `JSON-LD` (`@graph`, `Event`, `organizer`, `startDate`), `og:*`, `<link rel="canonical">`, `<h1>`, link thể lệ `.pdf`/`.docx`, link trang chính thức từ bài truyền thông/tổng hợp, và Regex ngày/năm/giải thưởng/quy mô đội/hình thức/lệ phí.
2. **Pre-LLM Scope Gate & Media-Partner Deduplication (`DIR-022`)**:
   - Loại bỏ trang rỗng/404 (`< 200` ký tự), cuộc thi ngoài lĩnh vực CNTT/AI/Dữ liệu/Bảo mật/Lập trình, cuộc thi chỉ dành cho học sinh phổ thông, cuộc thi ngoài khung `2025–2027`, cuộc thi không có trang web chính thức (`no_official_website`), và khử trùng lặp bài truyền thông về trang chính thức đã có trong batch (`media_partner_merged_to_official`).
3. **Bounded Semantic Transform (`Instructor`)**:
   - Chỉ gọi LLM cho các bản ghi vượt qua tầng lọc; tiêm khối `Ngữ cảnh tất định đã trích xuất` vào prompt để LLM tập trung vào trường ngữ nghĩa (`summary`, `challenge_overview`, `category`, `prizes`, `timeline_stages`).
4. **Post-LLM Validation & R2 Load**:
   - Ép `comp.url` về `canonical_official_url`, tái kiểm tra scope sau LLM, khử trùng lặp theo URL chuẩn hóa và đẩy đồng bộ lên R2: `silver/markdown/`, `silver/extractions/`, `silver/batches/`, `silver/_reports/`.

---

## 3. Kết quả kiểm thử & Benchmark thực tế trên Cloudflare R2 / Qdrant Cloud

### 3.1. Kiểm thử tự động & Kiểm định tài liệu
- `uv run pytest tests/test_silver_transform_v2.py tests/test_bronze_storage.py tests/test_discovery_v2.py tests/test_silver_schema.py -v`: **`29 passed, 1 xfailed`** (`1 xfailed` là test ghi nhận khoảng trống Schema v2 chờ `TASK-SLV-04`).
- `uv run ruff check src/acdp/v2/ tests/test_silver_transform_v2.py`: **`0` lỗi**.
- `uv run python .agents/skills/doc-decision-sync/scripts/audit_doc_drift.py --strict`: **`0` vi phạm (`CLEAN`)**.

### 3.2. Benchmark thực thi thực tế (`--date 2026-11-23`)

| Giai đoạn Pipeline | Đầu vào | Đầu ra / Kết quả thực đo | Chi tiết phân loại |
| :--- | :---: | :---: | :--- |
| **Silver Transform** (`--extract`) | `33` tệp HTML trên `bronze/` | **`26` cuộc thi hợp lệ** (`78.8%`) | Đẩy `26` tệp `.md` lên `silver/markdown/` + `26` tệp `.json` lên `silver/extractions/` + `1` batch manifest + `1` audit report. |
| **Lọc & Khử trùng lặp** (`DIR-022`) | `33` snapshot | **`7` bản ghi bị loại** (`21.2%`) | `out_of_scope_non_tech`: `3`, `out_of_scope_non_university`: `1`, `no_official_website`: `1`, `media_partner_merged_to_official`: `1`, `post_llm_scope_or_empty`: `1`. |
| **Silver-to-Qdrant RAG Ingest** | `26` Clean Markdown từ `silver/markdown/` | **`648` chunks (`26` domain)** | Nhúng bằng `@cf/baai/bge-m3` (`1024d`) và nạp vào collection `acdp_competitions_bge_m3` trên Qdrant Cloud. |

---

## 4. Tài liệu & Mã nguồn liên quan

- Mã nguồn Silver `v2`: [`src/acdp/v2/silver_transform.py`](../../src/acdp/v2/silver_transform.py)
- Mã nguồn RAG Ingest `v2`: [`src/acdp/v2/rag_ingest.py`](../../src/acdp/v2/rag_ingest.py)
- Bộ kiểm thử đơn vị & tích hợp: [`tests/test_silver_transform_v2.py`](../../tests/test_silver_transform_v2.py)
- Báo cáo trực quan HTML: [`TASK-SLV-03-hybrid-sandwich-and-rag-silver-implementation-visual-dossier.html`](./TASK-SLV-03-hybrid-sandwich-and-rag-silver-implementation-visual-dossier.html)
- Sổ cái quản lý task: [`docs/tasks/task-registry.md`](../tasks/task-registry.md)
