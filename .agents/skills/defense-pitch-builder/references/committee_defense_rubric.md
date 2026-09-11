# FIT-HCMUTE Committee Defense Rubric & Pacing Guide

This reference details the defense criteria, timing pace, and common adversarial lines of questioning used by the FIT-HCMUTE evaluation committee.

---

## 1. Presentation Timing Pacing (12-Minute Standard Budget)

| Slide Range | Focus | Target Duration | Pacing Tip |
| :--- | :--- | :---: | :--- |
| **Slides 1–3** | Introduction, Practical Bottlenecks & Scope | 2.5 minutes | Do not linger on generic motivation; emphasize the 4 specific bottlenecks. |
| **Slides 4–5** | Overall Architecture & Data Ingestion Lakehouse | 3.5 minutes | Focus on Data Engineering rigor (Bronze/Silver/Gold, DuckDB, Pydantic). |
| **Slides 6–7** | Semantic AI (RAG Copilot) & Matchmaking | 3.0 minutes | Highlight BM25 + Vector Hybrid Search and anti-hallucination guardrails. |
| **Slides 8–10** | Live Demo, Benchmark Evaluation & Outlook | 3.0 minutes | Show concrete empirical numbers (latency, Ragas faithfulness). |

---

## 2. Committee Evaluation Criteria & Weights

1. **Scientific & Engineering Rigor (35%)**: Depth of data architecture, proper use of Lakehouse principles, schema validation resilience.
2. **Implementation Quality & Demo (30%)**: Functional demonstration of ingestion pipeline, working RAG query engine, web portal responsiveness.
3. **Manuscript & Presentation Quality (20%)**: Clear visual slide hierarchy, academic phrasing, adherence to time limits.
4. **Adversarial Q&A Response (15%)**: Confidence, empirical backing, and honesty regarding technical trade-offs.

---

## 3. High-Frequency Committee Questions & Answering Cheat Sheet

- **Q1: "Tại sao dùng DuckDB thay vì PostgreSQL thuần túy?"**
  - *Answer*: DuckDB là hệ quản trị OLAP nhúng theo cột (columnar), tối ưu vượt trội cho các truy vấn tổng hợp phân tích dữ liệu lớn trên file Parquet mà không tốn chi phí vận hành cụm, trong khi PostgreSQL tối ưu cho giao dịch OLTP của ứng dụng web.
- **Q2: "Làm sao ngăn chặn ảo giác (hallucination) trong câu trả lời thể lệ thi?"**
  - *Answer*: Hệ thống sử dụng Hybrid Search (BM25 + Qdrant) kết hợp Cross-Encoder Re-ranking để truy xuất chính xác điều khoản quy chế, và prompt hệ thống cưỡng bức mô hình chỉ được trả lời dựa trên trích dẫn điều khoản thực tế.
