# Deliverable: Chốt Phản biện Kiến trúc Full Cloud (PA-1), Cấu hình MotherDuck Lite & Ban hành ADR-0002 (`TASK-CLD-07`)

| Thuộc tính | Giá trị |
| :--- | :--- |
| Task ID | `TASK-CLD-07` (Cycle 07, TLCN Phase 1) |
| Primary Owner | Đỗ Kiến Hưng (`@darktheDE`) & Nguyễn Văn Quang Duy (`@QuangDuyReal`) |
| Institution | Khoa Công nghệ Thông tin, Trường Đại học Công nghệ Kỹ thuật TP.HCM (HCM-UTE) |
| Date Completed | 2026-11-23 |
| Deliverable Type | Approved Architecture Decision Record (`ADR-0002`), MotherDuck Lite R2 Integration & Verification |
| Status | Done |

---

## 1. Tóm tắt điều hành (Executive Summary)

`TASK-CLD-07` hoàn tất bước phản biện nội bộ (`DIR-011`) giữa Đỗ Kiến Hưng và Nguyễn Văn Quang Duy trên cơ sở đề xuất [`TASK-CLD-03`](../deliverables/TASK-CLD-03-full-cloud-free-tier-architecture.md) và [`TASK-CLD-02`](../deliverables/TASK-CLD-02-web-dashboard-vs-metabase-boundary.md), đạt ba kết quả chính:

1. **Chốt phương án PA-1 (`FastAPI + DuckDB httpfs + In-Memory TTL Cache`) và ban hành [`ADR-0002`](../adr/0002-full-cloud-free-tier-architecture.md)**: Bảo toàn 100% mã nguồn `src/acdp/api/` và hợp đồng OpenAPI 3.1 (`SPEC-0004`), tránh giới hạn kích thước bundle `250 MB` của Next.js Serverless trên Vercel Hobby (PA-2) và tránh chậm tiến độ do viết lại sang Rust (PA-3). Container API tuân thủ chuẩn **Low-Footprint đa đích** (`DUCKDB_MEMORY_LIMIT=256MB`, `threads=2`, hỗ trợ cổng `7860` trên HF Spaces `16 GB RAM` và cổng `8000` trên Koyeb Eco / Render Free `512 MB RAM`).
2. **Tích hợp MotherDuck Lite Free (`--motherduck-sql` & `--verify-motherduck`)**: Bổ sung cấu hình `MOTHERDUCK_TOKEN` / `MOTHERDUCK_DATABASE` trong [`config.py`](../../src/acdp/config.py) và hàm `build_motherduck_r2_init_sql()` / `verify_motherduck_views_from_r2()` trong [`gold_star_schema.py`](../../src/acdp/v2/gold_star_schema.py) để tạo `IN MOTHERDUCK` R2 secret và `19` Gold Views (`15` Two-Tier Gold Parquet + `4` Virtual Views `gold_*`) đọc trực tiếp từ Cloudflare R2 mà không tiêu tốn quota `10 GB` của MotherDuck.
3. **Kiểm chứng thực tế trên Cloudflare R2 (`0.0 VND` Drift)**: Toàn bộ `19` views và `3` truy vấn Data Quality Scorecard đã chạy thành công trực tiếp trên `s3://acdp-lakehouse/gold/*.parquet` với `24` cuộc thi và độ lệch tổng giải thưởng `0.0 VND`.

---

## 2. Kết quả kiểm chứng MotherDuck Lite & 19 Gold Views trên R2

Thực thi `uv run python -m acdp.v2.gold_star_schema --verify-motherduck` trực tiếp trên Cloudflare R2 (`r2_direct_httpfs_verified`) ghi nhận đầy đủ dữ liệu thực tế:

| Nhóm thực thể | Tên View | Số dòng (Rows) | Nguồn Parquet trên R2 |
| :--- | :--- | :---: | :--- |
| Core Star Dimensions (`4`) | `dim_competition` | `24` | `s3://acdp-lakehouse/gold/dim_competition.parquet` |
| Core Star Dimensions (`4`) | `dim_date` | `106` | `s3://acdp-lakehouse/gold/dim_date.parquet` |
| Core Star Dimensions (`4`) | `dim_domain` | `6` | `s3://acdp-lakehouse/gold/dim_domain.parquet` |
| Core Star Dimensions (`4`) | `dim_organizer` | `76` | `s3://acdp-lakehouse/gold/dim_organizer.parquet` |
| Core Star Facts (`3`) | `fact_competitions` | `24` | `s3://acdp-lakehouse/gold/fact_competitions.parquet` |
| Core Star Facts (`3`) | `fact_prize_tiers` | `90` | `s3://acdp-lakehouse/gold/fact_prize_tiers.parquet` |
| Core Star Facts (`3`) | `fact_timeline_stages` | `89` | `s3://acdp-lakehouse/gold/fact_timeline_stages.parquet` |
| Core Star Bridges (`2`) | `bridge_competition_domain` | `51` | `s3://acdp-lakehouse/gold/bridge_competition_domain.parquet` |
| Core Star Bridges (`2`) | `bridge_competition_organizer` | `76` | `s3://acdp-lakehouse/gold/bridge_competition_organizer.parquet` |
| Pre-Aggregated Marts (`6`) | `mart_kpi_overview` | `1` | `s3://acdp-lakehouse/gold/mart_kpi_overview.parquet` |
| Pre-Aggregated Marts (`6`) | `mart_domain_analytics` | `5` | `s3://acdp-lakehouse/gold/mart_domain_analytics.parquet` |
| Pre-Aggregated Marts (`6`) | `mart_seasonality_academic` | `11` | `s3://acdp-lakehouse/gold/mart_seasonality_academic.parquet` |
| Pre-Aggregated Marts (`6`) | `mart_organizer_ecosystem` | `76` | `s3://acdp-lakehouse/gold/mart_organizer_ecosystem.parquet` |
| Pre-Aggregated Marts (`6`) | `mart_team_and_mode_matrix` | `11` | `s3://acdp-lakehouse/gold/mart_team_and_mode_matrix.parquet` |
| Pre-Aggregated Marts (`6`) | `mart_competition_explorer` | `24` | `s3://acdp-lakehouse/gold/mart_competition_explorer.parquet` |
| Virtual Legacy Views (`4`) | `gold_category_summary` / `gold_mode_distribution` / `gold_seasonality` / `gold_top_prizes` | `5` / `4` / `11` / `24` | Truy vấn ảo trên `mart_*` |

### Chỉ số Data Quality Scorecard & Bridge Invariant (Đo thực tế trên R2)
- Tổng số cuộc thi (`total_competitions`): `24`
- Thiếu hạn đăng ký (`missing_deadline_count`, `reg_deadline_date_sk = -1`): `6`
- Thiếu quy mô đội (`missing_team_size_count`, `dim_competition.team_size_max IS NULL`): `7`
- Chưa công bố cơ cấu giải (`missing_prize_tiers_count`, `prize_tier_count = 0`): `2`
- Bảo toàn tổng giải thưởng (`Bridge Weighting Invariant`): `fact_total_vnd = 6,997,591,840 VND`, `bridge_total_vnd = 6,997,591,840 VND`, `drift_vnd = 0.0 VND`.

---

## 3. Playbook kích hoạt MotherDuck Lite Free cho Hưng & Duy

1. Xuất câu lệnh khởi tạo an toàn (không in lộ secret ra terminal):
   ```powershell
   uv run python -m acdp.v2.gold_star_schema --motherduck-sql
   ```
2. Dán đoạn SQL vào **MotherDuck Web SQL Editor** (thay `<R2_ACCESS_KEY_ID>` và `<R2_SECRET_ACCESS_KEY>` bằng khóa R2 Read-Only) để tạo database `acdp_gold`, `SECRET r2_secret IN MOTHERDUCK` và `19` views.
3. Hoặc khai báo `MOTHERDUCK_TOKEN` trong `.env` và chạy một lệnh đồng bộ tự động:
   ```powershell
   uv run python -m acdp.v2.gold_star_schema --verify-motherduck
   ```

---

## 4. Nhật ký truy vấn và nguồn tham khảo (`DIR-020`)

| STT | Câu lệnh truy vấn (`search_web`) | Mục đích kiểm chứng | Nguồn chính thức |
| :---: | :--- | :--- | :--- |
| 1 | `MotherDuck Lite free tier limits 2025 2026 DuckDB S3 R2 integration` | Xác nhận gói Lite (`$0`, `10 GB`, `10 CU-hrs/tháng`, `3` users) và BYOB R2 miễn phí lưu trữ | https://motherduck.com/pricing/ |
| 2 | `"MotherDuck" "CREATE SECRET" Cloudflare R2 endpoint s3 read_parquet SQL 2025 2026` | Kiểm chứng cú pháp `CREATE SECRET ... IN MOTHERDUCK` với Cloudflare R2 | https://motherduck.com/docs/integrations/cloud-storage/amazon-s3/ |
| 3 | `DuckDB "CREATE SECRET" "TYPE R2" ACCOUNT_ID vs "TYPE S3" MotherDuck IN MOTHERDUCK 2025 2026` | Đối chiếu `TYPE R2` và `TYPE S3` khi lưu secret trên MotherDuck | https://duckdb.org/docs/stable/extensions/httpfs/overview |
| 4 | `"Hugging Face Spaces" "CPU basic" free tier Docker requires PRO account 2025 2026` | Kiểm chứng chính sách Docker SDK & CPU Basic (`2 vCPU`, `16 GB RAM`) trên HF Spaces | https://huggingface.co/docs/hub/spaces-sdks-docker |
| 5 | `Hugging Face Spaces free tier CPU basic 2 vCPU 16GB RAM sleep 48 hours FastAPI Docker 2025 2026` | Xác nhận cổng mặc định `7860`, non-root `UID 1000` và chu kỳ ngủ đông | https://huggingface.co/docs/hub/spaces-overview |

---

## 5. Tài liệu liên quan

- Quyết định kiến trúc chính thức: [`ADR-0002`](../adr/0002-full-cloud-free-tier-architecture.md) (thay thế [`ADR-0001`](../adr/0001-medallion-lakehouse-and-rag-stack.md))
- Báo cáo trực quan tương tác: [`TASK-CLD-07-adr-0002-and-motherduck-setup-visual-dossier.html`](./TASK-CLD-07-adr-0002-and-motherduck-setup-visual-dossier.html)
- Hồ sơ thiết kế gốc: [`TASK-CLD-03-full-cloud-free-tier-architecture.md`](./TASK-CLD-03-full-cloud-free-tier-architecture.md)
