# BẢN THUYẾT MINH ĐỀ TÀI NGHIÊN CỨU KHOA HỌC
**HỌC PHẦN: TIỂU LUẬN CHUYÊN NGÀNH (NGÀNH KỸ THUẬT DỮ LIỆU) — HK1 NĂM HỌC 2026–2027**  
**KHOA CÔNG NGHỆ THÔNG TIN — TRƯỜNG ĐẠI HỌC CÔNG NGHỆ KỸ THUẬT TP.HCM**

---

### TÊN ĐỀ TÀI
- **Tiếng Việt**: **Xây dựng hệ thống thu thập, xử lý dữ liệu và nền tảng hỗ trợ sinh viên tham gia các cuộc thi học thuật, công nghệ**
- **Tiếng Anh**: **Building a Data Pipeline and Platform for Academic Competition Discovery, Knowledge Management, and Teammate Recommendation**

### THÔNG TIN TÁC GIẢ VÀ CÁN BỘ HƯỚNG DẪN
- **Sinh viên thực hiện**:
  1. **Đỗ Kiến Hưng** — MSSV: `23133030` — Ngành Kỹ thuật Dữ liệu, Khoa CNTT, Trường ĐH Công nghệ Kỹ thuật TP.HCM
  2. **Nguyễn Văn Quang Duy** — MSSV: `23110086` — Ngành Kỹ thuật Dữ liệu, Khoa CNTT, Trường ĐH Công nghệ Kỹ thuật TP.HCM
- **Cán bộ hướng dẫn khoa học**: **ThS. Trần Quang Khải** — Bộ môn Hệ thống Thông tin, Khoa CNTT, Trường ĐH Công nghệ Kỹ thuật TP.HCM

---

## 1. TÓM TẮT ĐỀ TÀI (ABSTRACT)
Tham gia các sân chơi học thuật chuyên môn và các chương trình đào tạo tài năng công nghệ là phương thức quan trọng giúp sinh viên Công nghệ thông tin cọ xát thực tế và tích lũy kinh nghiệm dự án. Tuy nhiên, qua quan sát thực tế tại Trường ĐH Công nghệ Kỹ thuật TP.HCM, phần lớn sinh viên gặp nhiều trở ngại trong việc tiếp cận thông tin do các thông báo bị phân tán trên nhiều kênh khác nhau, thiếu kho lưu trữ tài liệu ôn luyện của các khóa trước và gặp khó khăn khi tìm kiếm đồng đội phù hợp hoặc giảng viên hướng dẫn. 

Đề tài này tập trung xây dựng một đường ống xử lý dữ liệu (Data Pipeline) từ khâu thu thập tự động đa nguồn, trích xuất cấu trúc văn bản bằng mô hình ngôn ngữ lớn (LLM), lưu trữ phân tầng theo kiến trúc Lakehouse, kết hợp mô hình RAG (Retrieval-Augmented Generation) phục vụ tra cứu quy chế và thuật toán ghép đội dựa trên sự tương đồng vector kỹ năng. Trong phạm vi 15 tuần của học phần Tiểu luận chuyên ngành, nhóm tập trung hoàn thiện phiên bản MVP với đường ống dữ liệu cốt lõi, kho lưu trữ chuẩn hóa và giao diện tra cứu cơ bản, làm cơ sở để phát triển thành hệ thống hoàn chỉnh trong học phần Khóa luận tốt nghiệp.

**Từ khóa**: *Data Pipeline, Web Scraping, Data Lakehouse, LLM Information Extraction, Retrieval-Augmented Generation (RAG), Teammate Recommendation, Higher Education Analytics.*

---

## 2. ĐẶT VẤN ĐỀ VÀ TÍNH CẤP THIẾT
Hàng năm, sinh viên ngành CNTT có nhiều cơ hội tham gia các kỳ thi chuyên môn (Olympic Tin học, ICPC, Sinh viên NCKH, Euréka, Sinh viên với An toàn thông tin, các cuộc thi Hackathon/AI Challenge) cũng như các chương trình đào tạo trọng điểm (VinUni AI, Samsung Innovation Campus, Google/NIC...). Dù vậy, tỉ lệ tham gia của sinh viên vẫn chưa tương xứng với tiềm năng vì bốn nguyên nhân cụ thể:

1. **Thông tin bị phân tán**: Các thông báo về cuộc thi xuất hiện rải rác trên nhiều fanpage Facebook, website đơn vị tổ chức, cổng thông tin Đoàn - Hội và nhóm mạng xã hội. Sinh viên không thường xuyên theo dõi sẽ dễ dàng bỏ lỡ thời hạn đăng ký.
2. **Khó tiếp cận quy chế và tài liệu ôn luyện**: Tài liệu thể lệ thường dài và phức tạp; thiếu một kho lưu trữ tập trung về đề thi các năm trước, lời giải tham khảo hay kinh nghiệm thực chiến từ các anh chị khóa trên.
3. **Trở ngại trong việc lập đội và liên hệ giảng viên**: Nhiều sinh viên có nguyện vọng dự thi nhưng không tìm được bạn cùng nhóm có kỹ năng bù trừ (ví dụ: cần người làm Frontend kết hợp với người làm Data/AI); đồng thời sinh viên gặp rào cản khi muốn liên hệ với thầy cô có hướng nghiên cứu phù hợp để xin hướng dẫn.
4. **Thiếu công cụ theo dõi cho Khoa**: Ban Chủ nhiệm Khoa chưa có hệ thống thống kê tự động để ghi nhận dữ liệu sinh viên tham gia, hỗ trợ quy trình khen thưởng kịp thời và đánh giá xu hướng công nghệ qua từng năm học.

Việc ứng dụng chuyên môn Kỹ thuật Dữ liệu để xây dựng hệ thống tự động thu thập, chuẩn hóa, phân tích và cung cấp dịch vụ tra cứu thông minh là giải pháp kỹ thuật có tính ứng dụng trực tiếp và giá trị thực tiễn cao cho Khoa CNTT.

---

## 3. CÂU HỎI VÀ MỤC TIÊU NGHIÊN CỨU

### Câu hỏi nghiên cứu:
- **RQ1**: Phương pháp nào giúp tự động hóa quá trình thu thập và trích xuất dữ liệu có cấu trúc (Schema JSON) từ các nguồn bài viết mạng xã hội và website động với độ chính xác cao và khả năng chịu lỗi tốt khi giao diện nguồn thay đổi?
- **RQ2**: Cấu trúc lưu trữ Lakehouse phân tầng nào đảm bảo tối ưu cho việc truy vấn phân tích (OLAP) và trích xuất vector phục vụ tìm kiếm ngữ nghĩa?
- **RQ3**: Thiết kế luồng RAG như thế nào để trả lời chính xác các câu hỏi về thể lệ cuộc thi dựa trên tài liệu quy chế mà không xảy ra hiện tượng sinh thông tin sai lệch (hallucination)?

### Mục tiêu cụ thể:
1. Xây dựng Data Pipeline tự động thu thập dữ liệu từ 5 đến 10 nguồn thông tin cuộc thi trọng điểm.
2. Thiết kế và triển khai kho lưu trữ Medallion (Bronze/Silver/Gold) đảm bảo tính toàn vẹn và khử trùng lặp dữ liệu sự kiện.
3. Xây dựng dịch vụ RAG hỗ trợ tra cứu thể lệ, điều kiện dự thi và gợi ý tài liệu ôn tập.
4. Xây dựng giao diện Web MVP và bảng thống kê số liệu cơ bản phục vụ sinh viên và cán bộ quản lý Khoa.

---

## 4. TỔNG QUAN NGHIÊN CỨU VÀ ĐÓNG GÓP MỚI
- **Nền tảng sự kiện học thuật**: Các hệ thống hiện có như Devpost, Unstop hay StudentCompetitions chủ yếu vận hành theo mô hình ban tổ chức tự đăng bài thủ công, không có cơ chế thu thập tự động từ mạng xã hội địa phương tại Việt Nam và chưa tích hợp sâu vào quy trình hỗ trợ sinh viên trong trường đại học.
- **Trích xuất thông tin bằng LLM**: Các công trình gần đây về Web Scraping tự động (như Crawl4AI, ScrapeGraphAI) đã chỉ ra rằng việc kết hợp công cụ render trình duyệt với LLM có ràng buộc cấu trúc (Schema Enforcement) giúp giảm thiểu đáng kể chi phí bảo trì so với việc viết bộ phân tích cú pháp (parser) tĩnh truyền thống.
- **Mô hình RAG trong tra cứu văn bản học thuật**: Ứng dụng RAG kết hợp giữa tìm kiếm từ khóa (BM25) và tìm kiếm ngữ nghĩa (Dense Vector Retrieval) đã được chứng minh đem lại độ chính xác cao đối với các văn bản quy định hành chính và học thuật.
- **Đóng góp của đề tài**: Tích hợp một quy trình hoàn chỉnh từ thu thập dữ liệu tự động, chuẩn hóa lưu trữ, tra cứu thông minh dựa trên AI đến thuật toán ghép đội và bảng phân tích chuyên biệt cho môi trường giáo dục đại học tại Việt Nam.

---

## 5. PHƯƠNG PHÁP NGHIÊN CỨU VÀ KIẾN TRÚC HỆ THỐNG

```
[Nguồn: Web / Fanpage / Cổng thông tin]
                  │ (Crawl4AI / Playwright / LLM Parser)
                  ▼
┌────────────────────────────────────────────────────────────────────────┐
│                        DATA PIPELINE & LAKEHOUSE                       │
│  [Bronze: Raw Payload] ──> [Silver: Cleaned Data] ──> [Gold: Data Mart] │
└────────────────────────────────────────────────────────────────────────┘
                  │                                        │
                  ▼ (Vector Embedding)                     ▼ (Query API)
┌───────────────────────────────────┐     ┌──────────────────────────────┐
│          AI & RAG ENGINE          │     │        SERVING LAYER         │
│  - Vector Database (Qdrant)       │     │  - Backend REST API (FastAPI)│
│  - Hybrid Search (BM25 + Vector)  │     │  - Web Portal (Next.js)      │
│  - Trợ lý tra cứu thể lệ          │     │  - Dashboard thống kê Khoa   │
└───────────────────────────────────┘     └──────────────────────────────┘
```

1. **Tầng Thu thập (Ingestion Layer)**: Sử dụng Playwright (v1.48+) và Crawl4AI (v0.9+) để tải nội dung các trang web động. Áp dụng LLM với cấu hình Pydantic Schema (v2.10+) để trích xuất các trường: *tên cuộc thi, đơn vị tổ chức, thời hạn đăng ký, bảng thi, link đăng ký, tóm tắt thể lệ*.
2. **Tầng Lưu trữ (Lakehouse Layer)**: Triển khai mô hình phân tầng Medallion sử dụng DuckDB (v1.2+)/Parquet kết hợp PostgreSQL (v17+) và dbt-core (v1.9+). Xử lý chuẩn hóa định dạng ngày tháng và thuật toán so khớp chuỗi (Fuzzy matching) để khử các bản ghi trùng lặp khi một cuộc thi được chia sẻ trên nhiều kênh.
3. **Tầng Xử lý AI (AI & RAG Layer)**: Phân đoạn tài liệu quy chế theo cấu trúc điều khoản, sinh vector nhúng và lưu vào cơ sở dữ liệu vector Qdrant (v1.19+). Luồng RAG sử dụng kỹ thuật Hybrid Search (BM25 + Dense Vectors) và Cross-Encoder Re-ranking để tăng độ khớp của ngữ cảnh trước khi đưa vào mô hình sinh câu trả lời.
4. **Tầng Phục vụ (Serving Layer)**: Cung cấp REST API qua FastAPI (v0.115+, Python 3.13+), giao diện người dùng xây dựng bằng Next.js (v15+) cho phép lọc tìm kiếm cuộc thi, giao tiếp với trợ lý AI và xem bảng biểu thống kê.

---

## 6. PHẠM VI VÀ KẾ HOẠCH THỰC HIỆN

### Phân định phạm vi Tiểu luận chuyên ngành và Khóa luận tốt nghiệp:
- **Tiểu luận chuyên ngành (15 tuần)**: Tập trung vào phần lõi kỹ thuật dữ liệu (MVP): Xây dựng bộ thu thập tự động 5–10 nguồn, hoàn thiện kho dữ liệu phân tầng, xây dựng dịch vụ RAG tra cứu thể lệ cơ bản và giao diện Web MVP kèm bảng thống kê.
- **Khóa luận tốt nghiệp (15 tuần tiếp theo)**: Mở rộng thu thập dữ liệu thời gian thực (Streaming/Webhook), hoàn thiện thuật toán gợi ý ghép đội và giảng viên hướng dẫn, xây dựng kho lưu trữ bài thi đạt giải và tự động hóa quy trình đề xuất khen thưởng cho Khoa.

### Lộ trình 15 tuần học phần Tiểu luận:
- **Tuần 1 – 3**: Khảo sát nguồn dữ liệu, thiết kế Schema và đặc tả kiến trúc. Báo cáo đề cương với GVHD.
- **Tuần 4 – 7**: Lập trình bộ thu thập đa nguồn, tích hợp trích xuất LLM và xử lý khử trùng dữ liệu.
- **Tuần 8 – 10**: Thiết lập cơ sở dữ liệu vector, xây dựng luồng RAG tra cứu và đánh giá độ chính xác.
- **Tuần 11 – 13**: Hoàn thiện giao diện Web người dùng, tích hợp API và xây dựng trang thống kê.
- **Tuần 14 – 15**: Kiểm thử hệ thống, viết báo cáo toàn văn và chuẩn bị bảo vệ đề tài (~07/12/2026).

---

## 7. Ý NGHĨA THỰC TIỄN
- **Đối với sinh viên**: Giúp tiếp cận cơ hội học thuật tập trung, nắm bắt thể lệ nhanh chóng và có thêm công cụ tìm kiếm đồng đội phù hợp.
- **Đối với giảng viên**: Tạo kênh kết nối với sinh viên có cùng hướng nghiên cứu chuyên môn và quan tâm đến các cuộc thi cụ thể.
- **Đối với Khoa CNTT**: Cung cấp dữ liệu thống kê phục vụ công tác quản lý, theo dõi phong trào học thuật và khen thưởng sinh viên.

---

## 8. TÀI LIỆU THAM KHẢO
1. **Lewis, P., Perez, E., Piktus, A., Petroni, F., Karpukhin, V., Goyal, N., Küttler, H., Lewis, M., Yih, W. T., Rocktäschel, T., Riedel, S., & Kiela, D.** (2020). *Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks*. Advances in Neural Information Processing Systems (NeurIPS), 33, 9459–9474.
2. **Armbrust, M., Ghodsi, A., Xin, R., & Zaharia, M.** (2021). *Lakehouse: A New Generation of Open Platforms that Unify Data Warehousing and Advanced Analytics*. Proceedings of the 11th Conference on Innovative Data Systems Research (CIDR 2021).
3. **Xu, D., Chen, W., Peng, W., Zhang, C., Xu, T., Zhao, X., Chen, X., & Zheng, Y.** (2024). *Large Language Models for Information Extraction: A Survey*. arXiv preprint arXiv:2308.07107.
4. **Lappas, T., Liu, K., & Terzi, E.** (2009). *Finding a team of experts in social networks*. In Proceedings of the 15th ACM SIGKDD International Conference on Knowledge Discovery and Data Mining (KDD '09), pp. 467–476. DOI: 10.1145/1557019.1557074.
5. **Gao, Y., Xiong, Y., Gao, X., Jia, K., Pan, J., Bi, Y., Dai, Y., Sun, J., & Wang, H.** (2023). *Retrieval-Augmented Generation for Large Language Models: A Survey*. arXiv preprint arXiv:2312.10997.
6. **Khoa Công nghệ Thông tin - Trường ĐH Công nghệ Kỹ thuật TP.HCM** (2026). *Quy định thực hiện Tiểu luận chuyên ngành và Khóa luận tốt nghiệp ngành Kỹ thuật Dữ liệu*.
