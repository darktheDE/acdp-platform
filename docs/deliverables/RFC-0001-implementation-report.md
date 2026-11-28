# DELIVERABLE: Báo cáo Triển khai RFC-0001 (Đồng bộ Spec `v2`, Cloud Parity & Khắc phục Lệch Phiên bản)

- Task ID: `TASK-QA-01` (Follow-up Implementation: `RFC-0001`)
- Related Sprint: Cycle 07–08 Realignment
- Primary Owner: Đỗ Kiến Hưng (`@darktheDE`) & Nguyễn Văn Quang Duy (`@QuangDuyReal`)
- Date Completed: 2026-11-26
- Deliverable Type: RFC Implementation & Verification Report
- Status: Implemented & Verified

---

## 1. Executive Summary & Objective

Báo cáo này tổng kết quá trình triển khai toàn bộ 6 hạng mục (`R1`–`R6`) trong [`RFC-0001`](../rfc/RFC-0001-spec-v2-and-cloud-parity-realignment.md), nhằm đóng dứt điểm các độ lệch giữa tài liệu đặc tả (`ADR-0002`, `SPEC.md`, `SPEC-0001`–`0006`) với mã nguồn vận hành thực tế (`src/acdp/v2/`, `src/acdp/api/`, `docker-compose.yml`, `keep-alive.yml`) và loại bỏ hoàn toàn cảnh báo `DeprecationWarning` cùng lỗi biến môi trường trong kiểm thử.

---

## 2. Chi tiết Các Thay đổi Đã Triển khai (`R1` $\rightarrow$ `R6`)

| Mã mục | Phạm vi tệp đã cập nhật | Nội dung thay đổi thực tế | Trạng thái |
| :---: | :--- | :--- | :---: |
| **R1** | [`SPEC-0001`](../specs/0001-system-foundation-spec.md), [`SPEC-0002`](../specs/0002-data-ingestion-and-schema-spec.md) | Chuyển toàn bộ mô tả từ pipeline v1 (`1_crawl_to_bronze.py` Markdown, `data/raw/` local, `2_instruction.py`) sang pipeline v2 R2-Exclusive (`v2/discovery.py`, `v2/bronze_crawl.py` Raw Rendered HTML `.html`, `v2/silver_transform.py`, `v2/schemas.py` `G1–G7`). | Hoàn tất |
| **R2** | [`SPEC-0003`](../specs/0003-gold-dimensional-modeling-spec.md) §3.5, [`SPEC-0004`](../specs/0004-serving-api-and-oltp-spec.md) §3.1/§3.3, [`SPEC.md`](../specs/SPEC.md) | Loại bỏ mô tả atomic swap tệp `acdp.duckdb` local và model cũ `qwen3-embedding:4b` / `acdp_competitions` / `3_ingest_to_qdrant.py`; cập nhật đúng DuckDB `1.5.6` `httpfs` trực tiếp trên R2 `gold/*.parquet` + `GoldMartsTTLCache`, `@cf/baai/bge-m3` (`1,024` dims), `acdp_competitions_bge_m3` và `v2/rag_ingest.py`. | Hoàn tất |
| **R3** | [`SPEC-0006`](../specs/0006-docker-infrastructure-and-resource-spec.md) §2.3/§2.4/§3.1, [`SPEC-0004`](../specs/0004-serving-api-and-oltp-spec.md) §2.2 | Đồng bộ bảng dịch vụ trong `SPEC-0006` với `docker-compose.yml` (`qdrant` ở `local-backup`, xóa mount `./data/lakehouse:ro` và `depends_on: qdrant`); cập nhật `alpine3.21` thành `alpine3.23` ở `SPEC-0004`. | Hoàn tất |
| **R4** | [`ADR-0002`](../adr/0002-full-cloud-free-tier-architecture.md) §6 | Sửa mô tả chu kỳ Keep-Alive từ *"mỗi 3 ngày"* thành *"hằng ngày (`02:15 UTC`, `15 2 * * *`)"* kèm `pg_dump` Chủ nhật (`30 2 * * 0`), khớp với `.github/workflows/keep-alive.yml`. | Hoàn tất |
| **R5** | [`docker-compose.yml`](../../docker-compose.yml), [`test_infra_spec0006.py`](../../tests/test_infra_spec0006.py), [`SPEC-0004`](../specs/0004-serving-api-and-oltp-spec.md) | Nâng tag `qdrant/qdrant` từ `v1.13.4` lên `v1.20.2` (khớp minor `qdrant-client==1.20.0`); thêm quy tắc DDL tương thích `PG 17+` giữa Supabase Free (`PG 17`) và Docker (`PG 18.7`); bổ sung `monkeypatch.delenv` cho `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `POSTGRES_HOST`, `POSTGRES_PORT` trong `test_infra_spec0006.py`. | Hoàn tất |
| **R6** | [`rag_ingest.py`](../../src/acdp/v2/rag_ingest.py), [`test_rag_eval.py`](../../tests/test_rag_eval.py) | Thay thế `langchain_experimental.text_splitter.SemanticChunker` bằng lớp `PercentileSemanticChunker` thuần Python (tách câu + khoảng cách cosine phân vị `90%`), xóa hoàn toàn `DeprecationWarning` của `langchain-experimental` và `langchain-community`; bổ sung unit test `test_percentile_semantic_chunker_splits_on_topic_shift_without_deprecation`. | Hoàn tất |

---

## 3. Benchmarks & Kiểm chứng Sau Triển khai

| Hạng mục kiểm chứng | Kết quả trước `RFC-0001` | Kết quả sau `RFC-0001` | Lệnh thực thi |
| :--- | :---: | :---: | :--- |
| **`tests/test_infra_spec0006.py`** | `1` fail (do OS env `POSTGRES_USER`) | **`5 / 5` passed (`0` warnings)** | `uv run pytest tests/test_infra_spec0006.py -v` |
| **`tests/test_rag_eval.py`** | `5` passed (`2` deprecation warnings) | **`6 / 6` passed (`0` warnings)** | `uv run pytest tests/test_rag_eval.py -v` |
| **Toàn bộ Offline Unit Tests (`tests --ignore=tests/api`)** | `1` fail + `2` warnings | **`61 / 61` passed (`5.15s`, `0` warnings)** | `uv run pytest tests --ignore=tests/api -v` |
| **`ruff check` mã nguồn & test** | Pass | **Pass (`All checks passed!`)** | `uv run ruff check src/acdp/v2/rag_ingest.py tests/` |
| **`audit_doc_drift.py --strict`** | `0` violations | **`0` violations (`CLEAN`, `116` files)** | `uv run python .agents/skills/doc-decision-sync/scripts/audit_doc_drift.py --strict` |

---

## 4. Hướng dẫn Kiểm tra Thủ công & Lệnh Chạy Xác nhận (`DIR-024`)

Chạy tuần tự hai nhóm lệnh sau trên PowerShell để kiểm chứng toàn bộ mã nguồn offline, bộ test và tính đồng bộ tài liệu sau `RFC-0001` (lưu ý `tests/api/` cần PostgreSQL/Supabase và R2 đang chạy):

```powershell
uv run pytest tests --ignore=tests/api -v
```

Output thực tế ghi nhận:

```text
61 passed in 5.15s
```

```powershell
uv run ruff check src/acdp/v2/rag_ingest.py tests/test_infra_spec0006.py tests/test_rag_eval.py tests/test_qa01_tech_decision_audit.py
uv run python .agents/skills/doc-decision-sync/scripts/audit_doc_drift.py --strict
uv run python .agents/skills/anti-slop-scientific-writer/scripts/detect_ai_slop.py docs/deliverables/RFC-0001-implementation-report.md --strict
```

Output thực tế ghi nhận:

```text
All checks passed!
Summary: 0 violation(s) found. Status: CLEAN
Slop Index: PRISTINE SCIENTIFIC PROSE (0/100)
```

---

## 5. Search Provenance & Verifiable References (`DIR-020`)

| STT | Câu lệnh truy vấn (`search_web`) | Mục đích kiểm chứng | Nguồn chính thức đã xác minh |
| :---: | :--- | :--- | :--- |
| 1 | `site:hub.docker.com/r/qdrant/qdrant OR site:github.com/qdrant/qdrant/releases "v1.17" OR "v1.18" OR "v1.19" OR "v1.20"` | Xác nhận tag phát hành `qdrant/qdrant:v1.20.2` trên Docker Hub và quy tắc tương thích minor 1-bước với `qdrant-client==1.20.0` | https://github.com/qdrant/qdrant/releases<br>https://qdrant.tech/documentation/guides/installation/ |
