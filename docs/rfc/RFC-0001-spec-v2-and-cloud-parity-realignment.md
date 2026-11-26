# RFC-0001: Đồng bộ Đặc tả Kiến trúc `v2`, Cloud Parity và Khắc phục Lệch Phiên bản (Spec-vs-Code Realignment)

- Status: Implemented (2026-11-26 — Đã triển khai đồng bộ tài liệu & mã nguồn)
- Author(s): Đỗ Kiến Hưng (`@darktheDE`), Nguyễn Văn Quang Duy (`@QuangDuyReal`)
- Created Date: 2026-11-26
- Target Component: Ingestion, Lakehouse, RAG Engine, Backend, Infrastructure
- Source Audit: [`TASK-QA-01`](../deliverables/TASK-QA-01-tech-decision-theory-practice-audit.md)

---

## 1. Motivation & Context

Kết quả kiểm toán chéo sau triển khai tại `TASK-QA-01` cho thấy mã nguồn thực tế trong `src/acdp/v2/`, `src/acdp/api/`, `docker-compose.yml` và `.github/workflows/keep-alive.yml` đã tiến hóa sang kiến trúc R2-Exclusive và Full Cloud Free-Tier (`DIR-021`, `DIR-022`, `ADR-0002`), nhưng 6 tài liệu đặc tả và quyết định gốc vẫn giữ nội dung của giai đoạn v1 hoặc Hybrid Local cũ:

| Mã lệch | Tài liệu bị lệch | Nội dung cũ trong tài liệu | Hiện trạng thực tế trong mã nguồn |
| :--- | :--- | :--- | :--- |
| **R1** | `SPEC-0001` §2, `SPEC-0002` §2–§5 | Mô tả `1_crawl_to_bronze.py` lưu Raw Markdown song song `data/raw/` và `2_instruction.py` + `schemas.py` v1. | `src/acdp/v2/bronze_crawl.py` lưu Raw Rendered HTML lên Cloudflare R2 (`DIR-021`); `v2/silver_transform.py` thực thi Hybrid Deterministic Sandwich + `v2/schemas.py` (`G1–G7`). |
| **R2** | `SPEC-0003` §3.5, `SPEC-0004` §3.1/§3.3, `SPEC.md` §3.3 | Mô tả hoán đổi file `data/lakehouse/acdp.duckdb` cục bộ; RAG dùng `qwen3-embedding:4b`, collection `acdp_competitions`, và `3_ingest_to_qdrant.py`. | `v2/gold_star_schema.py` xuất thẳng 15 Parquet lên R2 `s3://`; `gold_queries.py` dùng DuckDB `httpfs` + `GoldMartsTTLCache`; RAG dùng `@cf/baai/bge-m3`, `acdp_competitions_bge_m3` và `v2/rag_ingest.py`. |
| **R3** | `SPEC-0006` §2.4, `SPEC-0004` §2.2 | Blueprint YAML đặt `qdrant` vào profile `core` và mount `./data/lakehouse:ro`; `SPEC-0004` ghi `postgres:18.7-alpine3.21`. | `docker-compose.yml` chuyển `qdrant` sang `local-backup`, gỡ volume `./data/lakehouse`, và dùng `postgres:18.7-alpine3.23`. |
| **R4** | `ADR-0002` §6 | Ghi workflow Keep-Alive chạy *"mỗi 3 ngày"*. | `.github/workflows/keep-alive.yml` chạy hằng ngày (`15 2 * * *`) để tránh ngưỡng ngủ 48 giờ của Hugging Face Spaces, kèm `pg_dump` Chủ nhật (`30 2 * * 0`). |
| **R5** | `docker-compose.yml` vs `pyproject.toml`, `Supabase` | Docker Qdrant backup chốt `v1.13.4` trong khi `pyproject.toml` dùng `qdrant-client>=1.20.0`; local dùng PG `18.7` trong khi Supabase Free mặc định PG `17` (hỗ trợ `15–17`). | Nguy cơ lệch API Qdrant khi failover sang `--profile local-backup` và nguy cơ dùng cú pháp SQL chỉ có ở PG 18 làm lỗi migration trên Supabase Cloud. |
| **R6** | `src/acdp/v2/rag_ingest.py` | Dùng `langchain_experimental.text_splitter.SemanticChunker`. | Chạy `pytest` ghi nhận `DeprecationWarning`: `langchain-experimental` và `langchain-community` đã ngừng bảo trì chủ động (`sunset`). |

---

## 2. Proposed Change

1. **Cập nhật đồng bộ bộ đặc tả TLCN (`SPEC-0001..0006`, `SPEC.md`, `ADR-0002` §6)**:
   - Chỉnh đường dẫn module và mô hình dữ liệu trong `SPEC-0001` và `SPEC-0002` sang nhánh `src/acdp/v2/` và chế độ Cloudflare R2-only (`DIR-021`).
   - Thay thế mục Atomic Swap `acdp.duckdb` trong `SPEC-0003` §3.5 bằng quy trình xuất 15 tệp Parquet nguyên tử lên R2 + đồng bộ MotherDuck views (`gold_star_schema.py`).
   - Cập nhật `SPEC-0004` §3.1/§3.3 và `SPEC.md` §3.3 theo đúng kiến trúc `httpfs` + `GoldMartsTTLCache` + `@cf/baai/bge-m3` (`acdp_competitions_bge_m3`) + `src/acdp/v2/rag_ingest.py`.
   - Đồng bộ `SPEC-0006` §2.4 blueprint với `docker-compose.yml` thực tế.
   - Sửa câu mô tả chu kỳ trong `ADR-0002` §6 từ *"mỗi 3 ngày"* thành *"hằng ngày (02:15 UTC)"* để khớp với `keep-alive.yml`.
2. **Khóa tương thích phiên bản liên tầng (Cross-Version Parity Guardrails)**:
   - Bổ sung quy tắc SQL chuẩn tương thích PostgreSQL `17+` cho toàn bộ DDL/migration OLTP (không sử dụng cú pháp độc quyền PG 18 trên Supabase Free), đồng bộ `SPEC-0004` từ `alpine3.21` sang `alpine3.23`.
   - Nâng cấp tag ảnh `qdrant/qdrant` trong `docker-compose.yml` và `SPEC-0006` từ `v1.13.4` lên phiên bản tương thích trực tiếp với `qdrant-client>=1.20.0`, kiểm chứng lại bằng test failover.
   - Gỡ bỏ `SemanticChunker` của `langchain-experimental` khỏi `src/acdp/v2/rag_ingest.py`, thay bằng bộ tách đoạn ngữ nghĩa thuần Python + `httpx` / Markdown Header + Embedding Cosine Split để triệt tiêu phụ thuộc gói đã ngừng bảo trì.
3. **Bổ sung test `monkeypatch` môi trường trong `tests/test_infra_spec0006.py`**:
   - Đảm bảo `test_supabase_oltp_pooler_and_duckdb_r2_config` xóa thêm `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` khỏi biến môi trường OS trước khi kiểm tra giá trị mặc định của `AppConfig`.

---

## 3. Impact Analysis

| Khía cạnh | Mức độ tác động | Chi tiết cụ thể |
| :--- | :---: | :--- |
| **Breaking Changes** | Không | Không phá vỡ OpenAPI 3.1 contract hay schema Parquet đang chạy trên R2. |
| **Database & Lakehouse Schema** | Thấp | Chỉ đặt ràng buộc tương thích SQL `PG 17+` cho migration sắp tới (`TASK-SRV-01`, `TASK-SRV-02`). |
| **API Surface Changes** | Không | Toàn bộ 7 router FastAPI và DTO tại `src/acdp/api/schemas/` giữ nguyên chữ ký. |
| **Dependencies** | Giảm | Loại bỏ dần `langchain-experimental` và `langchain-community` khỏi nhóm `rag-ui`. |
| **Affected Docs & Files** | Trung bình | `SPEC-0001..0006`, `SPEC.md`, `ADR-0002` §6, `docker-compose.yml`, `src/acdp/v2/rag_ingest.py`, `tests/test_infra_spec0006.py`. |

---

## 4. Alternatives Considered

1. **Giữ nguyên các SPEC cũ với lý do "tài liệu phản ánh giai đoạn lịch sử"**: Bị loại bỏ vì gây mâu thuẫn trực tiếp khi Hội đồng hoặc lập trình viên mới đối chiếu đặc tả với mã nguồn, đồng thời vi phạm nguyên tắc không trôi dạt tài liệu (`DIR-017`).
2. **Nâng cấp Docker local PG xuống PG 17 thay vì dùng PG 18.7**: Không cần thiết nếu nhóm áp dụng quy tắc viết DDL tương thích chung cho PG `17+`, vì PG 18 trên Docker giúp kiểm thử sớm hướng nâng cấp dài hạn trong khi vẫn giữ tương thích ngược với Supabase PG 17.

---

## 5. Migration & Rollback Strategy

1. Áp dụng từng thay đổi tài liệu theo cụm và kiểm định bằng `audit_doc_drift.py --strict` sau mỗi bước cập nhật.
2. Khi nâng tag `qdrant/qdrant` trong `docker-compose.yml`, giữ lại bản sao snapshot collection trước khi chuyển đổi; có thể hoàn tác ngay bằng cách trả về tag cũ trong `docker-compose.yml`.
3. Khi thay thế `SemanticChunker` trong `v2/rag_ingest.py`, chạy lại `tests/test_rag_eval.py` và đối chiếu điểm Ragas với `NT-012` trước khi nạp lại Qdrant Cloud.

---

## 6. Action Items / Implementation Plan

- [x] Phản biện nội bộ và phê duyệt `RFC-0001` theo yêu cầu triển khai trực tiếp ngày 2026-11-26.
- [x] Cập nhật đồng bộ `SPEC-0001`, `SPEC-0002`, `SPEC-0003`, `SPEC-0004`, `SPEC-0006`, `SPEC.md` và `ADR-0002` §6.
- [x] Nâng tag `qdrant/qdrant` lên `v1.20.2` tương thích `qdrant-client>=1.20.0` và bổ sung `monkeypatch.delenv` trong `tests/test_infra_spec0006.py`.
- [x] Thay thế `langchain-experimental` `SemanticChunker` trong `src/acdp/v2/rag_ingest.py` bằng `PercentileSemanticChunker` thuần Python.
- [x] Chạy `uv run python .agents/skills/doc-decision-sync/scripts/audit_doc_drift.py --strict` và lập báo cáo tại [`RFC-0001-implementation-report.md`](../deliverables/RFC-0001-implementation-report.md).
