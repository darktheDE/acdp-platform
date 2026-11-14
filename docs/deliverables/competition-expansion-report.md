# Báo cáo mở rộng danh sách cuộc thi tại Việt Nam (Dedicated Event Landing Pages)

**Ngày cập nhật:** 14/11/2026  
**Tiêu chí lọc đã áp dụng:**
- Chỉ lấy **trang thông tin riêng của từng cuộc thi** (Dedicated Event Landing Page / Microsite), loại bỏ trang chủ tổ chức, nền tảng nộp bài chung, trang tin tức/báo chí và Facebook.
- **Ngoài ICPC**, không lấy giải quốc tế thuần; tập trung **cuộc thi tại Việt Nam** (hoạt động giai đoạn **2025–2026–2027**).
- Không trùng lặp với 7 cuộc thi baseline trong [`src/acdp/1_crawl_to_bronze.py`](../../src/acdp/1_crawl_to_bronze.py).

---

## 1. Danh sách 15 cuộc thi đạt chuẩn đã xác minh (HTTP 200 OK)

### A. Nhóm HTML tĩnh giàu nội dung (13 trang — Trích xuất trực tiếp toàn bộ Schema)

| STT | Tên cuộc thi | Link chính chủ (Event Landing Page) | Lĩnh vực | Mùa giải ghi nhận | Dữ liệu Schema có sẵn trên trang |
| :-: | :--- | :--- | :--- | :---: | :--- |
| 1 | **AI Thực Chiến** | https://thucchien.ai/ | AI | 2026 | Đơn vị tổ chức, giải thưởng, thể lệ/lịch trình, đối tượng |
| 2 | **LotusHacks 2026** | https://www.lotushack.org/ | AI Hackathon | 2026 | Đơn vị tổ chức, giải thưởng, lịch trình, tracks, đối tượng |
| 3 | **Data for Life** | https://dataforlife.vn/ | Data / AI / Chuyển đổi số | 2025–2026 | Đơn vị tổ chức, giải thưởng, thể lệ/lộ trình, đối tượng |
| 4 | **Vietnam Datathon** | https://vietnamdatathon.com/ | Data Science / Analytics | 2025–2026 | Đơn vị tổ chức, giải thưởng, timeline, đối tượng |
| 5 | **Datathon VinUniversity** | https://www.datathon.site/ | Data Science / AI | 2025–2026 | Đơn vị tổ chức (VinTelligence), giải thưởng, lộ trình, thể lệ |
| 6 | **AISC'26 (UIT)** | https://httt.uit.edu.vn/aisc/ | HTTT / AI / Data Analytics | 2026 | Đơn vị tổ chức (Khoa HTTT - UIT), giải thưởng, lịch trình, thể lệ |
| 7 | **RMIT Hack-A-Venture 2026** | https://www.rmithackaventure.com/ | FinTech / Hackathon | 2026 | Đơn vị tổ chức (RMIT FinTech Club), giải thưởng, quy chế, lịch trình |
| 8 | **QC4SG Vietnam 2026 (SEA Quantathon)** | https://vnquantum.org/events/quantum-hackathon-qc4sg/ | Quantum / AI Hackathon | 2026 | Đơn vị tổ chức (VNQuantum, NIC, OQI), giải thưởng, lịch trình, địa điểm |
| 9 | **Vietnam Japan AI Hackathon 2026** | https://www.vjaihackathon.com/ | Agentic AI Hackathon | 2026 | Chủ đề, số đội/vòng thi (Pitch Day, Demo Day) |
| 10 | **Qualcomm Vietnam Innovation Challenge (QVIC)** | https://qvic.vn/ | Deep Tech / AI / IoT | 2025–2027 | Đơn vị tổ chức (Qualcomm), giải thưởng, lộ trình, FAQs |
| 11 | **Vietnam Business Innovation Challenge (VBIC)** | https://vbic.vn/ | Business / Tech Innovation | 2025–2026 | Đơn vị tổ chức, giải thưởng, timeline, đối tượng |
| 12 | **Web3 HackFest 2025** | https://web3hackfest.org/ | Blockchain / AI / Game | 2025 | Đơn vị tổ chức, giải thưởng, lịch trình, hoạt động tại TP.HCM |
| 13 | **Marketing Arena 2026** | https://marketingarena.vn/ | Business / Marketing Case | 2026 | Đơn vị tổ chức, giải thưởng, thể lệ, đối tượng |

### B. Nhóm SPA (2 trang — Cần `Crawl4AI` bật JS như cấu hình hiện tại)

| STT | Tên cuộc thi | Link chính chủ (Event Landing Page) | Lĩnh vực | Mùa giải ghi nhận | Ghi chú kỹ thuật |
| :-: | :--- | :--- | :--- | :---: | :--- |
| 14 | **Zalo AI Challenge 2026** | https://challenge.zalo.ai/ | AI / Agentic AI | 2026 | Trang SPA (`og:title: Zalo AI Challenge 2026`); chạy qua `Crawl4AI` với `java_script_enabled=True` |
| 15 | **NAVER Vietnam AI Hackathon 2025** | https://event.navercorp.vn/event/naver-vietnam-ai-hackathon-2025/ | AI / Cloud Hackathon | 2025 | Trang SPA (`og:title: NAVER Việt Nam AI Hackathon 2025`); chạy qua `Crawl4AI` với `java_script_enabled=True` |

---

## 2. Đánh giá tương thích Schema ([`src/acdp/schemas.py`](../../src/acdp/schemas.py))

- **Độ tương thích:** **100% tương thích** với schema `Competition`, `TimelineStage`, `PrizeTier` hiện tại mà **không cần sửa cấu trúc Pydantic**.
- **Lý do:** Toàn bộ 15 URL đều là trang đơn giới thiệu **1 cuộc thi duy nhất**, chứa trực tiếp các trường `name`, `summary`, `organizers`, `category`, `target_audience`, `prizes`, `timeline_stages`, và `mode`/`location`.
- **Khuyến nghị khi đưa vào [`src/acdp/1_crawl_to_bronze.py`](../../src/acdp/1_crawl_to_bronze.py):** Ưu tiên nhóm **13 trang HTML tĩnh giàu nội dung** trước để đảm bảo tỷ lệ bóc tách đầy đủ nhất; với 2 trang SPA (`challenge.zalo.ai` và `event.navercorp.vn/...`), giữ nguyên `java_script_enabled=True` và kiểm tra độ dài Markdown trước khi upload Bronze.
