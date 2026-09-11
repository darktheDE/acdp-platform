# DELIVERABLE: Business Requirements, Technical Feasibility, and Architectural Review (T01 Review)

- **Notion Task ID**: `NT-013`
- **Related Sprint**: Sprint 01 (Week 1–Week 3: Foundation, Harness & Ingestion Design)
- **Primary Owner**: Do Kien Hung & Nguyen Van Quang Duy
- **Date Completed**: 2026-09-11
- **Deliverable Type**: Feasibility Study & Architectural Alignment Review
- **Status**: Complete & Verified

---

## 1. Executive Summary & Objective

Tài liệu này giải quyết và phản biện toàn diện 5 trăn trở nghiệp vụ và kỹ thuật được nêu ra trong task [`docs/rd-tasks/T01.md`](../rd-tasks/T01.md). Mục tiêu chính:
1. **Làm rõ ranh giới bài toán**: Khảo sát tính khả thi giữa bài toán Tìm kiếm (Discovery) vs. Cào có định hướng (Targeted Crawling).
2. **Bảo vệ tính chuyên ngành Kỹ thuật Dữ liệu (Data Engineering)**: Khẳng định vai trò sống còn của việc chuyển đổi văn bản phi cấu trúc thành dữ liệu có cấu trúc (Information Extraction via LLM/Pydantic) để xây dựng kho Lakehouse Medallion và Dashboard phân tích chiều dữ liệu (OLAP).
3. **Tinh giản phạm vi 15 tuần MVP (Tiểu luận chuyên ngành)**: Lược bỏ các tính năng gây rủi ro bảo mật (thông tin giảng viên) hoặc gây nghẽn tiến độ (cụm Airflow cồng kềnh), giữ lại bộ khung tinh gọn, hiệu quả cao.

---

## 2. Detailed Research Findings & Five-Point Feasibility Matrix

Dưới đây là bản đối chiếu chi tiết theo cấu trúc chuẩn **Problem - Action - Possibility** cho từng vấn đề nghiệp vụ trong [`docs/rd-tasks/T01.md`](../rd-tasks/T01.md):

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                             BẢN ĐỒ PHẢN BIỆN NGHIỆP VỤ & KỸ THUẬT (T01)                         │
├────────────────────────────────┬────────────────────────────────────────┬────────────────────────┤
│ Vấn đề nghiệp vụ (T01)         │ Giải pháp kỹ thuật (Action)            │ Tính khả thi & Đánh giá│
├────────────────────────────────┼────────────────────────────────────────┼────────────────────────┤
│ 1. Search vs. Ingestion & Đa   │ Hybrid Ingestion (Seed Sources + Agent │ Khả thi: 9/10          │
│    nguồn trùng lặp (Dedup)     │ Search) & Bronze Multi-source, Silver  │ Tránh phụ thuộc 100%   │
│                                │ Entity Resolution (Fuzzy Matching).    │ vào Search API.        │
├────────────────────────────────┼────────────────────────────────────────┼────────────────────────┤
│ 2. Sự tham gia của Giảng viên  │ Phase 1: Lược bỏ hoàn toàn role GV.    │ Khả thi: 10/10         │
│    (Quyền riêng tư & Quản lý)  │ Phase 2: Đề xuất hướng nghiên cứu & bộ │ Giảm 40% tải giao diện │
│                                │ môn phù hợp dựa trên dữ liệu công khai.│ và tránh rủi ro pháp lý│
├────────────────────────────────┼────────────────────────────────────────┼────────────────────────┤
│ 3. Thiếu tài liệu cũ & Cold-   │ Seed Data First (15-20 bộ đề ICPC,     │ Khả thi: 8.5/10        │
│    start của tính năng review  │ Euréka) + Crawl bài review từ cộng     │ Giải quyết triệt để bài│
│                                │ đồng + Aspect-Based Sentiment Analysis.│ toán Cold-Start.       │
├────────────────────────────────┼────────────────────────────────────────┼────────────────────────┤
│ 4. Dữ liệu văn bản khó làm     │ Khẳng định: Text -> Structured ELT là  │ BẮT BUỘC & Khả thi     │
│    Analytics, chỉ đếm số lượng │ cốt lõi Data Engineering! LLM Pydantic │ 9.5/10. Tạo nên điểm   │
│                                │ trích xuất 10+ trường định lượng/chiều.│ nhấn của đề tài.       │
├────────────────────────────────┼────────────────────────────────────────┼────────────────────────┤
│ 5. Vội vã chọn công nghệ,      │ Tinh giản hóa (Lean Stack): Bỏ Airflow,│ Khả thi: 10/10         │
│    nguy cơ over-engineering    │ bỏ Scrapy. Giữ DuckDB + Postgres +     │ Phù hợp hoàn hảo với   │
│                                │ Crawl4AI + FastAPI + Next.js 15.       │ nhóm 2 SV trong 15 tuần│
└────────────────────────────────┴────────────────────────────────────────┴────────────────────────┘
```

---

### Vấn đề 1: Đa nguồn và Khử trùng lặp sự kiện (Multi-source Ingestion & Deduplication)

#### Problem
Khi chuyển sang bài toán tìm kiếm (Agentic Search / Discovery), cùng một cuộc thi (như *ICPC National 2026*, *Euréka 2026*, *Olympic Tin học*) sẽ xuất hiện đồng thời trên nhiều kênh:
- **Trang chủ chính thức của Ban tổ chức (BTC)**: Thông tin điều lệ chuẩn xác nhất, có file PDF thể lệ và link nộp bài chính thức.
- **Fanpage Khoa / Đoàn trường**: Cập nhật tóm tắt, lịch trình sơ tuyển nội bộ trường, thông báo gia hạn hạn chót (extension) nhanh hơn website.
- **Trang tin tổng hợp sinh viên (Ybox, vncontest)**: Bài viết tổng quan, nhưng dễ trễ hạn hoặc thiếu chi tiết.
- *Câu hỏi*: Nên lấy nguồn nào? Lấy cả hai hay bỏ bớt?

#### Action
1. **Chiến lược Hybrid Ingestion (Seed Sources + Agentic Discovery)**:
   - Không chuyển dịch 100% sang Agentic Search tự do vì chi phí API (SerpApi/Tavily), rate limit và độ trễ cao.
   - Giữ **5–10 nguồn hạt giống (Seed Sources)** cố định cào theo lịch: Website ICPC Vietnam, Eureka Thành Đoàn, Cổng thông tin Khoa CNTT HCMUTE, Fanpage Đoàn - Hội FIT.
   - Sử dụng Agentic Search quét hàng tuần với query có cấu trúc nhằm phát hiện cuộc thi mới bên ngoài danh sách seed.
2. **Cơ chế Hợp nhất Medallion (Deduplication & Entity Resolution)**:
   - **Tầng Bronze (Raw)**: Thu thập và lưu giữ **TẤT CẢ** các nguồn bài viết. Không lọc bỏ bất kỳ dữ liệu thô nào.
   - **Tầng Silver (Cleaned & Consolidated)**:
     - Áp dụng thuật toán so khớp chuỗi mờ (*Fuzzy String Matching* qua `rapidfuzz` hoặc Cosine Distance trên Text Embedding) dựa trên bộ ba thuộc tính: `normalized_title`, `edition_year`, và `organizer_name`.
     - Tạo ra một thực thể chuẩn (**Canonical Competition Entity**).
     - Gán trọng số tin cậy: `Website BTC (1.0) > Cổng thông tin Trường/Khoa (0.8) > Fanpage (0.7) > Aggregator (0.5)`.
     - *Quy tắc hợp nhất thể lệ*: Ưu tiên văn bản thể lệ từ Website BTC.
     - *Quy tắc cập nhật hạn chót*: Nếu bài đăng Fanpage có thông báo gia hạn với timestamp mới hơn thời hạn ban đầu, cập nhật trường `registration_deadline` và kích hoạt cờ `is_deadline_extended = True`.
     - Lưu trường `source_urls` dạng mảng: `[{"source": "BTC Web", "url": "..."}, {"source": "FIT Fanpage", "url": "..."}]` để sinh viên có thể kiểm chứng đa kênh.

#### Possibility & Metrics
- **Độ khả thi**: 9/10.
- **Tài nguyên**: Xử lý hoàn toàn in-process bằng DuckDB và thư viện Python `rapidfuzz`, chi phí RAM < 200MB, tốc độ tính toán hàng nghìn bản ghi chỉ trong vài giây.

---

### Vấn đề 2: Giảng viên có nên tham gia quản trị & Sử dụng sản phẩm?

#### Problem
- Rủi ro quyền riêng tư (Privacy) và quy định nội bộ: Tự ý đưa số điện thoại, email cá nhân của giảng viên lên nền tảng khi chưa được phê duyệt có thể gây rắc rối về mặt quy chế.
- Tính khả thi thực tế (User Adoption): Giảng viên có khối lượng công việc giảng dạy và nghiên cứu rất lớn; việc yêu cầu giảng viên đăng nhập một portal mới để "duyệt đội sinh viên" hoặc "quản lý cuộc thi" là phi thực tế.
- Rào cản tâm lý: Đa phần giảng viên không sẵn lòng nhận lời hướng dẫn nhóm sinh viên xa lạ khi chưa rõ năng lực.

#### Action
1. **Quyết định cho Phase 1 (Tiểu luận chuyên ngành - 15 tuần MVP)**:
   - **LƯỢC BỎ HOÀN TOÀN** role Giảng viên và tính năng kết nối trực tiếp SV-GV.
   - Hệ thống chỉ có 2 nhóm người dùng:
     - **Sinh viên (End-User)**: Tra cứu cuộc thi, hỏi đáp thể lệ qua AI Copilot, lọc tìm kiếm.
     - **Quản trị viên Khoa (Admin)**: Xem Dashboard thống kê tổng quan.
2. **Định vị lại cho Phase 2 (Khóa luận tốt nghiệp)**:
   - Chuyển thành tính năng **"Gợi ý Hướng nghiên cứu & Bộ môn liên quan" (Research Domain Recommendation)**:
     - Chỉ khai thác thông tin **công khai** từ website Khoa CNTT (Họ tên Thầy/Cô, Bộ môn, Hướng nghiên cứu chính trên Cổng thông tin Khoa hoặc Google Scholar).
     - Khi sinh viên quan tâm cuộc thi về Xử lý ảnh / AI, hệ thống hiển thị thông tin tham khảo: *"Cuộc thi này liên quan đến hướng nghiên cứu Thị giác máy tính của Bộ môn Khoa học máy tính"*.
     - Cung cấp tính năng "Xuất bản tóm tắt ý tưởng dự thi (1-page Proposal PDF)" để sinh viên chủ động mang đến văn phòng Bộ môn xin ý kiến hướng dẫn một cách chuyên nghiệp.

#### Possibility & Metrics
- **Độ khả thi**: 10/10. Quyết định này giúp loại bỏ 40% khối lượng code không cần thiết trong Phase 1 và bảo đảm an toàn thông tin 100%.

---

### Vấn đề 3: Kho tài liệu cũ & Giải quyết bài toán Cold-Start của Review tiền bối

#### Problem
- Tài liệu đề thi và giải pháp các năm trước thường nằm phân tán trong kho lưu trữ cá nhân của thí sinh, nhiều cuộc thi không công khai source code.
- Vấn đề **Cold-Start**: Nếu phụ thuộc vào việc "chờ người dùng vào comment rồi mới chạy Sentiment Analysis", hệ thống mới triển khai sẽ có 0 comment, khiến tính năng phân tích bị tê liệt hoàn toàn.

#### Action
1. **Chiến lược "Seed Knowledge First"**:
   - Chủ động thu thập và chuẩn hóa dữ liệu từ 3 nhóm cuộc thi lớn có tài liệu công khai:
     - *Olympic Tin học & ICPC*: Đề thi, bộ test và lời giải bài thi các năm có sẵn trên `vnoi.info`.
     - *Euréka & NCKH Sinh viên*: Kỷ yếu tóm tắt các công trình đạt giải hàng năm do Thành Đoàn TP.HCM công bố.
     - *Kaggle / Open Hackathons*: Các repository mã nguồn mở và write-up của các đội quán quân trên GitHub / Medium.
   - Nhóm nạp trước 15–20 bộ tài liệu mẫu này vào cơ sở dữ liệu vector (Qdrant) để làm dữ liệu nền tảng ngay từ ngày đầu nghiệm thu.
2. **Thu thập Review từ các kênh thảo luận cộng đồng**:
   - Dùng crawler thu thập các bài viết chia sẻ kinh nghiệm ("Review thi Euréka", "Kinh nghiệm thi ICPC") từ các group sinh viên công nghệ thông tin.
3. **Mô hình Phân tích Khía cạnh (Aspect-Based Sentiment Analysis - ABSA)**:
   - Không chỉ dừng lại ở nhãn chung chung (Tích cực / Tiêu cực).
   - Sử dụng LLM Schema Parser bóc tách theo các khía cạnh nghiệp vụ cụ thể:
     - *Độ khó đề thi*: Khó, trung bình, dễ.
     - *Chất lượng khâu tổ chức*: Chuyên nghiệp, đúng giờ, hỗ trợ thí sinh tốt.
     - *Cơ hội nghề nghiệp*: Giá trị kết nối doanh nghiệp, cơ hội thực tập.

#### Possibility & Metrics
- **Độ khả thi**: 8.5/10. Việc nạp dữ liệu mồi (Seed data) loại bỏ hoàn toàn rủi ro Cold-Start.

---

### Vấn đề 4: Giá trị phân tích dữ liệu văn bản trong Data Lakehouse (Bảo vệ tính chuyên ngành Kỹ thuật Dữ liệu)

#### Problem
- Quan điểm trong T01: *"Hầu hết dữ liệu thu thập được sẽ ở dạng văn bản, khó có thể dùng để làm dashboard analytics hoặc ít nhất chỉ có thể thống kê số cuộc thi. ⇒ Dùng để hỗ trợ cho chatbot AI làm tài liệu là chính"*.
- **Phản biện**: Đây là hiểu lầm rất nguy hiểm cho một đề tài tốt nghiệp chuyên ngành **Kỹ thuật Dữ liệu**. Nếu chỉ làm Chatbot đơn thuần và đếm số lượng cuộc thi, Hội đồng chuyên môn sẽ chất vấn về khối lượng công việc Data Engineering (Pipeline, Modeling, Lakehouse, Analytics).

#### Action: Quy trình Unstructured-to-Structured ELT hiện đại
Bằng cách áp dụng **LLM Information Extraction có kiểm soát cấu trúc qua Pydantic Schema**, toàn bộ văn bản thông báo cuộc thi được bóc tách thành các trường định lượng và thuộc tính phân loại chuẩn xác:
1. **Chiều Thời gian (Temporal Dimension)**: `registration_start_date`, `registration_deadline`, `event_date`, `duration_days`, `season_quarter` (Q1–Q4).
2. **Chiều Lĩnh vực & Công nghệ (Domain Dimension)**: Gán nhãn đa nhãn (`tags`): `AI/ML`, `Web/Mobile`, `Cybersecurity`, `Cloud/DevOps`, `Data Science`, `Algorithmic Coding`.
3. **Chiều Giải thưởng (Financial Dimension)**: `total_prize_vnd`, `first_prize_vnd` (chuẩn hóa về kiểu số nguyên `BIGINT`, ví dụ `50000000`).
4. **Chiều Điều kiện dự thi (Constraint Dimension)**: `min_team_size`, `max_team_size`, `is_individual_allowed`, `target_student_years`, `registration_fee_vnd`.
5. **Chiều Đơn vị tổ chức (Organizer Dimension)**: `organizer_type` (Doanh nghiệp, Trường Đại học, Đoàn thể, Tổ chức Quốc tế).

#### Các chỉ số Dashboard Analytics chuyên sâu (Gold Layer / dbt Data Marts):
- **Bản đồ nhiệt mùa vụ học thuật (Competition Seasonality Heatmap)**: Thống kê số lượng cuộc thi theo từng tháng trong năm để Khoa bố trí lịch học và lịch thi phù hợp.
- **Biểu đồ xu hướng công nghệ (Technology Demand Trends)**: Tỷ lệ các cuộc thi đòi hỏi kỹ năng AI/Data Science tăng trưởng ra sao so với lập trình Web truyền thống qua các năm.
- **Phân bổ ngân sách giải thưởng (Prize Pool Distribution by Domain)**: So sánh tổng giá trị tài trợ giữa các mảng chuyên môn (AI vs ATTT vs Lập trình thuật toán).
- **Tỷ lệ thi đấu cá nhân vs. đồng đội**: Đánh giá nhu cầu lập nhóm thực tế của sinh viên.

#### Possibility & Metrics
- **Độ khả thi**: 9.5/10.
- Đây chính là bằng chứng thuyết phục nhất thể hiện chuyên môn **Kỹ thuật Dữ liệu** của nhóm sinh viên Đỗ Kiến Hưng và Nguyễn Văn Quang Duy.

---

### Vấn đề 5: Tinh giản công nghệ, tránh Over-Engineering

#### Problem
- Nhóm đối mặt với nguy cơ quá tải do danh sách công nghệ ban đầu quá rộng (Playwright, Crawl4AI, Scrapy, DuckDB, Parquet, dbt-core, PostgreSQL, Qdrant, Airflow, Prefect, FastAPI, Next.js 15...).
- Nỗi lo phân tán nguồn lực trong thời gian 15 tuần của học phần Tiểu luận.

#### Action: Bộ khung công nghệ tinh giản (Lean & High-Impact Architecture)
Nhóm thực hiện "cắt tỉa" các công cụ phức tạp, giữ lại các thành phần có ROI (Return on Investment) cao nhất:
1. **Thu thập (Ingestion)**:
   - Dùng **Crawl4AI + Playwright**.
   - ❌ **Loại bỏ Scrapy** để tránh viết hai kiểu crawler khác nhau.
2. **Điều phối (Orchestration)**:
   - ❌ **Loại bỏ Apache Airflow / Prefect** trong 15 tuần đầu.
   - Thay thế bằng: Kịch bản Python CLI hoặc background runner nhẹ tích hợp sẵn trong FastAPI / cron job hệ thống.
3. **Lưu trữ & Phân tích (Storage & Analytics)**:
   - Giữ nguyên **DuckDB + Parquet** cho tầng Bronze/Silver (in-process, tốc độ cực nhanh, không cần cấu hình cụm).
   - Dùng **PostgreSQL 17** cho tầng Gold và ứng dụng Web.
4. **Vector Database**:
   - Dùng **Qdrant (1 Docker container)** hoặc extension **`pgvector`** trực tiếp trong PostgreSQL để hợp nhất một cơ sở dữ liệu duy nhất.
5. **AI & Trích xuất**:
   - Sử dụng Gemini Flash API (chi phí thấp, context window lớn, tốc độ nhanh) kết hợp Pydantic v2.

#### Possibility & Metrics
- **Độ khả thi**: 10/10. Kiến trúc này chạy mượt mà trên một máy tính cá nhân 16GB RAM hoặc Docker WSL2 mà không gặp bất kỳ điểm nghẽn tài nguyên nào.

---

## 3. Key Decisions & Roadmap Alignment

1. **Khóa phạm vi Phase 1 (15 tuần MVP - Tiểu luận chuyên ngành)**:
   - Xây dựng Ingestion Pipeline cho 5–10 nguồn trọng điểm.
   - Hoàn thiện mô hình lưu trữ Medallion (DuckDB + PostgreSQL).
   - Triển khai Hybrid RAG (BM25 + Qdrant/pgvector) hỗ trợ tra cứu thể lệ.
   - Triển khai Web MVP (Next.js 15) và Dashboard thống kê cơ bản theo các chiều dữ liệu đã bóc tách.
2. **Dời sang Phase 2 (Khóa luận tốt nghiệp)**:
   - Gợi ý hướng nghiên cứu Bộ môn / Thầy Cô.
   - Thuật toán ghép đội nâng cao.
   - Tích hợp thông báo qua Bot (Telegram/Discord).

---

## 4. Associated Artifacts & Code Links

- **Task liên quan**: [`docs/rd-tasks/T01.md`](../rd-tasks/T01.md)
- **Đăng ký đề tài**: [`docs/academic/DangKy_DeTai_TLCN.md`](../academic/DangKy_DeTai_TLCN.md)
- **Thuyết minh NCKH**: [`docs/academic/Proposal_NCKH_TLCN.md`](../academic/Proposal_NCKH_TLCN.md)
- **Kiến trúc nền tảng**: [`docs/adr/0001-medallion-lakehouse-and-rag-stack.md`](../adr/0001-medallion-lakehouse-and-rag-stack.md)
- **Tiêu chuẩn hệ thống**: [`docs/specs/0001-system-foundation-spec.md`](../specs/0001-system-foundation-spec.md)
