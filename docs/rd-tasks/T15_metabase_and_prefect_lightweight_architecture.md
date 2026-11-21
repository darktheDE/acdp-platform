# T15: Đánh giá Vai trò Metabase & Kiến trúc Tối ưu Prefect UI (2026)

> **Mã tài liệu**: `T15` | **Ngày**: 2026-11-21 | **Phạm vi**: Phase 1 (TLCN) & Phase 2 (KLTN)  
> **Tham chiếu**: [docker-compose.yml](../../docker-compose.yml), [0006-docker-infrastructure-and-resource-spec.md](../specs/0006-docker-infrastructure-and-resource-spec.md)

---

## 1. Có cần Metabase khi Web Portal đã có Dashboard?

**Kết luận ngắn**: **Không cần bật thường trực cho người dùng cuối**, nhưng **nên giữ ở profile tách biệt (`--profile bi`)** cho mục đích kiểm định dữ liệu nội bộ (Data Engineering) và demo nhanh ad-hoc SQL.

| Tiêu chí | Web Dashboard (`Next.js 16 + Recharts`) | Metabase (`--profile bi`, cổng `:3001`) |
| :--- | :--- | :--- |
| **Đối tượng chính** | Sinh viên, Giảng viên, Quản trị viên (End-user) | Kỹ sư dữ liệu (DE), Hội đồng kiểm tra ad-hoc |
| **Nguồn dữ liệu** | FastAPI $\rightarrow$ DuckDB Gold `mart_*` (read-only) | Trực tiếp DuckDB Gold (`metabase-duckdb`) |
| **Khả năng tùy biến** | Toàn diện (Tailwind v4, dark mode, liên kết filter) | Cố định theo giao diện BI, khó đồng bộ UX |
| **Truy vấn ad-hoc** | Chỉ hỗ trợ các biểu đồ/filter đã lập trình sẵn | Viết SQL trực tiếp, slice-and-dice không cần code |
| **Chi phí tài nguyên** | `~53 MiB` (`acdp-web`) + `~128 MiB` (`acdp-api`) | Tốn thêm JVM RAM (`~400–600 MiB`) khi bật |

**Khuyến nghị vận hành cho ACDP**:
- **Phase 1 (TLCN)**: Mặc định chỉ chạy `docker compose --profile core up -d` (`~235 MiB` tổng RAM). Chỉ bật `docker compose --profile bi up -d metabase` khi cần soi dữ liệu thô, viết SQL kiểm chứng Star Schema, hoặc xuất CSV nhanh.
- **Phase 2 (KLTN)**: Nếu đội ngũ vận hành cần báo cáo nội bộ (tỷ lệ crawl lỗi theo domain, chi phí token LLM theo ngày), dùng Metabase cho internal ops và giữ Next.js + Recharts cho student/faculty portal.

---

## 2. Tối ưu Prefect UI nặng: 3 Phương án Kiến trúc (2026)

Trong `docker-compose.yml`, container `prefect-server` (`--profile pipeline`) chạy cả API + UI + PostgreSQL metadata riêng, gây tốn RAM không cần thiết cho quy mô 5–10 cuộc thi (TLCN).

### Phương án A: Chạy Ephemeral Local (Không bật Prefect Server) — *Khuyến nghị cho TLCN*
- Prefect 3.x cho phép chạy `@flow` trực tiếp như hàm Python thuần (`uv run python src/acdp/flows/medallion_pipeline.py`) với ephemeral SQLite/API tạm thời.
- **Ưu điểm**: `0 MiB` RAM nền khi không chạy pipeline; giữ nguyên retry, logging, và cấu trúc `@task`/`@flow` của Prefect.
- **Nhược điểm**: Không có UI lịch sử tập trung nếu chạy nhiều máy.

### Phương án B: GitHub Actions Scheduled Workflow (Serverless Cron) — *Khuyến nghị cho tự động hóa nhẹ*
- Dùng **GitHub Actions** (`on: schedule` + `workflow_dispatch`) chạy trực tiếp `uv run python src/acdp/flows/medallion_pipeline.py` trên runner `ubuntu-latest` miễn phí, đẩy kết quả Bronze/Silver/Gold lên **Cloudflare R2** và **Qdrant Cloud** qua GitHub Secrets.
- **Ưu điểm**: Loại bỏ hoàn toàn `prefect-server` khỏi máy local/VPS; có sẵn log chạy, badge trạng thái và nút *Run workflow* thủ công trên GitHub.
- **Nhược điểm**: Giới hạn thời gian chạy mỗi job (tối đa 6 giờ trên public/standard runner, thừa đủ cho 5–20 cuộc thi).

### Phương án C: Prefect Cloud (Free Tier) + Git Pull Step (`prefect.yaml`) — *Khuyến nghị cho KLTN*
- Dùng **Prefect Cloud** làm Control Plane (UI, lịch sử run, schedule, webhook) thay cho self-hosted `prefect-server`.
- Cấu hình `prefect.yaml` với `prefect.deployments.steps.git_clone` và deploy metadata qua GitHub Actions (`prefect deploy --all` khi push lên `main` với `PREFECT_API_KEY`, `PREFECT_API_URL`).
- Worker chỉ cần chạy nhẹ khi cần (`prefect worker start --pool ...`) hoặc dùng serverless work pool.
- **Ưu điểm**: Có đầy đủ Prefect UI, observability và retry phân tán mà không tốn RAM self-host server.

---

## 3. Ma trận Quyết định cho ACDP

| Giai đoạn | Giải pháp Orchestration | Giải pháp BI |
| :--- | :--- | :--- |
| **Phase 1 (TLCN)** | **Phương án A** (chạy script Python `@flow` on-demand) hoặc **Phương án B** (GitHub Actions `workflow_dispatch` / cron) | `Next.js 16 + Recharts` làm chính; `Metabase` chỉ bật tạm qua `--profile bi` khi debug SQL |
| **Phase 2 (KLTN)** | **Phương án C** (Prefect Cloud + `prefect.yaml` git pull + GitHub Actions CI/CD) | `Next.js 16` cho người dùng cuối + `Metabase` cho internal ops/DE |
