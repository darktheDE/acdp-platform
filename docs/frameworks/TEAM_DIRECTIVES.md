# TEAM_DIRECTIVES.md: Sổ Tay Quy Tắc Bất Biến & Bộ Nhớ Chỉ Thị Thường Trực (Team Directives & Memory Ledger)

> **Cơ quan ban hành**: Nhóm tác giả đề tài ACDP  
> **Thành viên sáng lập**: Đỗ Kiến Hưng (`@darktheDE`) & Nguyễn Văn Quang Duy (`@QuangDuyReal`)  
> **Đơn vị đào tạo**: Khoa Công nghệ Thông tin - Trường Đại học Công nghệ Kỹ thuật TP.HCM (HCM-UTE)  
> **Cán bộ hướng dẫn khoa học**: ThS. Trần Quang Khải  
> **Hiệu lực**: Vĩnh viễn và bắt buộc đối với tất cả các AI Agents (Google Antigravity, Gemini CLI, Claude Code, Cursor, Windsurf, Codex) và cộng tác viên.

---

## 1. Tôn Chỉ Hoạt Động & Cơ Chế Ghi Nhớ Tự Động (Continuous Memory Protocol)

Tài liệu này là **Nguồn Chân Lý Duy Nhất (Single Source of Truth - SSOT)** lưu trữ toàn bộ các quy tắc, chuẩn mực danh xưng, triết lý làm việc và những chỉ thị phát sinh do **Đỗ Kiến Hưng** hoặc **Nguyễn Văn Quang Duy** đưa ra trong suốt quá trình phát triển đề tài.

### Quy trình Tự động Ghi nhớ & Tiếp nhận Chỉ thị Mới (Dynamic Rule Ingestion)
Bất cứ khi nào Hưng hoặc Duy đưa ra một yêu cầu, chỉnh sửa hoặc quy ước mới trong bất kỳ phiên hội thoại nào (ví dụ: *"Nhớ là...", "Từ giờ quy ước X là...", "Trước khi làm việc Y thì phải..."*):
1. **Tiếp nhận tức thời**: Agent phải ghi nhận và áp dụng ngay lập tức vào tác vụ hiện hành mà không cần nhắc lại lần thứ hai.
2. **Khắc phục quên lãng (Active Persistence)**: Agent phải chủ động cập nhật quy tắc mới vào tài liệu này ([`docs/frameworks/TEAM_DIRECTIVES.md`](./TEAM_DIRECTIVES.md)) tại [Mục 6: Nhật Ký Quy Tắc Mới](#6-nhật-ký-quy-tắc-mới-phát-sinh-dynamic-directives-changelog).
3. **Đồng bộ hóa hợp đồng Agent**: Nếu quy tắc có tính chất bất biến trên toàn dự án, Agent phải đồng thời cập nhật vào [`AGENTS.md`](../../AGENTS.md) và [`GEMINI.md`](../../GEMINI.md) để hệ thống tự động tiêm vào bộ nhớ ngữ cảnh (`<user_rules>`) trong mọi lượt tương tác tiếp theo.
4. **Không bao giờ tái phạm**: Một khi quy tắc đã được lưu, Agent tuyệt đối không được vi phạm hoặc làm ngược lại trong các phiên làm việc tương lai.

---

## 2. Chỉ Thị Cốt Lõi: Triết Lý "Zero Parametric Trust" & Giao Thức Xác Minh Thực Tế Bắt Buộc (Verification-First Protocol)

> ⚠️ **TUYỆT ĐỐI KHÔNG TIN TƯỞNG DỮ LIỆU HUẤN LUYỆN TĨNH CỦA AI MODEL (NO BLIND TRUST IN PRE-TRAINED PARAMETRIC WEIGHTS)**  
> Dữ liệu được train sẵn của mô hình ngôn ngữ lớn (LLM) có thể bị ảo giác (hallucination), không đầy đủ, hoặc đã lỗi thời (outdated) so với thực tế các quy định giáo dục, thể lệ cuộc thi, các thư viện mã nguồn mở và các bài báo khoa học mới nhất.

### Giao thức Hành động Bắt buộc cho Agent:
1. **Luôn Xác Minh Trước Khi Phát Biểu (Search Before Claiming)**:
   - Khi Hưng hoặc Duy đưa ra một bài toán, thông tin, câu hỏi kỹ thuật hay đề xuất giải pháp, việc đầu tiên Agent **BẮT BUỘC PHẢI LÀM** là dùng công cụ (`search_web`, `read_url_content`, tìm kiếm Google Scholar, tài liệu chính thức, hoặc tra cứu mã nguồn) để kiểm chứng, đào sâu và làm rõ thông tin thực tế.
   - Không trả lời chung chung dựa trên "trí nhớ của AI"; phải trích xuất thông tin tươi mới nhất từ các nguồn uy tín.
2. **Minh bạch Nguồn & Bằng chứng Đối soát (Verifiable Grounding)**:
   - Mọi thông tin về: thể lệ cuộc thi, lịch thi đấu, API/phiên bản thư viện (Python 3.13, Next.js 15, DuckDB 1.2,...), thuật toán khoa học hay công trình nghiên cứu đều phải dẫn nguồn cụ thể (URL, trích dẫn BibTeX trong [`docs/academic/references.bib`](../academic/references.bib) hoặc điều khoản chính sách chính thức).
3. **Cảnh giác với Tri thức Mặc định (Challenge Assumptions)**:
   - Nếu phát hiện nội dung thảo luận có mâu thuẫn giữa thực tế internet và trí nhớ mô hình, Agent phải báo cáo rõ nguồn đối chiếu để hai tác giả cùng đánh giá và đưa ra quyết định cuối cùng.

---

## 3. Chuẩn Hóa Danh Xưng Học Thuật & Thông Tin Thực Thể (Institutional & Project Entity Standards)

Khi soạn thảo bất kỳ tài liệu nào (Proposal, Slide, Thesis, Deliverables, Code Docstring, Commit Message, Báo cáo):

| Thực thể | Tên Gọi Chuẩn Mực & Quy Ước | Tên Viết Tắt Cho Phép | Lưu ý Đặc Biệt |
| :--- | :--- | :---: | :--- |
| **Trường** | **Trường Đại học Công nghệ Kỹ thuật TP.HCM**<br>*(Được đổi tên theo Quyết định của Thủ tướng Chính phủ ký ngày 26/12/2025; tên cũ: Trường ĐH Sư phạm Kỹ thuật TP.HCM)* | **HCM-UTE**<br>*(hoặc: HCMUTE)* | Tuân thủ chính xác quy ước tên trường do tác giả chỉ định: **Trường Đại học Công nghệ Kỹ thuật TP.HCM (HCM-UTE)**. Tên tiếng Anh: *Ho Chi Minh City University of Technology and Engineering*. |
| **Khoa** | **Khoa Công nghệ Thông tin**<br>*(Faculty of Information Technology)* | **FIT-HCM-UTE** / **FIT** | Đơn vị chủ quản đề tài. |
| **Chuyên ngành** | **Kỹ thuật Dữ liệu**<br>*(Data Engineering)* | **KTDL** / **DE** | Đề tài thuộc định hướng Kỹ thuật Dữ liệu; mọi giải pháp phải làm nổi bật Data Pipelines, Lakehouse, Data Modeling, Information Extraction, Vector Indexing. |
| **Tên Đề tài** | **Nền Tảng Khám Phá Cuộc Thi Học Thuật Dành Cho Sinh Viên**<br>*(Academic Competition Discovery Platform)* | **ACDP** / **acdp-platform** | Nền tảng toàn diện tích hợp Data Lakehouse, Hybrid Ingestion, LLM Extraction và Hybrid RAG. |
| **Tác giả 1** | **Đỗ Kiến Hưng** | `darktheDE` | Đồng tác giả - Phụ trách Kỹ thuật, Hạ tầng & Nền tảng. |
| **Tác giả 2** | **Nguyễn Văn Quang Duy** | `QuangDuyReal` | Đồng tác giả - Phụ trách Nghiên cứu, Dữ liệu & Nghiệp vụ. |
| **CB Hướng dẫn** | **ThS. Trần Quang Khải** | - | Giảng viên hướng dẫn khoa học. |

---

## 4. Kỷ Luật Công Nghệ & Giới Hạn Kiến Trúc (Architectural Invariants)

1. ⚠️ **CHÍNH SÁCH THAO TÁC VỚI GIT (Cho phép kiểm tra ở chế độ Read-Only)**:
   - ❌ **CẤM TUYỆT ĐỐI các lệnh thay đổi trạng thái (Mutating Commands)**: `git add`, `git commit`, `git push`, tạo/xóa nhánh hoặc các thao tác ghi nhạy cảm. Toàn bộ thao tác này phải do chính Hưng và Duy trực tiếp review và gõ lệnh.
   - ✅ **CHO PHÉP các lệnh kiểm tra trạng thái chỉ đọc (Read-Only Inspection Commands)**: `git status`, `git log`, `git diff`, `git show`, kiểm tra commit log hoặc branch hiện tại để đối soát ngữ cảnh dự án.
2. ❌ **CẤM TẠO THƯ MỤC RỖNG (No Empty Skeleton Folders)**:
   - Tuân thủ nguyên tắc JIT (Just-In-Time). Chỉ tạo thư mục mã nguồn (`apps/`, `pipelines/`) khi bắt đầu cài đặt mã lệnh thực thi cụ thể đã được đặc tả trong `docs/specs/`.
3. ❌ **CẤM ĐẨY DỮ LIỆU THÔ, DUMP VÀ SECRET LÊN REPO**:
   - Tuyệt đối không commit file `.env`, file cơ sở dữ liệu (`.duckdb`, `.db`, `.parquet`, `.sqlite`), secret key hay dữ liệu cá nhân của người dùng/giảng viên.
4. ⚡ **TRIẾT LÝ LEAN DATA ENGINEERING (Tinh Giản Là Sức Mạnh)**:
   - Không dùng Apache Airflow hay Prefect trong 15 tuần MVP (dùng Python CLI script + cron/APScheduler nhẹ nhàng).
   - Không phân mảnh crawler (tập trung duy nhất Crawl4AI + Playwright).
   - Storage trọng tâm: DuckDB (xử lý phân tích in-process trên file Parquet) + PostgreSQL 17 (lưu trữ phục vụ Web & Gold Marts) + Qdrant (Hybrid search BM25 + dense vector).
5. ⚡ **CHUYỂN ĐỔI UNSTRUCTURED THÀNH STRUCTURED (Trọng Tâm Kỹ Thuật Dữ Liệu)**:
   - Không được để dữ liệu văn bản tồn tại dưới dạng text thuần chỉ để ném vào chatbot.
   - Luôn sử dụng LLM Schema Parser (Pydantic v2) bóc tách văn bản cuộc thi thành hơn 10 chiều dữ liệu định lượng (thời gian, tài chính, đơn vị, lĩnh vực, điều kiện) để phục vụ OLAP Data Marts trên DuckDB.

---

## 5. Quy Ước Phối Hợp & Quy Trình Nghiên Cứu R&D

1. **R&D Tasks (`docs/rd-tasks/`)**:
   - Tất cả các bài toán nghiên cứu, phản biện sơ khởi của Duy khởi tạo (`T01`, `T02`, `T03`,...) được lưu trữ và quản lý tại [`docs/rd-tasks/`](../rd-tasks/).
   - Cấu trúc bắt buộc: `Why this task exists ?` $\rightarrow$ `What should I do ?` $\rightarrow$ `Expect result` $\rightarrow$ `Cross-Review & Approval Checklist`.
2. **Nghiệm Thu Chéo Bắt Buộc (Cross-Review Protocol)**:
   - Trước khi bắt tay vào code các tính năng lớn, cả hai thành viên Hưng và Duy phải đối soát, phản biện và tích xác nhận trong phần `Cross-Review Checklist`.
3. **Liên Kết & Đồng Bộ Notion**:
   - Mọi báo cáo kết quả nghiên cứu, spike kỹ thuật phải được lập hồ sơ tại [`docs/deliverables/NT-XXX-[slug].md`](../deliverables/) và đồng bộ trạng thái trong [`docs/tasks/notion-task-mapping.md`](../tasks/notion-task-mapping.md).

---

## 6. Nhật Ký Quy Tắc Mới Phát Sinh (Dynamic Directives Changelog)

Bảng này được Agent tự động cập nhật liên tục mỗi khi Hưng hoặc Duy đưa ra yêu cầu bổ sung trong quá trình làm việc:

| Mã Quy Tắc | Ngày Ban Hành | Người Yêu Cầu | Tóm Tắt Quy Tắc & Chỉ Thị Bắt Buộc | Phạm Vi Áp Dụng |
| :---: | :---: | :---: | :--- | :--- |
| **DIR-001** | 2026-09-11 | Hưng & Duy | **Chuẩn hóa danh xưng trường**: Bắt buộc dùng đúng tên *"Trường Đại học Công nghệ Kỹ thuật TP.HCM (HCM-UTE)"* trên toàn bộ tài liệu và văn bản. | Toàn bộ dự án |
| **DIR-002** | 2026-09-11 | Hưng & Duy | **Zero Blind Trust & Verification-First**: Không bao giờ tin tưởng mù quáng vào pre-trained memory của AI model; việc đầu tiên Agent PHẢI làm luôn là search Google, internet, scholar để làm rõ và đối chiếu dữ liệu thực tế trước khi kết luận. | Toàn bộ tương tác AI |
| **DIR-003** | 2026-09-11 | Hưng & Duy | **Dynamic Memory Persistence**: Mọi quy tắc mới phát sinh trong chat phải được Agent tự động ghi vào `docs/frameworks/TEAM_DIRECTIVES.md` và đồng bộ vào `AGENTS.md` / `GEMINI.md`. | Quy trình Agent |
| **DIR-004** | 2026-09-11 | Hưng & Duy | **Tổ chức R&D Tasks**: Mọi task nghiên cứu do Duy tạo ra (`T01`, `T02`,...) phải nằm trong `docs/rd-tasks/` kèm hướng dẫn và cross-review checklist. | R&D Inception |
| **DIR-005** | 2026-09-11 | Hưng & Duy | **Chính sách Git (Chỉ cấm lệnh nhạy cảm ghi)**: Cấm tuyệt đối `git add`, `git commit`, `git push`. Cho phép chạy các lệnh chỉ đọc như `git status`, `git log`, `git diff`, `git show`. | Mọi Agent & Terminal |
| **DIR-006** | 2026-09-11 | Hưng & Duy | **Zero Broken Links & URL Verification**: Mọi URL, link bài báo khoa học, cổng thông tin và domain viết ra trong repo (hiện tại và sau này) bắt buộc phải được kiểm tra khả năng truy cập qua skill `url-link-verifier` (`verify_links.py`), cam kết 100% link sống. | Toàn bộ tài liệu & Specs |
| **DIR-007** | 2026-09-14 | Hưng & Duy | **Giao tiếp ngắn gọn, chuẩn khoa học, cấm AI Slop**: Phản hồi hội thoại phải vào thẳng kết quả (Answer-First), không chào hỏi rào đón, không lộ suy nghĩ nội bộ (Zero Reasoning Leak), không tóm tắt luẩn quẩn (No Tie-Back), không nịnh bợ. Soạn thảo tài liệu (.md, .html) phải súc tích, định lượng, loại bỏ triệt để từ ngữ và cấu trúc sáo rỗng AI theo skill `anti-slop-scientific-writer`. | Toàn bộ tương tác AI & Tài liệu |
| **DIR-008** | 2026-09-14 | Hưng & Duy | **Cơ chế tự động kích hoạt kỹ năng (Implicit Intent Activation)**: Toàn bộ các skill trong repo phải tự động kích hoạt dựa trên việc phân tích ý định (intent matching) trong câu hỏi/yêu cầu của người dùng; tuyệt đối không đòi hỏi hay bắt buộc người dùng phải gõ đúng tên skill mới sử dụng. | Mọi Agent & Kỹ năng |
| **DIR-009** | 2026-09-14 | Đỗ Kiến Hưng | **Tiêu Chuẩn Thuật Ngữ, Từ Viết Tắt & Phương Pháp Luận Khoa Học (FIT-HCMUTE Standard)**:<br>1. *Danh mục từ viết tắt*: Đặt trước Chương 1, sắp xếp A-Z theo bảng 3 cột: `Ký hiệu/Viết tắt \| Tên đầy đủ Tiếng Việt \| Tên Tiếng Anh nguyên bản`.<br>2. *Xuất hiện lần đầu*: Viết đầy đủ Tiếng Việt kèm *Thuật ngữ Tiếng Anh in nghiêng* và (Từ viết tắt). Các lần sau chỉ dùng từ viết tắt.<br>3. *Thuật ngữ chuyên ngành IT*: Giữ nguyên thuật ngữ quốc tế chuẩn (Pipeline, Lakehouse, Vector Embedding, Ingestion, Crawler, Prompt...), không dịch gượng ép thô kệch.<br>4. *Phương pháp nghiên cứu*: Phải là các phương pháp khoa học chuẩn mực (Nghiên cứu lý thuyết/tổng quan tài liệu, Mô hình hóa dữ liệu, Phương pháp điều tra khảo sát, Phương pháp thực nghiệm). Tuyệt đối không tự chế/bịa tên phương pháp.<br>5. *Ngôn ngữ chuẩn mực*: Sử dụng các danh từ khoa học phổ biến (như *"Đối tượng khảo sát"*), không dùng từ xa lạ, khiên cưỡng. | Toàn bộ tài liệu học thuật & Luận văn |
| **DIR-010** | 2026-09-14 | Đỗ Kiến Hưng | **Quy Chuẩn Soạn Thảo Văn Phong Tiếng Việt Học Thuật Tự Nhiên & Bài Trừ Triệt Để AI Slop**:<br>1. *Hạn chế in đậm*: Tuyệt đối không lạm dụng in đậm tràn lan trong câu văn. Chỉ in đậm tiêu đề mục lớn.<br>2. *Cấu trúc danh sách phẳng*: Thay pattern `1. **<Nội dung>**: <giải thích>` bằng `1. <Nội dung chính>. <giải thích chi tiết>` (dùng dấu chấm, văn xuôi liền mạch).<br>3. *Không giải thích tiếng Anh kèm sau từ tiếng Việt thông dụng*: Các từ thông thường (thời hạn đăng ký, hồ sơ cá nhân...) đã rõ nghĩa thì không chèn `(Registration Deadline)`, `(Curriculum Vitae)` phía sau. Không viết lặp lại kiểu `Công nghệ Thông tin (CNTT)` khi từ đã phổ biến.<br>4. *Không dịch thô kèm tiếng Anh ngoặc đơn*: Bỏ các pattern như *"Lý thuyết thu thập thích ứng và chính sách làm mới trang (Adaptive Page Refresh)"*. Dùng tiêu đề tiếng Việt tự nhiên, súc tích.<br>5. *Văn phong kết nối tự nhiên*: Hạn chế mở ngoặc liệt kê `(<liệt kê>)`, thay bằng câu văn dùng từ nối, dấu phẩy, *"như"*, *"và"*.<br>6. *Minh bạch chỉ số chưa đo đạc*: Các chỉ số định lượng chưa kiểm nghiệm thực tế (như Faithfulness, Answer Relevance) phải nêu rõ là *chỉ tiêu kỳ vọng / mục tiêu kiểm thử dự kiến*, không khẳng định như đã đạt được.<br>7. *Định dạng giản dị*: Không dùng khung ASCII art rườm rà. Liệt kê rành mạch, chuẩn văn bản in ấn. | Toàn bộ văn bản học thuật & Báo cáo |





