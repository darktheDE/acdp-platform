# Sổ Tay Kỹ Thuật HTTP Status & Xử Lý Anti-Bot Khi Xác Minh Link

> **Mã tài liệu**: `REF-URL-001`  
> **Áp dụng cho**: Skill `url-link-verifier` & Bộ công cụ Ingestion Crawler

---

## 1. Phân Loại Mã Trạng Thái HTTP (HTTP Status Classification)

Khi một AI Agent hoặc script kiểm tra tính khả thi của một đường link (URL) hoặc domain, mã phản hồi HTTP được phân thành các nhóm hành vi sau:

| Nhóm Mã | Tên Trạng Thái | Ý Nghĩa Kỹ Thuật | Phán Quyết Của Link Verifier |
| :---: | :--- | :--- | :---: |
| **`200`** | `OK` | Tài nguyên tồn tại, server phản hồi thành công nội dung đầy đủ. | 🟢 **HEALTHY (PASS)** |
| **`301` / `308`** | `Permanent Redirect` | Tài nguyên chuyển vĩnh viễn sang URL mới (thường là từ `http://` sang `https://` hoặc chuyển domain). | 🟢 **HEALTHY (PASS)**<br>*(Được tự động bám theo redirect)* |
| **`302` / `307`** | `Temporary Redirect` | Chuyển hướng tạm thời (thường gặp ở cổng đăng nhập SSO hoặc link tracking). | 🟢 **HEALTHY (PASS)** |
| **`401`** | `Unauthorized` | Domain hoạt động tốt nhưng yêu cầu đăng nhập (thường là cổng thi nội bộ, dashboard admin). | 🟡 **RESTRICTED_BOT (VALID DOMAIN)** |
| **`403`** | `Forbidden` | Domain hoạt động tốt nhưng tường lửa (WAF/Cloudflare) chặn truy cập từ crawler hoặc cấm User-Agent lạ. | 🟡 **RESTRICTED_BOT (VALID DOMAIN)** |
| **`429`** | `Too Many Requests` | Server giới hạn tốc độ (Rate Limit), yêu cầu giãn cách thời gian gọi. | 🟡 **RESTRICTED_BOT (VALID DOMAIN)** |
| **`404`** | `Not Found` | Trang không tồn tại, link hỏng hoặc bài viết đã bị xóa. | 🔴 **BROKEN (FAIL)** |
| **`410`** | `Gone` | Tài nguyên đã bị gỡ bỏ vĩnh viễn khỏi máy chủ. | 🔴 **BROKEN (FAIL)** |
| **`500..504`** | `Server Error` | Lỗi nội bộ hoặc cổng gateway máy chủ bên kia bị sập. | ⚪ **SERVER_ERROR / UNREACHABLE** |

---

## 2. Các Trường Hợp Anti-Bot Phổ Biến & Kỹ Thuật Bypass An Toàn

### A. Cơ chế chặn HTTP `HEAD` của các Cổng Học Thuật
Nhiều trang web học thuật (IEEE Xplore, ScienceDirect, ACM Digital Library, Springer, các website trường đại học) chặn phương thức HTTP `HEAD` vì coi đó là dấu hiệu của web scraper.
- **Biểu hiện**: Trả về `405 Method Not Allowed` hoặc `403 Forbidden`.
- **Giải pháp trong `verify_links.py`**: Khi gặp mã 405 hoặc 403 trên `HEAD`, script tự động chuyển đổi sang HTTP `GET` với header `Range: bytes=0-1024` (chỉ tải 1KB đầu tiên để xác nhận server sống mà không tốn băng thông).

### B. Giả lập Header Trình Duyệt Thực (Browser User-Agent Masking)
- Các thư viện Python mặc định gửi `User-Agent: Python-urllib/3.12` hoặc `python-requests/2.x`. Các hệ thống bảo vệ như Cloudflare, Incapsula sẽ chặn ngay lập tức với mã 403.
- **Giải pháp**: Luôn gửi Header User-Agent của Google Chrome phiên bản máy tính mới nhất:
  ```http
  User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36
  Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8
  Accept-Language: en-US,en;q=0.5
  ```

### C. Cơ Chế Xác Minh 2 Bước: DNS Pre-check $\rightarrow$ HTTP Reachability
1. **Bước 1 (DNS Resolution)**: Trước khi gửi gói tin HTTP, dùng `socket.getaddrinfo()` để kiểm tra xem tên miền (domain) có thực sự tồn tại trên Internet hay không. Nếu không giải quyết được DNS $\rightarrow$ Khẳng định domain ảo/chết (`DNS_FAILED`).
2. **Bước 2 (HTTP Reachability)**: Sau khi DNS thành công, gửi request kiểm tra tính sống còn của URL. Nếu gặp 403 nhưng DNS tồn tại $\rightarrow$ Kết luận link và domain vẫn tồn tại, chỉ bị hạn chế bot tự động.
