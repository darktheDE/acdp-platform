# Deliverable: Kiểm chứng Schema Lớp Bạc (`Competition` + `PrizeTier`) & Lưu trữ Parquet

- **Task ID**: `TASK-SLV-02`
- **Related Cycle**: Cycle 06 (TLCN Phase 1)
- **Primary Owner**: Do Kien Hung (`@darktheDE`) & Nguyen Van Quang Duy (`@QuangDuyReal`)
- **Institution**: Khoa Công nghệ Thông tin, Trường Đại học Công nghệ Kỹ thuật TP.HCM (HCM-UTE)
- **Date Completed**: 2026-11-23
- **Deliverable Type**: Data Schema Audit & Parquet Storage Validation
- **Status**: Complete (Audit & Proposal — Chờ phản biện Hưng & Duy trước khi sửa code ở `TASK-SLV-03`)

---

## 1. Tóm tắt điều hành (Executive Summary)

Tài liệu này kiểm chứng toàn diện hợp đồng dữ liệu Lớp Bạc (`Competition`, `PrizeTier`, `TimelineStage` trong [`src/acdp/schemas.py`](../../src/acdp/schemas.py)) và hai tệp Parquet đầu ra (`silver/competitions.parquet`, `silver/prizes.parquet` do `export_silver_parquet()` trong [`src/acdp/4_analytics_gold.py`](../../src/acdp/4_analytics_gold.py#L649-L744) sinh ra) đối chiếu với 6 tính năng mục tiêu của sản phẩm cuối cùng.

| Tính năng sản phẩm | Mức độ đáp ứng | Lý do chính |
| :--- | :---: | :--- |
| **1. Academic Competition Explorer** (`/competitions`) | **Thiếu một phần** | Có đủ tên, mô tả, hình thức, lệ phí, tổng giải; nhưng **4 trường ngày đều là `str` tự do** (100% dữ liệu thực tế trên R2 dùng `DD/MM/YYYY`, không sắp xếp/lọc ISO được) và **thiếu bảng `timeline_stages.parquet`** ở Silver. |
| **2. Ghép đội (Team Matching trên OLTP)** | **Thiếu một phần** | Ghép đội tạo/tham gia nhóm chạy trên PostgreSQL OLTP (không dùng AI), nhưng Silver mới có `team_size_min/max` (thiếu 20–33% trên R2), **chưa có trường điều kiện dự thi cấu trúc** (bậc học, ngành, giới hạn trường) và **chưa có `required_skills` / `tech_stack`** để đối chiếu với hồ sơ CV sinh viên. |
| **3. Màn hình gửi Giảng viên xin hướng dẫn** | **Thiếu** | Thiếu 4 trường cốt lõi: `official_rules_url` (link thể lệ gốc), `organizer_contact` (email/fanpage BTC), `requires_advisor` (có bắt buộc GVHD không), và `team_registration_deadline`. |
| **4. Thông báo cuộc thi mới (Email Service)** | **Thiếu** | Không có `registration_deadline_iso` (`DATE`) để tính ngưỡng nhắc hạn và không có `extracted_at` / `first_seen_at` để phát hiện cuộc thi mới xuất hiện. |
| **5. Analytics Dashboard (Gold / Metabase)** | **Thiếu một phần** | `total_prize_vnd` và `mode` đã chuẩn hóa, nhưng **ngày `DD/MM/YYYY` gây lỗi phân mùa `HK1`/`HK2`/`Hè`**, `PrizeTier` thiếu `quantity` (số suất giải) và `currency`, còn `timeline_stages` bị rơi mất khi xuất Silver Parquet. |
| **6. RAG Chatbot & Trích dẫn nguồn (Guardrail #4)** | **Thiếu một phần** | `url` có sẵn nhưng `schemas.py` **thiếu trường lineage** (`source_url`, `bronze_key`, `extracted_at`, `extractor_model`, `schema_version`, `competition_key`). |

> [!NOTE]
> Phân tích về tỷ lệ dùng LLM vs. Data Engineering tại Lớp Bạc đã được giải quyết trong [`TASK-SLV-01`](./TASK-SLV-01-hybrid-de-vs-llm-extraction-study.md) (kiến trúc *Deterministic Sandwich*). Tài liệu này chỉ tập trung kiểm chứng **Schema** và **Lưu trữ Parquet**.

---

## 2. Ma trận truy vết: Tính năng cuối $\rightarrow$ Silver Schema $\rightarrow$ Parquet $\rightarrow$ Downstream

| Tính năng | Trường cần dùng | Có trong `schemas.py`? | Có trong Silver Parquet? | Người tiêu thụ (DTO / Gold Mart) | Trạng thái |
| :--- | :--- | :---: | :---: | :--- | :---: |
| **Explorer** | `name`, `tagline`, `url`, `summary`, `mode`, `location` | Có | Có (`competitions.parquet`) | `CompetitionSummaryDTO`, `mart_competition_explorer` | Đạt |
| **Explorer** | `registration_deadline_iso` (`DATE`), `event_start_iso` (`DATE`) | **Không** (chỉ có `str`) | **Không** (chỉ có `str`) | Lọc/sắp xếp hạn nộp, `fact_competitions` | **Thiếu (G1)** |
| **Explorer** | `timeline_stages` (từng vòng thi) | Có (`TimelineStage`) | **Không** (không xuất Parquet) | `CompetitionDetailDTO.timeline_stages`, `fact_timeline_stages` | **Thiếu (G8)** |
| **Ghép đội** | `team_size_min`, `team_size_max`, `is_team_required` | Có (`min/max`) | Có | `CompetitionSummaryDTO`, OLTP `teams` | Đạt (null 20–33%) |
| **Ghép đội** | `eligibility_student_only`, `allowed_majors`, `is_individual_allowed` | **Không** (chỉ có `target_audience: str`) | **Không** | Đối chiếu hồ sơ `/profile` (MSSV, ngành, năm học) | **Thiếu (G2)** |
| **Ghép đội** | `required_skills` / `tech_stack` | **Không** | **Không** | Khớp `skills` từ CV sinh viên khi tìm đồng đội | **Thiếu (G3)** |
| **Màn hình GV** | `official_rules_url`, `organizer_contact`, `requires_advisor`, `team_reg_deadline` | **Không** | **Không** | Màn hình tóm tắt gửi email xin Giảng viên hướng dẫn | **Thiếu (G4)** |
| **Analytics** | `prizes` (`tier_rank`, `tier`, `reward`, `estimated_value_vnd`, `is_scholarship`) | Có (trừ `tier_rank`) | Có (`prizes.parquet`) | `PrizeTierDTO`, `fact_prize_tiers` | Thiếu `quantity`, `currency` (G5) |
| **RAG & Lineage** | `competition_key`, `source_url`, `bronze_key`, `extracted_at`, `schema_version` | **Không** (`key` chỉ tính lúc xuất) | Chỉ có `competition_key` | `rag_service.py` (Guardrail #4), audit pipeline | **Thiếu (G6)** |

---

## 3. Hồ sơ dữ liệu thực tế trên Cloudflare R2 (Read-Only Audit)

Kiểm tra trực tiếp hai tệp Silver Parquet đang lưu trên Cloudflare R2 (`silver/competitions.parquet` và `silver/prizes.parquet`) ngày 23/11/2026:

### 3.1. Tổng quan tệp Silver trên R2
- `silver/competitions.parquet`: **15 dòng**, **25 cột**, dung lượng **22.9 KB**. Khóa `competition_key` duy nhất **15/15** (0 trùng lặp).
- `silver/prizes.parquet`: **50 dòng**, **7 cột**, dung lượng **6.7 KB**. Thuộc **14/15** cuộc thi (1 cuộc thi không có giải chi tiết; **0 bản ghi giải thưởng mồ côi**).
- `silver/extractions/`: Hiện chưa có snapshot JSON trên R2; mới có lớp Parquet hợp nhất.

### 3.2. Tỷ lệ trống / Null & Bất thường dữ liệu thực tế

| Nhóm trường | Tên cột (`competitions.parquet`) | Kiểu Arrow suy luận | Tỷ lệ trống / Null | Vấn đề phát hiện |
| :--- | :--- | :---: | :---: | :--- |
| **Định danh** | `competition_key`, `name`, `url`, `summary` | `string` | `0/15` (0%) | `competition_key` không có trong Pydantic, chỉ sinh khi chạy `4_analytics_gold.py`. |
| **Thời gian** | `registration_start` | `string` | `4/15` (26%) | **11/11** giá trị là `DD/MM/YYYY` (vd: `'01/11/2026'`), không phải ISO `YYYY-MM-DD`. |
| **Thời gian** | `registration_deadline` | `string` | `3/15` (20%) | **12/12** giá trị là `DD/MM/YYYY` (vd: `'16/11/2025'`, `'25/09/2026'`). |
| **Thời gian** | `event_start` / `event_end` | `string` | `0%` / `13%` | **14/15** `event_start` và **12/13** `event_end` không theo chuẩn ISO 8601. |
| **Đội thi** | `team_size_min` / `team_size_max` | `int64` | `20%` / `33%` | 5/15 cuộc thi thiếu `team_size_max`, gây khó cho lọc quy mô đội ở Explorer & Ghép đội. |
| **Tài trợ & Địa điểm** | `partners_and_sponsors`, `location` | `list<string>`, `string` | `46%`, `13%` | Chuỗi rỗng `""` bị ép từ `None` khi xuất Parquet, làm mất phân biệt *chưa có dữ liệu* vs *chuỗi rỗng*. |
| **Giải thưởng** | `total_prize_vnd` (`competitions`) | `int64` | `0%` (4/15 = `0`) | 4/15 cuộc thi có tổng giải = `0 VNĐ` (chủ yếu giải hiện vật/chưa quy đổi). |
| **Giải thưởng** | `estimated_value_vnd` (`prizes.parquet`) | `int64` | `0%` (13/50 = `0`) | 13/50 hạng giải = `0 VNĐ` (vd: `'ZAIC gift package'`), `empty_tier=0`, `empty_reward=0`. |

---

## 4. Tổng hợp 8 Lỗ hổng Schema & Lưu trữ (G1–G8)

| Mã | Mô tả lỗ hổng | Bằng chứng từ code / R2 | Ảnh hưởng |
| :---: | :--- | :--- | :--- |
| **G1** | Toàn bộ trường ngày là `str` tự do, thiếu cột `DATE` chuẩn ISO 8601 | 100% `registration_deadline` trên R2 là `DD/MM/YYYY` | Sai thứ tự khi `ORDER BY`, hỏng bộ lọc hạn chót, phân kỳ `HK1`/`HK2`/`Hè` bị đẩy vào `'Khác'`. |
| **G2** | Thiếu trường điều kiện dự thi có cấu trúc (`eligibility`) | Chỉ có `target_audience: str` tự do | Không lọc được cuộc thi chỉ dành cho SV ĐH, đúng ngành CNTT hay cho phép thi cá nhân. |
| **G3** | Thiếu `required_skills` / `tech_stack` | `category` quá rộng (`AI`, `Hackathon`) | Sinh viên không lọc được theo kỹ năng từ `/profile` (Python, React, SQL) khi ghép đội. |
| **G4** | Thiếu trường phục vụ **Màn hình gửi Giảng viên** | Không có `official_rules_url`, `organizer_contact`, `requires_advisor`, `team_registration_deadline` | Sinh viên phải tự mở lại web gốc để chép link thể lệ và email BTC khi gửi GVHD. |
| **G5** | `PrizeTier` thiếu `tier_rank`, `quantity`, `currency`, `prize_type` | `total_prize_pool` là `str`; `tier_rank` chỉ tự đánh số thứ tự mảng | Không nhân được tổng tiền khi có nhiều suất giải (vd: *3 giải Khuyến khích x 5 triệu*). |
| **G6** | Thiếu siêu dữ liệu nguồn gốc (Lineage) | Không có `source_url`, `bronze_key`, `extracted_at`, `extractor_model`, `schema_version` | Khó kiểm toán khi RAG trích dẫn (Guardrail #4) và không biết cuộc thi nào mới để gửi email. |
| **G7** | `PrizeTier.clean_fields` ép `None` thành `""` | `schemas.py:48-49` | Các hạng giải rỗng (`tier=""`, `reward=""`) vẫn vượt qua Pydantic validation mà không bị loại. |
| **G8** | Xuất Parquet dùng suy luận kiểu động (`pa.Table.from_pylist`), ép `None` thành `""`, và bỏ rơi `timeline_stages` | `4_analytics_gold.py:666-707` | Rủi ro lệch kiểu Arrow giữa các batch; mất hoàn toàn dữ liệu `timeline_stages` ở Silver Parquet. |

---

## 5. Đánh giá Kỹ thuật Lưu trữ Parquet & Kiến trúc Silver

1. **Tách bảng chuẩn hóa (`competitions.parquet` + `prizes.parquet` + `timeline_stages.parquet`) vs. 1 tệp Nested Parquet**:
   - **Kết luận: Giữ mô hình tách bảng chuẩn hóa (Normalized Tables)** và bổ sung thêm `silver/timeline_stages.parquet`.
   - **Cơ sở kỹ thuật**: Theo chuẩn Medallion (Databricks) và PyArrow/DuckDB, mối quan hệ **1:N** (`1 Competition : N Prizes`, `1 Competition : N TimelineStages`) nếu nhồi thành `pa.list_(pa.struct(...))` trong 1 tệp sẽ gây khó cho *predicate pushdown* khi lọc theo giá trị giải thưởng hoặc ngày vòng thi, đồng thời dễ gãy *schema evolution* khi nâng cấp `PrizeTier` (G5). Tách bảng phẳng nén `ZSTD` cho tỷ lệ nén cao và khớp trực tiếp 1-1 với `fact_prize_tiers` và `fact_timeline_stages` ở Lớp Vàng.
2. **Khai báo PyArrow Schema tường minh (`pa.schema`)**:
   - Không dùng `pa.Table.from_pylist(rows)` suy luận ngầm; phải truyền `schema=SILVER_COMPETITIONS_ARROW_SCHEMA` (với `pa.date32()` cho cột ngày ISO, `pa.int32()` cho `team_size_*`, `pa.int64()` cho `*_vnd`, giữ nguyên `None` thay vì ép `""`).
3. **Phân vùng (Partitioning)**:
   - Với quy mô TLCN **5–10 cuộc thi** (`< 50 KB` tổng dung lượng Parquet, theo `DIR-015`), **không chia partition thư mục** (`year=/month=`) ở `silver/*.parquet` để tránh bài toán *small files* khi DuckDB `httpfs` đọc từ Cloudflare R2. Lịch sử snapshot theo ngày giữ nguyên ở `silver/extractions/<domain>/year=...`.

---

## 6. Đề xuất Silver Schema v2 (Chờ phản biện Hưng & Duy — `DIR-011`)

> [!IMPORTANT]
> Theo `DIR-011`, mọi thay đổi dưới đây là **đề xuất kỹ thuật để hai thành viên phản biện** trước khi chốt SPEC/ADR và triển khai code tại `TASK-SLV-03`. Tất cả trường mới đều là `Optional` (`default=None` / `default_factory=list`) để bảo đảm tương thích ngược.

```python
# Đề xuất mở rộng cho src/acdp/schemas.py (Schema v2 - Backward Compatible)
class PrizeTier(BaseModel):
    tier: str
    reward: str
    tier_rank: int | None = None              # G5: Thứ hạng tường minh (1, 2, 3...)
    quantity: int = Field(default=1, ge=1)    # G5: Số suất giải ở hạng này
    currency: Literal["VND", "USD", "OTHER"] = "VND"
    prize_type: Literal["cash", "scholarship", "credits", "merch", "mixed"] = "cash"
    estimated_value_vnd: float | None = Field(default=None, ge=0)
    is_scholarship: bool = False
    # G7: Bỏ ép None -> ""; yêu cầu ít nhất tier không rỗng hoặc loại bỏ ở validator Competition

class Competition(BaseModel):
    # ... giữ nguyên các trường hiện tại ...
    # G1: Giữ *_raw (str) cho hiển thị + thêm cột ISO date chuẩn hóa (tất định ở bước Validate)
    registration_start_date: date | None = None
    registration_deadline_date: date | None = None
    event_start_date: date | None = None
    event_end_date: date | None = None

    # G2 & G3: Phục vụ Ghép đội & Explorer (khớp hồ sơ /profile)
    is_individual_allowed: bool | None = None
    eligibility_level: Literal["undergraduate", "all_students", "open", "unknown"] = "unknown"
    allowed_majors: list[str] = Field(default_factory=list)
    required_skills: list[str] = Field(default_factory=list)

    # G4: Phục vụ Màn hình gửi Giảng viên xin hướng dẫn
    official_rules_url: str | None = None
    organizer_contact: str | None = None
    requires_advisor: bool | None = None
    team_registration_deadline_date: date | None = None

    # G6: Lineage & Audit (Guardrail #4 + Email thông báo cuộc thi mới)
    source_url: str | None = None
    bronze_key: str | None = None
    extracted_at: datetime | None = None
    extractor_model: str | None = None
    schema_version: str = "2.0"
```

---

## 7. Liên kết & Bước tiếp theo

- **Kiểm chứng tự động**: Đã bổ sung bộ test hợp đồng Parquet cho `export_silver_parquet` tại [`tests/test_silver_schema.py`](../../tests/test_silver_schema.py) (gồm cả test `xfail` đánh dấu rõ 8 lỗ hổng G1–G8).
- **Visual Dossier**: [`TASK-SLV-02-silver-schema-and-parquet-validation-visual-dossier.html`](./TASK-SLV-02-silver-schema-and-parquet-validation-visual-dossier.html)
- **Bước tiếp theo (`TASK-SLV-03`)**: Sau khi Hưng và Duy phản biện Schema v2, triển khai Hybrid *Deterministic Sandwich* trong `2_instruction.py`, cập nhật `schemas.py` và `export_silver_parquet` (bổ sung `timeline_stages.parquet` + PyArrow explicit schema).

---

## 8. Search Provenance & References (`DIR-020`)

1. **Query**: `Databricks medallion architecture silver layer definition best practices 2025 2026`
   - Databricks Medallion Architecture & Domain Knowledge Rule (Silver = cleaned, typed, deduplicated, 3NF/conformed entities): [databricks.com](https://www.databricks.com/glossary/medallion-architecture), [cosmosthrace.com](https://cosmosthrace.com)
2. **Query**: `PyArrow explicit schema Parquet nested struct vs normalized tables DuckDB httpfs R2 2025 2026`
   - PyArrow explicit `pa.schema`, ZSTD compression, nested struct vs normalized tables for 1:N, DuckDB `httpfs` R2 secret & predicate pushdown: [apache.org (PyArrow)](https://arrow.apache.org/docs/python/parquet.html), [duckdb.org (httpfs & Cloudflare R2)](https://duckdb.org/docs/extensions/httpfs/s3api)
3. **Query**: `Pydantic v2 field_validator strict mode date ISO 8601 official docs`
   - Pydantic v2 `date` parsing (`mode='before'` custom `DD/MM/YYYY` normalization & strict mode): [docs.pydantic.dev](https://docs.pydantic.dev/latest/concepts/validators/)
4. **Query**: `schema.org Event EducationEvent properties eligibility startDate organizer`
   - Schema.org `EducationEvent` / `Event` (`startDate` ISO 8601, `organizer`, `audience`, `educationalLevel`): [schema.org/EducationEvent](https://schema.org/EducationEvent)
5. **Query**: `Devpost Unstop hackathon competition eligibility team size prize structure data model`
   - Devpost & Unstop competition domain modeling (eligibility, team lead, prize tiers with category/value/currency): [devpost.com](https://devpost.com), [unstop.com](https://unstop.com)
