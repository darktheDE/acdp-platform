# TASK-GLD-02: Hiệu chỉnh Two-Tier Gold (A1–A4) & Nạp Metadata Gold cho Dual-Layer RAG

> **Task ID**: `TASK-GLD-02` | **Cycle**: Cycle 06 | **Phạm vi**: TLCN (Phase 1)  
> **Trạng thái**: `done` | **Ngày hoàn tất**: `2026-11-23`  
> **Modules**: [`src/acdp/v2/gold_star_schema.py`](../../src/acdp/v2/gold_star_schema.py), [`src/acdp/v2/rag_ingest.py`](../../src/acdp/v2/rag_ingest.py), [`tests/test_gold_star_schema.py`](../../tests/test_gold_star_schema.py), [`SPEC-0003`](../specs/0003-gold-dimensional-modeling-spec.md)

---

## 1. Tóm tắt điều hành (Executive Summary)

`TASK-GLD-02` hiện thực hóa các kiến nghị kiến trúc từ [`TASK-GLD-01`](./TASK-GLD-01-kimball-star-schema-audit-and-alternatives.md) trên nhánh `src/acdp/v2/` và dữ liệu thực tế tại Cloudflare R2 `s3://acdp-lakehouse/`:

1. **Khắc phục lệch chuẩn Kimball (`A1`, `A2`, `A4`)**:
   - **A1**: Loại bỏ `team_size_min` và `team_size_max` khỏi `fact_competitions` (chỉ giữ trên `dim_competition` và `mart_competition_explorer`).
   - **A2**: Tinh gọn `dim_competition` về chuẩn 1NF (loại bỏ `raw_categories[]`, `organizers[]`, `partners_and_sponsors[]`, `challenge_overview`), tổng hợp mảng tổ chức/tài trợ qua `bridge_competition_organizer` + `dim_organizer` và đẩy văn bản hiển thị dài vào OBT `mart_competition_explorer`.
   - **A4**: Rút gọn materialize trên Cloudflare R2 `gold/` từ **21 tệp** xuống **15 tệp Parquet ZSTD** (`9` bảng Core + `6` Data Marts), tự động xóa 6 tệp `gold_*.parquet` thừa và giữ 4 view `gold_*` dưới dạng virtual SQL view trong `build_metabase_r2_init_sql()`.
2. **Dual-Layer RAG (`v2/rag_ingest.py`)**: Đọc Clean Markdown từ `silver/markdown/` và làm giàu Qdrant payload từ `gold/mart_competition_explorer.parquet` (`competition_key`, `domain_slugs`, `domain_groups`, `mode_canonical`, `is_free`, `total_prize_vnd`, `has_scholarship`, `registration_status`, `team_profile`) kèm payload index phục vụ pre-filtering.
3. **Kiểm chứng thực tế trên Cloudflare R2**:
   - Tổng hợp `24` cuộc thi từ `26` domain (`r2:silver/extractions@latest(2026-11-23)`), tổng quỹ giải thưởng `6,997,591,840 VNĐ` với sai số phân bổ bridge **`0.00 VND`**.
   - Dual-Layer RAG đạt tỷ lệ làm giàu Gold **`26/26` (100%)** tài liệu Clean Markdown.

---

## 2. Đối chiếu chuẩn hóa A1–A4

| Mã | Hiện trạng v1 (`4_analytics_gold.py`) | Hiệu chỉnh v2 (`v2/gold_star_schema.py`) | Kết quả kiểm chứng |
| :--- | :--- | :--- | :--- |
| **A1** | `team_size_min`, `team_size_max` trùng ở cả `dim_competition` và `fact_competitions`. | Xóa khỏi `fact_competitions` (13 cột measure); `mart_kpi_overview` tính `AVG(d.team_size_max)` từ `dim_competition`. | `PRAGMA table_info('fact_competitions')` xác nhận không còn `team_size_*`. |
| **A2** | `dim_competition` chứa `VARCHAR[]` (`raw_categories`, `organizers`, `partners_and_sponsors`) và `challenge_overview`. | Bỏ 4 cột khỏi `dim_competition`; `mart_competition_explorer` join `bridge_competition_organizer` + `dim_organizer` + `_stg_competition_text`. | `dim_competition` đạt 1NF; `mart_competition_explorer` giữ đủ cột cho `gold_queries.py`. |
| **A3** | Surrogate key tăng dần `1..N` trong bộ nhớ (SCD Type 1). | Giữ SCD Type 1 cho TLCN; OLTP liên kết qua `competition_key` (SHA-256). | Kế hoạch nâng cấp SCD Type 2 ở `TASK-GLD-03` (KLTN). |
| **A4** | Xuất 21 tệp Parquet lên R2 `gold/` (gồm 6 `gold_*.parquet` thừa). | Xuất đúng **15 tệp** (`9` Core + `6` Marts, nén ZSTD) và xóa stale `gold_*.parquet` trên R2. | R2 `gold/` còn đúng **15 tệp** (`104,865 bytes`). |

---

## 3. Kết quả chạy thực tế trên Cloudflare R2 & Benchmark

### 3.1. Chỉ số tổng quan trên R2 (`2026-11-23`)

| Chỉ số | Giá trị đo trên R2 | Ghi chú |
| :--- | :---: | :--- |
| Tổng cuộc thi Gold (`dim_competition`) | **24** | Khử trùng từ `26` domain Silver (`2026-11-23`) |
| Cuộc thi đang mở (`open_competitions`) | **3** | Đã chuẩn hóa tự động đóng các cuộc thi quá hạn |
| Tổng quỹ giải thưởng (`total_prize_pool_vnd`) | **6,997,591,840 VNĐ** | Sai số phân bổ `bridge_competition_domain`: **`0.00 VND`** |
| Tỷ lệ miễn phí (`free_participation_pct`) | **95.8%** | `3` cuộc thi có học bổng, `76` đơn vị tổ chức/tài trợ |
| Số tệp Gold Parquet trên R2 | **15 tệp** | Tổng dung lượng `104,865 bytes` (~`102.4 KB`, nén ZSTD) |
| Tỷ lệ làm giàu Dual-Layer RAG | **26 / 26 (100%)** | Khớp `gold/mart_competition_explorer.parquet` |

### 3.2. Phân bổ giải thưởng theo 5 nhóm lĩnh vực (Weighted Bridge)

| Nhóm lĩnh vực (`dim_domain`) | Số cuộc thi | Quỹ giải thưởng phân bổ (VNĐ) |
| :--- | :---: | :---: |
| `AI & Data Science` | 22 | `2,598,389,627` |
| `Software, Web & Mobile` | 18 | `2,478,389,627` |
| `Security, IoT & Embedded` | 5 | `875,156,293` |
| `Startup, Design & Interdisciplinary` | 5 | `841,333,333` |
| `Web3, Blockchain & FinTech` | 1 | `204,322,960` |
| **Tổng cộng** | — | **`6,997,591,840` (`0.00 VND` chênh lệch)** |

### 3.3. Benchmark độ trễ truy vấn DuckDB `httpfs` trên R2

| Kịch bản truy vấn qua R2 `httpfs` | Độ trễ đo thực tế | Ghi chú |
| :--- | :---: | :--- |
| **OBT Cold** (`mart_competition_explorer.parquet`, 1 tệp) | **453.5 ms** | Nhanh hơn **2.93x** so với Star Join 4 bảng |
| **OBT Warm Avg** (trung bình 5 lượt đọc `mart_competition_explorer`) | **139.8 ms** | Đạt mục tiêu API latency `< 210 ms` |
| **Star 4-Table Join Cold** (`dim_competition` + `fact_competitions` + `bridge_*` + `dim_domain`) | **1,330.3 ms** | Chi phí mở 4 kết nối HTTP/Parquet header |

---

## 4. Kiểm thử & Chất lượng mã nguồn

- `uv run pytest tests/test_gold_star_schema.py -v`: **7/7 PASSED** (`test_currency_normalization_edge_cases`, `test_date_resolution_and_academic_terms`, `test_fee_and_team_and_domain_classification`, `test_load_silver_prefers_newest_batch_and_deduplicates`, `test_star_schema_bridge_allocation_and_edge_cases`, `test_r2_end_to_end_silver_to_gold_zero_local_disk`, `test_expired_open_status_normalizes_to_closed`).
- `uv run ruff check src/acdp/v2/gold_star_schema.py src/acdp/v2/rag_ingest.py tests/test_gold_star_schema.py`: **All checks passed**.
- `uv run python -m acdp.v2.gold_star_schema --build-gold-r2 --verify`: **Exit 0**, xác nhận 15 tệp trên R2 và `Bridge Diff: 0.00 VND`.
- `uv run python -m acdp.v2.rag_ingest --dry-run`: **Exit 0**, nạp `26` tài liệu Silver Clean Markdown với `26/26` enriched từ Gold.

---

## 5. Search Provenance & References

- **Internal Design Baseline**: [`TASK-GLD-01-kimball-star-schema-audit-and-alternatives.md`](./TASK-GLD-01-kimball-star-schema-audit-and-alternatives.md) (điểm chuẩn `A1–A5`, Two-Tier Gold, Dual-Layer RAG).
- **Specification**: [`0003-gold-dimensional-modeling-spec.md`](../specs/0003-gold-dimensional-modeling-spec.md) (`SPEC-0003` cập nhật chuẩn `A1, A2, A4`).
- **API Consumer Contract**: [`src/acdp/api/services/gold_queries.py`](../../src/acdp/api/services/gold_queries.py) và [`src/acdp/api/db/duckdb_client.py`](../../src/acdp/api/db/duckdb_client.py).
