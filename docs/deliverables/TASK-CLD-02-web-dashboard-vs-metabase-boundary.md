# Deliverable: Phân định Ranh giới Web Dashboard vs Metabase (`TASK-CLD-02`)

| Thuộc tính | Giá trị |
| :--- | :--- |
| Task ID | `TASK-CLD-02` (Cycle 07, TLCN Phase 1) |
| Primary Owner | Do Kien Hung (`@darktheDE`) & Nguyen Van Quang Duy (`@QuangDuyReal`) |
| Institution | Khoa Công nghệ Thông tin, Trường Đại học Công nghệ Kỹ thuật TP.HCM (HCM-UTE) |
| Date Completed | 2026-11-23 |
| Deliverable Type | BI Architecture Boundary, Resource Quantification & DataOps Playbook |
| Status | Done |

---

## 1. Tóm tắt điều hành (Executive Summary)

Trên cổng thông tin ACDP, trang [`apps/web/app/dashboard/page.tsx`](../../apps/web/app/dashboard/page.tsx) đã cung cấp Dashboard phân tích trực quan bằng **Next.js 16 + Recharts**, trong khi [`docker-compose.yml`](../../docker-compose.yml) vẫn khai báo container `acdp-metabase` (`1024 MB` RAM JVM). `TASK-CLD-02` chốt ranh giới kiến trúc **3 Tầng BI (3-Tier Analytics & BI Boundary)** trong tài liệu [`T15`](../rd-tasks/T15_metabase_and_prefect_lightweight_architecture.md) để triệt tiêu sự chồng chéo khi bảo vệ Tiểu luận Chuyên ngành (TLCN) và đồng bộ với kiến trúc **100% Cloud Free-Tier (`TASK-CLD-03`)**:

1. **Tầng 1 — Customer-Facing Product Analytics (`Next.js 16 + Recharts` tại `/dashboard`)**: Kênh hiển thị duy nhất cho **Sinh viên & Giảng viên** trên Cloud (Vercel Hobby) và Docker `core`. Đọc trực tiếp **6 bảng Pre-Aggregated Data Marts (`mart_*`)** qua FastAPI + DuckDB `httpfs` + TTL Cache (`< 20 ms` warm, `~183 ms` cold), đồng bộ Dark/Light mode và liên kết thẳng sang luồng tìm kiếm (`/competitions`) và ghép đội (`/teams`).
2. **Tầng 2 — Cloud DataOps & Ad-hoc SQL Workbench (`MotherDuck Lite Free`)**: Thay thế hoàn toàn Metabase trên Cloud Free-Tier (vì Metabase Cloud không có gói miễn phí, giá từ `$100/tháng`, còn self-host JVM ngốn `650–850 MB` RAM không vừa PaaS `512 MB`). MotherDuck Lite (`$0/tháng`, `10 GB` storage, `10 CU-hours` Pulse/tháng) truy vấn trực tiếp **9 bảng Core Kimball Star Schema** trên Cloudflare R2 để Kỹ sư Dữ liệu chạy ad-hoc SQL và kiểm toán chất lượng dữ liệu (**Data Quality Scorecard**).
3. **Tầng 3 — On-Demand Local Self-Service BI (`Metabase Docker --profile bi`, cổng `:3001`)**: Tắt mặc định (`0 MB` RAM ở profile `core`) và không triển khai lên Cloud. Chỉ bật tạm thời tại local (`docker compose --profile bi up -d metabase`) khi cần demo trực quan Self-Service BI trước Hội đồng hoặc dự phòng mất mạng tại phòng bảo vệ (Rủi ro `R6`).

---

## 2. Ma trận Đối sánh 3 Tầng BI & Ngân sách Tài nguyên

| Tiêu chí | Tầng 1: Web `/dashboard` (`Next.js 16 + Recharts`) | Tầng 2: `MotherDuck Lite Free` | Tầng 3: `Metabase Docker` (`--profile bi`) |
| :--- | :--- | :--- | :--- |
| **Đối tượng** | Sinh viên & Giảng viên | Kỹ sư Dữ liệu (Hưng & Duy) | DE & Hội đồng (Demo / Offline) |
| **Nguồn Gold** | 6 bảng `mart_*` (`0-Join`) | 9 bảng Star Schema + 4 views `gold_*` | 9 bảng Star Schema + 4 views `gold_*` |
| **RAM Local** | Nằm trong `core` (`1408 MB` tổng) | `0 MB` (Cloud SaaS) | `+1024 MB` JVM Limit (`650–850 MB` thực tế) |
| **Cloud Free Tier** | Vercel Hobby + HF Spaces (`$0`) | MotherDuck Lite (`$0`, `10 GB`, `10h`) | Không có Cloud Free Tier (`Starter $100/tháng`) |
| **Trạng thái mặc định** | **Luôn bật** | **Luôn sẵn sàng trên Cloud** | **Tắt mặc định** (`0 MB` khi chạy `core`) |

### Ngân sách RAM theo Profile Docker (`SPEC-0006`)
- **`core` (Cloud-First mặc định)**: `postgres` (`256M`) + `api` (`640M`) + `web` (`512M`) = **`1408 MB` (`1.38 GB`)**.
- **`core + local-backup`**: **`1920 MB` (`1.88 GB`)** (thêm `qdrant` `512M`).
- **`core + bi`**: **`2432 MB` (`2.38 GB`)** (bật tạm `metabase` `1024M` với `-Xmx768m -Xms256m`).

---

## 3. Playbook Vận hành On-Demand (`--metabase-sql`)

```powershell
# 1. Xuất SQL tạo Secret R2 và Views cho MotherDuck Lite hoặc Metabase
uv run python -m acdp.v2.gold_star_schema --metabase-sql

# 2. Bật tạm Metabase local ở cổng :3001 khi cần kiểm định Star Schema hoặc demo offline
docker compose --profile bi up -d metabase

# 3. Tắt ngay sau khi xong để giải phóng ~650–850 MB RAM
docker compose --profile bi stop metabase
```

---

## 4. Search Provenance & Verifiable References (`DIR-020`)

Toàn bộ dữ liệu giá, giới hạn bộ nhớ JVM và tính năng Cloud Free Tier năm 2026 được kiểm chứng qua 7 câu lệnh `search_web` và lưu đầy đủ nhật ký trong [`T15_metabase_and_prefect_lightweight_architecture.md`](../rd-tasks/T15_metabase_and_prefect_lightweight_architecture.md):

| Nguồn chính thức | Nội dung kiểm chứng | URL |
| :--- | :--- | :--- |
| **Metabase Pricing** | Xác nhận không có Cloud Free Tier (Starter `$100/tháng`, Pro `$575/tháng`) | https://www.metabase.com/pricing/ |
| **Metabase Docker Docs** | Yêu cầu RAM tối thiểu & quy tắc đặt JVM `-Xmx` (`70–80%` RAM container) | https://www.metabase.com/docs/latest/installation-and-operation/running-metabase-on-docker |
| **MotherDuck Pricing** | Hạn mức Lite Free (`$0`, `10 GB`, `10 CU-hours` Pulse/tháng, `3` users) | https://motherduck.com/pricing/ |
| **MotherDuck S3 / R2 Docs** | Đọc trực tiếp Parquet trên S3/R2 không tính vào quota `10 GB` của MotherDuck | https://motherduck.com/docs/integrations/cloud-storage/amazon-s3/ |
| **Metabase DuckDB Driver** | Driver `ghcr.io/motherduckdb/metabase-duckdb`, `httpfs`, `access_mode=READ_ONLY` | https://github.com/motherduckdb/metabase_duckdb_driver |
| **Prefect & GitHub Actions** | Prefect Cloud Hobby (`5` deployments, `500` phút) & GHA runner specs | https://www.prefect.io/pricing |

---

## 5. Tài liệu liên quan

- Hồ sơ nghiên cứu đầy đủ: [`T15_metabase_and_prefect_lightweight_architecture.md`](../rd-tasks/T15_metabase_and_prefect_lightweight_architecture.md)
- Báo cáo trực quan tương tác: [`TASK-CLD-02-web-dashboard-vs-metabase-boundary-visual-dossier.html`](./TASK-CLD-02-web-dashboard-vs-metabase-boundary-visual-dossier.html)
- Kiến trúc Full Cloud Free-Tier: [`TASK-CLD-03-full-cloud-free-tier-architecture.md`](./TASK-CLD-03-full-cloud-free-tier-architecture.md)
- Đặc tả hạ tầng Docker: [`0006-docker-infrastructure-and-resource-spec.md`](../specs/0006-docker-infrastructure-and-resource-spec.md)
