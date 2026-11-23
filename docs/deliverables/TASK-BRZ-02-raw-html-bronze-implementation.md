# Deliverable: Triển khai Lưu trữ Raw Rendered HTML ở Lớp Đồng (`src/acdp/v2/bronze_crawl.py`)

- **Task ID**: `TASK-BRZ-02`
- **Related Cycle**: Cycle 06 (TLCN Phase 1)
- **Primary Owner**: Do Kien Hung (`@darktheDE`) & Nguyen Van Quang Duy (`@QuangDuyReal`)
- **Institution**: Khoa Công nghệ Thông tin, Trường Đại học Công nghệ Kỹ thuật TP.HCM (HCM-UTE)
- **Date Completed**: 2026-11-23
- **Deliverable Type**: Bronze Layer Engineering Implementation & Live R2 Benchmark
- **Status**: Complete

---

## 1. Tóm tắt điều hành

Hiện thực hóa quyết định kiến trúc từ [`TASK-BRZ-01`](./TASK-BRZ-01-bronze-raw-vs-markdown-justification.md) và quy chuẩn tách nhánh `v2` theo `DIR-022`, hệ thống đã triển khai [`src/acdp/v2/bronze_crawl.py`](../../src/acdp/v2/bronze_crawl.py) (giữ nguyên mã nguồn cũ [`src/acdp/1_crawl_to_bronze.py`](../../src/acdp/1_crawl_to_bronze.py)) để thu thập và lưu trữ **Raw Rendered HTML (`result.html`)** nguyên bản lên Cloudflare R2 `bronze/`.

Các thay đổi chính:
1. Lưu tệp `.html` (`text/html; charset=utf-8`) thay vì `raw_markdown`, bảo toàn 100% `<head>`, `JSON-LD`, `<meta property="og:*">` và payload trạng thái SPA.
2. Đóng gói nhiều trang con từ `AdaptiveCrawler.knowledge_base` bằng thẻ phân cách `<!-- ACDP_PAGE_BOUNDARY url="..." -->`.
3. Chuẩn hóa tên các module `src/acdp/v2/` theo chuẩn Python (`discovery.py`, `bronze_crawl.py`, `silver_transform.py`, `rag_ingest.py`, `gold_star_schema.py`).

---

## 2. Thiết kế kỹ thuật & Cơ chế chịu lỗi

- **`package_bronze_html(knowledge_base, fallback_url="")`**: Lọc bỏ trang `success=False` hoặc `html` rỗng, escape dấu ngoặc kép trong URL và chèn `<!-- ACDP_PAGE_BOUNDARY url="..." -->` trước mỗi bản chụp HTML.
- **`upload_to_bronze(html_content, dm_name, page_count)`**: Chặn upload 0-byte khi crawl thất bại; đẩy trực tiếp lên Cloudflare R2 theo key `bronze/{domain}/year={YYYY}/month={MM}/day={DD}/{ts}.html` kèm `Metadata` (`source`, `layer=bronze`, `format=raw_html`, `page_count`).
- **`_single_page_fallback()`**: Chỉ kích hoạt khi `AdaptiveCrawler.digest()` gặp lỗi hoặc trả về 0 trang hợp lệ, thực hiện fetch 1 trang bằng Playwright để không mất dữ liệu trang chính.
- **Đầu vào CLI linh hoạt**: Hỗ trợ `--url`, `--from-discovery` (đọc `canonical_url` từ `bronze/_discovery/latest_manifest.json` trên R2), `--all-sources` (gộp `DEFAULT_URLS` + Discovery khử trùng lặp), và `--max-urls`.

---

## 3. Kết quả kiểm thử & Benchmark thực tế trên Cloudflare R2

### 3.1. Kiểm thử tự động
- `uv run pytest tests/test_bronze_storage.py tests/test_discovery_v2.py -v`: **15/15 passed**.
- `uv run ruff check`: **0 errors**.
- `uv run python .agents/skills/doc-decision-sync/scripts/audit_doc_drift.py --strict`: **0 violation(s) found (`CLEAN`)**.

### 3.2. Benchmark Full Batch lên Cloudflare R2 (`--all-sources`)
*(Báo cáo JSON lưu trực tiếp trên R2 tại `s3://acdp-lakehouse/bronze/_benchmarks/crawl_bronze_1795418426.json`)*

| Chỉ số | Giá trị thực đo |
| :--- | :--- |
| **Tổng số URL đầu vào** | `36` (`DEFAULT_URLS` + Discovery manifest, đã khử trùng lặp) |
| **Thành công lên R2** | **`33 / 36` (`91.7%`)** — Adaptive: `31` \| Fallback 1 trang: `2` |
| **Bỏ qua (0-byte guard)** | `3` (`skipped_empty`: `vjaihackathon.com`, `mlai-hackathon.devpost.com`, `mlai-hackathon.devpost.com/updates/...`) |
| **Tổng số trang con (`ACDP_PAGE_BOUNDARY`)** | `93` trang |
| **Tổng dung lượng Raw HTML trên R2** | **`17,054,203 B` (`16.264 MB`)** (TB `516,794 B` / URL) |
| **Tổng thời gian batch** | **`1,513.93s`** (~`25 phút 14 giây`, TB **`42.05s / URL`**) |

**Sự cố & Fallback ghi nhận thực tế**:
- `skh.quangngai.gov.vn/...`: `AdaptiveCrawler` gặp lỗi Cloudflare Workers AI embedding vượt ngữ cảnh (`AiError: Max context reached 201792 tokens > 60000`, mã `8007`), `_single_page_fallback` đã lấy thành công `1` trang (`34.02s`).
- `qvic.vn/`: Kích hoạt `_single_page_fallback` thành công (`1` trang, `54.67s`).
- `gemini/gemini-3.5-flash`: Chạm hạn mức `20 RPD` (`429 RESOURCE_EXHAUSTED`) ở nửa sau batch; `_resilient_map_query_semantic_space` tự fallback về query gốc nên batch hoàn tất bình thường.

---

## 4. Định hướng tối ưu & Bước tiếp theo

1. **Tối ưu tốc độ cào cho đợt sau**: Chuyển `wait_until="domcontentloaded"` + `delay_before_return_html=2.0`, cache query expansion 1 lần/batch và chạy song song với `asyncio.Semaphore(3)`.
2. **Triển khai Lớp Bạc (`TASK-SLV-03`)**: Xây dựng `src/acdp/v2/silver_transform.py` đọc 33 tệp `.html` từ `bronze/`, xuất Clean Markdown lên `silver/markdown/` và áp dụng bộ lọc scope + truy tìm trang chính thức theo `DIR-022`.

---

## 5. Tài liệu & Mã nguồn liên quan

- Mã nguồn Bronze `v2`: [`src/acdp/v2/bronze_crawl.py`](../../src/acdp/v2/bronze_crawl.py)
- Kiểm thử đơn vị: [`tests/test_bronze_storage.py`](../../tests/test_bronze_storage.py)
- Luận chứng kiến trúc Bronze: [`TASK-BRZ-01-bronze-raw-vs-markdown-justification.md`](./TASK-BRZ-01-bronze-raw-vs-markdown-justification.md)
- Sổ cái quản lý task: [`docs/tasks/task-registry.md`](../tasks/task-registry.md)
