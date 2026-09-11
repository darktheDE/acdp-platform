# Danh Mục Tên Miền Học Thuật & Đơn Vị Tổ Chức Được Kiểm Chứng

> **Mã tài liệu**: `REF-URL-002`  
> **Áp dụng cho**: Skill `url-link-verifier` & Tầng Ingestion của ACDP

---

## 1. Các Hub Khoa Học & Cổng Trích Dẫn Toàn Cầu (Global Academic & DOI Resolvers)

| Tên Miền (Domain) | Đơn Vị Chủ Quản | Mục Đích Sử Dụng Trong ACDP | Đặc Điểm Truy Cập |
| :--- | :--- | :--- | :--- |
| `doi.org` | International DOI Foundation | Định danh vĩnh viễn các bài báo khoa học (ACM, IEEE, VLDB, Nature). | Luôn tự động chuyển hướng (HTTP 302/301) sang nhà xuất bản gốc. |
| `vldb.org` | Very Large Data Bases Endowment | Kỷ yếu hội nghị hàng đầu thế giới về Cơ sở dữ liệu và Kỹ thuật Dữ liệu. | Truy cập trực tiếp (HTTP 200). |
| `acm.org` / `dl.acm.org` | Association for Computing Machinery | Tạp chí và kỷ yếu ACM (TODS, WWW, SIGMOD). | Yêu cầu User-Agent hợp lệ; DOI link chuyển hướng tốt. |
| `ieee.org` / `ieeexplore.ieee.org` | IEEE | Thư viện điện tử IEEE Xplore. | Có tường lửa chặn bot (HTTP 403 trên crawler thuần). |
| `mdpi.com` | MDPI Open Access Journals | Các công trình nghiên cứu mở về Focused Web Crawling và Event Detection. | Truy cập trực tiếp (HTTP 200). |
| `github.com` | GitHub Inc. | Mã nguồn mở, test datasets, write-up của các đội quán quân ICPC. | HTTP 200; bám theo rate limit. |

---

## 2. Hệ Thống Cổng Thông Tin Đại Học & Cơ Quan Nhà Nước Tại Việt Nam

| Tên Miền (Domain) | Đơn Vị Chủ Quản | Phạm Vi Cuộc Thi | Ghi Chú Kỹ Thuật |
| :--- | :--- | :--- | :--- |
| `hcmute.edu.vn` | Trường Đại học Công nghệ Kỹ thuật TP.HCM | Các cuộc thi nội bộ FIT, nghiên cứu khoa học sinh viên. | HTTP 200 / SSL chính thức. |
| `fit.hcmute.edu.vn` | Khoa Công nghệ Thông tin - HCM-UTE | Thông báo OLP, ICPC vòng trường, Hackathon mở rộng. | Subdomain trường. |
| `vnuhcm.edu.vn` | Đại học Quốc gia TP.HCM | Giải thưởng cấp ĐHQG, chương trình ươm mầm tài năng. | Cổng ĐHQG. |
| `uit.edu.vn` | Trường ĐH Công nghệ Thông tin (ĐHQG-HCM) | Giải UIT CTF, cuộc thi AI & An toàn thông tin. | Subdomain ĐHQG. |
| `hcmut.edu.vn` | Trường ĐH Bách Khoa (ĐHQG-HCM) | Giải Bach Khoa Innovation (BKI). | Subdomain ĐHQG. |
| `khoahoctre.com.vn` | Trung tâm Phát triển KH&CN Trẻ - Thành Đoàn TP.HCM | Giải thưởng Sinh viên NCKH Euréka, Tin học Trẻ TP.HCM. | Hub tổng hợp cuộc thi TP.HCM. |
| `vnoi.info` | Cộng đồng Thuật toán và Lập trình Việt Nam | ICPC Vietnam, Olympic Tin học Sinh viên (OLP). | Hub bài thi thuật toán. |
| `chinhphu.vn` | Cổng Thông tin Điện tử Chính phủ | Văn bản quy phạm pháp luật, quyết định đổi tên trường đại học. | Cổng thông tin Quốc gia. |
