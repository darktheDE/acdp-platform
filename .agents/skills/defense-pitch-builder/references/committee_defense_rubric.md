# FIT-HCMUTE Committee Defense Rubric & Pacing Guide (`Quy dinh bao cao/` Mẫu 1, Mẫu 2, Mẫu 3)

This reference codifies the official evaluation rubrics (`Mẫu 1` for Đồ án CNTT & Tiểu luận chuyên ngành; `Mẫu 2` for Khóa luận tốt nghiệp), official defense time allocations (`Mẫu 3`), and adversarial Q&A preparation for the Faculty of Information Technology, Ho Chi Minh City University of Technology and Engineering (FIT-HCMUTE).

---

## 1. Official Defense Time Allocation (`Mẫu 3 - Hướng Dẫn Làm Luận Văn`, Mục IV.2)

According to `Mẫu 3` of `Quy dinh bao cao/`, the total time for a thesis/project defense session is strictly structured into three segments focusing on the three core questions ***"Làm gì? Làm như thế nào? Kết quả ra sao?"***:

| Defense Segment | Official Time Allocation (`Mẫu 3`) | Focus & Slide Mapping |
| :--- | :---: | :--- |
| **1. Slide Presentation** | **15 – 20 minutes** | - **Làm gì? (Slides 1–3, ~4 mins)**: Practical bottlenecks at FIT-HCMUTE, research objectives, and 5–10 competition TLCN scope vs KLTN scope.<br>- **Làm như thế nào? (Slides 4–7, ~7 mins)**: 4-Tier Architecture, `Crawl4AI` + `Cloudflare R2` Bronze layer, `Instructor` + `Pydantic v2` (`SilverCompetitionRecord`) Silver Parquet layer, `DuckDB` Gold OLAP, and Hybrid RAG (`BM25` + `Qdrant` + `Cross-Encoder`).<br>- **Kết quả ra sao? (Slides 8–10, ~5 mins)**: Empirical results on 7 real-world competitions (>92% HTML noise reduction, 100% schema validity), limitations, and KLTN roadmap. |
| **2. Live Program Demo** | **5 minutes** | Live end-to-end demonstration using the test dataset reported in the manuscript (`1_crawl_to_bronze.py` $\rightarrow$ `2_instruction.py` $\rightarrow$ DuckDB SQL OLAP & Web Portal / RAG query). |
| **3. Committee Q&A** | **10 minutes** | Answering reviewer (GVPB) and committee questions concisely with empirical evidence. |

---

## 2. Official Committee Evaluation Rubrics (`Mẫu 1` & `Mẫu 2`)

### 2.1. Rubric Đánh Giá Đồ Án CNTT & Tiểu Luận Chuyên Ngành (`Mẫu 1`)

| STT | Tiêu chí đánh giá (`Mẫu 1`) | Trọng số | Chuẩn Xuất Sắc (`8.5 – 10 điểm`) | Chuẩn Tốt (`7.0 – 8.4 điểm`) |
| :---: | :--- | :---: | :--- | :--- |
| **1** | **Khối lượng và tính thực tiễn của đề tài** | **30%** | Khối lượng đồ sộ, có tính thực tiễn cao, nhiều đóng góp có giá trị. | Đáp ứng đầy đủ khối lượng theo yêu cầu, có tính thực tiễn. |
| **2** | **Kiến thức cơ sở và phương pháp nghiên cứu** | **20%** | Hiểu rõ và vận dụng rất tốt kiến thức cơ sở, đề xuất cách tiếp cận sáng tạo. | Hiểu rõ và vận dụng tốt kiến thức cơ sở cùng các công trình liên quan. |
| **3** | **Kỹ năng phân tích, thiết kế và mức độ hoàn thiện sản phẩm** | **20%** | Phân tích cặn kẽ, thiết kế hoàn chỉnh, giải pháp hoàn hảo, sản phẩm đầy đủ chức năng và thẩm mỹ. | Phân tích, thiết kế hoàn chỉnh, giải pháp hợp lý, sản phẩm chạy tốt các chức năng chính. |
| **4** | **Kỹ năng tổng hợp kết quả và viết báo cáo** | **15%** | Nêu bật kết quả qua bảng biểu/đồ thị, phân tích sâu sắc; báo cáo đúng chuẩn `Mẫu 5`, súc tích, không lỗi chính tả. | Nêu bật kết quả qua bảng biểu/đồ thị; báo cáo đúng quy định, văn phong khoa học. |
| **5** | **Kỹ năng trình bày và trả lời câu hỏi** | **15%** | Trình bày thuyết phục, đúng giờ, slide trực quan; trả lời đầy đủ và chính xác các câu hỏi. | Trình bày rõ ràng, tự tin, đúng thời gian; trả lời đúng đa số câu hỏi. |

### 2.2. Rubric Đánh Giá Khóa Luận Tốt Nghiệp (`Mẫu 2`)

| STT | Tiêu chí đánh giá (`Mẫu 2`) | Trọng số | Yêu cầu cốt lõi ở mức Tốt – Xuất sắc (`7.0 – 10 điểm`) |
| :---: | :--- | :---: | :--- |
| **1** | **Tính thực tiễn của đề tài và sự hiểu biết về vấn đề** | **10%** | Có tính thực tiễn cao, giải quyết bài toán thực tế rõ ràng. |
| **2** | **Tính đúng đắn của phương pháp, thiết kế, giải pháp & hoàn thiện sản phẩm** | **40%** | Phân tích cặn kẽ, thiết kế hoàn chỉnh, giải pháp sáng tạo, sản phẩm hoàn thiện đầy đủ chức năng. |
| **3** | **Kỹ năng trình bày của sinh viên** | **10%** | Trình bày thuyết phục, đúng thời gian quy định (15–20 phút slide + 5 phút demo), slide súc tích. |
| **4** | **Khả năng đọc hiểu tài liệu tham khảo bằng ngoại ngữ** | **5%** | Tham khảo nhiều công trình tiếng Anh quốc tế uy tín (VLDB, CIDR, NeurIPS, SIGMOD), vận dụng đúng đắn. |
| **5** | **Khả năng tổng hợp kết quả và viết luận văn** | **10%** | Nêu bật và phân tích sâu kết quả qua bảng biểu/đồ thị; lập luận chặt chẽ. |
| **6** | **Hình thức của luận văn (bố cục, định dạng, chính tả)** | **5%** | Bố cục đúng chuẩn `Mẫu 5` & `Noi dung_Hinh thuc.doc` (có Kết luận từng chương, không dùng số La Mã cho mục, trích dẫn IEEE `[1]`), không lỗi chính tả. |
| **7** | **Trả lời các câu hỏi của Hội đồng** | **20%** | Trả lời trực diện, chính xác và có số liệu thực nghiệm đối chứng cho toàn bộ câu hỏi của Hội đồng. |

---

## 3. High-Frequency Committee Questions & Answering Cheat Sheet (Lean TLCN Stack - DIR-015)

- **Q1: "Tại sao trong giai đoạn Tiểu luận chuyên ngành nhóm chỉ thu thập 5–10 cuộc thi (7 cuộc thi mẫu) và lưu trực tiếp văn bản Markdown kèm DuckDB thay vì dùng PostgreSQL hay nén Zstandard?"**
  - *Answer*: Trong khuôn khổ 15 tuần của học phần Tiểu luận chuyên ngành, mục tiêu cốt lõi là kiểm chứng tính khả thi toàn trình (End-to-End Feasibility) của đường ống Kỹ thuật Dữ liệu từ khâu cào web động đến hỏi đáp RAG. Với 7 cuộc thi tiêu biểu, tổng dung lượng HTML gốc chỉ khoảng `975.6 KB` và sau khi làm sạch qua `Crawl4AI` còn `68.5 KB` văn bản Markdown (`UTF-8`, giảm hơn 92% nhiễu). Ở quy mô này, việc lưu trực tiếp văn bản `UTF-8` tại tầng Bronze trên Cloudflare R2 và tệp Parquet tại tầng Silver giúp nhóm kiểm tra dữ liệu minh bạch và truy vấn phân tích OLAP tức thời qua động cơ in-process `DuckDB` mà không phát sinh chi phí vận hành máy chủ `PostgreSQL` hay độ trễ giải nén `zstandard`. Khi mở rộng lên hàng chục ngàn bản ghi cào tự động ở Khóa luận tốt nghiệp, hệ thống mới kích hoạt nén payload và gom tệp nhỏ (`OPTIMIZE`).
- **Q2: "Làm sao ngăn chặn hiện tượng ảo giác (hallucination) khi sinh viên hỏi điều kiện dự thi hoặc hạn chót nộp bài?"**
  - *Answer*: Hệ thống kết hợp hai lớp bảo vệ: (1) Các thuộc tính định lượng như `registration_deadline`, `min_team_size`, `max_team_size`, `registration_fee_vnd` đã được ép kiểu tường minh qua `Pydantic v2` (`SilverCompetitionRecord`) với tỷ lệ hợp lệ lược đồ đạt 100%; (2) Đối với các điều khoản thể lệ chi tiết trong `rules_text_content`, hệ thống phân đoạn theo điều khoản và sử dụng Hybrid Search (`BM25` + `Qdrant`) kết hợp `Cross-Encoder Re-ranking`, cưỡng bức mô hình chỉ sinh câu trả lời kèm trích dẫn điều khoản gốc.
