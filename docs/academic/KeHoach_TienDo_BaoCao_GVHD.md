# BÁO CÁO KẾ HOẠCH VÀ TIẾN ĐỘ THỰC HIỆN TIỂU LUẬN CHUYÊN NGÀNH
*(Báo cáo định kỳ gửi Giáo viên hướng dẫn: ThS. Trần Quang Khải)*

**TRƯỜNG ĐẠI HỌC CÔNG NGHỆ KỸ THUẬT TP.HCM (HCM-UTE)**  
**KHOA CÔNG NGHỆ THÔNG TIN — BỘ MÔN HỆ THỐNG THÔNG TIN**  
**CHUYÊN NGÀNH: KỸ THUẬT DỮ LIỆU**

---

- **Tên đề tài**: XÂY DỰNG HỆ THỐNG THU THẬP, XỬ LÝ DỮ LIỆU VÀ NỀN TẢNG HỖ TRỢ SINH VIÊN THAM GIA CÁC CUỘC THI HỌC THUẬT, CÔNG NGHỆ
- **Sinh viên thực hiện 1**: Nguyễn Văn Quang Duy — **MSSV 1**: 23110086
- **Sinh viên thực hiện 2**: Đỗ Kiến Hưng — **MSSV 2**: 23133030
- **Giáo viên hướng dẫn khoa học**: ThS. Trần Quang Khải
- **Thời gian báo cáo**: Tuần 8 (Học kỳ 1, Năm học 2026–2027)
- **Giai đoạn hiện tại**: Hoàn thành Tầng Bronze và Thiết kế Lược đồ Lớp Bạc (Silver Layer)

---

## 1. TÓM TẮT TỔNG QUAN TIẾN ĐỘ HIỆN TẠI

Tính đến hết Tuần 8 của học phần Tiểu luận chuyên ngành, nhóm nghiên cứu đã bám sát đề cương khoa học và tập trung triển khai lõi Kỹ thuật Dữ liệu (Data Engineering Core) với các kết quả định lượng:

1. **Khảo sát & Cơ sở lý thuyết**: Hoàn thành nghiên cứu tài liệu từ các hội nghị quốc tế (CIDR, VLDB, NeurIPS), đánh giá đối sánh các nền tảng thực tế (Devpost, Unstop, Ybox) và thống nhất kiến trúc phân tầng Medallion Lakehouse tinh gọn phù hợp cấu hình máy trạm 16GB RAM (không dùng cụm JVM/Spark cồng kềnh).
2. **Tầng Thu thập & Tầng Đồng (Bronze Layer)**: Cài đặt engine thu thập Playwright/Crawl4AI và module lưu trữ Delta Lake (`delta-rs`). Đã kiểm thử thu thập và nén 7 snapshot cuộc thi học thuật thực tế bằng thuật toán Zstandard (Level 3), đạt mức tiết kiệm dung lượng đĩa cứng **80.2%** (từ 975KB xuống 192KB).
3. **Thiết kế Lược đồ Lớp Bạc (Silver Schema)**: Hoàn thành thiết kế lớp dữ liệu `SilverCompetitionRecord` trên Pydantic v2 với 8 nhóm thuộc tính định lượng, tập trung vào các trường dễ cào và người dùng sinh viên quan tâm nhất (Tên cuộc thi, đơn vị tổ chức, hạn chót đăng ký, link đăng ký, cơ cấu giải thưởng, điều kiện nhóm và tóm tắt thể lệ). Tích hợp thuật toán sinh mã băm đại diện `generate_fingerprint()` và khử trùng lặp sự kiện đa kênh trên DuckDB.
4. **Kiểm thử tự động**: Xây dựng 7 bài kiểm thử đơn vị (`tests/test_bronze_storage.py` và `tests/test_silver_schema.py`), đạt tỷ lệ vượt qua 100%.

---

## 2. BẢNG TIẾN ĐỘ THỰC HIỆN TIỂU LUẬN CHUYÊN NGÀNH

Bảng dưới đây trình bày chi tiết các công việc nhóm **ĐÃ HOÀN THÀNH** (Tuần 1 đến Tuần 8), công việc **TRỌNG TÂM SẼ THỰC HIỆN TRONG TUẦN TỚI** (Tuần 9), và kế hoạch dự kiến cho các tuần tiếp theo:

### Bảng: Báo cáo tiến độ thực tế học phần Tiểu luận chuyên ngành

| STT | Tuần / Thời gian | Tình trạng | Nội dung công việc chi tiết | Sản phẩm / Minh chứng kỹ thuật | Phụ trách |
| :---: | :---: | :---: | :--- | :--- | :---: |
| **1** | Tuần 1<br>(31/8 - 6/9) | **ĐÃ LÀM** | Khảo sát nhu cầu thực tế của sinh viên FIT-HCMUTE; phân tích 4 nút thắt tiếp cận thông tin; thiết lập kho lưu trữ Git và Docker Compose nền tảng. | Bản khảo sát nhu cầu sinh viên; Cấu hình Docker Compose ban đầu. | Hưng<br>Duy |
| **2** | Tuần 2<br>(7/9 - 13/9) | **ĐÃ LÀM** | Nghiên cứu tổng quan tài liệu khoa học quốc tế (Cho, Armbrust, Lewis, Xu); phân tích đối sánh các nền tảng thực tế; khởi tạo R&D Task T01 và T02. | Báo cáo R&D T01, T02; Bảng đối sánh nền tảng học thuật. | Duy |
| **3** | Tuần 3<br>(14/9 - 20/9) | **ĐÃ LÀM** | Thiết kế kiến trúc phân tầng 4 lớp; phân định ranh giới 15 tuần TLCN và KLTN; soạn thảo bản Thuyết minh đề tài (Proposal) và báo cáo với GVHD ThS. Trần Quang Khải. | Bản Thuyết minh đề tài; Slide báo cáo đề cương. | Hưng<br>Duy |
| **4** | Tuần 4<br>(21/9 - 27/9) | **ĐÃ LÀM** | Đánh giá công cụ cào web động Playwright và Crawl4AI; thu thập bộ dữ liệu kiểm thử thực tế từ 7 nguồn trọng điểm (Code Tour, AI Challenge TP.HCM, DataDNA, HackAITHON...). | Bộ dữ liệu snapshot HTML tại `data/raw/html/`; Kịch bản cào web thử nghiệm. | Hưng |
| **5** | Tuần 5<br>(28/9 - 4/10) | **ĐÃ LÀM** | Nghiên cứu sâu tầng lưu trữ Bronze (Task T13); benchmark đối sánh các định dạng bảng mở (Delta Lake, Iceberg, Lance) và kho đối tượng (Cloudflare R2, SeaweedFS, Local SSD). | Báo cáo nghiệm thu NT-018; Ma trận đánh giá Open Table Formats. | Duy<br>Hưng |
| **6** | Tuần 6<br>(5/10 - 11/10) | **ĐÃ LÀM** | Cài đặt engine lưu trữ Bronze Delta Lake bằng thư viện `delta-rs` (Rust, zero-JVM); tích hợp thuật toán nén payload Zstandard Level 3; xử lý triệt để bài toán phân mảnh tệp nhỏ. | Module `src/acdp/lakehouse/bronze.py`; 5 bài test `test_bronze_storage.py` (Passed 100%). | Hưng |
| **7** | Tuần 7<br>(12/10 - 18/10) | **ĐÃ LÀM** | Thiết kế lược đồ dữ liệu lớp Bạc (Silver Schema) trên Pydantic v2; xây dựng thuật toán sinh mã băm đại diện `generate_fingerprint()` khử trùng lặp và cơ chế kiểm kiểu dữ liệu tài chính. | Lớp `SilverCompetitionRecord` tại `schema.py`; Bộ test `test_silver_schema.py` (Passed 100%). | Duy |
| **8** | Tuần 8<br>(19/10 - 25/10) | **ĐÃ LÀM** | Khảo sát quy trình migrate kho dữ liệu lên Cloudflare R2; xây dựng tài liệu hướng dẫn kỹ thuật đồng bộ 3 tầng Đồng - Bạc - Vàng; tối ưu hóa truy vấn zero-copy qua DuckDB. | Tài liệu `HUONG_DAN_MIGRATE_R2_LAKEHOUSE.md` (NT-022); Bản thảo báo cáo TLCN đến Lớp Bạc. | Hưng<br>Duy |
| **9** | **Tuần 9**<br>**(26/10 - 1/11)** | **SẼ LÀM TRONG TUẦN TỚI** | **1. Triển khai pipeline trích xuất tự động từ Bronze sang Silver bằng mô hình ngôn ngữ lớn kết hợp cơ chế Pydantic Schema Enforcement.<br>2. Cấu hình Bucket Cloudflare R2 thực tế và chạy script migrate dữ liệu Bronze lên mây.<br>3. Kiểm thử phân giải thực thể và khử trùng lặp trên 20 cuộc thi mẫu.** | **Pipeline trích xuất Bronze-to-Silver; Dữ liệu Bronze thực tế trên Cloudflare R2; Báo cáo độ chính xác trích xuất.** | **Hưng**<br>**Duy** |
| 10 | Tuần 10<br>(2/11 - 8/11) | *Dự kiến* | Thiết kế các bảng Data Marts Tầng Vàng (Gold Layer); mô hình hóa bảng sự kiện Fact_Competitions và các bảng chiều Dim_Time, Dim_Domain trên DuckDB. | Lược đồ bảng Tầng Vàng; Các câu truy vấn phân tích SQL OLAP. | Hưng<br>Duy |
| 11 | Tuần 11<br>(9/11 - 15/11) | *Dự kiến* | Cài đặt cơ sở dữ liệu vector Qdrant; phân đoạn thể lệ cuộc thi theo cấu trúc điều khoản; thử nghiệm mô hình embedding văn bản tiếng Việt. | Container Qdrant; Module phân đoạn điều khoản và vector hóa. | Duy |
| 12 | Tuần 12<br>(16/11 - 22/11) | *Dự kiến* | Xây dựng pipeline Hybrid Search (BM25 + Dense Vectors + Cross-Encoder re-ranking); đo lường chất lượng câu trả lời theo khung Ragas. | Module Hybrid RAG; Bảng điểm đo lường Faithfulness. | Duy |
| 13 | Tuần 13<br>(23/11 - 29/11) | *Dự kiến* | Xây dựng Backend REST API bằng FastAPI (Python 3.13) cung cấp các endpoint tra cứu dữ liệu cuộc thi và hỏi đáp thể lệ. | Mã nguồn FastAPI backend; Tài liệu Swagger OpenAPI. | Hưng |
| 14 | Tuần 14<br>(30/11 - 6/12) | *Dự kiến* | Xây dựng giao diện Web Portal sinh viên và Bảng điều khiển phân tích số liệu mùa vụ cho Khoa CNTT (Next.js 15, Tailwind CSS). | Giao diện Web Portal sinh viên; Màn hình Dashboard quản trị. | Hưng<br>Duy |
| 15 | Tuần 15<br>(7/12 - 13/12) | *Dự kiến* | Kiểm thử toàn diện hệ thống (End-to-End); hoàn thiện toàn văn quyển báo cáo Tiểu luận chuyên ngành và slide bảo vệ trước Hội đồng chuyên môn. | Toàn văn Báo cáo TLCN; Slide bảo vệ đề tài. | Hưng<br>Duy |

---

## 3. CHI TIẾT CÁC CÔNG VIỆC TRỌNG TÂM TRONG TUẦN TỚI (TUẦN 9)

Trong tuần tiếp theo (từ ngày 26/10 đến 01/11/2026), nhóm nghiên cứu sẽ tập trung giải quyết 3 nhiệm vụ kỹ thuật cụ thể:

1. **Cài đặt Pipeline trích xuất tự động Bronze sang Silver**:
   - Sử dụng thư viện `deltalake` và DuckDB để đọc các payload HTML nén từ bảng Bronze.
   - Sử dụng mô hình ngôn ngữ lớn (Gemini API) với cơ chế Structured Outputs ép kiểu theo schema `SilverCompetitionRecord`.
   - Chuẩn hóa toàn bộ ngày tháng sang chuẩn ISO 8601 (`YYYY-MM-DD`) và giá trị giải thưởng sang kiểu số nguyên `BIGINT` VND.
2. **Triển khai kết nối Cloudflare R2 chính thức**:
   - Kích hoạt Bucket `acdp-lakehouse` trên Cloudflare R2.
   - Cấu hình các biến môi trường S3 credentials trên cả 2 máy của Hưng và Duy.
   - Đẩy toàn bộ bảng Delta Bronze và các bản ghi Silver thử nghiệm lên R2 để Duy kiểm thử truy vấn trực tiếp bằng DuckDB.
3. **Đánh giá thuật toán khử trùng lặp sự kiện**:
   - Thử nghiệm bóc tách và so khớp đối với 20 bài đăng cuộc thi được thu thập từ nhiều nguồn khác nhau (Website chính thức, Fanpage Đoàn Hội, Ybox).
   - Đo lường độ chính xác của mã vân tay `generate_fingerprint()` và thuật toán so khớp chuỗi mờ Levenshtein trên DuckDB.

---

## 4. CÁC NỘI DUNG XIN Ý KIẾN CHỈ ĐẠO CỦA GIÁO VIÊN HƯỚNG DẪN

Nhóm kính mong nhận được ý kiến góp ý và định hướng của ThS. Trần Quang Khải về các vấn đề kỹ thuật sau:

1. **Về danh mục trường thuộc tính Lớp Bạc (`SilverCompetitionRecord`)**:
   - Hiện tại lược đồ tập trung vào 11 trường thông tin cốt lõi mà sinh viên quan tâm nhất (Tên, Đơn vị tổ chức, Hạn chót đăng ký, Link đăng ký, Thời gian thi, Lĩnh vực, Đối tượng dự thi, Quy mô nhóm, Lệ phí, Cơ cấu giải thưởng, Tóm tắt thể lệ).
   - Kính xin Thầy nhận xét xem cấu trúc này đã đủ chặt chẽ và phù hợp cho bài toán quản lý phong trào học thuật của Khoa CNTT hay cần bổ sung thêm trường thuộc tính nào khác.
2. **Về giải pháp lưu trữ đối tượng Cloudflare R2**:
   - Nhóm lựa chọn Cloudflare R2 thay vì AWS S3 hay MinIO cục bộ nhằm tận dụng chính sách miễn phí 100% băng thông tải dữ liệu (Zero-Egress fees) và 10GB dung lượng miễn phí, giúp hai sinh viên đồng bộ dữ liệu mượt mà mà không tốn chi phí thuê máy chủ.
   - Nhóm kính xin ý kiến Thầy về tính khả thi của giải pháp này khi mở rộng quy mô trong giai đoạn Khóa luận tốt nghiệp.

---
*Kính chúc Thầy nhiều sức khỏe và công tác tốt!*  
**Nhóm sinh viên thực hiện đề tài**: Nguyễn Văn Quang Duy & Đỗ Kiến Hưng
