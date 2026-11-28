# RFC-0002: Ngưỡng Kích hoạt Tiến hóa Kiến trúc Quy mô KLTN (Scale-Up Triggers)

- Status: Draft (Định hướng Phase 2 KLTN — Chờ nghiệm thu sau TLCN)
- Author(s): Đỗ Kiến Hưng (`@darktheDE`), Nguyễn Văn Quang Duy (`@QuangDuyReal`)
- Created Date: 2026-11-26
- Target Component: Lakehouse, RAG Engine, Backend, Infrastructure
- Source Audit: [`TASK-QA-01`](../deliverables/TASK-QA-01-tech-decision-theory-practice-audit.md)

---

## 1. Motivation & Context

Ở giai đoạn Tiểu luận Chuyên ngành (`TLCN`, `5–20` cuộc thi, `1` Uvicorn worker), kiến trúc tinh giản hiện tại (Plain Parquet trên Cloudflare R2, In-Memory TTL Cache, Dense-only RAG trên Qdrant, GitHub Actions keep-alive) đạt hiệu năng tốt ở mức chi phí `$0/tháng`. Tuy nhiên, khi chuyển sang giai đoạn Khóa luận Tốt nghiệp (`KLTN`, `100–500` cuộc thi, `500–1.000` sinh viên, cào tự động định kỳ), 4 thành phần sẽ chạm giới hạn thiết kế nếu không có lộ trình nâng cấp định lượng.

RFC này thiết lập các **ngưỡng kích hoạt (Scale Triggers)** rõ ràng để không mở rộng sớm gây phình hệ thống trong TLCN (`DIR-015`), đồng thời chuẩn bị sẵn phương án kỹ thuật có kiểm chứng cho KLTN (`TASK-GLD-03`, `TASK-DQ-11..13`, `TASK-AI-01`, `TASK-OPS-03`).

---

## 2. Proposed Change (4 Ngưỡng Tiến hóa Kiến trúc KLTN)

| Trục kiến trúc | Trạng thái TLCN hiện hành | Ngưỡng kích hoạt chuyển đổi (Trigger) | Giải pháp mục tiêu cho KLTN | Task KLTN liên kết |
| :--- | :--- | :--- | :--- | :---: |
| **T1. Table Format & SCD-2** | Plain PyArrow Parquet trên R2 (`overwrite` snapshot) | Số cuộc thi `> 100` hoặc phát sinh yêu cầu lưu lịch sử thay đổi giải thưởng/deadline (`SCD Type 2`, `CDC`) | Chuyển sang **Apache Iceberg** (Cloudflare R2 Data Catalog) hoặc **DuckLake** (metadata trên Supabase Postgres + data Parquet trên R2) | `TASK-GLD-03`, `TASK-DQ-12` |
| **T2. AI Gateway & Hybrid RAG** | Chuỗi fallback tuần tự (`Gemini -> Groq -> OpenRouter :free`) + Dense-only `@cf/baai/bge-m3` | Tỷ lệ HTTP `429` của Gemini `> 5%` khi xử lý Silver batch `> 100` URLs hoặc Ragas Context Recall `< 0.85` trên tên riêng/mã cuộc thi | Triển khai **Quota-Aware Multi-Provider AI Gateway** + Semantic Cache (`TASK-AI-01`) và **Hybrid Dense + Sparse Search** (BGE-M3 lexical + dense trên Qdrant `query_points`) | `TASK-AI-01`, `TASK-QA-07`, `TASK-EVL-01` |
| **T3. Distributed State & Rate Limit** | `GoldMartsTTLCache`, `RagResponseTTLCache`, và Sliding-Window Rate Limiter nằm trong RAM 1 process | Triển khai `workers > 1` hoặc nhiều container API song song, hoặc có lưu lượng bot/spam công khai | Đưa Rate Limit và Response Cache ra **Upstash Redis Free** (hoặc Cloudflare Workers Cache) kết hợp **Cloudflare Turnstile** bảo vệ form/API công khai | `TASK-OPS-03`, `TASK-BE-01` |
| **T4. Pipeline Orchestration** | Chạy CLI thủ công + `keep-alive.yml` cron hằng ngày | Cần lịch cào phân tầng theo mùa vụ, tự động retry từng URL lỗi và backfill dữ liệu thiếu | Đối chiếu thực nghiệm **GitHub Actions Matrix vs. Prefect 3 vs. Dagster** để chốt Orchestrator chính thức cho KLTN | `TASK-DQ-11`, `TASK-ING-02`, `TASK-DQ-13` |

---

## 3. Impact Analysis

- **Breaking Changes**: Không ảnh hưởng tới giai đoạn TLCN vì toàn bộ thay đổi chỉ kích hoạt khi vượt ngưỡng tại Phase 2 (KLTN).
- **Database & Lakehouse Schema**: T1 bổ sung cột hiệu lực thời gian (`effective_from`, `effective_to`, `is_current`) cho `dim_competition` và metadata bảng Iceberg/DuckLake.
- **API Surface Changes**: T2 và T3 giữ nguyên hợp đồng OpenAPI `/api/v1/*`, chỉ thay đổi lớp adapter bên trong `rag_service.py`, `gold_queries.py` và `middleware/security.py`.
- **New Dependencies**: Tùy chọn thêm `pyiceberg` / `ducklake` (T1), `redis` / Upstash REST client (T3) khi mở `ADR-0003` ở Cycle 09.

---

## 4. Alternatives Considered

1. **Áp dụng ngay Apache Iceberg, Redis và Prefect vào TLCN**: Bị từ chối theo `DIR-015` vì tăng chi phí vận hành, cấu hình catalog và rủi ro phát sinh độ trễ không cần thiết trên tập `18–19` cuộc thi của TLCN.
2. **Không đặt ngưỡng kích hoạt cho KLTN**: Bị từ chối vì thiếu lộ trình tiến hóa rõ ràng khi Hội đồng chất vấn khả năng chịu tải ở quy mô `500` cuộc thi và `1.000` sinh viên.

---

## 5. Migration & Rollback Strategy

1. Mỗi mục từ `T1` đến `T4` chỉ được triển khai sau khi có benchmark thực nghiệm ở Cycle 09 và qua phản biện hai tác giả (`TASK-QA-15`) để ban hành `ADR-0003`.
2. Tách nhánh triển khai hoặc feature flag (`USE_DISTRIBUTED_CACHE`, `ENABLE_HYBRID_SPARSE_RAG`) để có thể hạ cấp tức thời về cấu hình đơn giản của TLCN nếu dịch vụ miễn phí ngoài gặp gián đoạn.

---

## 6. Action Items / Implementation Plan

- [ ] Dùng ma trận ngưỡng `T1–T4` làm luận cứ trả lời Hội đồng bảo vệ TLCN (`TASK-ACD-01`).
- [ ] Đo hiệu năng baseline tại `TASK-BE-01` và `TASK-QA-07` để xác định mốc thực tế kích hoạt `T2` và `T3`.
- [ ] Thực thi đánh giá công nghệ chi tiết ở đầu Phase 2 (`TASK-DQ-11`, `TASK-DQ-12`, `TASK-AI-01`, `TASK-QA-15`) trước khi ban hành `ADR-0003`.
