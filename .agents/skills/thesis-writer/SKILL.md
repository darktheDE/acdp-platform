---
name: thesis-writer
description: >-
  Guide the drafting of formal academic manuscripts, undergraduate theses, and scientific proposals
  conforming strictly to FIT-HCMUTE formatting regulations and Vietnamese/English academic writing conventions.
  Use when the user asks for: thesis drafting, chapter writing (Chương 1 đến 5), academic proposals, or manuscript refinement.
  DO NOT use for: Writing casual conversational chats, quick code prototyping, running terminal commands, or informal notes.
compatibility: LaTeX, Markdown, FIT-HCMUTE Thesis Guidelines 2026
---

# Thesis Writer Skill

This skill guides the AI agent in drafting formal academic manuscripts, reports, and chapter drafts in Vietnamese or English, conforming strictly to the official regulations of the Faculty of Information Technology, Ho Chi Minh City University of Technology and Engineering (FIT-HCMUTE).

---

## 1. Trigger Conditions & Boundaries

- **Activate when**:
  - Drafting or revising thesis chapters (Chương 1: Mở đầu đến Chương 5: Kết luận).
  - Converting technical implementation notes into publication-grade academic prose.
  - Writing formal academic sections (Đặt vấn đề, Cơ sở lý thuyết, Thiết kế kiến trúc, Đánh giá thực nghiệm).
  - Formatting LaTeX or Markdown manuscripts with numbered equations, tables, figures, and citations.
- **DO NOT activate when**:
  - Writing frontend React components (`apps/web/`).
  - Executing terminal git commands or environment setups.
  - Drafting conversational chat responses.

---

## 2. Invariant Academic Standards

1. **Objective Third-Person Voice**: Never use informal first-person singular pronouns (*"tôi", "em", "mình"*). Use objective phrases: *"Nhóm tác giả nhận thấy...", "Hệ thống được thiết kế...", "Kết quả thực nghiệm chỉ ra..."*.
2. **Standardized 5-Chapter Structure**: Must adhere to the canonical FIT-HCMUTE structure detailed in [`references/fit_hcmute_thesis_guideline.md`](./references/fit_hcmute_thesis_guideline.md):
   - Chương 1: Giới thiệu và Tổng quan đề tài.
   - Chương 2: Cơ sở lý thuyết và Tổng quan nghiên cứu.
   - Chương 3: Thiết kế kiến trúc và Hệ thống.
   - Chương 4: Cài đặt thực nghiệm và Đánh giá.
   - Chương 5: Kết luận và Hướng phát triển.
3. **Rigorous Cross-Referencing**: Every table, figure, and equation must be explicitly numbered and cross-referenced in paragraph text (e.g. *"như minh họa tại Hình 3.2"*, *"kết quả ghi nhận tại Bảng 4.1"*).
4. **Citation Discipline**: Never make unsupported factual assertions; link claims to valid BibTeX citations using `\cite{...}` in LaTeX or `[Author, Year]` in Markdown.

---

## 3. Step-by-Step Execution Protocol

### Step 1: Chapter Outline & Dependency Mapping
Verify that the active chapter references approved specifications in `docs/specs/` and decisions in `docs/adr/`.

### Step 2: Drafting Academic Prose
Draft sections conforming to the sample style demonstrated in [`examples/sample_chapter_section.md`](./examples/sample_chapter_section.md). Maintain clear heading hierarchy (`#`, `##`, `###`).

### Step 3: Format & Style Verification Gate
Always execute the automated thesis linter before delivery:
```bash
python .agents/skills/thesis-writer/scripts/check_thesis_formatting.py --file docs/academic/Proposal_NCKH_TLCN.md
```

---

## 4. Edge Cases & Gotchas Catalog

| Gotcha / Common Failure Mode | Root Cause | Enforced Solution |
| :--- | :--- | :--- |
| **Use of Informal Pronouns** | Casual phrasing leaking from conversational prompts | Replace all instances of *"chúng tôi", "tôi"* with passive voice or *"Nhóm nghiên cứu"*. |
| **Dangling Figures / Tables** | Inserting a diagram or table without citing it in text | Precede or follow every figure with: *"Quy trình xử lý được mô tả cụ thể trong Hình X.Y..."*. |
| **Non-Standard Terminology** | Inconsistent translations of technical terms | Use standardized terms: *Đường ống dữ liệu (Data Pipeline)*, *Kho dữ liệu hồ (Data Lakehouse)*. |

---

## 5. Verification Checklist

- [ ] Execute `python .agents/skills/thesis-writer/scripts/check_thesis_formatting.py --file <manuscript.md>`.
- [ ] Confirm zero informal first-person pronouns exist in text.
- [ ] Ensure all tables and figures have descriptive captions and are referenced in text.
- [ ] Verify bibliography keys match `docs/academic/references.bib`.
