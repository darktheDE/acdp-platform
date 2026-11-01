# BÁO CÁO KẾ HOẠCH VÀ TIẾN ĐỘ THỰC HIỆN TIỂU LUẬN CHUYÊN NGÀNH
*(Báo cáo định kỳ gửi Giáo viên hướng dẫn: ThS. Trần Quang Khải)*

**TRƯỜNG ĐẠI HỌC CÔNG NGHỆ KỸ THUẬT TP.HCM (HCM-UTE)**  
**KHOA CÔNG NGHỆ THÔNG TIN — BỘ MÔN HỆ THỐNG THÔNG TIN**  
**CHUYÊN NGÀNH: KỸ THUẬT DỮ LIỆU**

---

| Hạng mục thông tin | Chi tiết đăng ký |
| :--- | :--- |
| **Tên đề tài** | XÂY DỰNG HỆ THỐNG THU THẬP, XỬ LÝ DỮ LIỆU VÀ NỀN TẢNG HỖ TRỢ SINH VIÊN THAM GIA CÁC CUỘC THI HỌC THUẬT, CÔNG NGHỆ |
| **Sinh viên thực hiện 1** | Nguyễn Văn Quang Duy (MSSV 1: `23110086`) |
| **Sinh viên thực hiện 2** | Đỗ Kiến Hưng (MSSV 2: `23133030`) |
| **Giáo viên hướng dẫn khoa học** | ThS. Trần Quang Khải |
| **Thời gian báo cáo** | Tuần 9 (Học kỳ 1, Năm học 2026–2027) |
| **Giai đoạn hiện tại** | Hoàn thành thu thập Tầng Bronze trên bộ 7 cuộc thi mẫu và triển khai trích xuất Tầng Bạc (Silver Layer) |

---

## 1. TÓM TẮT TỔNG QUAN TIẾN ĐỘ HIỆN TẠI

Tính đến hết Tuần 9 của học phần Tiểu luận chuyên ngành, nhóm nghiên cứu đã bám sát đề cương khoa học và tập trung kiểm chứng tính khả thi của đường ống Kỹ thuật Dữ liệu (Data Engineering Pipeline) trên quy mô **5–10 cuộc thi học thuật tiêu biểu** (7 cuộc thi mẫu thực tế) trước khi mở rộng quy mô tự động hóa ở giai đoạn Khóa luận tốt nghiệp:

1. **Khảo sát & Cơ sở lý thuyết**: Hoàn thành nghiên cứu tài liệu từ các hội nghị quốc tế (CIDR, VLDB, NeurIPS, SIGMOD), đánh giá đối sánh các nền tảng thực tế (Devpost, Unstop, Ybox) và thống nhất bộ công nghệ Medallion Lakehouse tinh gọn phù hợp quy mô 5–10 cuộc thi trên máy trạm 16GB RAM (loại bỏ các bước nén trung gian không cần thiết như Zstandard hay cụm máy ảo JVM/Spark cồng kềnh).
2. **Tầng Thu thập & Tầng Đồng (Bronze Layer)**: Cài đặt kịch bản thu thập theo yêu cầu (`src/acdp/1_crawl_to_bronze.py`) sử dụng `Crawl4AI` (`AdaptiveCrawler`) để cào và làm sạch nội dung văn bản Markdown (`UTF-8`) từ 7 cuộc thi thực tế (*Code Tour, AI Challenge TP.HCM, Vietnam AI Challenge, DataDNA Onyx, IT Consultant Challenge, RMIT Hackathon, HackAITHON*) và đẩy trực tiếp lên kho lưu trữ đối tượng đám mây **Cloudflare R2** (`s3://acdp-lakehouse/bronze/`).
3. **Thiết kế Lược đồ Lớp Bạc (Silver Schema)**: Hoàn thành thiết kế lớp dữ liệu `SilverCompetitionRecord` trên Pydantic v2 (`src/acdp/lakehouse/schema.py`) với 8 nhóm thuộc tính định lượng, tập trung vào các trường thông tin thiết yếu cho sinh viên (Tên cuộc thi, đơn vị tổ chức, hạn chót đăng ký, link đăng ký, cơ cấu giải thưởng, điều kiện nhóm và tóm tắt thể lệ). Tích hợp hàm sinh mã băm đại diện `generate_fingerprint()` và khởi tạo module trích xuất có cấu trúc bằng thư viện `instructor` (`src/acdp/2_instruction.py`).
4. **Kiểm thử tự động**: Xây dựng và vượt qua 100% bộ 7 bài kiểm thử đơn vị (`tests/test_bronze_storage.py` và `tests/test_silver_schema.py`).

---

## 2. BẢNG TIẾN ĐỘ THỰC HIỆN TIỂU LUẬN CHUYÊN NGÀNH

Bảng dưới đây trình bày chi tiết các công việc nhóm **ĐÃ HOÀN THÀNH** (Tuần 1 đến Tuần 9), công việc **TRỌNG TÂM SẼ THỰC HIỆN TRONG TUẦN TỚI** (Tuần 10), và kế hoạch dự kiến cho các tuần tiếp theo:

### Bảng: Báo cáo tiến độ thực tế học phần Tiểu luận chuyên ngành

| STT | Tuần / Thời gian | Tình trạng | Nội dung công việc chi tiết | Sản phẩm / Minh chứng kỹ thuật | Phụ trách |
| :---: | :---: | :---: | :--- | :--- | :---: |
| **1** | Tuần 1<br>(31/8 - 6/9) | **ĐÃ LÀM** | Khảo sát nhu cầu thực tế của sinh viên FIT-HCMUTE; phân tích 4 nút thắt tiếp cận thông tin; thiết lập kho lưu trữ Git và môi trường dự án. | Bản khảo sát nhu cầu sinh viên; Cấu hình kho lưu trữ ban đầu. | Hưng<br>Duy |
| **2** | Tuần 2<br>(7/9 - 13/9) | **ĐÃ LÀM** | Nghiên cứu tổng quan tài liệu khoa học quốc tế (Cho, Armbrust, Lewis, Xu); phân tích đối sánh các nền tảng thực tế; khởi tạo R&D Task T01 và T02. | Báo cáo R&D T01, T02; Bảng đối sánh nền tảng học thuật. | Duy |
| **3** | Tuần 3<br>(14/9 - 20/9) | **ĐÃ LÀM** | Thiết kế kiến trúc phân tầng 4 lớp; phân định ranh giới TLCN (mô phỏng khả thi trên 5–10 cuộc thi) và KLTN (mở rộng quy mô và tự động hóa); báo cáo đề cương với GVHD ThS. Trần Quang Khải. | Bản Thuyết minh đề tài; Slide báo cáo đề cương. | Hưng<br>Duy |
| **4** | Tuần 4<br>(21/9 - 27/9) | **ĐÃ LÀM** | Đánh giá công cụ cào web động Playwright và Crawl4AI; thu thập bộ dữ liệu kiểm thử thực tế từ 7 cuộc thi trọng điểm (Code Tour, AI Challenge TP.HCM, DataDNA, HackAITHON...). | Bộ dữ liệu 7 cuộc thi mẫu tại `data/raw/html/` và `data/raw/markdown/`. | Duy<br>Hưng |
| **5** | Tuần 5<br>(28/9 - 4/10) | **ĐÃ LÀM** | Nghiên cứu tầng lưu trữ Bronze (Task T13); đối sánh các phương án lưu trữ (Local Files, Cloudflare R2, SeaweedFS) và định dạng bảng; chốt phương án tối giản cho quy mô 5–10 cuộc thi. | Báo cáo nghiệm thu NT-018; Đặc tả kỹ thuật SPEC-0001 & SPEC-0002. | Duy<br>Hưng |
| **6** | Tuần 6<br>(5/10 - 11/10) | **ĐÃ LÀM** | Xây dựng module quản lý cấu hình và tiện ích lưu trữ tầng Bronze (`src/acdp/lakehouse/bronze.py`) kèm bộ kiểm thử tự động. | Module `src/acdp/lakehouse/bronze.py`; 5 bài test `test_bronze_storage.py` (Passed 100%). | Hưng |
| **7** | Tuần 7<br>(12/10 - 18/10) | **ĐÃ LÀM** | Thiết kế lược đồ dữ liệu lớp Bạc (Silver Schema) trên Pydantic v2; xây dựng hàm sinh mã băm đại diện `generate_fingerprint()` và kiểm kiểu dữ liệu tài chính. | Lớp `SilverCompetitionRecord` tại `schema.py`; Bộ test `test_silver_schema.py` (Passed 100%). | Duy |
| **8** | Tuần 8<br>(19/10 - 25/10) | **ĐÃ LÀM** | Thiết lập Bucket `acdp-lakehouse` trên Cloudflare R2; xây dựng tài liệu hướng dẫn đồng bộ dữ liệu đám mây giữa hai thành viên và hoàn thiện bản thảo báo cáo TLCN. | Tài liệu `HUONG_DAN_MIGRATE_R2_LAKEHOUSE.md` (NT-022); Bản thảo báo cáo TLCN. | Hưng<br>Duy |
| **9** | Tuần 9<br>(26/10 - 1/11) | **ĐÃ LÀM** | Cài đặt kịch bản `src/acdp/1_crawl_to_bronze.py` tích hợp `Crawl4AI AdaptiveCrawler` đẩy trực tiếp văn bản Markdown của 7 cuộc thi lên tầng Bronze Cloudflare R2; tích hợp thư viện `instructor` & `litellm` (`src/acdp/2_instruction.py`) và chốt phương án tinh giản bộ công nghệ (lược bỏ nén Zstandard dư thừa). | Kịch bản `1_crawl_to_bronze.py`; Dữ liệu Markdown trên R2; Khởi tạo `2_instruction.py`. | Duy<br>Hưng |
| **10** | **Tuần 10**<br>**(2/11 - 8/11)** | **SẼ LÀM TRONG TUẦN TỚI** | **1. Hoàn thiện kịch bản `src/acdp/2_instruction.py` sử dụng `instructor` để trích xuất 7 file Markdown từ tầng Bronze sang thực thể `SilverCompetitionRecord` và lưu thành tệp Parquet trên R2.<br>2. Dọn dẹp dependency `zstandard` trong `src/acdp/lakehouse/` và xây dựng các câu truy vấn phân tích SQL OLAP (Tầng Gold) trực tiếp bằng DuckDB trên tập 7 cuộc thi.** | **Bộ dữ liệu Silver Parquet của 7 cuộc thi trên R2; Tập truy vấn phân tích DuckDB Tầng Gold.** | **Duy**<br>**Hưng** |
| 11 | Tuần 11<br>(9/11 - 15/11) | *Dự kiến* | Cài đặt cơ sở dữ liệu vector Qdrant; phân đoạn văn bản thể lệ của 7 cuộc thi mẫu theo cấu trúc điều khoản và tạo vector nhúng. | Module phân đoạn điều khoản và chỉ mục vector trên Qdrant. | Duy |
| 12 | Tuần 12<br>(16/11 - 22/11) | *Dự kiến* | Xây dựng pipeline Hybrid Search (BM25 + Dense Vectors + Cross-Encoder re-ranking) trên tập thể lệ mẫu; đánh giá chất lượng câu trả lời theo khung Ragas. | Module Hybrid RAG; Bảng điểm đo lường Ragas. | Duy |
| 13 | Tuần 13<br>(23/11 - 29/11) | *Dự kiến* | Xây dựng Backend REST API bằng FastAPI cung cấp các endpoint tra cứu danh sách cuộc thi từ DuckDB và hỏi đáp thể lệ qua RAG. | Mã nguồn FastAPI backend; Tài liệu OpenAPI. | Hưng |
| 14 | Tuần 14<br>(30/11 - 6/12) | *Dự kiến* | Xây dựng giao diện Web Portal sinh viên và màn hình biểu đồ thống kê cho Khoa CNTT (Next.js 15, Tailwind CSS). | Giao diện Web Portal sinh viên; Màn hình Dashboard thống kê. | Hưng<br>Duy |
| 15 | Tuần 15<br>(7/12 - 13/12) | *Dự kiến* | Kiểm thử tích hợp toàn hệ thống trên bộ dữ liệu mẫu; hoàn thiện toàn văn quyển báo cáo Tiểu luận chuyên ngành và slide bảo vệ trước Hội đồng. | Toàn văn Báo cáo TLCN; Slide bảo vệ đề tài. | Hưng<br>Duy |

---

## 3. CHI TIẾT CÁC CÔNG VIỆC TRỌNG TÂM TRONG TUẦN TỚI (TUẦN 10)

Trong tuần tiếp theo (từ ngày 02/11 đến 08/11/2026), nhóm nghiên cứu tập trung giải quyết các nhiệm vụ kỹ thuật trên bộ 7 cuộc thi mẫu:

1. **Hoàn thiện Pipeline trích xuất có cấu trúc Bronze sang Silver (`src/acdp/2_instruction.py`)**:
   - Đọc nội dung văn bản Markdown nguyên bản của 7 cuộc thi từ tầng Bronze trên Cloudflare R2 (hoặc `data/raw/markdown/`).
   - Sử dụng thư viện `instructor` kết hợp `litellm` để ép kiểu phản hồi của mô hình ngôn ngữ lớn theo đúng schema `SilverCompetitionRecord` (Pydantic v2).
   - Chuẩn hóa toàn bộ ngày tháng sang chuẩn ISO 8601 (`YYYY-MM-DD`), giá trị giải thưởng sang kiểu số nguyên VND và xuất kết quả ra tệp `silver/competitions.parquet` trên Cloudflare R2.
2. **Tinh giản mã nguồn Lakehouse & Truy vấn phân tích Tầng Gold bằng DuckDB**:
   - Loại bỏ bước nén `zstandard` cũ trong `src/acdp/lakehouse/` để đồng nhất với định dạng Markdown/Parquet thuần trên R2.
   - Sử dụng động cơ phân tích in-process `DuckDB` (kèm extension `httpfs`) đọc trực tiếp tệp `silver/competitions.parquet` từ Cloudflare R2 để thống kê tổng giải thưởng, phân bố cuộc thi theo lĩnh vực và thời hạn đăng ký.

---

## 4. CÁC NỘI DUNG XIN Ý KIẾN CHỈ ĐẠO CỦA GIÁO VIÊN HƯỚNG DẪN

Nhóm kính mong nhận được ý kiến góp ý và định hướng của ThS. Trần Quang Khải về các nội dung sau:

1. **Về phạm vi dữ liệu thực nghiệm của giai đoạn Tiểu luận chuyên ngành (5–10 cuộc thi)**:
   - Trong giai đoạn Tiểu luận chuyên ngành hiện tại, nhóm giới hạn phạm vi ở **5–10 cuộc thi tiêu biểu** (7 cuộc thi thực tế đã thu thập) chạy theo yêu cầu (on-demand) nhằm tập trung hoàn thiện trọn vẹn đường ống từ khâu cào web, trích xuất Pydantic Schema, lưu trữ R2/DuckDB đến hỏi đáp RAG. Các bài toán cào tự động số lượng lớn theo lịch định kỳ (batch job) hoặc thời gian thực (realtime) được nhóm định hướng đưa vào giai đoạn **Khóa luận tốt nghiệp**.
   - Kính xin Thầy cho ý kiến về sự phân bổ phạm vi này giữa hai học phần.
2. **Về việc tinh giản bộ công nghệ lưu trữ theo quy mô dữ liệu**:
   - Với quy mô 5–10 cuộc thi (dung lượng văn bản dưới 1.5MB), nhóm đã lược bỏ bước nén nhị phân Zstandard trung gian để lưu trực tiếp văn bản Markdown (`UTF-8`) ở tầng Bronze và tệp Parquet ở tầng Silver trên Cloudflare R2, giúp dễ dàng kiểm tra dữ liệu trực tiếp và truy vấn tức thời bằng DuckDB.

---
*Kính chúc Thầy nhiều sức khỏe và công tác tốt!*  
**Nhóm sinh viên thực hiện đề tài**: Nguyễn Văn Quang Duy & Đỗ Kiến Hưng
