# Deliverable: Triển khai Silver Schema v2 (`G1–G8`) & PyArrow Explicit Parquet (`v2/schemas.py`, `v2/gold_star_schema.py`)

- **Task ID**: `TASK-SLV-04`
- **Related Cycle**: Cycle 06 (TLCN Phase 1)
- **Primary Owner**: Do Kien Hung (`@darktheDE`) & Nguyen Van Quang Duy (`@QuangDuyReal`)
- **Institution**: Khoa Công nghệ Thông tin, Trường Đại học Công nghệ Kỹ thuật TP.HCM (HCM-UTE)
- **Date Completed**: 2026-11-23
- **Deliverable Type**: Silver Data Contract Upgrade, Explicit PyArrow Parquet & Live R2 Sync
- **Status**: Complete

---

## 1. Tóm tắt điều hành (Executive Summary)

Hiện thực hóa toàn bộ đề xuất từ [`TASK-SLV-02`](./TASK-SLV-02-silver-schema-and-parquet-validation.md) trên nhánh mã nguồn `src/acdp/v2/` (giữ nguyên mã nguồn v1 tại `src/acdp/schemas.py` và `src/acdp/4_analytics_gold.py` theo `DIR-022`), đóng trọn vẹn **8 lỗ hổng `G1–G8`**:

1. **[`src/acdp/v2/schemas.py`](../../src/acdp/v2/schemas.py)**: Nâng cấp `PrizeTier`, `TimelineStage`, `Competition`, `CompetitionExtractionResult` lên **Schema v2** tương thích ngược 100% với JSON v1 trên R2, bổ sung chuẩn hóa ngày ISO `date`, điều kiện dự thi & kỹ năng cho Ghép đội (`G2`, `G3`), 4 trường Màn hình gửi Giảng viên (`G4`), `tier_rank`/`quantity`/`currency`/`prize_type` cho `PrizeTier` (`G5`), siêu dữ liệu lineage (`G6`), và loại bỏ ép `None -> ""` ở `PrizeTier` (`G7`).
2. **[`src/acdp/v2/gold_star_schema.py`](../../src/acdp/v2/gold_star_schema.py)**: Định nghĩa 3 PyArrow explicit `pa.schema` (`SILVER_COMPETITIONS_ARROW_SCHEMA`, `SILVER_PRIZES_ARROW_SCHEMA`, `SILVER_TIMELINE_STAGES_ARROW_SCHEMA`), nén **ZSTD**, giữ chuẩn `None` (`null` thực trong Parquet), và xuất đủ 3 tệp lên Cloudflare R2 `silver/` (`competitions.parquet`, `prizes.parquet`, `timeline_stages.parquet`).
3. **[`src/acdp/v2/silver_transform.py`](../../src/acdp/v2/silver_transform.py)**: Chuyển sang sử dụng `acdp.v2.schemas`, bổ sung hướng dẫn trích xuất các trường Schema v2 trong `SYSTEM_PROMPT` và tự động điền `source_url` / `official_rules_url` ở tầng post-LLM guard.

---

## 2. Ma trận giải quyết 8 lỗ hổng (`G1–G8`)

| Mã | Lỗ hổng từ `TASK-SLV-02` | Giải pháp đã triển khai trong `v2` | Nơi triển khai |
| :---: | :--- | :--- | :--- |
| **G1** | Trường ngày chỉ là `str` tự do (`DD/MM/YYYY`) | Bổ sung `registration_start_date`, `registration_deadline_date`, `event_start_date`, `event_end_date`, `team_registration_deadline_date` và `TimelineStage.start_date_iso` / `end_date_iso` (`pa.date32()`), tự chuẩn hóa qua `parse_date_value()`. | `v2/schemas.py`, `v2/gold_star_schema.py` |
| **G2** | Thiếu cấu trúc điều kiện dự thi cho Ghép đội | Bổ sung `is_individual_allowed`, `eligibility_level` (`undergraduate` / `all_students` / `open` / `unknown`), `allowed_majors: list[str]`. | `v2/schemas.py` |
| **G3** | Thiếu kỹ năng/công nghệ đối chiếu CV | Bổ sung `required_skills: list[str]` chuẩn hóa qua `_clean_string_list()`. | `v2/schemas.py` |
| **G4** | Thiếu trường Màn hình gửi Giảng viên | Bổ sung `official_rules_url`, `organizer_contact`, `requires_advisor`, `team_registration_deadline` + `team_registration_deadline_date`. | `v2/schemas.py`, `v2/silver_transform.py` |
| **G5** | `PrizeTier` thiếu `tier_rank`, `quantity`, `currency`, `prize_type` | Bổ sung đầy đủ 4 trường; `_compute_competition_total_prize_vnd()` nhân `estimated_value_vnd * quantity`. | `v2/schemas.py`, `v2/gold_star_schema.py` |
| **G6** | Thiếu Lineage & Audit metadata | Bổ sung `competition_key` (SHA-256), `source_url`, `bronze_key`, `extracted_at`, `extractor_model`, `schema_version="2.0"`; tự động làm giàu từ `_metadata` khi nạp JSON v1. | `v2/schemas.py`, `v2/gold_star_schema.py` |
| **G7** | `PrizeTier` ép `None -> ""` gây lọt giải rỗng | `PrizeTier.validate_tier_non_empty` từ chối `None`/placeholder; `Competition.filter_invalid_prizes` lọc bỏ dict rỗng trước khi validate. | `v2/schemas.py` |
| **G8** | Suy luận kiểu Arrow động, ép `""`, rơi `timeline_stages` | Dùng 3 `pa.schema` tường minh (`43`, `10`, `9` cột), giữ `None` thật, nén `ZSTD`, xuất đủ `competitions.parquet`, `prizes.parquet`, `timeline_stages.parquet`. | `v2/gold_star_schema.py` |

---

## 3. Kết quả kiểm thử & Thực thi thực tế trên Cloudflare R2

### 3.1. Kiểm thử tự động & Kiểm định tài liệu
- `uv run pytest tests/test_silver_schema.py tests/test_silver_transform_v2.py tests/test_gold_star_schema.py -v`: **`24 passed`** (`0 failed`, `0 xfailed`; đã gỡ `xfail` trong `tests/test_silver_schema.py`).
- `uv run ruff check src/acdp/v2/ tests/test_silver_schema.py tests/test_silver_transform_v2.py`: **`0` lỗi**.

### 3.2. Kết quả xuất & kiểm chứng Parquet trực tiếp trên Cloudflare R2 (`2026-11-23`)
Chạy `uv run python -m acdp.v2.gold_star_schema --export-silver-r2 --verify` trên tập `26` domain (`24` cuộc thi duy nhất sau khử trùng lặp `r2:silver/extractions@latest(2026-11-23)`):

| Tệp Silver Parquet trên R2 | Số dòng | Số cột | Dung lượng (bytes) | Codec nén | Ghi chú kiểm chứng |
| :--- | :---: | :---: | :---: | :---: | :--- |
| `s3://acdp-lakehouse/silver/competitions.parquet` | `24` | `43` | `36,040` | `ZSTD` | Đủ 5 cột `pa.date32()`, giữ `null` chuẩn, lineage đầy đủ |
| `s3://acdp-lakehouse/silver/prizes.parquet` | `90` | `10` | `8,401` | `ZSTD` | Đủ `tier_rank`, `quantity`, `currency`, `prize_type` |
| `s3://acdp-lakehouse/silver/timeline_stages.parquet` | `89` | `9` | `11,443` | `ZSTD` | Bảng mới bổ sung (`start_date_iso`, `end_date_iso` dạng `date32`) |

### 3.3. Kiểm định chất lượng dữ liệu thực tế trên R2 (`audit_r2_silver.py`)
- **Toàn vẹn tham chiếu**: `24/24` `competition_key` duy nhất; `0` bản ghi mồ côi ở `prizes.parquet` (`90` dòng) và `timeline_stages.parquet` (`89` dòng).
- **Lineage & True Nulls**: `24/24` bản ghi có đủ `source_url`, `bronze_key`, `extracted_at`; `0` rò rỉ chuỗi rỗng `""` ở các cột nullable (`tagline`, `location`, `official_rules_url`, `organizer_contact`).
- **Độ phủ ngày ISO (`pa.date32()`)**: `event_start_date` đạt `24/24` (`100%`), `event_end_date` đạt `23/24` (`95.8%`), `registration_deadline_date` đạt `18/24` (`75%`), `timeline_stages` đạt `76/89` (`85.4%`).
- **Tổng giá trị giải thưởng**: `17/24` cuộc thi có `total_prize_vnd > 0` với tổng cộng `6,997,591,840 VND`.

---

## 4. Liên kết mã nguồn & Tài liệu

- Schema v2: [`src/acdp/v2/schemas.py`](../../src/acdp/v2/schemas.py)
- Silver Parquet Exporter v2: [`src/acdp/v2/gold_star_schema.py`](../../src/acdp/v2/gold_star_schema.py)
- Bộ kiểm thử Silver Schema & Parquet: [`tests/test_silver_schema.py`](../../tests/test_silver_schema.py)
- Báo cáo trực quan HTML: [`TASK-SLV-04-silver-schema-v2-and-parquet-implementation-visual-dossier.html`](./TASK-SLV-04-silver-schema-v2-and-parquet-implementation-visual-dossier.html)
- Sổ cái quản lý task: [`docs/tasks/task-registry.md`](../tasks/task-registry.md)

---

## 5. Search Provenance & References (`DIR-020`)

1. **Query**: `PyArrow explicit schema Parquet ZSTD compression date32 timestamp UTC`
   - Apache Arrow Python Parquet & Schema Reference: [arrow.apache.org/docs/python/parquet.html](https://arrow.apache.org/docs/python/parquet.html)
2. **Query**: `Pydantic v2 model_validator field_validator mode before after date parsing`
   - Pydantic v2 Validators Documentation: [docs.pydantic.dev/latest/concepts/validators/](https://docs.pydantic.dev/latest/concepts/validators/)
3. **Query**: `TASK-SLV-02 Silver Schema v2 gap audit G1-G8`
   - Internal Audit Deliverable: [`docs/deliverables/TASK-SLV-02-silver-schema-and-parquet-validation.md`](./TASK-SLV-02-silver-schema-and-parquet-validation.md)
