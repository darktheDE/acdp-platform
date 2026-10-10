# Data Directory Architecture & Storage Conventions

> **Repository**: `acdp-platform` (Academic Competition Discovery Platform)  
> **Faculty**: Faculty of Information Technology, Ho Chi Minh City University of Technology and Engineering (HCM-UTE)  
> **Major**: Data Engineering (Kỹ thuật Dữ liệu)  
> **Related Research**: [`docs/rd-tasks/T13.md`](../docs/rd-tasks/T13.md) & [`docs/deliverables/NT-018-bronze-storage-and-table-format-evaluation.md`](../docs/deliverables/NT-018-bronze-storage-and-table-format-evaluation.md)

---

## 1. Overview & Directory Layout

Thư mục `data/` là không gian lưu trữ dữ liệu cục bộ phục vụ quy trình phát triển, kiểm thử đường ống thu thập (crawling), và vận hành kiến trúc **Medallion Lakehouse** trên máy trạm dev.

```
data/
├── README.md                      # Tài liệu kiến trúc và quy ước lưu trữ dữ liệu
├── raw/                           # [TRACKED IN GIT] Dữ liệu mẫu phục vụ kiểm thử và tái lập vết
│   ├── html/                      # Snapshot HTML thô từ các cổng thông tin và fanpage cuộc thi
│   │   ├── .gitkeep
│   │   ├── codetour.org.html
│   │   ├── datadna.onyxdata.co.uk.html
│   │   └── ... (sample HTMLs)
│   └── markdown/                  # Nội dung văn bản markdown trích xuất bởi Crawl4AI
│       ├── .gitkeep
│       ├── codetour.org.md
│       └── ... (sample Markdowns)
└── lakehouse/                     # [IGNORED IN GIT] Lưu trữ tầng dữ liệu Medallion Lakehouse cục bộ
    ├── bronze/                    # Delta Lake Bronze (raw payloads nén Zstandard, _delta_log/)
    │   └── .gitkeep
    ├── silver/                    # Delta Lake Silver (thực thể Pydantic đã làm sạch & khử trùng)
    │   └── .gitkeep
    └── gold/                      # Delta/DuckDB Gold (data marts phân tích chiều và phục vụ BI/API)
        └── .gitkeep
```

---

## 2. Chi Tiết Từng Phân Tầng Dữ Liệu

### A. Phân tầng Kiểm thử (`data/raw/`)
- **Mục đích**: Chứa các snapshot trang web mẫu đã thu thập thực tế từ các cuộc thi học thuật (như *Code Tour, AI Challenge TP.HCM, DataDNA Onyx, HackAITHON, RMIT Hackathon*).
- **Chính sách Git**: **Được commit vào Git** nhằm đảm bảo tính tái lập (reproducibility) của các bài kiểm thử đơn vị (Unit Tests), kiểm thử tích hợp parser (LLM Extraction Spikes), và đánh giá benchmark mà không phụ thuộc vào kết nối mạng trực tiếp tới website nguồn.

### B. Phân tầng Medallion Lakehouse (`data/lakehouse/`)
Theo kết luận nghiên cứu tại [`T13`](../docs/rd-tasks/T13.md) và hồ sơ nghiệm thu [`NT-018`](../docs/deliverables/NT-018-bronze-storage-and-table-format-evaluation.md):
1. **`data/lakehouse/bronze/`**:
   - Định dạng bảng: **Delta Lake** (`delta-rs` / Rust engine, Zero-JVM).
   - Nội dung: Chứa các batch file Parquet và nhật ký giao dịch `_delta_log/`. Cột `raw_html_bytes` lưu toàn bộ payload HTML gốc được nén bằng **Zstandard** để triệt tiêu bài toán phân mảnh file nhỏ (*Small-File Problem / Inode Exhaustion*).
2. **`data/lakehouse/silver/`**:
   - Nội dung: Dữ liệu sự kiện cuộc thi đã được bóc tách cấu trúc theo schema Pydantic v2 chuẩn, làm giàu thông tin (dates, prizes, eligibility) và khử trùng lặp qua `content_hash`.
3. **`data/lakehouse/gold/`**:
   - Nội dung: Các bảng chiều (Dimensions) và bảng sự kiện (Facts) phục vụ trực tiếp cho động cơ truy vấn phân tích **DuckDB 1.2+**, FastAPI backend, và màn hình thống kê Faculty BI Dashboard.

---

## 3. Chính Sách Quản Trị & Trừu Tượng Hóa Lưu Trữ (Storage Abstraction)

Hệ thống ACDP sử dụng giao diện lưu trữ trừu tượng (`Storage Interface`) thông qua biến môi trường trong file `.env`:

| Môi Trường | Cấu Hình `BRONZE_STORAGE_URI` | Mô Tả & Backend |
| :--- | :--- | :--- |
| **Local Dev (Mặc định)** | `./data/lakehouse/bronze` | Ghi trực tiếp vào ổ cứng SSD cục bộ, 0MB RAM phụ tải mạng. |
| **Shared Team (Cloud)** | `s3://acdp-bronze/events` | Stream trực tiếp lên **Cloudflare R2** (Zero-Egress fees) để chia sẻ dữ liệu online giữa Hưng và Duy. |
| **Docker Self-Hosted** | `s3://acdp-bronze/events` | Giao tiếp với **SeaweedFS** S3 container (Port 8333) theo chuẩn kiến trúc Facebook Haystack (OSDI 2010). |

---

## 4. Quy Tắc Phiên Bản Hóa (Git & `.gitignore` Policy)

1. ❌ **Tuyệt đối không commit dữ liệu runtime của Lakehouse**:
   - Toàn bộ các file `.parquet`, `.duckdb`, `.db`, `.sqlite3`, thư mục `_delta_log/`, và dữ liệu phát sinh trong `data/lakehouse/` bị `.gitignore` loại trừ hoàn toàn.
2. ✅ **Bảo toàn cấu trúc thư mục bằng `.gitkeep`**:
   - Mọi thư mục con trong `data/` đều duy trì file `.gitkeep` để khi clone repo sang máy mới, cây thư mục Lakehouse tự động sẵn sàng hoạt động.
3. ✅ **Bảo toàn dữ liệu kiểm thử `data/raw/`**:
   - Các file HTML và Markdown mẫu trong `data/raw/` được theo dõi bởi Git để phục vụ test pipeline liên tục.
