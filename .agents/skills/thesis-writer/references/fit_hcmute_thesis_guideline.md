# Quy Định Định Dạng Luận Văn Khoa CNTT - Trường Đại học Công nghệ Kỹ thuật TP.HCM (HCM-UTE)

Tài liệu này tổng hợp các quy định bắt buộc về hình thức trình bày và văn phong học thuật của Khoa CNTT, Trường Đại học Công nghệ Kỹ thuật TP.HCM (HCM-UTE).

---

## 1. Bố Cục 5 Chương Chuẩn của Đề Tài Kỹ Thuật Dữ Liệu

1. **Chương 1: Giới thiệu và Tổng quan đề tài**:
   - Nêu rõ bối cảnh, 4 nút thắt thực tế của sinh viên, mục tiêu tổng quát, 4 mục tiêu cụ thể, và giới hạn phạm vi 15 tuần TLCN vs 15 tuần KLTN.
2. **Chương 2: Cơ sở lý thuyết và Tổng quan nghiên cứu**:
   - Trình bày sâu về kiến trúc Medallion Lakehouse, trích xuất thực thể bằng LLM, kỹ thuật Hybrid RAG (BM25 + Vector), và thuật toán ghép đội.
3. **Chương 3: Thiết kế kiến trúc và Hệ thống**:
   - Sơ đồ phân tầng 4 lớp (Ingestion, Lakehouse, Semantic AI, Serving), đặc tả Schema Pydantic, luồng dữ liệu Bronze $\rightarrow$ Silver $\rightarrow$ Gold.
4. **Chương 4: Cài đặt thực nghiệm và Đánh giá**:
   - Trình bày môi trường Docker, kết quả chạy pipeline thực tế, đánh giá định lượng theo khung Ragas (Faithfulness $> 0.90$, Answer Relevance $> 0.85$) và độ trễ truy vấn.
5. **Chương 5: Kết luận và Hướng phát triển**:
   - Đánh giá mức độ hoàn thành so với mục tiêu ban đầu, các mặt hạn chế và lộ trình mở rộng cho Khóa luận tốt nghiệp.

---

## 2. Quy Tắc Trình Bày Hình Ảnh & Bảng Biểu

- **Đánh số thứ tự kép theo chương**: `Hình <chương>.<thứ tự>` (ví dụ: *Hình 3.1: Kiến trúc tổng thể hệ thống ACDP*).
- **Vị trí chú thích**:
  - Đối với **Hình (Figure)**: Chú thích đặt **ở dưới** hình.
  - Đối với **Bảng (Table)**: Chú thích đặt **ở trên** bảng.
- **Ràng buộc dẫn nhập**: Tuyệt đối không để hình hoặc bảng "mồ côi" mà không có câu văn viện dẫn trong đoạn văn lân cận (*"như được thể hiện trong Bảng 3.2..."*).
