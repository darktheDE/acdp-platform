# ADR-0002: Kiến trúc Đồng bộ 100% Cloud Free-Tier, Phân tách PA-1 Serving (FastAPI + DuckDB httpfs) và Cloud BI (MotherDuck Lite)

- **Status**: Accepted & Active — Supersedes [`ADR-0001`](./0001-medallion-lakehouse-and-rag-stack.md) Deployment & Serving Topology
- **Date**: 2026-11-23
- **Authors**: Đỗ Kiến Hưng (`@darktheDE`), Nguyễn Văn Quang Duy (`@QuangDuyReal`)
- **Scientific Advisor**: ThS. Trần Quang Khải
- **Institution**: Khoa Công nghệ Thông tin, Trường Đại học Công nghệ Kỹ thuật TP.HCM (HCM-UTE)
- **Related Tasks & Specs**: [`TASK-CLD-01`](../deliverables/TASK-CLD-01-qdrant-cloud-and-local-backup-architecture.md), [`TASK-CLD-02`](../deliverables/TASK-CLD-02-web-dashboard-vs-metabase-boundary.md), [`TASK-CLD-03`](../deliverables/TASK-CLD-03-full-cloud-free-tier-architecture.md), [`SPEC-0004`](../specs/0004-serving-api-and-oltp-spec.md), [`SPEC-0006`](../specs/0006-docker-infrastructure-and-resource-spec.md)

---

## 1. Bối cảnh và vấn đề kiến trúc

Trong giai đoạn Web Sprint 02 ([`SPEC-0006`](../specs/0006-docker-infrastructure-and-resource-spec.md)), hệ thống ACDP vận hành theo mô hình lai (Hybrid Local–Cloud). Ba tầng lưu trữ Lakehouse (Bronze, Silver, Gold) đã chạy trên Cloudflare R2 theo chỉ thị `DIR-021`, nhưng 6 dịch vụ tính toán và cơ sở dữ liệu gồm PostgreSQL 18 (`256 MB`), Qdrant (`512 MB`), FastAPI + DuckDB (`640 MB`), Next.js 16 (`512 MB`), Metabase (`1024 MB`) và Prefect Server (`512 MB`) vẫn phụ thuộc vào Docker Desktop cục bộ trên máy trạm `16 GB RAM`.

Theo góp ý của Giảng viên hướng dẫn ThS. Trần Quang Khải, dữ liệu cuộc thi học thuật mang tính công khai, không chịu ràng buộc bảo mật doanh nghiệp. Việc duy trì tầng phục vụ ở máy trạm cá nhân gây ra ba điểm nghẽn: sai lệch trạng thái OLTP và Vector giữa hai thành viên, phụ thuộc cấu hình máy cá nhân khi trình diễn, và thiếu địa chỉ công khai thường trực cho sinh viên dùng thử. Do đó, nhóm cần ban hành quyết định kiến trúc chính thức để đồng bộ toàn bộ hệ thống lên môi trường **100% Cloud Free-Tier** ở chi phí **0 USD/tháng**, bảo đảm vận hành thông suốt từ Tiểu luận chuyên ngành (TLCN: `5–20` cuộc thi) đến Khóa luận tốt nghiệp (KLTN: `100–500` cuộc thi, `500–1.000` sinh viên).

---

## 2. Biên bản phản biện nội bộ (`DIR-011`): PA-1 vs PA-2 vs PA-3

Thực hiện quy trình phản biện hai giai đoạn theo `DIR-011`, hai tác giả Đỗ Kiến Hưng và Nguyễn Văn Quang Duy đã đối chiếu ba phương án kiến trúc cho tầng Serving API và Query Engine từ hồ sơ [`TASK-CLD-03`](../deliverables/TASK-CLD-03-full-cloud-free-tier-architecture.md):

| Tiêu chí phản biện | PA-1: Giữ FastAPI + DuckDB `httpfs` + TTL Cache | PA-2: Gộp vào Next.js Route Handlers BFF + Supabase | PA-3: Viết lại sang Rust (`Axum` + `DataFusion`) |
| :--- | :--- | :--- | :--- |
| Tái sử dụng mã nguồn | Tái sử dụng 100% `src/acdp/api/` (5 router) và `Pydantic v2` | Phải viết lại toàn bộ route, auth JWT và RAG từ Python sang TypeScript | Phải viết lại toàn bộ backend và pipeline sang Rust |
| Hỗ trợ Kimball Star Schema | Hỗ trợ đầy đủ Star Join (`9` bảng Core) và `6` OBT `mart_*` | `hyparquet` không có SQL JOIN; `@duckdb/node-api` dễ vượt trần `250 MB` | Hỗ trợ SQL nhưng thiếu hệ sinh thái RAG/LLM trưởng thành như Python |
| Độ trễ & bộ nhớ đệm | In-Memory TTL Cache (`5–15 phút`) giữ `< 20 ms` warm, giảm `> 95%` `httpfs` | Serverless function mất cache RAM sau mỗi cold start | Thấp (`~40 MB` RAM), nhưng tốc độ phát triển tính năng chậm 3–5 lần |
| Đích triển khai `$0/tháng` | HF Spaces Docker (`16 GB RAM`, `:7860`) hoặc Koyeb/Render (`512 MB`, `:8000`) | Vercel Hobby (`100 GB` transfer, `1M` invocations) | Koyeb Eco / Render Free (`512 MB RAM`) |
| Phán quyết đồng thuận | **Chấp thuận (Selected)** | Lưu làm phương án tối giản dự phòng | **Bác bỏ chuyển đổi toàn phần** |

### Kết luận phản biện tầng Serving (PA-1 Multi-Target Low-Footprint)

Hai tác giả thống nhất chọn **PA-1 (Giữ FastAPI + DuckDB `httpfs` + In-Memory TTL Cache)** với năm luận cứ kỹ thuật:
1. Bảo toàn toàn bộ mã nguồn `src/acdp/api/`, bộ kiểm thử `pytest` và hợp đồng OpenAPI 3.1 (`SPEC-0004`), tập trung nguồn lực cho Cycle 08 (`TASK-SRV-01..04`: Hồ sơ Mini-CV, Ghép đội OLTP, Team Summary và RAG cá nhân hóa).
2. Giữ nguyên nhân DuckDB `httpfs` (`read_only=True`) để chứng minh năng lực Kỹ thuật Dữ liệu trên mô hình Star Schema và Data Marts, tránh phụ thuộc vào thư viện đọc phẳng không hỗ trợ JOIN.
3. Khắc phục rủi ro giới hạn tài khoản Docker Space trên Hugging Face: kiểm chứng chính sách năm 2026 cho thấy tài khoản Free có thể bị hạn chế quyền tạo mới Docker Space nếu chưa nâng gói PRO (`$9/tháng`), trong khi phần cứng CPU Basic (`2 vCPU`, `16 GB RAM`) vẫn miễn phí giờ chạy cho tài khoản đủ điều kiện. Vì vậy, `Dockerfile.api` được thiết kế theo chuẩn **Low-Footprint đa đích** (`DUCKDB_MEMORY_LIMIT=256MB`, `threads=2`, 1 Uvicorn worker, biến môi trường `PORT` hỗ trợ cả `7860` của HF Spaces lẫn `8000` của Koyeb Eco / Render Free `512 MB RAM`).
4. Triệt tiêu độ trễ mạng R2 lặp lại bằng lớp **In-Memory TTL Cache (`5–15 phút`)** cho 6 bảng `mart_*`, giữ độ trễ warm `< 20 ms` thay vì `182,9 ms` cold.
5. Duy trì cấu trúc phân tách rõ ràng: Next.js 16 trên Vercel Hobby đảm nhận SSR/UI và giao diện người dùng; FastAPI đảm nhận OLTP (`asyncpg`), OLAP (`duckdb httpfs`) và RAG (`qdrant-client` + `google-genai`/`litellm`).

---

## 3. Ma trận quyết định kiến trúc toàn hệ thống (TLCN đến KLTN)

| Thành phần hệ thống | Công nghệ chốt (ADR-0002) | Hạn mức Free Tier (2026) | Vai trò & Dự phòng (Failover) |
| :--- | :--- | :--- | :--- |
| Frontend Web Portal | Vercel Hobby (`Next.js 16 + Tailwind v4 + Recharts`) | `100 GB` transfer/tháng, `1M` invocations, `8 GB` build RAM | Giao diện công khai cho Sinh viên & Giảng viên; backup Cloudflare Workers |
| Serving Backend API | FastAPI + DuckDB `httpfs` + TTL Cache (Docker) | HF Spaces (`16 GB RAM`) hoặc Koyeb/Render (`512 MB RAM`) | Chạy theo chuẩn Low-Footprint `256 MB` DuckDB cap; giữ Docker local dự phòng |
| OLTP App Database | Supabase Free (PostgreSQL Managed) | `500 MB` DB, `5 GB` egress, `50.000 MAU` | Lưu Users, Auth, Bookmarks, `/profile`, `/teams`; backup sang Neon Free (`1 GB`) |
| Medallion Lakehouse | Cloudflare R2 (`DIR-021`) | `10 GB` lưu trữ, `1M` Class A, `10M` Class B, `$0` egress | Nguồn chân lý bất biến (SSOT): Bronze HTML, Silver Parquet, Gold 15 Parquets |
| Vector Database | Qdrant Cloud Free (`TASK-CLD-01`) | `1 GB RAM`, `4 GB Disk` (~750k vector 1024-dim) | Phục vụ Dual-Layer RAG (`v1.20.2` Docker backup `--profile local-backup`, RTO `< 60s`) |
| Embeddings & LLM | Workers AI (`@cf/baai/bge-m3`) + Gemini 3.5 Flash-Lite | `10.000 Neurons/ngày`; Gemini `10–15 RPM`, `500–1.500 RPD` | Fallback `LiteLLM` sang Groq / OpenRouter `:free`; embedding backup `fastembed` |
| Cloud BI Workbench | MotherDuck Lite Free (`TASK-CLD-02`) | `10 GB` storage, `10 CU-hours` Pulse/tháng, `3` users | Thay Metabase trên Cloud; đọc trực tiếp R2 Parquet không tốn quota `10 GB` |
| Pipeline & Keep-Alive | GitHub Actions (`ubuntu-latest`) | Unlimited phút (Public) / `2.000 phút/tháng` (Private) | Chạy Crawl/ETL định kỳ (KLTN), Keep-Alive 3 ngày và Weekly `pg_dump` |
| Email Service (KLTN) | Resend Free | `3.000 emails/tháng`, giới hạn cứng `100 emails/ngày` | Gửi thông báo cuộc thi mới theo `TASK-SRV-05` (`0 USD` hard-cap) |

---

## 4. Kiến trúc 3 tầng BI và cấu hình MotherDuck Lite Free

Kế thừa ranh giới phân tách trong [`TASK-CLD-02`](../deliverables/TASK-CLD-02-web-dashboard-vs-metabase-boundary.md), hệ thống vận hành 3 tầng phân tích dữ liệu trên nền **Two-Tier Gold Layer** (`15` tệp Parquet trên Cloudflare R2):

1. Tầng 1 — Customer-Facing Product Analytics (`Next.js 16 + Recharts` tại `/dashboard`): Kênh hiển thị duy nhất cho Sinh viên và Giảng viên trên Vercel Hobby, đọc 6 bảng `mart_*` qua FastAPI TTL Cache.
2. Tầng 2 — Cloud DataOps & Ad-hoc SQL Workbench (`MotherDuck Lite Free`): Thay thế hoàn toàn Metabase trên Cloud vì Metabase Cloud không có gói miễn phí (tối thiểu `$100/tháng`) và không hỗ trợ cài custom DuckDB driver. Kỹ sư dữ liệu khởi tạo kết nối bằng lệnh `uv run python -m acdp.v2.gold_star_schema --motherduck-sql` để tạo cơ sở dữ liệu `acdp_gold`, lưu khóa R2 bằng `CREATE OR REPLACE SECRET r2_secret IN MOTHERDUCK`, tạo `19` Views (`15` bảng Gold + `4` Virtual Views `gold_*`) và chạy `3` truy vấn kiểm toán **Data Quality Scorecard** cùng **Bridge Weighting Factor Invariant**.
3. Tầng 3 — On-Demand Local Self-Service BI (`Metabase Docker --profile bi`, cổng `:3001`): Tắt mặc định (`0 MB` RAM ở profile `core`) trong `docker-compose.yml`, chỉ bật tạm thời tại local khi cần trình diễn Self-Service BI hoặc dự phòng mất mạng tại phòng bảo vệ.

---

## 5. Quy tắc an toàn thẻ quốc tế 0 đồng (`0-Balance Card Guardrail`)

Nhóm tác giả áp dụng nguyên tắc chỉ sử dụng các dịch vụ không yêu cầu thẻ thanh toán hoặc có cơ chế ngắt cứng (`Hard-Cap`) ở mức `0 USD/tháng`. Hai dịch vụ bị loại bỏ vĩnh viễn khỏi kiến trúc gồm:
1. **Google Cloud Run Always Free**: Bắt buộc gắn Billing Account và không có công tắc tự ngắt cứng khi vượt ngưỡng miễn phí; lưu lượng tăng đột biến sẽ gây từ chối thanh toán trên thẻ 0 đồng và dẫn tới khóa tài khoản Google Cloud dây chuyền.
2. **Oracle Cloud PAYG**: Quá trình nâng cấp từ Always Free sang PAYG thực hiện giữ cọc tạm `~100 USD` và kiểm tra số dư định kỳ, không khả thi với thẻ quốc tế 0 đồng, trong khi bản Always Free thường xuyên hết tài nguyên ARM tại khu vực châu Á.

---

## 6. Cơ chế chống ngủ đông, sao lưu và kịch bản Demo Day

1. **Keep-Alive tự động hằng ngày (`TASK-CLD-06`, cập nhật theo `RFC-0001`)**: Workflow `.github/workflows/keep-alive.yml` chạy định kỳ mỗi ngày lúc `02:15 UTC` (`15 2 * * *`) nhằm ngăn chính sách ngủ đông và xóa dữ liệu của gói miễn phí (Qdrant Cloud suspend sau 7 ngày và xóa vĩnh viễn sau 28 ngày; Supabase pause sau 7 ngày; HF Spaces ngủ sau 48 giờ), kết hợp sao lưu `pg_dump` mỗi Chủ nhật lúc `02:30 UTC` (`30 2 * * 0`).
2. **Sao lưu và khôi phục thảm họa (RTO `< 60 giây`)**: Toàn bộ dữ liệu gốc và trung gian nằm bất biến trên Cloudflare R2 (`bronze/`, `silver/`, `gold/`). Nếu Qdrant Cloud gặp sự cố, lệnh `uv run python -m acdp.v2.rag_ingest` tái dựng toàn bộ vector từ `silver/markdown/` trong dưới 60 giây; dữ liệu OLTP Supabase được sao lưu hàng tuần qua `pg_dump --format=custom` và có thể chuyển sang Neon Free khi cần.
3. **Kịch bản bảo vệ Hội đồng (`T-15 phút`)**: Thực hiện quy trình Pre-warm trước giờ báo cáo 15 phút để đánh thức API Container, Supabase và Qdrant Cloud; đồng thời luôn chuẩn bị sẵn profile `--profile local-backup` trên laptop cá nhân làm phương án dự phòng offline nếu mạng phòng bảo vệ gặp sự cố.

---

## 7. Hệ quả kỹ thuật và ràng buộc thực thi

1. **Mở khóa `TASK-CLD-04`**: Cấu hình `AppConfig` kết nối Supabase PostgreSQL qua Transaction/Session Pooler (`asyncpg`, tắt `statement_cache_size` nếu dùng port `6543`) và xác nhận `duckdb_client.py` đọc 100% Gold Parquet từ `s3://` trên R2.
2. **Mở khóa `TASK-CLD-05`**: Đóng gói `Dockerfile.api` theo chuẩn Low-Footprint (`256 MB` DuckDB cap, TTL Cache cho `6` bảng `mart_*`), triển khai FastAPI lên HF Spaces (hoặc Koyeb/Render) và triển khai `apps/web` lên Vercel Hobby.
3. **Mở khóa `TASK-CLD-06`**: Thiết lập `.github/workflows/keep-alive.yml`, job sao lưu `pg_dump` hàng tuần và chuỗi `LiteLLM` fallback (`Gemini 3.5 Flash-Lite` $\rightarrow$ `Groq` $\rightarrow$ `OpenRouter :free`).

---

## 8. Nhật ký truy vấn và nguồn tham khảo kiểm chứng (`DIR-020`)

| STT | Câu lệnh truy vấn (`search_web`) | Mục đích kiểm chứng | Nguồn chính thức (URL) |
| :---: | :--- | :--- | :--- |
| 1 | `MotherDuck Lite free tier limits 2025 2026 DuckDB S3 R2 integration` | Xác nhận gói MotherDuck Lite (`$0`, `10 GB`, `10 CU-hrs`, `3` users) và BYOB R2 không tính vào quota | https://motherduck.com/pricing/ |
| 2 | `"MotherDuck" "CREATE SECRET" Cloudflare R2 endpoint s3 read_parquet SQL 2025 2026` | Kiểm chứng cú pháp `CREATE SECRET ... IN MOTHERDUCK` với Cloudflare R2 | https://motherduck.com/docs/integrations/cloud-storage/amazon-s3/ |
| 3 | `DuckDB "CREATE SECRET" "TYPE R2" ACCOUNT_ID vs "TYPE S3" MotherDuck IN MOTHERDUCK 2025 2026` | Đối chiếu `TYPE R2` (`ACCOUNT_ID`) và `TYPE S3` (`ENDPOINT`) trong MotherDuck | https://duckdb.org/docs/stable/extensions/httpfs/overview |
| 4 | `"Hugging Face Spaces" "CPU basic" free tier Docker requires PRO account 2025 2026` | Kiểm chứng chính sách Docker SDK & CPU Basic (`2 vCPU`, `16 GB RAM`) trên HF Spaces | https://huggingface.co/docs/hub/spaces-sdks-docker |
| 5 | `Hugging Face Spaces free tier CPU basic 2 vCPU 16GB RAM sleep 48 hours FastAPI Docker 2025 2026` | Xác nhận cổng mặc định `7860`, non-root `UID 1000` và chu kỳ ngủ đông | https://huggingface.co/docs/hub/spaces-overview |
