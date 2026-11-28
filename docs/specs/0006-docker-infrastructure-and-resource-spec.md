# SPEC-0006: Docker Infrastructure, Version Pinning & 16GB RAM Resource Budget

> **Task ID**: `TASK-W105` | **Task Registry**: [`NT-027`](../tasks/task-registry.md)
> **Status**: Implemented (Web Sprint 02)
> **Dependencies**: [`SPEC-0004`](./0004-serving-api-and-oltp-spec.md), [`SPEC-0005`](./0005-frontend-design-system-and-ux-spec.md), [`docker-compose.yml`](../../docker-compose.yml)
> **Target Files (Sprint 02 Implementation)**: `docker-compose.yml`, `Dockerfile.api`, `apps/web/Dockerfile`, `.dockerignore`

---

## 1. Objective & Scope

Tài liệu này đặc tả kiến trúc hạ tầng container hóa bằng **Docker Compose `v2.30+`** phục vụ toàn bộ ngăn xếp ACDP (Web Frontend Next.js 16, Backend API FastAPI, PostgreSQL 18.7 OLTP, Qdrant Vector DB, cùng tùy chọn Metabase BI và Prefect ETL) trên cấu hình máy trạm phát triển chuẩn của nhóm (**Intel Core i7-13700H, 16GB RAM, 512GB NVMe SSD**, trích Mục 4.1 `BaoCao_TieuLuan_ChuyenNganh_KTDL.md`).

Bốn mục tiêu bắt buộc của đặc tả hạ tầng gồm:
1. **Xóa bỏ hoàn toàn thẻ `:latest`:** Thay thế `qdrant/qdrant:latest` và `ghcr.io/motherduckdb/metabase-duckdb:latest` trong `docker-compose.yml` hiện tại bằng phiên bản khóa cứng (exact tag pinning).
2. **Phân lớp Compose Profiles (`core`, `local-backup`, `bi`, `pipeline`):** Mặc định profile `core` chỉ bật 3 dịch vụ (`postgres`, `api`, `web`) và kết nối trực tiếp **Qdrant Cloud** (`TASK-CLD-01`); tách Qdrant Docker vào `local-backup` (dự phòng khi Cloud gián đoạn), Metabase vào `bi`, và Prefect vào `pipeline`.
3. **Giới hạn ngân sách tài nguyên `<= 2.0 GB` RAM cho Profile `core`:** `core` tiêu thụ tối đa `1408M (~1.38 GB)` RAM (và `1920M` khi bật kèm `local-backup`), thi hành qua `deploy.resources.limits`.
4. **Đóng gói Multi-Stage & Non-Root:** Tối thiểu hóa dung lượng Docker Image và thu hẹp bề mặt tấn công bằng người dùng không đặc quyền (`appuser`, `nextjs`).

---

## 2. Data Contracts & Schemas

### 2.1. Bảng Khóa Phiên bản Image (Version Pinning Matrix)

| Dịch vụ | Trạng thái hiện tại (`docker-compose.yml`) | Thẻ khóa phiên bản chuẩn (`SPEC-0006`) | Vai trò & Lý do chọn |
| :--- | :--- | :--- | :--- |
| `postgres` | Chưa có | `postgres:18.7-alpine3.23` | OLTP App DB; biến thể Alpine giảm ~65% kích thước so với Debian |
| `qdrant` | `qdrant/qdrant:latest` | `qdrant/qdrant:v1.20.2` | Vector Store dự phòng (`local-backup`); đồng bộ minor `v1.20.x` với `qdrant-client>=1.20.0` (`RFC-0001`) |
| `api` (Runtime) | Chưa có | `python:3.13-slim-bookworm` | Thực thi FastAPI & DuckDB `1.5.x`; dùng `ghcr.io/astral-sh/uv:0.6` ở stage build |
| `web` (Runtime) | Chưa có | `node:22.14-alpine3.21` | Chạy Next.js 16 `output: "standalone"` tối giản dung lượng RAM & ổ đĩa |
| `metabase` | `ghcr.io/motherduckdb/metabase-duckdb:latest` | `ghcr.io/motherduckdb/metabase-duckdb:0.63.17-duckdb1.5.6.0` | Khớp phiên bản DuckDB `>=1.5.6` trong `pyproject.toml`, bật theo profile `bi` |
| `prefect-server` | `prefecthq/prefect:3-python3.11` | `prefecthq/prefect:3-python3.11` (khóa thêm `@sha256` khi pull) | Điều phối ETL batch, bật riêng theo profile `pipeline` |

### 2.2. Ngân sách RAM & CPU trên Máy trạm 16GB RAM

| Dịch vụ | Profile | Giới hạn RAM (`limits.memory`) | Giới hạn CPU (`limits.cpus`) | Mức tiêu thụ ước tính thực tế | Thiết lập tiết kiệm RAM bên trong container |
| :--- | :---: | :---: | :---: | :---: | :--- |
| `postgres` | `core` | `256M` | `0.50` | `80–130 MB` | `-c shared_buffers=128MB -c work_mem=4MB -c maintenance_work_mem=32MB -c max_connections=40` |
| `api` | `core` | `640M` | `1.00` | `180–300 MB` | DuckDB ép `SET memory_limit='256MB'`, `SET threads=2`; 1 worker Uvicorn ở local dev |
| `web` | `core` | `512M` | `0.75` | `120–220 MB` | `NODE_OPTIONS="--max-old-space-size=384"` |
| **Tổng Profile `core` (Cloud-First)** | **`core`** | **`1408M (~1.38 GB)`** | **`2.25 vCPU`** | **`380–650 MB`** | **Giảm 512 MB nhờ dùng Qdrant Cloud mặc định (`TASK-CLD-01`)** |
| `qdrant` | `local-backup` | `512M` | `0.75` | `150–250 MB` | `QDRANT__STORAGE__PERFORMANCE__MAX_SEARCH_THREADS=2` (bật khi `QDRANT_MODE=local`) |
| `metabase` | `bi` | `1024M` | `1.00` | `650–850 MB` | `JAVA_TOOL_OPTIONS="-Xmx768m -Xms256m"` (Tắt mặc định; Cloud dùng MotherDuck Lite theo `TASK-CLD-02`) |
| `prefect-server` | `pipeline` | `512M` | `0.50` | `250–350 MB` | Tắt mặc định; chỉ bật khi kiểm thử lịch trình ETL |

### 2.3. Kiến trúc Docker Multi-Stage & Non-Root

#### `Dockerfile.api` (FastAPI + DuckDB `httpfs` + RAG Client)

Xem tệp triển khai chuẩn tại [`Dockerfile.api`](../../Dockerfile.api): chạy non-root `UID 1000` (`appuser`), cài sẵn DuckDB `httpfs` extension ở build/runtime (`DUCKDB_EXTENSION_DIRECTORY=/app/.duckdb`), khóa `DUCKDB_MEMORY_LIMIT=256MB`, `DUCKDB_THREADS=2`, bật `GOLD_MART_CACHE_ENABLED=true`, và hỗ trợ động `PORT=${PORT:-7860}` cho HF Spaces / Koyeb / Render / Docker local (`8000`).

#### `apps/web/Dockerfile` (Next.js 16 `output: "standalone"`)

Yêu cầu tệp `apps/web/next.config.ts` khai báo `output: "standalone"` để `next build` tự trích xuất tập phụ thuộc tối thiểu vào `.next/standalone`, loại bỏ toàn bộ `node_modules` phát triển khỏi runtime image:

```dockerfile
# syntax=docker/dockerfile:1
FROM node:22.14-alpine3.21 AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund

FROM node:22.14-alpine3.21 AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

FROM node:22.14-alpine3.21 AS runner
WORKDIR /app
ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    PORT=3000 \
    HOSTNAME="0.0.0.0"

RUN addgroup --system --gid 10002 nodejs && \
    adduser --system --uid 10002 nextjs

COPY --from=builder --chown=nextjs:nodejs /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs
EXPOSE 3000

CMD ["node", "server.js"]
```

#### `.dockerignore` (Kiểm soát Build Context `< 5 MB`)

```gitignore
.git
.venv
__pycache__
*.pyc
.pytest_cache
.ruff_cache
.scratchpad
data/lakehouse
data/raw
data/extractions
node_modules
apps/web/.next
.env
*.duckdb
*.parquet
```

### 2.4. Cấu trúc `docker-compose.yml` Chuẩn hóa (Đồng bộ theo `DIR-021`, `ADR-0002`, `RFC-0001`)

Cấu hình chuẩn tại [`docker-compose.yml`](../../docker-compose.yml) phân tách thành 4 profile (`core`, `local-backup`, `bi`, `pipeline`) và loại bỏ hoàn toàn mount đĩa `./data/lakehouse`:

| Dịch vụ | Profile | Image / Build | Giới hạn RAM | Kết nối & Ghi chú kiến trúc |
| :--- | :---: | :--- | :---: | :--- |
| `postgres` | `core` | `postgres:18.7-alpine3.23` | `256M` | OLTP local dự phòng (hoặc dùng Supabase Cloud qua `POSTGRES_MODE=auto`) |
| `api` | `core` | `Dockerfile.api` | `640M` | Đọc Gold Parquet trực tiếp từ Cloudflare R2 qua `httpfs` (`BUCKET_NAME`, `AWS_*`); không phụ thuộc container `qdrant` local |
| `web` | `core` | `apps/web/Dockerfile` | `512M` | Next.js 16 standalone (`NODE_OPTIONS="--max-old-space-size=384"`) |
| `qdrant` | `local-backup` | `qdrant/qdrant:v1.20.2` | `512M` | Vector backup local khi `QDRANT_MODE=local`; mặc định dùng Qdrant Cloud Free |
| `metabase` | `bi` | `ghcr.io/motherduckdb/metabase-duckdb:0.63.17-duckdb1.5.6.0` | `1024M` | Kết nối trực tiếp Cloudflare R2 qua biến môi trường S3/R2 (port `3001:3000`) |
| `prefect-server` | `pipeline` | `prefecthq/prefect:3-python3.11` | `512M` | Tắt mặc định; chỉ bật khi kiểm thử điều phối batch cục bộ |

---

## 3. Core Processing Logic & Algorithms

### 3.1. Truy vấn Lakehouse R2 Không Ghi Đĩa Cục Bộ (`DIR-021`, `RFC-0001`)

Theo `DIR-021` và `ADR-0002`, container `api` và `metabase` không gắn volume `./data/lakehouse` mà đọc trực tiếp Gold Parquet (`s3://{BUCKET_NAME}/gold/*.parquet`) trên Cloudflare R2 thông qua DuckDB `httpfs` và biến môi trường R2 (`AWS_ENDPOINT_URL`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`). Tầng ứng dụng chỉ đọc ở mức HTTP/S3 read-only với tài khoản R2 phân quyền tối thiểu.

### 3.2. Phân giải Cổng (Port Allocation) Tránh Xung đột

Do Next.js 16 giữ cổng mặc định `3000` ở chế độ `core`, dịch vụ `metabase` thuộc profile `bi` được chuyển ánh xạ host port sang `3001:3000` (so với cổng `3000` cũ trong `docker-compose.yml`), triệt tiêu hoàn toàn lỗi xung đột cổng khi người dùng muốn bật cả Web lẫn Metabase để đối chiếu số liệu cùng lúc.

### 3.3. Khởi động và Điều khiển theo Ngữ cảnh Công việc

1. Chạy phát triển Web hàng ngày dùng Qdrant Cloud (`core`): `docker compose --profile core up -d --build`
2. Chạy luồng dự phòng Full Local Backup (`core` + `local-backup`): `$env:QDRANT_MODE="local"; docker compose --profile core --profile local-backup up -d`
3. Bật tạm Metabase local kiểm định Star Schema hoặc demo offline (`core` + `bi`, xem [`T15`](../rd-tasks/T15_metabase_and_prefect_lightweight_architecture.md)): `docker compose --profile core --profile bi up -d` (kèm `uv run python -m acdp.v2.gold_star_schema --metabase-sql`)
4. Xem mức RAM thực tế của từng container: `docker stats --no-stream --format "table {{.Name}}\t{{.MemUsage}}\t{{.MemPerc}}\t{{.CPUPerc}}"`

---

## 4. Error Handling & Edge Cases

| Tình huống biên | Nguyên nhân | Cách phòng tránh & Xử lý |
| :--- | :--- | :--- |
| **EC-D1: `api` khởi động trước khi `postgres` nhận kết nối** | Postgres 18 đang chạy `initdb` lần đầu | Dùng `depends_on` kết hợp `condition: service_healthy` dựa trên `pg_isready` |
| **EC-D2: Context build Docker quá lớn (> 500 MB)** | Bị kéo nhầm `.venv/`, `node_modules/`, `data/` vào build daemon | Tệp `.dockerignore` loại bỏ triệt để toàn bộ thư mục phụ thuộc cục bộ và dữ liệu lakehouse |
| **EC-D3: WSL2 trên Windows ăn hết RAM hệ thống** | Docker Desktop mặc định dùng bộ nhớ đệm không giới hạn | Giới hạn tổng container `core` ở mức `1920M` và khuyến nghị `.wslconfig` giới hạn `memory=6GB` |
| **EC-D4: Lệnh `healthcheck` bên trong `slim-bookworm` thiếu `curl`** | Image Debian slim lược bỏ `curl` và `wget` | Dùng trực tiếp trình thông dịch `python -c "import urllib.request..."` sẵn có trong container `api` |
| **EC-D5: Metabase tranh cổng `3000` với Next.js 16** | Hai dịch vụ cùng khai báo host port `3000` | Chuyển host port của `metabase` sang `3001:3000` và tách vào profile `bi` |

---

## 5. Verification & Acceptance Criteria

1. **Kiểm tra cú pháp Compose (`docker compose config`):** Lệnh `docker compose --profile core config` hoàn thành với mã thoát `0`, không còn bất kỳ thẻ `:latest` nào trong danh sách image đã phân giải.
2. **Định mức Build Context & Image Footprint:** Build thành công `Dockerfile.api` và `apps/web/Dockerfile`; ngữ cảnh truyền lên Docker daemon `< 5 MB` (kiểm chứng qua `.dockerignore`).
3. **Kiểm định Trần Bộ nhớ thực tế (`docker stats`):** Khi bật toàn bộ 4 container của profile `core` (`postgres`, `qdrant`, `api`, `web`) và thực thi tải truy vấn `/dashboard`, tổng RAM đo được qua `docker stats --no-stream` không vượt quá `2.0 GB`.
4. **Kiểm định Không Lưu Lakehouse Cục bộ (`DIR-021`):** Kiểm tra `docker compose --profile core config` xác nhận container `api` không gắn volume `./data/lakehouse` và cấu hình đầy đủ biến môi trường R2 (`BUCKET_NAME`, `AWS_ENDPOINT_URL`).
