---
name: thesis-writer
description: >-
  Guide the drafting of formal academic manuscripts, undergraduate theses, and scientific proposals
  conforming strictly to FIT-HCMUTE formatting regulations and Vietnamese/English academic writing conventions.
  Use when the user asks for: thesis drafting, chapter writing (Chương 1 đến 5), academic proposals, or manuscript refinement.
  DO NOT use for: Writing casual conversational chats, quick code prototyping, running terminal commands, or informal notes.
compatibility: LaTeX, Markdown, FIT-HCMUTE Thesis Guidelines 2026 (Quy dinh bao cao Mẫu 0-6)
---

# Thesis Writer Skill

This skill guides the AI agent in drafting formal academic manuscripts, reports, and chapter drafts in Vietnamese or English, conforming strictly to the official regulations of the Faculty of Information Technology, Ho Chi Minh City University of Technology and Engineering (FIT-HCMUTE) documented in `Quy dinh bao cao/` (`Mẫu 0` through `Mẫu 6`, `Noi dung_Hinh thuc.doc`, `BiaTTTN.doc`, `Dinh dang.doc`).

---

## 1. Trigger Conditions & Boundaries

- **Activate when**:
  - Drafting or revising thesis chapters (`Phần 1: MỞ ĐẦU`, `Phần 2: NỘI DUNG` — `Chương 1` đến `Chương 4`, `Phần 3: KẾT LUẬN`).
  - Converting technical implementation notes into publication-grade academic prose answering the 3 core questions of `Mẫu 3`: *"Làm gì? Làm như thế nào? Kết quả ra sao?"*.
  - Writing formal academic sections (Đặt vấn đề, Cơ sở lý thuyết, Thiết kế kiến trúc, Đặc tả lược đồ, Đánh giá thực nghiệm, Kết luận chương).
  - Formatting LaTeX or Markdown manuscripts with numbered equations, tables, figures, frontmatter forms (`Mẫu 4`, `Mẫu 6`), and IEEE citations.
- **DO NOT activate when**:
  - Writing frontend React components (`apps/web/`).
  - Executing terminal git commands or environment setups.
  - Drafting conversational chat responses.

---

## 2. Invariant Academic Standards (`Quy dinh bao cao/` Source of Truth)

1. **Institutional Naming Standard (`DIR-001`)**: Always use the official university name **Trường Đại học Công nghệ Kỹ thuật TP.HCM (HCM-UTE)**, **Khoa Công nghệ Thông tin**, **Ngành Kỹ thuật Dữ liệu**, while strictly following the structural templates of `Quy dinh bao cao/`.
2. **Objective Third-Person Voice**: Never use informal first-person singular pronouns (*"tôi", "em", "mình", "tụi mình"*). Use objective academic phrasing: *"Nhóm nghiên cứu nhận thấy...", "Hệ thống được thiết kế...", "Kết quả thực nghiệm chỉ ra..."*.
3. **Arabic Numerals Only for Chapters & Sections (`Mẫu 5` Line 78)**:
   - Chapters and sections inside `Phần 2: NỘI DUNG` must use Arabic numerals only (`Chương 1`, `1.1`, `1.1.1`). **Never use Roman numerals (`I.`, `II.`, `III.`)** for chapter or section headings.
   - Do not exceed 3 levels of decimal numbering (`1.1.1`) to avoid visual clutter (`Mẫu 3`).
   - Do not use abbreviations in section headings or in the opening sentence of a chapter (`Mẫu 3`).
4. **Mandatory Chapter Conclusions (`Noi dung_Hinh thuc.doc`)**: Every chapter in `Phần 2: NỘI DUNG` (`Chương 1`, `Chương 2`, `Chương 3`, `Chương 4`) **must** end with a dedicated `### Kết luận Chương X` section summarizing the chapter's contributions and transitioning to the next chapter.
5. **Canonical 14-Part Manuscript Sequence (`Mẫu 5` & `Noi dung_Hinh thuc.doc`)**:
   - Full reports must include: (1) Bìa chính, (2) Bìa phụ, (3) Phiếu nhận xét GVHD (`Mẫu 6`), (4) Phiếu nhận xét GVPB (`Mẫu 6`), (5) Lời cảm ơn, (6) Đề cương chi tiết có chữ ký (`Mẫu 4`), (7) Mục lục, (8) Danh mục bảng biểu, (9) Danh mục hình vẽ, (10) Danh mục từ viết tắt (xếp A–Z), (11) Tóm tắt / Abstract, (12) Phần 1: MỞ ĐẦU, (13) Phần 2: NỘI DUNG, (14) Phần 3: KẾT LUẬN, `TÀI LIỆU THAM KHẢO`, và `PHỤ LỤC`.
6. **Rigorous Cross-Referencing & Caption Placement (`Mẫu 5` Lines 65–72)**:
   - Every table and figure is numbered by chapter (`Bảng <chương>.<thứ tự>`, `Hình <chương>.<thứ tự>`, or `Bảng 0.<thứ tự>` in the Outline).
   - **Table captions (`###### Bảng X.Y: ...`)** are placed **ABOVE** the table; **Figure captions (`###### Hình X.Y: ...`)** are placed **BELOW** the figure.
   - Every table and figure must be explicitly cited in the surrounding paragraph text.
7. **Unified IEEE Citation Discipline (`Noi dung_Hinh thuc.doc`)**: Every external concept, formula, benchmark, or figure must be cited using IEEE numbered brackets (`[1]`, `[2]`) matching `# TÀI LIỆU THAM KHẢO`. Never mix `[Author, Year]` with IEEE numbered references.
8. **High Sentence Burstiness (Anti-Monotonous Bullets)**: Begin every technical subsection with a 4–6 sentence analytical paragraph. Never write more than 4 consecutive `- **Bold Keyword**: Description` bullet points; convert multi-attribute schemas into Markdown Data Dictionary tables.

---

## 3. Step-by-Step Execution Protocol

### Step 1: Regulation & Spec Alignment
Consult [`references/fit_hcmute_thesis_guideline.md`](./references/fit_hcmute_thesis_guideline.md) and verify that the manuscript aligns with `DIR-015` (Lean TLCN 5–10 competitions scope: `Crawl4AI` + `Cloudflare R2` + `Instructor/Pydantic v2` + `Parquet` + `DuckDB`).

### Step 2: Drafting Academic Prose
Draft sections conforming to the canonical structure in [`references/fit_hcmute_thesis_guideline.md`](./references/fit_hcmute_thesis_guideline.md) and sample style in [`examples/sample_chapter_section.md`](./examples/sample_chapter_section.md). Ensure every chapter concludes with `### Kết luận Chương X`.

### Step 3: Format & Anti-Slop Verification Gate
Always execute both deterministic linters before delivery:
```bash
python .agents/skills/thesis-writer/scripts/check_thesis_formatting.py --file docs/academic/BaoCao_TieuLuan_ChuyenNganh_KTDL.md
python .agents/skills/anti-slop-scientific-writer/scripts/detect_ai_slop.py docs/academic/BaoCao_TieuLuan_ChuyenNganh_KTDL.md --strict
```

---

## 4. Edge Cases & Gotchas Catalog

| Gotcha / Common Failure Mode | Root Cause | Enforced Solution |
| :--- | :--- | :--- |
| **Roman Numerals in Section Headings** | Using `I.1`, `III.1` in Mở đầu / Kết luận | `Mẫu 5` prohibits Roman numerals for chapter/section numbering. Use unnumbered descriptive headings from `Mẫu 4` in Mở đầu / Kết luận and Arabic `1.1`, `2.1` in Chapters. |
| **Missing Chapter Conclusions** | Ending chapters right after the last technical subsection | Add `### Kết luận Chương X` at the end of every chapter (`Noi dung_Hinh thuc.doc`). |
| **Use of Informal Pronouns** | Casual phrasing leaking from conversational prompts | Replace all instances of *"chúng tôi", "tôi", "mình"* with passive voice or *"Nhóm nghiên cứu"*. |
| **Dangling Figures / Tables** | Inserting a diagram or table without citing it in text | Precede or follow every figure/table with an explicit narrative reference (*"như được thể hiện tại Bảng X.Y..."*). |

---

## 5. Verification Checklist

- [ ] Execute `python .agents/skills/thesis-writer/scripts/check_thesis_formatting.py --file <manuscript.md>`.
- [ ] Execute `python .agents/skills/anti-slop-scientific-writer/scripts/detect_ai_slop.py <manuscript.md> --strict`.
- [ ] Confirm zero Roman numeral section prefixes (`I.1`, `II.1`, `III.1`) and zero informal pronouns exist.
- [ ] Confirm every chapter in `Phần 2: NỘI DUNG` ends with `### Kết luận Chương X`.
- [ ] Confirm all required frontmatter sections (`Mẫu 4`, `Mẫu 6`, Mục lục, Danh mục bảng biểu, Danh mục hình vẽ, Danh mục từ viết tắt, Tóm tắt) are present in full thesis reports.
