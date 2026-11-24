# BẢNG ĐĂNG KÝ ĐỀ TÀI TIỂU LUẬN CHUYÊN NGÀNH
**HỌC KỲ 1 - NĂM HỌC 2026 - 2027**  
**KHOA CÔNG NGHỆ THÔNG TIN - TRƯỜNG ĐẠI HỌC CÔNG NGHỆ KỸ THUẬT TP.HCM**

---

## I. THÔNG TIN ĐĂNG KÝ (THEO FORM EXCEL KHOA CNTT)

| Cột thông tin | Sinh viên 1 | Sinh viên 2 |
| :--- | :--- | :--- |
| **STT** | *(Theo danh sách Khoa)* | |
| **Mã nhóm** | *(Khoa phân bổ)* | |
| **Loại hình đăng ký** | **Tiểu luận chuyên ngành** | **Tiểu luận chuyên ngành** |
| **Mã số sinh viên (MSSV)** | **23133030** | **23110086** |
| **Họ và tên sinh viên** | **Đỗ Kiến Hưng** | **Nguyễn Văn Quang Duy** |
| **Hệ đào tạo** | **Đại trà** | **Đại trà** |
| **Ngành / Chuyên ngành** | **Kỹ thuật dữ liệu** | **Kỹ thuật dữ liệu** |
| **Số lượng SV** | **2** | |
| **Tên đề tài (Tiếng Việt)** | <div colspan="2">**Xây dựng hệ thống thu thập, xử lý dữ liệu và nền tảng hỗ trợ sinh viên tham gia các cuộc thi học thuật, công nghệ**</div> | |
| **Tên đề tài (Tiếng Anh)** | <div colspan="2">**Building a Data Pipeline and Platform for Academic Competition Discovery, Knowledge Management, and Teammate Recommendation**</div> | |
| **Mã Giảng viên hướng dẫn** | **6452** | |
| **Họ tên Giảng viên hướng dẫn** | **ThS. Trần Quang Khải** | |
| **Giảng viên phản biện (GVPB)** | *(Khoa phân công)* | |
| **Ghi chú** | Đề tài đăng ký mới, ngành Kỹ thuật Dữ liệu, định hướng nghiên cứu và phát triển tiếp nối lên Khóa luận tốt nghiệp. | |

---

## II. MỤC TIÊU ĐỀ TÀI

1. **Xây dựng Data Pipeline thu thập và chuẩn hóa dữ liệu**: Tự động hóa quá trình thu thập thông tin các cuộc thi học thuật, hội thi công nghệ và chương trình đào tạo chuyên môn từ website trường/viện, cổng thông tin Đoàn - Hội và các fanpage mạng xã hội. Trích xuất văn bản phi cấu trúc thành dữ liệu có cấu trúc phục vụ lưu trữ tập trung.
2. **Thiết kế kiến trúc lưu trữ Lakehouse và kiểm soát chất lượng dữ liệu**: Xây dựng kho lưu trữ theo mô hình phân tầng (Bronze, Silver, Gold), khử trùng lặp dữ liệu sự kiện, chuẩn hóa mốc thời gian và lưu vết thay đổi của thể lệ thi.
3. **Xây dựng hệ thống tra cứu và quản trị tri thức cuộc thi**: Ứng dụng mô hình RAG (Retrieval-Augmented Generation) để hỗ trợ sinh viên tra cứu nhanh thể lệ, điều kiện dự thi, mốc thời gian và ngân hàng đề thi các năm trước.
4. **Phát triển thuật toán ghép đội và kết nối giảng viên hướng dẫn**: Đề xuất thành viên lập đội dựa trên mức độ bổ trợ kỹ năng chuyên môn giữa các sinh viên; gợi ý giảng viên hướng dẫn phù hợp với định hướng chủ đề cuộc thi.
5. **Xây dựng Dashboard phân tích số liệu cho Khoa CNTT**: Cung cấp công cụ thống kê trực quan về mức độ quan tâm của sinh viên theo ngành, theo khóa và xu hướng chủ đề của các cuộc thi qua từng giai đoạn.

---

## III. YÊU CẦU ĐỀ TÀI & CÔNG NGHỆ SỬ DỤNG

### 1. Công nghệ sử dụng
- **Thu thập dữ liệu (Ingestion Layer)**:
  - Công cụ thu thập: Crawl4AI (v0.9+), Playwright (v1.48+), Scrapy (v2.12+) phục vụ crawl dữ liệu web động và bài đăng mạng xã hội.
  - Xử lý trích xuất: Sử dụng LLM Schema Parser (Pydantic v2.10+) định hình dữ liệu đầu ra theo cấu trúc JSON chuẩn (tên cuộc thi, đơn vị tổ chức, thời hạn, thể lệ, bảng đấu, giải thưởng).
- **Lưu trữ và Xử lý dữ liệu (Lakehouse & Storage Layer)**:
  - Cơ sở dữ liệu: PostgreSQL (v17+ - lưu trữ quan hệ, nghiệp vụ người dùng), DuckDB (v1.2+) / Parquet (lưu trữ phân tích và dữ liệu thô).
  - Chuẩn hóa dữ liệu: dbt-core (v1.9+) và các kịch bản Python (v3.13+) kiểm tra chất lượng dữ liệu (Data Quality validation).
  - Điều phối luồng công việc: Apache Airflow (v2.10+) hoặc Prefect (v3.0+) lập lịch thu thập và biến đổi dữ liệu định kỳ.
- **Xử lý ngữ nghĩa & AI (Semantic & AI Layer)**:
  - Vector Database: Qdrant (v1.19+) / pgvector (v0.8+) lưu trữ vector embedding của thể lệ và đề thi.
  - Tra cứu thông tin: Kết hợp BM25 và Vector Search (Hybrid Search) với mô hình Re-ranking phục vụ RAG.
  - Thuật toán ghép đội: Tính độ tương đồng vector kỹ năng kết hợp luật lọc điều kiện bắt buộc (Rule-based filtering).
- **Giao diện & Ứng dụng (Serving Layer)**:
  - Backend API: FastAPI (v0.115+, Python 3.13+) cung cấp REST API cho các dịch vụ dữ liệu và AI.
  - Giao diện người dùng: Next.js (v15+), React 19, Tailwind CSS (v4.0).
  - Bảng điều khiển phân tích: Thư viện biểu đồ nhúng (Recharts, Chart.js) hoặc Apache Superset.

### 2. Môi trường phát triển và Triển khai
- Hệ thống: Linux (Ubuntu) / WSL2, Docker & Docker Compose (v2.30+) cho container hóa dịch vụ.
- Quản lý phiên bản: Git, GitHub Actions kiểm thử tự động.
- Triển khai thử nghiệm: Máy chủ nội bộ hoặc Cloud VM.

### 3. Phân định phạm vi thực hiện (Tiểu luận chuyên ngành vs Khóa luận tốt nghiệp)

```
[PHẠM VI TIỂU LUẬN CHUYÊN NGÀNH - MVP 15 TUẦN]
1. Xây dựng Data Pipeline thu thập tự động từ 5 - 10 nguồn thông tin trọng điểm.
2. Xây dựng tầng lưu trữ phân tầng (Bronze/Silver/Gold) và xử lý khử trùng lặp sự kiện.
3. Xây dựng hệ thống RAG cơ bản phục vụ tra cứu quy chế, thể lệ cuộc thi.
4. Xây dựng Web App MVP cho phép sinh viên tìm kiếm, lọc cuộc thi và chat tra cứu.
5. Xây dựng Dashboard phân tích cơ bản số lượng và phân loại cuộc thi theo chủ đề.

[PHẠM VI KHÓA LUẬN TỐT NGHIỆP - MỞ RỘNG 15 TUẦN TIẾP THEO]
1. Nâng cấp Pipeline thu thập thời gian thực (Streaming & Webhook integration).
2. Hoàn thiện thuật toán ghép đội sinh viên và gợi ý giảng viên hướng dẫn.
3. Xây dựng kho lưu trữ tri thức: mã nguồn, báo cáo và cẩm nang kinh nghiệm từ các đội đạt giải.
4. Tự động hóa quy trình đề xuất khen thưởng và liên kết ghi nhận điểm rèn luyện.
5. Xây dựng Dashboard quản trị nâng cao cho Ban Chủ nhiệm Khoa và kênh thông báo qua Bot.
```

---

## IV. KẾ HOẠCH THỰC HIỆN 15 TUẦN TIỂU LUẬN CHUYÊN NGÀNH (HK1 2026-2027)

| Giai đoạn | Thời gian | Nội dung công việc | Sản phẩm bàn giao | Phụ trách chính |
| :--- | :---: | :--- | :--- | :--- |
| **Khảo sát & Thiết kế** | Tuần 1 - 3 | - Khảo sát thực tế nhu cầu sinh viên và nguồn thông tin cuộc thi.<br>- Thiết kế cấu trúc dữ liệu và kiến trúc hệ thống tổng thể.<br>- Báo cáo đề cương chi tiết với GVHD. | - Bản đề cương nghiên cứu.<br>- Bản vẽ kiến trúc dữ liệu. | Đỗ Kiến Hưng<br>Nguyễn Văn Quang Duy |
| **Xây dựng Data Pipeline** | Tuần 4 - 7 | - Xây dựng module thu thập từ các nguồn chỉ định.<br>- Viết logic trích xuất schema bằng LLM và làm sạch dữ liệu.<br>- Thiết lập kiểm tra chất lượng dữ liệu và khử trùng lặp. | - Pipeline thu thập tự động.<br>- Cơ sở dữ liệu lưu trữ đã làm sạch. | Đỗ Kiến Hưng |
| **Phát triển RAG & Vector Store** | Tuần 8 - 10 | - Tách đoạn văn bản thể lệ và tạo vector embedding.<br>- Xây dựng API tra cứu tài liệu theo kỹ thuật Hybrid Search.<br>- Đánh giá độ chính xác câu trả lời của mô hình RAG. | - Dịch vụ RAG hoàn chỉnh.<br>- Báo cáo thử nghiệm độ chính xác. | Nguyễn Văn Quang Duy |
| **Phát triển Giao diện & BI** | Tuần 11 - 13 | - Xây dựng giao diện Web cho sinh viên tìm kiếm và hỏi đáp.<br>- Xây dựng trang phân tích số liệu cho quản trị viên.<br>- Tích hợp Backend API với giao diện người dùng. | - Ứng dụng Web MVP chạy ổn định.<br>- Dashboard phân tích dữ liệu. | Đỗ Kiến Hưng<br>Nguyễn Văn Quang Duy |
| **Đánh giá & Báo cáo** | Tuần 14 - 15 | - Kiểm thử toàn diện hệ thống và tối ưu hiệu năng.<br>- Viết báo cáo toàn văn theo quy định của Khoa CNTT.<br>- Chuẩn bị slide và báo cáo trước Hội đồng bảo vệ (~07/12/2026). | - Báo cáo toàn văn TLCN.<br>- Slide báo cáo & Source code. | Đỗ Kiến Hưng<br>Nguyễn Văn Quang Duy |

---

## V. XÁC NHẬN CỦA CÁC BÊN

**TP. Hồ Chí Minh, ngày 23 tháng 08 năm 2026**

| Sinh viên thực hiện 1 | Sinh viên thực hiện 2 | Giảng viên hướng dẫn |
| :---: | :---: | :---: |
| *(Ký và ghi rõ họ tên)* | *(Ký và ghi rõ họ tên)* | *(Ký và ghi rõ họ tên)* |
| <br><br>**Đỗ Kiến Hưng** | <br><br>**Nguyễn Văn Quang Duy** | <br><br>**ThS. Trần Quang Khải** |
