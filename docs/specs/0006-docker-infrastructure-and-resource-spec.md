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
| `qdrant` | `qdrant/qdrant:latest` | `qdrant/qdrant:v1.13.4` | Vector Store cho RAG; khóa minor cố định tương thích `qdrant-client>=1.20` |
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

#### `Dockerfile.api` (FastAPI + DuckDB Read-Only + RAG Client)

```dockerfile
# syntax=docker/dockerfile:1
FROM python:3.13-slim-bookworm AS builder

COPY --from=ghcr.io/astral-sh/uv:0.6 /uv /uvx /bin/
WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    uv sync --frozen --no-dev --no-install-project

COPY src /app/src
COPY pyproject.toml uv.lock /app/

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

FROM python:3.13-slim-bookworm AS runtime
WORKDIR /app

RUN groupadd --gid 10001 appgroup && \
    useradd --uid 10001 --gid appgroup --shell /usr/sbin/nologin --no-create-home appuser

COPY --from=builder --chown=appuser:appgroup /app/.venv /app/.venv
COPY --from=builder --chown=appuser:appgroup /app/src /app/src

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

USER appuser
EXPOSE 8000

CMD ["uvicorn", "src.acdp.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

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

### 2.4. Bản thiết kế `docker-compose.yml` Mục tiêu (Sprint 02 Implementation Blueprint)

```yaml
services:
  postgres:
    image: postgres:18.7-alpine3.23
    container_name: acdp-postgres
    profiles: ["core"]
    restart: unless-stopped
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-acdp}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-acdp_local_dev_only}
      POSTGRES_DB: ${POSTGRES_DB:-acdp_app}
    command:
      - "postgres"
      - "-c"
      - "shared_buffers=128MB"
      - "-c"
      - "work_mem=4MB"
      - "-c"
      - "maintenance_work_mem=32MB"
      - "-c"
      - "max_connections=40"
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-acdp} -d ${POSTGRES_DB:-acdp_app}"]
      interval: 10s
      timeout: 5s
      retries: 5
    deploy:
      resources:
        limits:
          memory: 256M
          cpus: "0.50"

  qdrant:
    image: qdrant/qdrant:v1.13.4
    container_name: acdp-qdrant
    profiles: ["core"]
    restart: unless-stopped
    environment:
      QDRANT__STORAGE__PERFORMANCE__MAX_SEARCH_THREADS: "2"
    ports:
      - "6333:6333"
      - "6334:6334"
    volumes:
      - qdrant_data:/qdrant/storage
    healthcheck:
      test: ["CMD-SHELL", "bash -c 'exec 3<>/dev/tcp/127.0.0.1/6333 && printf \"GET /healthz HTTP/1.1\\r\\nHost: localhost\\r\\nConnection: close\\r\\n\\r\\n\" >&3 && grep -q \"200 OK\" <&3'"]
      interval: 15s
      timeout: 5s
      retries: 5
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: "0.75"

  api:
    build:
      context: .
      dockerfile: Dockerfile.api
    container_name: acdp-api
    profiles: ["core"]
    restart: unless-stopped
    depends_on:
      postgres:
        condition: service_healthy
      qdrant:
        condition: service_healthy
    environment:
      DATABASE_URL: postgresql+asyncpg://${POSTGRES_USER:-acdp}:${POSTGRES_PASSWORD:-acdp_local_dev_only}@postgres:5432/${POSTGRES_DB:-acdp_app}
      DUCKDB_DATABASE_PATH: /app/data/lakehouse/acdp.duckdb
      QDRANT_URL: http://qdrant:6333
      GEMINI_API_KEY: ${GEMINI_API_KEY:-}
    ports:
      - "8000:8000"
    volumes:
      - ./data/lakehouse:/app/data/lakehouse:ro
    healthcheck:
      test: ["CMD-SHELL", "python -c \"import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/health')\""]
      interval: 15s
      timeout: 5s
      retries: 5
    deploy:
      resources:
        limits:
          memory: 640M
          cpus: "1.00"

  web:
    build:
      context: ./apps/web
      dockerfile: Dockerfile
    container_name: acdp-web
    profiles: ["core"]
    restart: unless-stopped
    depends_on:
      api:
        condition: service_healthy
    environment:
      INTERNAL_API_URL: http://api:8000
      NEXT_PUBLIC_API_URL: http://localhost:8000
      NODE_OPTIONS: "--max-old-space-size=384"
    ports:
      - "3000:3000"
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: "0.75"

  metabase:
    image: ghcr.io/motherduckdb/metabase-duckdb:0.63.17-duckdb1.5.6.0
    container_name: acdp-metabase
    profiles: ["bi"]
    restart: unless-stopped
    environment:
      JAVA_TOOL_OPTIONS: "-Xmx768m -Xms256m"
      MB_DB_FILE: /metabase-data/metabase.db
    ports:
      - "3001:3000"
    volumes:
      - ./data/lakehouse:/data/lakehouse:ro
      - metabase_data:/metabase-data
    deploy:
      resources:
        limits:
          memory: 1024M
          cpus: "1.00"

  prefect-server:
    image: prefecthq/prefect:3-python3.11
    container_name: acdp-prefect
    profiles: ["pipeline"]
    command: prefect server start --host 0.0.0.0
    ports:
      - "4200:4200"
    volumes:
      - prefect_data:/root/.prefect
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: "0.50"

volumes:
  postgres_data:
  qdrant_data:
  metabase_data:
  prefect_data:
```

---

## 3. Core Processing Logic & Algorithms

### 3.1. Cơ chế Gắn Volume Read-Only cho Lakehouse

Container `api` và `metabase` gắn thư mục `./data/lakehouse` với cờ `:ro` (`read-only`). Thiết kế này bảo đảm không một lỗ hổng hoặc lỗi truy vấn nào ở tầng Web API hoặc BI có thể ghi đè hoặc làm hỏng tệp dữ liệu Vàng (`acdp.duckdb` và `gold/*.parquet`). Quyền ghi dữ liệu Lakehouse chỉ thuộc về tiến trình ETL chạy ở máy chủ host hoặc container worker thuộc profile `pipeline`.

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
4. **Kiểm định Tính bất biến Lakehouse:** Thực thi thử lệnh ghi tệp từ bên trong container `api` vào `/app/data/lakehouse/test_write` phải bị từ chối với lỗi `Read-only file system`.
