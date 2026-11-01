#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_thesis_formatting.py - Deterministic linter for academic manuscripts under FIT-HCMUTE standards.
Part of the thesis-writer skill in ACDP (grounded in 'Quy dinh bao cao/' Mẫu 0 - Mẫu 6 & Noi dung_Hinh thuc.doc).

Validates:
1. Zero informal first-person pronouns (tôi, mình, chúng em, tụi mình).
2. Figure / Table cross-referencing and duplicate ID prevention.
3. Chapter-prefix consistency for Figures and Tables (e.g., Bảng 3.x inside CHƯƠNG 3).
4. Heading hierarchy, duplicate section numbering, and zero Roman numeral section numbering (Mẫu 5 Line 78).
5. Mandatory Chapter Conclusions ('Kết luận Chương X') at the end of every Chapter (Noi dung_Hinh thuc.doc).
6. Full Report Frontmatter & Backmatter completeness (Mẫu 4, Mẫu 5, Mẫu 6) when checking a full report.
7. Control character / escaped string corruption (e.g. \t turning into TAB inside filenames).
8. IEEE Citation consistency ([1]..[N] in References vs in-text citations, zero unmapped [Author, Year]).
"""

import argparse
import re
import sys
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")


def check_formatting(file_path: Path) -> int:
    if not file_path.exists():
        print(f"[FAIL] Manuscript file not found: {file_path}")
        return 1

    content = file_path.read_text(encoding="utf-8")
    lines = content.splitlines()
    errors = []
    warnings = []

    # Check 1: Informal pronouns in Vietnamese (excluding code blocks)
    clean_content = re.sub(r"```[\s\S]*?```", "", content)
    informal_pronouns = [r"\btôi\b", r"\bmình\b", r"\bchúng em\b", r"\btụi mình\b"]
    for p in informal_pronouns:
        matches = list(re.finditer(p, clean_content, re.IGNORECASE))
        if matches:
            errors.append(
                f"Found {len(matches)} instance(s) of informal pronoun '{p}'. Use 'Nhóm nghiên cứu' or passive voice."
            )

    # Check 2 & 3: Figure / Table definitions, duplicates, chapter alignment, and cross-references
    defined_captions = []
    current_chapter = 0
    in_code_block = False
    in_toc_or_list_section = False

    for idx, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith("```"):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue

        # Detect if we are inside MỤC LỤC, DANH MỤC BẢNG BIỂU, DANH MỤC HÌNH VẼ
        if re.match(r"^#{1,3}\s+(?:MỤC LỤC|DANH MỤC)", stripped, re.IGNORECASE):
            in_toc_or_list_section = True
        elif re.match(r"^#{1,2}\s+(?:TÓM TẮT|ABSTRACT|Phần\s+\d+|CHƯƠNG\s+\d+)", stripped, re.IGNORECASE):
            in_toc_or_list_section = False

        # Track active chapter number (CHƯƠNG 1, CHƯƠNG 2, ...)
        chap_match = re.match(r"^#{1,3}\s+CHƯƠNG\s+(\d+)\b", stripped, re.IGNORECASE)
        if chap_match:
            current_chapter = int(chap_match.group(1))
        elif re.match(r"^#\s+Phần\s+3\b", stripped, re.IGNORECASE):
            current_chapter = 0

        # Detect formal Figure/Table caption lines (e.g., "###### Bảng 1.1:...")
        if not in_toc_or_list_section:
            cap_match = re.match(
                r"^(?:#{1,6}\s+|\*+)?(Hình|Bảng)\s+(\d+\.\d+)\s*:", stripped, re.IGNORECASE
            )
            if cap_match:
                kind = cap_match.group(1).capitalize()
                num = cap_match.group(2)
                defined_captions.append((kind, num, idx, current_chapter))

    seen_captions = {}
    for kind, num, line_no, chap in defined_captions:
        key = f"{kind} {num}"
        if key in seen_captions:
            errors.append(
                f"Duplicate {key} defined at line {line_no} (previously defined at line {seen_captions[key]})."
            )
        else:
            seen_captions[key] = line_no

        # Verify chapter prefix if inside CHƯƠNG 1..9 (allow 0.x in frontmatter before CHƯƠNG 1)
        major_prefix = int(num.split(".")[0])
        if chap > 0 and major_prefix != chap:
            errors.append(
                f"Line {line_no}: '{key}' is inside CHƯƠNG {chap} but uses prefix '{major_prefix}.x' (expected '{kind} {chap}.x')."
            )

        # Verify narrative cross-reference
        ref_pattern = rf"(?:trong|tại|theo|như|qua|ở)\s+{kind}\s+{re.escape(num)}\b"
        if not re.search(ref_pattern, clean_content, re.IGNORECASE):
            warnings.append(
                f"{key} (line {line_no}) is defined but not explicitly cross-referenced in narrative text."
            )

    # Check 4: Heading hierarchy, Duplicate numeric section prefixes, and Zero Roman numerals (Mẫu 5 Line 78)
    prev_level = 0
    seen_section_numbers = {}
    chapters_found = []
    chapter_conclusions_found = set()
    in_code_block = False

    for idx, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith("```"):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue

        if stripped.startswith("#"):
            hashes = stripped.split()[0]
            level = len(hashes)
            is_caption_heading = bool(
                re.match(r"^#{6}\s+(?:Hình|Bảng)\s+\d+\.\d+", stripped, re.IGNORECASE)
            )
            is_part_to_sec1 = prev_level == 1 and level == 3
            if not is_caption_heading:
                if level > prev_level + 1 and prev_level > 0 and not is_part_to_sec1:
                    warnings.append(
                        f"Line {idx}: Heading level skipped from #{prev_level} to #{level}."
                    )
                prev_level = level

            # Check prohibited Roman numeral chapter or section numbering (Mẫu 5 Line 78)
            roman_chap = re.match(r"^#{1,4}\s+Chương\s+[IVXLCDM]+\b", stripped, re.IGNORECASE)
            roman_sec = re.match(r"^#{1,5}\s+[IVXLCDM]+\.\d+", stripped)
            if roman_chap or roman_sec:
                errors.append(
                    f"Line {idx}: Prohibited Roman numeral heading '{stripped}' (Mẫu 5 Line 78 requires Arabic numerals only, no Roman numerals)."
                )

            # Track chapters and chapter conclusions (Noi dung_Hinh thuc.doc)
            c_match = re.match(r"^##\s+Chương\s+(\d+)\b", stripped, re.IGNORECASE)
            if c_match:
                chapters_found.append(int(c_match.group(1)))

            concl_match = re.match(
                r"^#{3,4}\s+(?:\d+\.\d+\.?\s+)?Kết\s+luận\s+Chương\s+(\d+)\b",
                stripped,
                re.IGNORECASE,
            )
            if concl_match:
                chapter_conclusions_found.add(int(concl_match.group(1)))

            # Check duplicate decimal section numbers like "### 1.1." or "## 1.1."
            sec_match = re.match(r"^#{2,4}\s+(\d+\.\d+(?:\.\d+)?)\.?\s+", stripped)
            if sec_match:
                sec_num = sec_match.group(1)
                if sec_num in seen_section_numbers:
                    errors.append(
                        f"Line {idx}: Duplicate section number '{sec_num}' (already used at line {seen_section_numbers[sec_num]})."
                    )
                else:
                    seen_section_numbers[sec_num] = idx

    # Check 5: Mandatory Chapter Conclusions for multi-chapter reports (Noi dung_Hinh thuc.doc)
    if chapters_found:
        for ch_num in chapters_found:
            if ch_num not in chapter_conclusions_found:
                errors.append(
                    f"Missing mandatory chapter conclusion ('### Kết luận Chương {ch_num}') at the end of Chương {ch_num} (required by Noi dung_Hinh thuc.doc)."
                )

    # Check 6: Full Report Frontmatter & Backmatter completeness (Mẫu 5 & Noi dung_Hinh thuc.doc)
    if len(chapters_found) >= 3:
        required_sections = [
            (r"PHIẾU NHẬN XÉT CỦA GIÁO VIÊN HƯỚNG DẪN", "Phiếu nhận xét của GVHD (Mẫu 6)"),
            (r"PHIẾU NHẬN XÉT CỦA GIÁO VIÊN PHẢN BIỆN", "Phiếu nhận xét của GVPB (Mẫu 6)"),
            (r"^##\s+LỜI CẢM ƠN", "Lời cảm ơn (Mẫu 5)"),
            (r"^##\s+ĐỀ CƯƠNG", "Đề cương chi tiết (Mẫu 4)"),
            (r"^##\s+MỤC LỤC", "Mục lục (Mẫu 5)"),
            (r"^##\s+DANH MỤC BẢNG BIỂU", "Danh mục bảng biểu (Mẫu 5 / Noi dung_Hinh thuc.doc)"),
            (r"^##\s+DANH MỤC HÌNH VẼ", "Danh mục hình vẽ (Mẫu 5 / Noi dung_Hinh thuc.doc)"),
            (r"^##\s+DANH MỤC TỪ VIẾT TẮT", "Danh mục từ viết tắt (Mẫu 5)"),
            (r"^##\s+TÓM TẮT", "Tóm tắt báo cáo (Mẫu 5)"),
            (r"^#\s+Phần 1:\s+MỞ ĐẦU", "Phần 1: MỞ ĐẦU (Mẫu 5)"),
            (r"^#\s+Phần 2:\s+NỘI DUNG", "Phần 2: NỘI DUNG (Mẫu 5)"),
            (r"^#\s+Phần 3:\s+KẾT LUẬN", "Phần 3: KẾT LUẬN (Mẫu 5)"),
            (r"^#\s+TÀI LIỆU THAM KHẢO", "Danh mục tài liệu tham khảo (Mẫu 5)"),
            (r"^#\s+PHỤ LỤC", "Phụ lục (Mẫu 5)"),
        ]
        for pattern, label in required_sections:
            if not re.search(pattern, content, re.MULTILINE | re.IGNORECASE):
                errors.append(f"Full report is missing mandatory section: {label}.")

    # Check 7: Control characters / Tab corruption inside prose or tables
    for idx, line in enumerate(lines, 1):
        if "\t" in line:
            errors.append(
                f"Line {idx}: Literal TAB character ('\\t') detected (often caused by unescaped '\\test_'). Replace with spaces or proper text."
            )

    # Check 8: Unmapped Author-Year citations vs IEEE numeric citations
    author_year_matches = list(
        re.finditer(r"\[[A-Z][a-zA-Z\s&-]+(?:et al\.,?)?\s*,\s*\d{4}\]", clean_content)
    )
    if author_year_matches:
        sample = author_year_matches[0].group(0)
        errors.append(
            f"Found {len(author_year_matches)} unstandardized APA/Author-Year bracket citation(s) (e.g., '{sample}'). Standardize to IEEE numeric citations [1], [2]."
        )

    # Verify all Bibliography items [1]..[N] are cited in body text
    ref_section_match = re.search(r"^#{1,2}\s+(?:\d+\.\s+)?TÀI LIỆU THAM KHẢO", content, re.MULTILINE)
    if ref_section_match:
        body_text = content[: ref_section_match.start()]
        ref_text = content[ref_section_match.start() :]
        bib_ids = re.findall(r"^\[(\d+)\]", ref_text, re.MULTILINE)
        for bid in bib_ids:
            if not re.search(rf"\[{bid}\]", body_text):
                warnings.append(
                    f"Bibliography entry [{bid}] is listed in TÀI LIỆU THAM KHẢO but never cited in the manuscript body."
                )

    # Report output
    print(f"=== FIT-HCMUTE Thesis Manuscript Report: {file_path.name} ===")
    if errors:
        print(f"[FAIL] Found {len(errors)} stylistic/structural error(s):")
        for e in errors:
            print(f"  - ERROR: {e}")
    else:
        print("[PASS] Zero informal pronouns, zero Roman numeral conflicts, mandatory chapter conclusions verified, and clean IEEE citations.")

    if warnings:
        print(f"[WARN] Found {len(warnings)} warning(s):")
        for w in warnings:
            print(f"  - WARNING: {w}")

    return 1 if errors else 0


def main():
    parser = argparse.ArgumentParser(description="Lint FIT-HCMUTE Thesis Manuscript")
    parser.add_argument("--file", required=True, help="Path to markdown manuscript file")
    args = parser.parse_args()

    sys.exit(check_formatting(Path(args.file)))


if __name__ == "__main__":
    main()
