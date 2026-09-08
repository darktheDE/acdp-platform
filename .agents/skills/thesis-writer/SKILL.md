---
name: thesis-writer
description: Guide the drafting of formal academic manuscripts, undergraduate theses, and scientific proposals conforming strictly to FIT-HCMUTE formatting rules and academic writing conventions.
---

# Thesis Writer Skill

This skill guides the AI agent in drafting formal academic manuscripts, reports, and chapter drafts in Vietnamese or English, conforming strictly to the regulations of the Faculty of Information Technology, Ho Chi Minh City University of Technology and Engineering (FIT-HCMUTE).

---

## 1. When to Activate This Skill
Activate this skill whenever the user prompts for:
- Drafting or revising thesis chapters (Chương 1 đến Chương 5).
- Writing formal academic sections (Mục tiêu đề tài, Cơ sở lý thuyết, Thiết kế kiến trúc, Đánh giá thực nghiệm).
- Converting informal engineering notes into publication-grade academic prose.
- Generating formal LaTeX or Markdown chapters with properly numbered equations, tables, figures, and citations.

---

## 2. FIT-HCMUTE Thesis Structural Standards

A standard thesis manuscript under FIT-HCMUTE must be organized into 5 core chapters:

### Chương 1: Giới thiệu và Tổng quan đề tài (Introduction)
- **1.1. Đặt vấn đề & Tính cấp thiết**: Nêu rõ 4 nút thắt (thông tin phân tán, thể lệ phức tạp, khó tìm đội/GVHD, thiếu công cụ thống kê cho Khoa).
- **1.2. Mục tiêu nghiên cứu**: Mục tiêu tổng quát và 4 mục tiêu cụ thể.
- **1.3. Đối tượng và Phạm vi nghiên cứu**: Phân định rõ phạm vi 15 tuần Tiểu luận chuyên ngành (MVP) và 15 tuần Khóa luận tốt nghiệp.
- **1.4. Bố cục báo cáo**: Tóm tắt nội dung các chương tiếp theo.

### Chương 2: Cơ sở lý thuyết và Tổng quan nghiên cứu (Theoretical Foundations)
- **2.1. Kiến trúc Data Lakehouse & Mô hình Medallion**: Nguyên lý lưu trữ phân tầng Bronze, Silver, Gold; cơ chế ACID và định dạng cột (Parquet).
- **2.2. Trích xuất thông tin bằng LLM kết hợp Headless Scraping**: Crawl4AI, Playwright, Schema Enforcement với Pydantic.
- **2.3. Kỹ thuật Retrieval-Augmented Generation (RAG)**: Chunking văn bản thể lệ, Dense Embeddings, Vector Database (Qdrant), BM25, Cross-Encoder Re-ranking.
- **2.4. Thuật toán gợi ý ghép đội & ghép cặp nghiên cứu**: Độ tương đồng cosine trên vector kỹ năng, bài toán tối ưu ràng buộc (Constraint Satisfaction).
- **2.5. Khảo sát các công trình liên quan**: So sánh với Devpost, Unstop, StudentCompetitions và các nghiên cứu RAG học thuật.

### Chương 3: Thiết kế kiến trúc và Hệ thống (System Architecture & Design)
- **3.1. Kiến trúc tổng thể hệ thống**: Sơ đồ 4 phân tầng (Ingestion, Lakehouse, Semantic AI, Serving).
- **3.2. Thiết kế tầng Thu thập dữ liệu (Ingestion Layer)**: Workflow bóc tách schema JSON từ bài đăng fanpage/web động.
- **3.3. Thiết kế tầng Lưu trữ & Xử lý (Lakehouse Layer)**: Mô hình dữ liệu DuckDB, pipeline dbt, thuật toán khử trùng lặp sự kiện (Fuzzy Matching).
- **3.4. Thiết kế tầng AI & Tra cứu (Semantic & RAG Layer)**: Pipeline index tài liệu, Hybrid Search, prompt template kiểm soát chống ảo giác.
- **3.5. Thiết kế tầng Ứng dụng & Bảng điều khiển (Serving Layer)**: Thiết kế REST API (FastAPI) và giao diện Web (Next.js 15).

### Chương 4: Cài đặt thực nghiệm và Đánh giá (Implementation & Evaluation)
- **4.1. Môi trường cài đặt & Công nghệ**: Thông số phần cứng, Docker, phiên bản thư viện.
- **4.2. Triển khai các phân hệ cốt lõi**: Trình bày kết quả cài đặt thực tế từng tầng.
- **4.3. Kịch bản thực nghiệm & Bộ dữ liệu kiểm thử**: Thu thập từ 5–10 nguồn thực tế.
- **4.4. Đánh giá định lượng & Định tính**: Đo độ trễ pipeline, đo độ chính xác trích xuất schema, đánh giá độ chính xác câu trả lời RAG theo khung Ragas (Faithfulness, Answer Relevance).

### Chương 5: Kết luận và Hướng phát triển (Conclusion & Future Work)
- **5.1. Kết quả đạt được**: Đối chiếu với mục tiêu đặt ra ban đầu.
- **5.2. Hạn chế còn tồn đọng**: Những điểm chưa giải quyết trọn vẹn trong phạm vi TLCN.
- **5.3. Hướng phát triển cho Khóa luận tốt nghiệp**: Mở rộng streaming, bot tự động, tính năng khen thưởng.

---

## 3. Stylistic & Linguistic Rules
1. **Academic Tone**: Use objective, formal, third-person perspective (*"Nhóm nghiên cứu nhận thấy...", "Hệ thống được thiết kế...", "Kết quả thực nghiệm chỉ ra..."*). Never use informal first-person singular pronouns (*"tôi", "mình"*).
2. **Standardized Terminology**:
   - Sử dụng thuật ngữ chuyên ngành chuẩn hóa (VD: *Đường ống dữ liệu* hoặc *Data Pipeline*, *Kho dữ liệu hồ* hoặc *Data Lakehouse*, *Truy xuất thông tin tăng cường* hoặc *RAG*).
   - Đối với các từ viết tắt lần đầu xuất hiện, phải viết rõ từ nguyên bản và từ viết tắt trong ngoặc đơn: *Mô hình ngôn ngữ lớn (Large Language Model - LLM)*.
3. **Cross-Referencing**: Every table, figure, and formula must be explicitly referenced in the text (*"như thể hiện trong Hình 3.2"*, *"bảng số liệu Bảng 4.1"*).
4. **Citation Discipline**: Always link empirical claims, algorithms, and architectures to valid citations using `\cite{...}` in LaTeX or `[Author, Year]` in Markdown.
