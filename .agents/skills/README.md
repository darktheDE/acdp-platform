# ACDP Agent Skills Suite & Engineering Standards
> **Central Skills Registry and Quality Standards for All AI Agents**  
> **Repository**: `acdp-platform` | Faculty of Information Technology, HCMUTE  

---

## 1. Skills Directory Overview

Thư mục `.agents/skills/` chứa các gói kỹ năng chuyên biệt (Modular Agent Skills) được nạp theo cơ chế **Progressive Disclosure** (Nạp lũy tiến theo nhu cầu). Toàn bộ 6 kỹ năng trong kho lưu trữ đã được nâng cấp toàn diện và chứng nhận đạt chuẩn kỹ thuật:
👉 **[`docs/frameworks/AGENT_SKILL_ENGINEERING_SPEC.md`](../../docs/frameworks/AGENT_SKILL_ENGINEERING_SPEC.md)**

---

## 2. Active Skills Registry (Certified Production-Grade)

| Tên Kỹ năng (Skill Name) | Thư mục & Cấu trúc Tầng 3 | Mục đích & Phạm vi Kích hoạt | Trạng thái Nghiệm thu |
| :--- | :--- | :--- | :---: |
| **`academic-researcher`** | [`academic-researcher/`](./academic-researcher/)<br>• `scripts/validate_bibtex.py`<br>• `references/sota_venues_and_fields.md`<br>• `examples/sample_sota_matrix.md` | Nghiên cứu tổng quan y văn (Literature Review), tìm kiếm bài báo khoa học CS/Data Engineering, lập ma trận SOTA, quản lý trích dẫn BibTeX. | ✅ **ĐẠT CHUẨN (10/10)**<br>Script test PASS |
| **`competitor-benchmark`** | [`competitor-benchmark/`](./competitor-benchmark/)<br>• `scripts/validate_swot_format.py`<br>• `references/competitor_profiles.md`<br>• `examples/uvp_differentiation_matrix.md` | Đánh giá đối thủ cạnh tranh (Devpost, Unstop, Kaggle), lập ma trận SWOT, định vị giá trị độc bản (UVP) cho ACDP. | ✅ **ĐẠT CHUẨN (10/10)**<br>Script test PASS |
| **`defense-pitch-builder`**| [`defense-pitch-builder/`](./defense-pitch-builder/)<br>• `scripts/validate_slides_html.py`<br>• `references/committee_defense_rubric.md`<br>• `examples/sample_defense_slide.html` | Xây dựng slide thuyết trình bảo vệ đề tài (HTML/Tailwind self-contained), kịch bản pitching và ngân hàng câu hỏi phản biện hóc búa. | ✅ **ĐẠT CHUẨN (10/10)**<br>Script test PASS |
| **`experiment-evaluator`** | [`experiment-evaluator/`](./experiment-evaluator/)<br>• `scripts/compute_ragas_scorecard.py`<br>• `references/ragas_metric_definitions.md`<br>• `examples/sample_evaluation_scorecard.md` | Thiết kế khung thực nghiệm đo lường định lượng, đánh giá RAG theo chuẩn Ragas (Faithfulness, Context Precision), đo latency. | ✅ **ĐẠT CHUẨN (10/10)**<br>Script test PASS |
| **`frontend-designer`** | [`frontend-designer/`](./frontend-designer/)<br>• `scripts/validate_ui_component.py`<br>• `references/design_tokens.md`<br>• `examples/competition_card.tsx` | Thiết kế và xây dựng giao diện người dùng Next.js 15, mockup HTML/Tailwind xem trước nhanh, widget biểu đồ phân tích Recharts. | ✅ **ĐẠT CHUẨN (10/10)**<br>Script test PASS |
| **`thesis-writer`** | [`thesis-writer/`](./thesis-writer/)<br>• `scripts/check_thesis_formatting.py`<br>• `references/fit_hcmute_thesis_guideline.md`<br>• `examples/sample_chapter_section.md` | Soạn thảo các chương báo cáo Tiểu luận chuyên ngành và Khóa luận tốt nghiệp theo chuẩn văn phong học thuật Khoa CNTT - HCMUTE. | ✅ **ĐẠT CHUẨN (10/10)**<br>Script test PASS |
| **`url-link-verifier`** | [`url-link-verifier/`](./url-link-verifier/)<br>• `scripts/verify_links.py`<br>• `references/http_status_and_antibot_guide.md`<br>• `examples/sample_link_audit_report.json` | Tự động quét và kiểm chứng tính sống còn, khả dụng của toàn bộ URL, link bài báo khoa học và domain trên toàn repo. | ✅ **ĐẠT CHUẨN (10/10)**<br>Script test PASS |


---

## 3. Kiến Trúc 3 Tầng Bắt Buộc Của Mỗi Skill

Mỗi skill bắt buộc phải bao gồm đầy đủ:
1. **Tier 1 - Discovery (Metadata)**: YAML frontmatter trong `SKILL.md` (chứa `name`, `description` với positive keywords và **negative triggers** rõ ràng, cùng `compatibility`).
2. **Tier 2 - Activation (Workflow)**: Thân file `SKILL.md` chứa quy trình từng bước, tiêu chuẩn bất biến, bảng **Gotchas Catalog** và checklist kiểm tra.
3. **Tier 3 - Execution (Artifacts)**:
   - `scripts/`: Chứa mã Python/Bash tất định để kiểm tra tính hợp lệ tự động.
   - `references/`: Chứa tài liệu thông số kỹ thuật, bảng mã lỗi và hướng dẫn chi tiết một cấp.
   - `examples/`: Chứa ít nhất một mẫu đầu ra hoàn chỉnh đạt tiêu chuẩn vàng (Few-shot grounding).
