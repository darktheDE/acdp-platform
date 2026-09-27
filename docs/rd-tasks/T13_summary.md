# T13: Khảo sát Tech Stack lớp Bronze (Lưu trữ & Format)

### Goals
- Chọn storage và table format cho lớp Bronze để lưu dữ liệu crawl (HTML, JSON, ảnh).
- Xử lý bài toán nghẽn I/O do file nhỏ, giữ máy 16GB RAM chạy êm (không dùng Spark/JVM).
- Chuẩn bị đủ tài liệu (paper, video, benchmark) để bảo vệ trước thầy Khải, hội đồng và chốt với Hưng.
- Chốt stack dùng ngay cho TLCN và hướng mở rộng sang KLTN.

---

### List các tools
- **Object Storage**: Local SSD, SeaweedFS, Cloudflare R2, MinIO, AWS S3.
- **Table Format**: Delta Lake (`delta-rs`), Apache Iceberg (`pyiceberg`), Lance, Apache Hudi.

---

### Phân tích pros and cons
- **Local SSD**: Đọc ghi nhanh nhất, 0MB RAM. Nhược điểm: Khó share data giữa 2 máy.
- **SeaweedFS**: Kiến trúc Haystack (Facebook), đọc ghi file nhỏ <1MB cực nhanh (O(1)), Docker ngốn chỉ ~120MB RAM, Apache 2.0. Nhược điểm: Ít tài liệu hơn MinIO.
- **Cloudflare R2**: Chuẩn S3, miễn phí 100% băng thông tải ra (Zero-Egress). Gói free cho 10GB và 1M write/tháng (đủ cho đồ án). Nhược điểm: Cần add thẻ Visa để mở.
- **MinIO**: Ngốn 1.5 - 2GB RAM, dính bản quyền AGPLv3, ghi file nhỏ chậm. Bỏ qua.
- **AWS S3**: Đắt do phí tải dữ liệu (Egress), không hợp sinh viên.
- **Delta Lake (`delta-rs`)**: Viết bằng Rust, chạy thẳng trong Python, 0MB RAM nền (Zero-JVM). Đủ ACID, Time-Travel, lệnh `OPTIMIZE` gom file nhỏ siêu tốt, DuckDB đọc native.
- **Apache Iceberg (`pyiceberg`)**: Chuẩn mở xịn, nhưng bản Python luồng ghi và dọn file còn yếu, thường phải kéo thêm Spark.
- **Lance**: Rất nhanh cho AI và vector, nhưng hệ sinh thái ETL chung chưa phổ biến bằng Delta.
- **Apache Hudi**: Bắt buộc có cụm Spark/JVM, ngốn nhiều GB RAM. Loại ngay vì máy 16GB không gánh nổi.

---

### Tại sao không dùng Apache XTable?
- **Dính Java/JVM**: Viết 100% bằng Java, Python muốn gọi phải cài `jpype` kéo cả JVM lên chạy, vi phạm tiêu chí nhẹ máy 16GB.
- **Đã có Delta UniForm**: Delta Lake có sẵn tính năng tự sinh metadata Iceberg khi commit, không cần tool ngoài.
- **Thêm điểm lỗi rủi ro**: XTable là tool chạy sync bất đồng bộ sau khi crawl, dễ bị lệch metadata nếu tiến trình crash.
- **Thừa thãi**: ACDP chỉ có Python crawl ghi vào Delta và DuckDB đọc trực tiếp qua `duckdb_delta`, không có nhu cầu dịch metadata lòng vòng.

---

### Luồng nạp dữ liệu vào lớp Bronze (Data Flow)
```
[ 1. Crawler cào web ] -> URL, HTML thô (1MB), mã HTTP 200, timestamp
        │
[ 2. Đóng gói Python ] -> Gom thành 1 record: raw_id, url, raw_html, metadata
        │
[ 3. Ghi vào Bronze Delta ] -> deltalake.write_deltalake(path, table, mode="append")
        │                      Lưu tại Local SSD hoặc Cloudflare R2:
        │                      - _delta_log/: Ghi nhận transaction, time-travel
        │                      - part-xxxx.parquet: File nén gom 50-100 trang web
        ▼
[ 4. Lớp Silver đọc ] -> DuckDB: SELECT raw_html FROM delta_scan(...) 
                         -> Đưa raw_html cho LLM trích xuất Pydantic Schema
```
- **Lợi ích**: Không sinh hàng vạn file `.html` rác đĩa; nén tiết kiệm 75% dung lượng; giữ nguyên 100% HTML gốc để replay lại khi cần mà không phải cào lại web.

---

### List bài báo, video, tài liệu benchmark
- **Paper SIGMOD 2024**: [LST-Bench (Microsoft)](https://arxiv.org/abs/2403.17224) - Chuẩn benchmark đo Delta, Iceberg trên cloud storage.
- **Paper VLDB 2025**: [Ursa (Best Industry Paper)](https://www.vldb.org/) - Kỹ thuật stream thẳng dữ liệu crawl vào Lakehouse không qua đĩa trung gian.
- **Paper CIDR 2023**: [LHBench (UC Berkeley & Stanford)](https://www.cidrdb.org/cidr2023/papers/p92-jain.pdf) - So sánh chi tiết Delta, Iceberg, Hudi về chi phí ghi và metadata.
- **Paper OSDI 2010**: [Facebook Haystack](https://www.usenix.org/conference/osdi10/finding-needle-haystack-facebooks-photo-storage) - Lý thuyết gom file nhỏ giải quyết nghẽn inode, gốc của SeaweedFS.
- **Chuẩn ISO 28500**: [WARC format](https://iipc.github.io/warc-specifications/) - Chuẩn lưu trữ web crawl.
- **Video CIDR DB**: [Paras Jain so sánh Lakehouse](https://www.youtube.com/) - Mổ xẻ độ trễ metadata và compaction.
- **Video Data+AI Summit**: [Denny Lee mổ xẻ Delta Lake](https://www.youtube.com/) - Transaction log và atomic commit.
- **Repo mã nguồn**: [delta-rs](https://github.com/delta-io/delta-rs), [Apache XTable](https://github.com/apache/incubator-xtable), [SeaweedFS](https://github.com/seaweedfs/seaweedfs).

---

### Overall benchmark
- **Tốc độ ghi batch**: Local SSD > Delta-rs (Rust) $\approx$ SeaweedFS > R2 > Iceberg > MinIO.
- **Xử lý file nhỏ (<200KB)**: SeaweedFS (tuyệt đối nhờ O(1)) và Delta-rs (nhờ gom file `OPTIMIZE`). MinIO và Local SSD dễ nghẽn IOPS.
- **Chi phí RAM nền**: Local SSD, Delta-rs (0MB in-process) < SeaweedFS (~120MB) << MinIO (1.5 - 2GB) << Hudi (nhiều GB do ôm cụm Spark).
- **DuckDB 1.2+**: Đọc Delta Lake và Iceberg zero-copy cực mượt.

---

### Decision
1. **Đóng gói**: Nén HTML bằng Zstandard rồi lưu dạng binary thẳng vào cột `raw_html_bytes` của bảng Delta. Triệt tiêu nghẽn file nhỏ ngay từ nguồn.
2. **Table format**: Chọn **Delta Lake** qua thư viện Rust **`delta-rs`**. Nhẹ, chạy thẳng trong Python, 0MB RAM daemon, đủ ACID, Time-Travel, DuckDB đọc trực tiếp. Bật Delta UniForm để tự sinh metadata Iceberg phòng khi cần đổi engine.
3. **Storage**:
   - **Giai đoạn 1 (TLCN)**: Dùng **Cloudflare R2** để Hưng và Duy dùng chung data online với giá 0đ (10GB free). Chưa kịp add thẻ thì lưu tạm Local SSD qua file `.env`, chuyển lên R2 sau mất đúng 5 phút đổi config.
   - **Giai đoạn 2 (KLTN)**: Dựng server riêng thì bật **SeaweedFS** bằng Docker để tự quản trị nội bộ.
