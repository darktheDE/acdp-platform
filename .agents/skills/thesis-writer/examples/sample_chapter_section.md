# Bản Thảo Đoạn Mẫu: Chương 3 - Thiết Kế Kiến Trúc Hệ Thống (Chuẩn FIT-HCMUTE)

### 3.1. Kiến trúc phân tầng tổng thể hệ thống

Nhằm đáp ứng đồng thời yêu cầu thu thập dữ liệu bất định từ mạng xã hội, đảm bảo tính toàn vẹn giao dịch và phục vụ truy vấn phân tích (OLAP) với độ trễ thấp, nhóm nghiên cứu đề xuất kiến trúc hệ thống 4 phân tầng độc lập như được minh họa trong **Hình 3.1**.

```
┌────────────────────────────────────────────────────────────────────────┐
│ 1. Tầng Thu thập (Ingestion): Crawl4AI + Playwright + Pydantic Schema   │
├────────────────────────────────────────────────────────────────────────┤
│ 2. Tầng Lưu trữ Hồ dữ liệu (Lakehouse): Bronze -> Silver -> Gold (dbt) │
├────────────────────────────────────────────────────────────────────────┤
│ 3. Tầng Xử lý Ngữ nghĩa & AI: Qdrant Vector Store + Hybrid Search RAG  │
├────────────────────────────────────────────────────────────────────────┤
│ 4. Tầng Dịch vụ & Trực quan (Serving): FastAPI Backend + Next.js 15 Web│
└────────────────────────────────────────────────────────────────────────┘
```
*Hình 3.1: Sơ đồ kiến trúc 4 phân tầng của nền tảng ACDP.*

#### Phân tích chức năng các phân tầng:
1. **Tầng Thu thập Dữ liệu (Ingestion Layer)**: Sử dụng Playwright kết hợp Crawl4AI để tải nội dung các trang web động JavaScript. Các bài viết sau đó được chuẩn hóa về định dạng JSON có cấu trúc bằng mô hình ngôn ngữ lớn thông qua các ràng buộc schema nghiêm ngặt định nghĩa bởi Pydantic v2 [Xu et al., 2024].
2. **Tầng Lưu trữ Hồ dữ liệu (Lakehouse Layer)**: Triển khai theo mô hình Medallion phân tầng. Toàn bộ dữ liệu thô ban đầu được lưu giữ bất biến tại tầng Bronze dưới định dạng Parquet. Tại tầng Silver, các tiến trình DuckDB thực hiện khử trùng lặp sự kiện và chuẩn hóa mốc thời gian trước khi nạp vào các bảng dữ liệu tinh gọn (Data Marts) tại tầng Gold trong PostgreSQL [Armbrust et al., 2021].
3. **Tầng Xử lý Ngữ nghĩa & AI**: Cung cấp khả năng tìm kiếm ngữ nghĩa và trợ lý tra cứu quy chế dựa trên kiến trúc Hybrid Search kết hợp giữa tìm kiếm từ khóa chính xác BM25 và tìm kiếm vector dày đặc trong Qdrant [Lewis et al., 2020].
4. **Tầng Dịch vụ & Trực quan hóa**: Cung cấp các giao diện lập trình ứng dụng RESTful thông qua FastAPI và cổng thông tin trực quan cho sinh viên xây dựng trên nền tảng Next.js 15.
