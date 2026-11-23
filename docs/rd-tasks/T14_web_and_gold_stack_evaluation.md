# T14: Đánh Giá Tech Stack Web Application, OLTP Backend & Gold Layer Star Schema (2026–2027)

> **Task ID**: `TASK-W101` | **Notion Mapping**: [`NT-023`](../tasks/notion-task-mapping.md)
> **Người thực hiện**: Đỗ Kiến Hưng (`@darktheDE`) & Nguyễn Văn Quang Duy (`@QuangDuyReal`)
> **Mốc tham chiếu công nghệ**: Q4/2026 – 2027 (`DIR-012`, `DIR-015`, `DIR-016`)
> **Học phần & Đơn vị**: Tiểu luận Chuyên ngành Kỹ thuật Dữ liệu, Khoa CNTT, Trường Đại học Công nghệ Kỹ thuật TP.HCM (HCM-UTE)

---

## 1. Why this task exists ?

Giai đoạn 1 của dự án ACDP (Tiểu luận Chuyên ngành, TLCN) đã hoàn thiện chuỗi xử lý Bronze và Silver với 17 nguồn mục tiêu thu thập được 18 bản ghi cuộc thi học thuật hợp lệ tại `data/extractions/extractions_2026-11-15_1794720683.json` và lớp tìm kiếm ngữ nghĩa RAG trên Qdrant (`src/acdp/3_ingest_to_qdrant.py`). Tuy nhiên, lớp phục vụ người dùng cuối (Web Application) và tầng phân tích dữ liệu (Gold Layer) vẫn tồn tại 4 điểm nghẽn kỹ thuật cần nghiên cứu và chuẩn hóa trước khi viết mã nguồn ứng dụng (`apps/web/`, `src/acdp/api/`):

1. **Tầng Gold (`src/acdp/4_analytics_gold.py`) chưa đạt chuẩn Data Engineering.** Mã nguồn hiện tại tạo các bảng phẳng mang tính mô phỏng Silver, thiếu tách biệt Dimension/Fact theo mô hình Kimball Star Schema, làm mất dữ liệu `timeline_stages` và `partners_and_sponsors`, đồng thời dính lỗi nhân đôi tổng giá trị giải thưởng khi thực hiện `unnest(category)`.
2. **Thiếu ranh giới OLTP và OLAP.** Việc ghép dữ liệu đăng nhập thí sinh, phiên trò chuyện RAG hoặc bookmark cuộc thi trực tiếp vào DuckDB sẽ gây khóa ghi file (single-writer lock) và xung đột mô hình giao dịch.
3. **Cần kiểm chứng tính tối ưu của ngăn xếp Web đã chốt tại `DIR-016`.** Nhóm cần ma trận đối sánh định lượng cho bộ công nghệ **Next.js 16 (Active LTS) + TypeScript + Tailwind CSS v4 + Recharts + FastAPI + PostgreSQL 18 + DuckDB** đặt cạnh các phương án thay thế năm 2026–2027.
4. **Ràng buộc phần cứng máy trạm 16GB RAM.** Theo mục 4.1 của `BaoCao_TieuLuan_ChuyenNganh_KTDL.md`, môi trường phát triển chạy trên máy Intel Core i7-13700H, 16GB RAM, 512GB NVMe SSD. Toàn bộ cụm dịch vụ lõi khi chạy đồng thời phải kiểm soát bộ nhớ trong ngưỡng cho phép (`<= 2.0 GB` RAM cho Docker core profile).

---

## 2. What should I do ?

### PHẦN I: Đối sánh Kỹ thuật Lớp Vàng (Kimball Star Schema vs Flat/OBT)

Ở quy mô TLCN (18 cuộc thi, mở rộng lên hàng trăm cuộc thi ở KLTN), bảng phẳng One Big Table (OBT) tuy viết truy vấn đơn giản cho một số biểu đồ đơn lẻ nhưng phát sinh hai khuyết tật nghiêm trọng trong ngữ cảnh ngành Kỹ thuật Dữ liệu:

1. **Lỗi Fan-out Aggregation trên quan hệ N-N.** Một cuộc thi thuộc nhiều lĩnh vực (`category` là danh sách) hoặc có nhiều nhà tổ chức (`organizers`). Khi `unnest()` trực tiếp trên OBT rồi tính `SUM(total_prize_vnd)` theo nhóm ngành, tổng giá trị giải thưởng bị cộng lặp theo số lượng danh mục.
2. **Thiếu cấu trúc chuẩn hóa cho hội đồng KTDL.** Đánh giá đồ án chuyên ngành Kỹ thuật Dữ liệu yêu cầu minh họa rõ Grain của bảng Fact, Surrogate Keys (`*_sk`), Slow/Fast Attributes ở Dimension và Bridge Table với trọng số phân bổ (`allocation_weight`).

| Tiêu chí so sánh | Flat Table / OBT (`4_analytics_gold.py` cũ) | Kimball Star Schema + Bridge + Marts (Đề xuất) |
| :--- | :--- | :--- |
| **Xử lý quan hệ 1-N (`prizes`, `timeline_stages`)** | Bỏ qua `timeline_stages`, gộp thô `prizes` | Tách thành `fact_prize_tiers` và `fact_timeline_stages` theo đúng grain |
| **Xử lý quan hệ N-N (`category`, `organizers`)** | `unnest()` trực tiếp gây phình số tiền khi `SUM()` | Dùng `bridge_competition_domain` với `allocation_weight = 1.0 / count` |
| **Chuẩn hóa thời gian học thuật** | Chỉ khớp chuỗi `____-__-__`, dồn sai định dạng vào `'Khác'` | `dim_date` chứa thuộc tính `academic_term` (`HK1`, `HK2`, `Hè`) và key `-1` (Unknown) |
| **Khả năng mở rộng sang KLTN** | Phải viết lại toàn bộ SQL khi thêm thuộc tính | Chỉ bổ sung Dimension hoặc cột mới, giữ nguyên hợp đồng `mart_*` cho API |
| **Chi phí thực thi trên DuckDB 1.5.x** | `< 2 ms` | `2–6 ms` cho 19–1.000 bản ghi nhờ columnar scan & view materialization |

**Kết luận phần I**: Áp dụng Kimball Star Schema (`4 dim_*`, `3 fact_*`, `2 bridge_*`) làm tầng lõi tính toán chính xác, sau đó phơi bày 6 Data Marts (`mart_*`) dạng bảng/view chuẩn hóa cho FastAPI và Metabase truy vấn trực tiếp.

---

### PHẦN II: Ma trận Đối sánh Ngăn xếp Web, Backend API & Cơ sở dữ liệu (2026–2027)

#### II.1. Cơ sở dữ liệu ứng dụng (OLTP App DB): PostgreSQL 18 vs Các lựa chọn khác

Phiên bản **PostgreSQL 18.7** (phát hành tháng 11/2026) kế thừa hàng loạt cải tiến I/O bất đồng bộ (Async I/O subsystem) và B-tree skip scan từ nhánh PostgreSQL 18. Bảng dưới đây đối sánh PostgreSQL 18 với các lựa chọn phổ biến cho tầng OLTP (`users`, `user_sessions`, `saved_competitions`, `chat_sessions`, `chat_messages`):

| Tiêu chí | PostgreSQL 18.7 (`postgres:18.7-alpine3.21`) | SQLite 3.x (Embedded file) | MySQL 8.4 LTS / 9.x | MongoDB 8.0 |
| :--- | :--- | :--- | :--- | :--- |
| **Tính toàn vẹn tham chiếu & ACID** | Đầy đủ (`FOREIGN KEY`, `CHECK`, `UNIQUE(user_id, competition_key)`) | Đầy đủ nhưng khóa ghi mức toàn file | Đầy đủ với InnoDB | Yếu với đa tài liệu, không tối ưu quan hệ chặt |
| **Xử lý đồng thời với Docker Web + Worker** | Đa tiến trình TCP qua `asyncpg` pool | Dễ gặp `database is locked` khi nhiều container ghi chung | Đa tiến trình TCP | Đa tiến trình TCP |
| **Hỗ trợ JSONB + Hybrid Text + Vector mở rộng** | Mạnh (`JSONB`, GIN index, `pg_trgm`) | Hạn chế hơn ở chế độ đồng thời | Kém linh hoạt hơn với `JSONB` indexing | Lưu document tốt nhưng dư thừa vì đã có Qdrant |
| **Giá trị học thuật & đồng bộ Prefect** | Chuẩn công nghiệp cho hệ thống Data Engineering | Chỉ phù hợp prototype đơn luồng | Ít phổ biến hơn Postgres trong hệ sinh thái AI/Data Python | Không cần thiết cho bảng user/bookmark quan hệ |
| **Mức tiêu thụ RAM (tinh chỉnh container)** | ~80–160 MB (giới hạn `256 MB`) | ~10 MB (nằm trong process API) | ~350–500 MB mặc định | ~400–600 MB mặc định |

**Ranh giới lưu trữ dữ liệu (Dual-Engine Separation)**:

1. **PostgreSQL 18 (OLTP)** chỉ giữ 5 bảng trạng thái người dùng và hội thoại. Tuyệt đối không nhân bản dữ liệu phân tích cuộc thi sang PostgreSQL để tránh sai lệch hai nguồn sự thật (split-brain).
2. **DuckDB 1.5.x (OLAP)** giữ toàn bộ dữ liệu phân tích Bronze/Silver/Gold dưới dạng `.duckdb` và `.parquet`, được FastAPI gắn kết ở chế độ `read_only=True`.
3. **Qdrant v1.13.4 (Vector DB)** giữ embeddings phục vụ tìm kiếm ngữ nghĩa RAG (`acdp_competitions`).

#### II.2. Backend API Framework: FastAPI vs Litestar vs Django Ninja vs Flask

| Tiêu chí | FastAPI (`fastapi[standard]`, Python 3.13) | Litestar 2.x | Django Ninja | Flask 3.1 |
| :--- | :--- | :--- | :--- | :--- |
| **Tích hợp sẵn với code lõi ACDP** | Dùng chung `Pydantic v2` của `src/acdp/schemas.py` | Tốt nhưng hệ sinh thái tài liệu ít hơn | Ép theo Django ORM, dư thừa khi dùng DuckDB + SQLModel | Không có OpenAPI/validation chuẩn nếu thiếu thư viện ngoài |
| **Sinh hợp đồng Spec-Driven (`OpenAPI 3.1`)** | Tự động xuất schema JSON chính xác từng kiểu Pydantic | Tự động | Tự động OpenAPI 3.1/3.0 | Phải ghép thêm plugin thủ công |
| **Hiệu năng Async cho RAG & SSE Streaming** | Bất đồng bộ gốc (ASGI/Uvicorn), hỗ trợ `StreamingResponse` mượt cho chatbot | Rất cao | Hỗ trợ async hạn chế hơn ở một số middleware | Mặc định WSGI đồng bộ, kém hơn khi stream LLM |
| **Độ nhẹ & thời gian học nhóm** | Nhẹ, chuẩn công nghiệp AI/Data tại Việt Nam | Đường cong học cao hơn | Nặng về boilerplate | Dễ phát sinh code thiếu kiểm soát kiểu |

#### II.3. Frontend Framework: Next.js 16 vs Vite React SPA vs Streamlit vs Evidence.dev

| Tiêu chí | Next.js 16 Active LTS (`16.4.6`, App Router) | Vite + React 19 SPA | Streamlit 1.x | Evidence.dev |
| :--- | :--- | :--- | :--- | :--- |
| **Thẩm mỹ UI/UX & Thương hiệu (`Logo`, Tailwind v4)** | Tùy biến hoàn toàn giao diện sản phẩm chuyên nghiệp | Tùy biến hoàn toàn | Giao diện đóng khung, khó thiết kế UX cổng sinh viên | Chỉ tối ưu cho báo cáo BI tĩnh dạng Markdown |
| **Bảo mật & SSR/RSC cho Dashboard** | Server Components ẩn chi tiết gọi nội bộ backend, `output: "standalone"` gọn nhẹ | Toàn bộ mã và logic gọi API chạy phía client | Reruns toàn script Python mỗi tương tác, giật lag | Không phù hợp luồng Auth + Bookmark + Chat đa phiên |
| **Phân tách vai trò Student & Lecturer** | Dễ chia Route Groups `(student)` và `(analytics)` | Tốt nhưng thiếu tối ưu SEO/SSR | Không tách được trải nghiệm cổng người dùng chuẩn | Không hỗ trợ chatbot RAG tương tác |
| **Kích thước Docker Image (`standalone`)** | ~140–180 MB trên `node:22.14-alpine3.21` | ~40 MB (Nginx tĩnh) nhưng mất SSR/BFF | ~600–900 MB kèm Python runtime | ~300 MB |

#### II.4. Thư viện Biểu đồ: Recharts vs ECharts vs Chart.js vs Tremor

| Tiêu chí | Recharts (`v2.15+ / v3`) | Apache ECharts (`echarts-for-react`) | Chart.js (`react-chartjs-2`) | Visx / D3 thuần |
| :--- | :--- | :--- | :--- | :--- |
| **Mô hình lập trình React** | Component khai báo JSX (`<BarChart>`, `<Tooltip />`), thân thiện TypeScript | Dạng cấu hình JSON khổng lồ (`option`), khó kiểm tra kiểu tĩnh | Dạng Canvas, khó tùy biến Tooltip JSX phức tạp | Rất mạnh nhưng tốn nhiều công sức viết trục và chú giải |
| **Dung lượng Bundle & Tải trình duyệt** | Nhẹ hơn ECharts trọn bộ, chỉ import đúng biểu đồ cần dùng (tree-shaking tốt) | Bundle nặng hơn (~300KB+ gzip nếu không tách module cẩn thận) | Nhẹ nhưng Canvas mờ trên màn Retina nếu thiếu DPI scaling | Nhẹ nhưng đòi hỏi nhiều code |
| **Đáp ứng Dashboard ACDP (5–6 biểu đồ cốt lõi)** | Đủ Bar, Composed (Line+Bar), Area, Pie/Donut, Scatter/Treemap + Tooltip tùy biến | Dư thừa tính năng 3D/Geo chưa cần ở TLCN | Thiếu linh hoạt khi gắn nút filter hoặc link cuộc thi ngay trong Tooltip | Chậm tiến độ Sprint Web |
| **Khả năng truy cập & Tailwind CSS v4** | Render SVG trực tiếp, đọc CSS variables (`--chart-1..5`) dễ dàng cho Light/Dark mode | Cần hàm JS đọc lại CSS tokens mỗi khi đổi theme | Canvas không ăn CSS tokens trực tiếp bằng biến `:root` | Tốt nhưng code dài dòng |

---

### PHẦN III: Tính khả thi Hạ tầng trên Máy trạm 16GB RAM

Hệ thống vận hành theo nguyên lý **Profile-based Docker Compose** để tránh bật đồng thời các dịch vụ không cần thiết trong lúc lập trình Web:

| Profile / Dịch vụ | Vai trò | Memory Limit | Dự kiến RAM thực tế | Ghi chú vận hành |
| :--- | :--- | :---: | :---: | :--- |
| `core`: `postgres` (`18.7-alpine3.21`) | OLTP App DB | `256 MB` | `~90 MB` | Bật `-c shared_buffers=128MB -c work_mem=4MB` |
| `core`: `qdrant` (`v1.13.4`) | Vector Store RAG | `512 MB` | `~180 MB` | Tập dữ liệu TLCN ~18 cuộc thi tốn rất ít RAM |
| `core`: `api` (`FastAPI + DuckDB RO`) | Serving Gateway | `640 MB` | `~220 MB` | DuckDB ép `memory_limit='256MB'`, `threads=2` |
| `core`: `web` (`Next.js 16 standalone`) | Frontend UI/UX | `512 MB` | `~160 MB` | Node heap giới hạn `--max-old-space-size=384` |
| **Tổng Profile `core` (Chạy Web hàng ngày)** | **4 container lõi** | **`1.92 GB`** | **`~650 MB – 1.1 GB`** | **An toàn cho máy 16GB RAM (dư >12GB cho IDE & OS)** |
| `bi`: `metabase` | Công cụ BI đối chiếu | `1024 MB` | `~750 MB` | Chỉ bật khi giảng viên/nhóm kiểm tra ad-hoc SQL |
| `pipeline`: `prefect-server` | Điều phối ETL | `512 MB` | `~320 MB` | Chỉ bật khi chạy batch crawl/Gold refresh |

---

## 3. Expect result

1. Thống nhất tài liệu nghiên cứu T14 làm căn cứ học thuật cho Chương Công nghệ & Kiến trúc trong Tiểu luận Chuyên ngành (`BaoCao_TieuLuan_ChuyenNganh_KTDL.md`).
2. Chốt ranh giới tách bạch giữa 3 cơ sở dữ liệu (`DuckDB` OLAP RO, `PostgreSQL 18` OLTP, `Qdrant` Vector) trước khi bước vào các bản đặc tả kỹ thuật `SPEC-0003` đến `SPEC-0006`.
3. Xác nhận khả năng vận hành toàn bộ cụm Web + API + DB + Vector trong hạn mức `<= 2.0 GB` RAM trên máy trạm phát triển 16GB RAM.

---

## 4. Cross-Review & Approval Checklist

Mục tiêu của danh mục kiểm tra dưới đây nhằm phục vụ phiên phản biện nội bộ (Peer Defense theo `DIR-011`) giữa Đỗ Kiến Hưng và Nguyễn Văn Quang Duy trước khi chuyển sang Sprint triển khai code (`Sprint Web 02`):

- [ ] **Câu hỏi phản biện 1 (Duy -> Hưng | OLTP vs OLAP Sync):** Khi một thí sinh nhấn "Lưu cuộc thi" (bookmark) lưu `competition_key` vào PostgreSQL, điều gì xảy ra nếu pipeline Gold làm mới dữ liệu và thay đổi tiêu đề hoặc xóa một cuộc thi cũ khỏi DuckDB? Phương án xử lý `competition_key` là URL hash bất biến (SHA-256) trong `SPEC-0003` và `SPEC-0004` đã đủ an toàn chưa?
- [ ] **Câu hỏi phản biện 2 (Hưng -> Duy | DuckDB Concurrency):** Ở môi trường local, nếu người dùng chạy `python -m src.acdp.4_analytics_gold` ghi đè file `acdp.duckdb` trong lúc container `api` đang mở kết nối `read_only=True`, DuckDB có ném lỗi khóa file không? Có cần cơ chế atomic swap hoặc đóng/mở kết nối theo từng request hoặc đọc qua Gold Parquet views không?
- [ ] **Câu hỏi phản biện 3 (Cả hai | Recharts vs Thư viện nhẹ hơn):** Trên trang `/dashboard`, kích thước JS bundle của các biểu đồ Recharts có làm chậm First Contentful Paint trên thiết bị sinh viên hay không, và ranh giới Server Component / `'use client'` tại `SPEC-0005` đã tối ưu chưa?
- [ ] **Xác nhận đồng thuận**: Ghi nhận chữ ký duyệt của `@darktheDE` và `@QuangDuyReal` trước khi tạo ADR chính thức cho ngăn xếp Web & Gold.
