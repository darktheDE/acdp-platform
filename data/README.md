# Data Directory Architecture & Storage Conventions

> **Repository**: `acdp-platform` (Academic Competition Discovery Platform)  
> **Faculty**: Faculty of Information Technology, Ho Chi Minh City University of Technology and Engineering (HCM-UTE)  
> **Major**: Data Engineering (Kỹ thuật Dữ liệu)  
> **Related Specification**: [`docs/specs/0002-data-ingestion-and-schema-spec.md`](../docs/specs/0002-data-ingestion-and-schema-spec.md)

---

## 1. Overview & Directory Layout (Lean MVP Scale: 5–10 Competitions)

Thư mục `data/` là không gian lưu trữ dữ liệu cục bộ phục vụ quy trình phát triển, kiểm thử kịch bản cào web (`Crawl4AI`), và vận hành kiến trúc **Medallion Lakehouse** tinh gọn trên máy trạm cá nhân.

Trong giai đoạn **Tiểu luận chuyên ngành (TLCN)**, nhóm tập trung vào bộ dữ liệu nhỏ gồm **5–10 cuộc thi học thuật tiêu biểu** (hiện tại là 7 cuộc thi thực tế, dung lượng $< 1.5\text{ MB}$) để mô phỏng luồng dữ liệu và kiểm chứng tính khả thi kỹ thuật trước khi mở rộng quy mô tự động hóa ở giai đoạn Khóa luận tốt nghiệp (KLTN).

```text
data/
├── README.md                      # Tài liệu kiến trúc và quy ước lưu trữ dữ liệu
├── raw/                           # [TRACKED IN GIT] Dữ liệu mẫu 7 cuộc thi phục vụ kiểm thử
│   ├── html/                      # Snapshot HTML gốc từ các cổng thông tin cuộc thi
│   │   ├── .gitkeep
│   │   ├── codetour.org.html
│   │   ├── datadna.onyxdata.co.uk.html
│   │   └── ... (7 sample HTMLs)
│   └── markdown/                  # Nội dung văn bản Markdown sạch trích xuất bởi Crawl4AI
│       ├── .gitkeep
│       ├── codetour.org.md
│       └── ... (7 sample Markdowns)
└── lakehouse/                     # [IGNORED IN GIT] Lưu trữ tầng dữ liệu Medallion cục bộ
    ├── bronze/                    # Tầng Đồng: Dữ liệu Markdown/HTML gốc (UTF-8 nguyên bản)
    │   └── .gitkeep
    ├── silver/                    # Tầng Bạc: Thực thể SilverCompetitionRecord (Parquet / JSON)
    │   └── .gitkeep
    └── gold/                      # Tầng Vàng: Các bảng phân tích chiều phục vụ DuckDB / API
        └── .gitkeep
```

---

## 2. Chi Tiết Từng Phân Tầng Dữ Liệu

### A. Phân tầng Kiểm thử (`data/raw/`)
- **Mục đích**: Chứa 7 snapshot trang web mẫu thu thập thực tế từ các cuộc thi công nghệ tiêu biểu (*Code Tour, AI Challenge TP.HCM, Vietnam AI Challenge, DataDNA Onyx, IT Consultant Challenge, RMIT Hackathon, HackAITHON*).
- **Chính sách Git**: **Được commit vào Git** nhằm đảm bảo tính tái lập (reproducibility) cho các bài kiểm thử đơn vị (`pytest`) và kịch bản trích xuất thực thể bằng mô hình ngôn ngữ lớn (`src/acdp/2_instruction.py`) mà không phụ thuộc vào kết nối mạng trực tiếp tới website nguồn.

### B. Phân tầng Medallion Lakehouse Tinh Gọn (`data/lakehouse/` & Cloudflare R2)
Theo định hướng tinh giản công nghệ **DIR-015** cho quy mô 5–10 cuộc thi:
1. **Tầng Bronze (`bronze/`)**:
   - Lưu trữ trực tiếp văn bản Markdown/HTML nguyên bản (`UTF-8`) được cào bởi `src/acdp/1_crawl_to_bronze.py` (hoặc nạp từ `data/raw/markdown/`).
   - **Không sử dụng nén nhị phân `zstandard`** ở quy mô 5–10 cuộc thi để giữ dữ liệu minh bạch, dễ đọc kiểm tra trực tiếp và giảm độ phức tạp của pipeline.
2. **Tầng Silver (`silver/`)**:
   - Dữ liệu sự kiện cuộc thi được bóc tách từ văn bản Markdown ở tầng Bronze thông qua thư viện `instructor` + `litellm`, tuân thủ chặt chẽ lược đồ Pydantic v2 `SilverCompetitionRecord` và lưu dưới dạng tệp `.parquet` / `.json`.
3. **Tầng Gold (`gold/`)**:
   - Các bảng chiều (Dimensions) và bảng sự kiện (Facts) được truy vấn trực tiếp bằng động cơ phân tích in-process **DuckDB** để phục vụ FastAPI backend và giao diện người dùng.

---

## 3. Chính Sách Đồng Bộ Dữ Liệu Giữa Các Thành Viên (Local vs. Cloudflare R2)

Hệ thống hỗ trợ lưu trữ cục bộ và đồng bộ trực tiếp lên đám mây **Cloudflare R2** (miễn phí 100% băng thông tải ra) thông qua tệp cấu hình `.env`:

| Môi Trường | Công Cụ & Đường Dẫn Lưu Trữ | Mô Tả & Mục Đích Sử Dụng |
| :--- | :--- | :--- |
| **Local Dev** | `./data/raw/markdown/` & `./data/lakehouse/` | Phát triển, chạy unit test (`pytest`) và thử nghiệm nhanh trên ổ cứng cục bộ (0MB RAM phụ tải). |
| **Shared Team (Cloudflare R2)** | Bucket `acdp-lakehouse` (`bronze/{domain}/...` & `silver/...`) | Đồng bộ trực tiếp dữ liệu 5–10 cuộc thi giữa máy của Duy và Hưng qua S3 API (`boto3` & `duckdb httpfs`). |

---

## 4. Quy Tắc Phiên Bản Hóa (Git & `.gitignore` Policy)

1. ❌ **Tuyệt đối không commit dữ liệu runtime của Lakehouse**:
   - Toàn bộ các tệp `.parquet`, `.duckdb`, `.db`, `.sqlite3`, thư mục `_delta_log/`, và dữ liệu phát sinh trong `data/lakehouse/` bị `.gitignore` loại trừ hoàn toàn.
2. ✅ **Bảo toàn cấu trúc thư mục bằng `.gitkeep`**:
   - Mọi thư mục con trong `data/` đều duy trì tệp `.gitkeep` để khi clone repository sang máy mới, cây thư mục sẵn sàng hoạt động.
3. ✅ **Bảo toàn dữ liệu kiểm thử `data/raw/`**:
   - Các tệp HTML và Markdown của 7 cuộc thi mẫu trong `data/raw/` được theo dõi bởi Git để phục vụ kiểm thử liên tục.
