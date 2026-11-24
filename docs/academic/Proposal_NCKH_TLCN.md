# BẢN THUYẾT MINH ĐỀ TÀI NGHIÊN CỨU KHOA HỌC
**HỌC PHẦN: TIỂU LUẬN CHUYÊN NGÀNH (NGÀNH KỸ THUẬT DỮ LIỆU) — HK1 NĂM HỌC 2026–2027**  
**KHOA CÔNG NGHỆ THÔNG TIN — TRƯỜNG ĐẠI HỌC CÔNG NGHỆ KỸ THUẬT TP.HCM**

---

### THÔNG TIN ĐỀ TÀI, TÁC GIẢ VÀ CÁN BỘ HƯỚNG DẪN

| Hạng mục | Nội dung chi tiết |
| :--- | :--- |
| **Tên đề tài (Tiếng Việt)** | **Xây dựng hệ thống thu thập, xử lý dữ liệu và nền tảng hỗ trợ sinh viên tham gia các cuộc thi học thuật, công nghệ** |
| **Tên đề tài (Tiếng Anh)** | **Building a Data Pipeline and Platform for Academic Competition Discovery, Knowledge Management, and Teammate Recommendation** |
| **Sinh viên thực hiện 1** | Đỗ Kiến Hưng (MSSV: `23133030`) - Ngành Kỹ thuật Dữ liệu, Khoa CNTT, Trường ĐH Công nghệ Kỹ thuật TP.HCM |
| **Sinh viên thực hiện 2** | Nguyễn Văn Quang Duy (MSSV: `23110086`) - Ngành Kỹ thuật Dữ liệu, Khoa CNTT, Trường ĐH Công nghệ Kỹ thuật TP.HCM |
| **Cán bộ hướng dẫn** | **ThS. Trần Quang Khải** - Bộ môn Hệ thống Thông tin, Khoa CNTT, Trường ĐH Công nghệ Kỹ thuật TP.HCM |

---

## 1. TÓM TẮT ĐỀ TÀI (ABSTRACT)
Tham gia các sân chơi học thuật chuyên môn và các chương trình đào tạo tài năng công nghệ là phương thức quan trọng giúp sinh viên Công nghệ thông tin cọ xát thực tế và tích lũy kinh nghiệm dự án. Tuy nhiên, qua quan sát thực tế tại Trường ĐH Công nghệ Kỹ thuật TP.HCM, phần lớn sinh viên gặp nhiều trở ngại trong việc tiếp cận thông tin do các thông báo bị phân tán trên nhiều kênh khác nhau, thiếu kho lưu trữ tài liệu ôn luyện của các khóa trước và gặp khó khăn khi tìm kiếm đồng đội phù hợp hoặc giảng viên hướng dẫn. 

Đề tài này tập trung xây dựng một đường ống xử lý dữ liệu (Data Pipeline) từ khâu thu thập tự động đa nguồn, trích xuất cấu trúc văn bản bằng mô hình ngôn ngữ lớn (LLM), lưu trữ phân tầng theo kiến trúc Lakehouse, kết hợp mô hình RAG (Retrieval-Augmented Generation) phục vụ tra cứu quy chế và thuật toán ghép đội dựa trên sự tương đồng vector kỹ năng. Trong phạm vi 15 tuần của học phần Tiểu luận chuyên ngành, nhóm tập trung hoàn thiện phiên bản MVP với đường ống dữ liệu cốt lõi, kho lưu trữ chuẩn hóa và giao diện tra cứu cơ bản, làm cơ sở để phát triển thành hệ thống hoàn chỉnh trong học phần Khóa luận tốt nghiệp.

**Từ khóa**: *Data Pipeline, Web Scraping, Data Lakehouse, LLM Information Extraction, Retrieval-Augmented Generation (RAG), Teammate Recommendation, Higher Education Analytics.*

---

## 2. ĐẶT VẤN ĐỀ VÀ TÍNH CẤP THIẾT
Hàng năm, sinh viên ngành CNTT có nhiều cơ hội tham gia các kỳ thi chuyên môn (Olympic Tin học, ICPC, Sinh viên NCKH, Euréka, Sinh viên với An toàn thông tin, các cuộc thi Hackathon/AI Challenge) cũng như các chương trình đào tạo trọng điểm (VinUni AI, Samsung Innovation Campus, Google/NIC...). Dù vậy, tỉ lệ tham gia của sinh viên vẫn chưa tương xứng với tiềm năng vì bốn nguyên nhân cụ thể:

1. Thông tin bị phân tán: Các thông báo về cuộc thi xuất hiện rải rác trên nhiều fanpage Facebook, website đơn vị tổ chức, cổng thông tin Đoàn - Hội và nhóm mạng xã hội. Sinh viên không thường xuyên theo dõi sẽ dễ dàng bỏ lỡ thời hạn đăng ký.
2. Khó tiếp cận quy chế và tài liệu ôn luyện: Tài liệu thể lệ thường dài và phức tạp; thiếu một kho lưu trữ tập trung về đề thi các năm trước, lời giải tham khảo hay kinh nghiệm thực tế từ các anh chị khóa trên.
3. Trở ngại trong việc lập đội và liên hệ giảng viên: Nhiều sinh viên có nguyện vọng dự thi nhưng không tìm được bạn cùng nhóm có kỹ năng bù trừ (ví dụ: cần người làm Frontend kết hợp với người làm Data/AI); đồng thời sinh viên gặp rào cản khi muốn liên hệ với thầy cô có hướng nghiên cứu phù hợp để xin hướng dẫn.
4. Thiếu công cụ theo dõi cho Khoa: Ban Chủ nhiệm Khoa chưa có hệ thống thống kê tự động để ghi nhận dữ liệu sinh viên tham gia, hỗ trợ quy trình khen thưởng kịp thời và đánh giá xu hướng công nghệ qua từng năm học.

Việc ứng dụng chuyên môn Kỹ thuật Dữ liệu để xây dựng hệ thống tự động thu thập, chuẩn hóa, phân tích và cung cấp dịch vụ tra cứu thông minh là giải pháp kỹ thuật có tính ứng dụng trực tiếp và giá trị thực tiễn cao cho Khoa CNTT.

---

## 3. CÂU HỎI VÀ MỤC TIÊU NGHIÊN CỨU

### Câu hỏi nghiên cứu:
- Phương pháp nào giúp tự động hóa quá trình thu thập và trích xuất dữ liệu có cấu trúc (Schema JSON) từ các nguồn bài viết mạng xã hội và website động với độ chính xác cao và khả năng chịu lỗi tốt khi giao diện nguồn thay đổi (RQ1)?
- Cấu trúc lưu trữ Lakehouse phân tầng nào đảm bảo tối ưu cho việc truy vấn phân tích (OLAP) và trích xuất vector phục vụ tìm kiếm ngữ nghĩa (RQ2)?
- Thiết kế luồng RAG như thế nào để trả lời chính xác các câu hỏi về thể lệ cuộc thi dựa trên tài liệu quy chế mà không xảy ra hiện tượng sinh thông tin sai lệch (RQ3)?

### Mục tiêu cụ thể:
1. Xây dựng Data Pipeline tự động thu thập dữ liệu từ 5 đến 10 nguồn thông tin cuộc thi trọng điểm.
2. Thiết kế và triển khai kho lưu trữ Medallion (Bronze/Silver/Gold) đảm bảo tính toàn vẹn và khử trùng lặp dữ liệu sự kiện.
3. Xây dựng dịch vụ RAG hỗ trợ tra cứu thể lệ, điều kiện dự thi và gợi ý tài liệu ôn tập.
4. Xây dựng giao diện Web MVP và bảng thống kê số liệu cơ bản phục vụ sinh viên và cán bộ quản lý Khoa.

---

## 4. TỔNG QUAN NGHIÊN CỨU VÀ ĐÓNG GÓP MỚI
Trên cơ sở khảo sát các công trình khoa học và hệ thống thực tế, đề tài kế thừa và phát triển bốn hướng nghiên cứu chính:
- Đối với các nền tảng sự kiện học thuật hiện có như Devpost, Unstop hay StudentCompetitions, các hệ thống này chủ yếu vận hành theo mô hình ban tổ chức tự đăng bài thủ công, không có cơ chế thu thập tự động từ mạng xã hội địa phương tại Việt Nam và chưa tích hợp sâu vào quy trình hỗ trợ sinh viên trong trường đại học.
- Về kỹ thuật trích xuất thông tin bằng mô hình ngôn ngữ lớn, các công trình gần đây [3] đã chỉ ra rằng việc kết hợp công cụ dựng trang trình duyệt (`Crawl4AI` + `Playwright`) với mô hình ngôn ngữ lớn có ràng buộc cấu trúc (`instructor` + `Pydantic v2`) giúp giảm thiểu đáng kể chi phí bảo trì so với việc viết bộ phân tích cú pháp tĩnh truyền thống.
- Về kiến trúc lưu trữ và tra cứu văn bản học thuật, mô hình kho dữ liệu phân tầng Medallion Lakehouse [2] kết hợp kiến trúc RAG lai ghép giữa tìm kiếm từ khóa (BM25) và tìm kiếm ngữ nghĩa (Dense Vector Retrieval) [1], [5] đem lại độ chính xác cao đối với các văn bản quy định hành chính và học thuật, đồng thời hỗ trợ bài toán gợi ý ghép đội chuyên môn [4].
- Từ đó, đóng góp trọng tâm của đề tài là tích hợp một quy trình hoàn chỉnh tuân thủ quy định học thuật của Khoa CNTT [6], từ thu thập dữ liệu cuộc thi, chuẩn hóa lưu trữ trên Cloudflare R2 và DuckDB, tra cứu quy chế thông minh dựa trên Hybrid RAG đến định hướng ghép đội và bảng phân tích số liệu cho môi trường giáo dục đại học tại Việt Nam.

---

## 5. PHƯƠNG PHÁP NGHIÊN CỨU VÀ KIẾN TRÚC HỆ THỐNG

```
[Nguồn: 5–10 Website Cuộc thi Học thuật Tiêu biểu]
                  │ (Crawl4AI / Playwright / Instructor + Pydantic v2)
                  ▼
┌────────────────────────────────────────────────────────────────────────┐
│            MEDALLION LAKEHOUSE TINH GỌN (CLOUDFLARE R2 & LOCAL)        │
│  [Bronze: UTF-8 Markdown] ──> [Silver: Parquet] ──> [Gold: DuckDB OLAP] │
└────────────────────────────────────────────────────────────────────────┘
                  │                                        │
                  ▼ (Clause Chunking)                      ▼ (Zero-Copy SQL)
┌───────────────────────────────────┐     ┌──────────────────────────────┐
│          AI & RAG ENGINE          │     │        SERVING LAYER         │
│  - Vector Database (Qdrant)       │     │  - Backend REST API (FastAPI)│
│  - Hybrid Search (BM25 + Vector)  │     │  - Web Portal (Next.js 15)   │
│  - Cross-Encoder Re-ranking       │     │  - Dashboard thống kê Khoa   │
└───────────────────────────────────┘     └──────────────────────────────┘
```

1. **Tầng Thu thập (Ingestion Layer)**: Sử dụng `Playwright` và `Crawl4AI` (`AdaptiveCrawler`) để tải và làm sạch nội dung các trang web cuộc thi động sang định dạng văn bản Markdown (`UTF-8`). Áp dụng mô hình ngôn ngữ lớn kết hợp thư viện `instructor` và lược đồ `Pydantic v2` (`SilverCompetitionRecord`) [3] để trích xuất các trường định lượng cốt lõi gồm: *tên cuộc thi, đơn vị tổ chức, thời hạn đăng ký, bảng thi, đường dẫn đăng ký, cơ cấu giải thưởng và toàn văn thể lệ*.
2. **Tầng Lưu trữ (Lean Medallion Lakehouse Layer)**: Triển khai mô hình phân tầng Medallion tinh gọn [2] phù hợp với quy mô kiểm chứng 5–10 cuộc thi của giai đoạn Tiểu luận chuyên ngành: lưu trữ trực tiếp văn bản Markdown (`UTF-8`) tại tầng Bronze trên kho đối tượng đám mây **Cloudflare R2** và ổ cứng cục bộ (lược bỏ bước nén nhị phân trung gian không cần thiết); lưu trữ thực thể đã chuẩn hóa dưới dạng tệp cột **Apache Parquet** tại tầng Silver kèm hàm băm SHA-256 `generate_fingerprint()` khử trùng lặp; và sử dụng động cơ phân tích nhúng **DuckDB** tại tầng Gold để truy vấn trực tiếp (zero-copy SQL) mà không cần vận hành máy chủ cơ sở dữ liệu cồng kềnh.
3. **Tầng Xử lý AI (AI & RAG Layer)**: Phân đoạn tài liệu quy chế theo cấu trúc điều khoản, sinh vector nhúng và lưu vào cơ sở dữ liệu vector **Qdrant**. Luồng RAG sử dụng kỹ thuật Hybrid Search (BM25 + Dense Vectors) và mô hình `Cross-Encoder Re-ranking` [1], [5] để nâng cao độ chính xác của ngữ cảnh trước khi tổng hợp câu trả lời kèm trích dẫn nguồn.
4. **Tầng Phục vụ (Serving Layer)**: Cung cấp REST API qua **FastAPI (Python 3.13)** kết nối trực tiếp với DuckDB và Qdrant; giao diện người dùng xây dựng bằng **Next.js 15** và **Tailwind CSS** cho phép lọc tìm kiếm cuộc thi, hỏi đáp quy chế và xem bảng biểu thống kê mùa vụ.

---

## 6. PHẠM VI VÀ KẾ HOẠCH THỰC HIỆN

### Phân định phạm vi Tiểu luận chuyên ngành và Khóa luận tốt nghiệp:
- **Tiểu luận chuyên ngành (15 tuần)**: Tập trung mô phỏng hệ thống và kiểm chứng tính khả thi kỹ thuật (Proof of Feasibility) trên tập dữ liệu chọn lọc gồm **5 đến 10 cuộc thi học thuật tiêu biểu** (7 cuộc thi thực tế được thu thập theo yêu cầu), hoàn thiện kho dữ liệu phân tầng Bronze - Silver - Gold tinh gọn trên Cloudflare R2 và DuckDB, xây dựng dịch vụ Hybrid RAG tra cứu thể lệ và giao diện Web MVP kèm bảng thống kê.
- **Khóa luận tốt nghiệp (15 tuần tiếp theo)**: Mở rộng thu thập dữ liệu số lượng lớn tự động theo lô định kỳ (batch job) và thời gian thực (webhooks), kích hoạt các kỹ thuật tối ưu lưu trữ quy mô lớn, hoàn thiện thuật toán gợi ý ghép đội bù trừ kỹ năng [4] và kết nối giảng viên hướng dẫn, xây dựng kho lưu trữ bài giải mẫu và tự động hóa quy trình đề xuất cộng điểm rèn luyện cho Khoa.

### Lộ trình 15 tuần học phần Tiểu luận:

| Giai đoạn | Nội dung công việc thực hiện |
| :---: | :--- |
| **Tuần 1 – 3** | Khảo sát nhu cầu sinh viên, nghiên cứu tài liệu khoa học, thiết kế kiến trúc 4 tầng và báo cáo đề cương với GVHD [6]. |
| **Tuần 4 – 9** | Cài đặt đường ống thu thập `Crawl4AI` đẩy văn bản Markdown của 7 cuộc thi mẫu lên tầng Bronze Cloudflare R2 (`1_crawl_to_bronze.py`); thiết kế lược đồ `SilverCompetitionRecord` trên Pydantic v2, kiểm thử đơn vị và khởi tạo module trích xuất `instructor` (`2_instruction.py`). |
| **Tuần 10** | Hoàn thiện trích xuất 7 cuộc thi sang tệp Parquet tầng Silver trên R2 và xây dựng bộ truy vấn phân tích OLAP tầng Gold bằng DuckDB. |
| **Tuần 11 – 12** | Thiết lập cơ sở dữ liệu vector Qdrant, xây dựng luồng Hybrid RAG tra cứu thể lệ và đánh giá theo khung Ragas. |
| **Tuần 13 – 15** | Xây dựng FastAPI backend, giao diện Web Portal (Next.js 15), kiểm thử tích hợp toàn hệ thống, hoàn thiện quyển báo cáo toàn văn và chuẩn bị bảo vệ đề tài (~07/12/2026). |

---

## 7. Ý NGHĨA THỰC TIỄN
Hệ thống ACDP mang lại giá trị ứng dụng trực tiếp cho ba nhóm đối tượng trong môi trường đại học:
- Đối với sinh viên: Giúp tiếp cận cơ hội học thuật tập trung, nắm bắt thể lệ nhanh chóng và có thêm công cụ tìm kiếm đồng đội phù hợp.
- Đối với giảng viên: Tạo kênh kết nối với sinh viên có cùng hướng nghiên cứu chuyên môn và quan tâm đến các cuộc thi cụ thể.
- Đối với Khoa CNTT: Cung cấp dữ liệu thống kê phục vụ công tác quản lý, theo dõi phong trào học thuật và khen thưởng sinh viên.

---

# TÀI LIỆU THAM KHẢO

[1] P. Lewis, E. Perez, A. Piktus, F. Petroni, V. Karpukhin, N. Goyal, H. Küttler, M. Lewis, W. T. Yih, T. Rocktäschel, S. Riedel, và D. Kiela, "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks", *Advances in Neural Information Processing Systems (NeurIPS)*, tập 33, tr. 9459–9474, 2020.

[2] M. Armbrust, A. Ghodsi, R. Xin, và M. Zaharia, "Lakehouse: A New Generation of Open Platforms that Unify Data Warehousing and Advanced Analytics", trong *Kỷ yếu Hội nghị Innovative Data Systems Research (CIDR 2021)*, 2021.

[3] D. Xu, W. Chen, W. Peng, C. Zhang, T. Xu, X. Zhao, X. Chen, và Y. Zheng, "Large Language Models for Information Extraction: A Survey", *arXiv preprint arXiv:2308.07107*, 2024.

[4] T. Lappas, K. Liu, và E. Terzi, "Finding a team of experts in social networks", trong *Kỷ yếu Hội nghị Quốc tế ACM SIGKDD (KDD '09)*, tr. 467–476, 2009.

[5] Y. Gao, Y. Xiong, X. Gao, K. Jia, J. Pan, Y. Bi, Y. Dai, J. Sun, và H. Wang, "Retrieval-Augmented Generation for Large Language Models: A Survey", *arXiv preprint arXiv:2312.10997*, 2023.

[6] Khoa Công nghệ Thông tin - Trường Đại học Công nghệ Kỹ thuật TP.HCM, *Quy định thực hiện Tiểu luận chuyên ngành và Khóa luận tốt nghiệp ngành Kỹ thuật Dữ liệu*, FIT HCMUTE, 2026.
