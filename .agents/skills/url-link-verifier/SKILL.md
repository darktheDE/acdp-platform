---
name: url-link-verifier
description: >-
  Systematically scan, validate, and verify the reachability and availability of all external URLs,
  web links, and domain names across repository documents, research papers, university portals, and specs.
  Trigger on: link check, verify url, check broken links, domain audit, kiểm tra link, kiểm tra domain,
  broken link detector, link reachability, test urls.
  DO NOT use for: internal markdown file links (file:///, relative paths), checking database connections,
  or testing python pip package dependencies.
compatibility: Python 3.10+, Standard Library only (Zero external pip dependencies)
---

# URL & Domain Reachability Verifier (`url-link-verifier`)

This skill provides an automated, deterministic quality gate to ensure that **every external URL, domain name, research paper DOI, university portal, or competition hub link cited anywhere in the repository is 100% alive, reachable, and accessible**.

---

## 1. Trigger Conditions & Boundaries

- **Activate this skill when**:
  - The user requests checking or auditing links, URLs, or domains across the repository or in specific files.
  - A new research document, competitor analysis, thesis chapter, or data ingestion spec containing external URLs is authored or edited.
  - Pre-commit or pre-defense verification is conducted to ensure zero broken citations (`404 Not Found` or `DNS_FAILED`).
- **DO NOT activate this skill for**:
  - Local filesystem paths or internal GitHub Markdown links (`file:///...`, `../deliverables/...`, `#anchor`).
  - Checking SQL database connection strings or vector database ports.
  - Auditing Python virtual environment packages or npm dependencies.

---

## 2. Invariant Project Standards (Quy Chuẩn Bất Biến)

1. **Chính sách Zero Broken Links (Không Chấp Nhận Link Chết)**:
   - Mọi liên kết bài báo (DOI), website cuộc thi, hoặc cổng thông tin được đưa vào tài liệu nghiệm thu (`docs/deliverables/`), đặc tả (`docs/specs/`), hoặc thư viện trích dẫn (`docs/academic/references.bib`) phải được kiểm chứng khả năng truy cập thực tế.
2. **Tính Tất Định Tuyệt Đối (Deterministic Execution)**:
   - Không để mô hình LLM phỏng đoán hoặc tự suy diễn trạng thái sống còn của URL. Mọi kết quả kiểm tra **BẮT BUỘC PHẢI THỰC THI QUA SCRIPT** [`scripts/verify_links.py`](./scripts/verify_links.py).
3. **Phân Định Rõ Ràng: Link Chết (404/NXDOMAIN) vs. Tường Lửa Bot (401/403/429)**:
   - Nếu domain tồn tại và website đang hoạt động bình thường nhưng trả về mã `401/403` do tường lửa Cloudflare/WAF chặn bot tự động, script phân loại là `RESTRICTED_BOT` (Hợp lệ, trang web thực tế vẫn sống).
   - Chỉ khi domain không tồn tại (`DNS_FAILED`) hoặc trả về `404 Not Found` / `410 Gone`, link mới bị kết luận là `BROKEN`.

---

## 3. Step-by-Step Execution Protocol (Quy Trình Kiểm Tra 4 Bước)

### Bước 1: Quét và Trích Xuất Toàn Bộ URLs
- Chạy script kiểm tra trên toàn bộ kho lưu trữ hoặc thư mục chỉ định:
  ```bash
  python .agents/skills/url-link-verifier/scripts/verify_links.py --path docs/
  ```
- Hoặc kiểm tra một tệp tài liệu cụ thể vừa được viết mới:
  ```bash
  python .agents/skills/url-link-verifier/scripts/verify_links.py --path docs/rd-tasks/T02.md
  ```

### Bước 2: Kiểm Tra Tên Miền (DNS Pre-check & Anti-Hijacking)
- Script tự động phân giải DNS của domain qua `socket.getaddrinfo`.
- Tự động nhận diện và loại trừ các địa chỉ IP chuyển hướng tìm kiếm của nhà mạng (ISP NXDOMAIN Wildcard Hijacking như VNPT `125.235.4.59`).

### Bước 3: Kiểm Tra Tính Sống Còn HTTP Đa Luồng (Concurrent Reachability)
- Script sử dụng `ThreadPoolExecutor(max_workers=10)` để gửi request kiểm tra song song:
  - Thử phương thức HTTP `HEAD` trước với User-Agent trình duyệt thực.
  - Tự động fallback sang HTTP `GET` (kèm header `Range: bytes=0-1024`) nếu máy chủ từ chối phương thức `HEAD` (mã 405/403).
  - Tự động bám theo chuỗi chuyển hướng (Redirect 301, 302, 307, 308).

### Bước 4: Xuất Báo Cáo & Xử Lý Link Lỗi (Remediation)
- Nếu phát hiện bất kỳ link nào bị `BROKEN` hoặc `DNS_FAILED`:
  1. Đối soát số dòng và tệp nguồn được liệt kê trong báo cáo.
  2. Dùng công cụ `search_web` tìm kiếm URL thay thế chính thức hoặc cập nhật URL mới nhất.
  3. Cập nhật lại tệp tài liệu và chạy lại script để xác nhận kết quả đạt chuẩn `0 (PASS)`.
- Xuất báo cáo chi tiết ra file JSON hoặc Markdown nếu cần:
  ```bash
  python .agents/skills/url-link-verifier/scripts/verify_links.py --path docs/ --markdown docs/deliverables/link_audit_report.md
  ```

---

## 4. Edge Cases & Gotchas (Lỗi Thường Gặp & Cách Xử Lý)

| Hiện tượng / Lỗi phát sinh | Nguyên nhân gốc rễ | Cách xử lý chuẩn |
| :--- | :--- | :--- |
| **Bị mã 403 Forbidden trên các trang IEEE / MDPI** | Tường lửa Cloudflare chặn header User-Agent mặc định của Python (`python-urllib`). | Script tự động gắn User-Agent của Google Chrome phiên bản mới nhất kèm fallback sang GET. |
| **Dấu ngoặc đơn `)` dính vào đuôi URL** | Cú pháp Markdown `[Tên](https://domain.com/path)` khiến regex lấy luôn dấu đóng ngoặc hoặc dấu chấm câu cuối câu. | Hàm `clean_url()` tự động gọt sạch dấu chấm câu và cân bằng dấu ngoặc trước khi gửi request. |
| **Domain không tồn tại nhưng trả về IP thật** | Một số nhà mạng tại Việt Nam (VNPT/Viettel) chuyển hướng truy vấn DNS không tồn tại về cổng tìm kiếm riêng (`125.235.4.59`). | `KNOWN_DNS_HIJACK_IPS` lọc bỏ các IP giả lập này và phán quyết chính xác `DNS_FAILED`. |
| **Cổng thông tin DOI (`doi.org`) trả về 302** | Bản chất của DOI là bộ phân giải chuyển hướng (Resolver) trỏ về bài báo gốc của nhà xuất bản. | Bộ nạp HTTP tự động bám theo redirect và xác nhận `HEALTHY`. |

---

## 5. Verification & Tooling Links

- Script kiểm tra chính: [`scripts/verify_links.py`](./scripts/verify_links.py)
- Kịch bản smoke test: [`scripts/test_verify_links.py`](./scripts/test_verify_links.py)
- Hướng dẫn mã trạng thái HTTP & Anti-bot: [`references/http_status_and_antibot_guide.md`](./references/http_status_and_antibot_guide.md)
- Danh mục domain học thuật tiêu biểu: [`references/academic_domain_whitelist.md`](./references/academic_domain_whitelist.md)
- Báo cáo mẫu chuẩn: [`examples/sample_link_audit_report.json`](./examples/sample_link_audit_report.json)
