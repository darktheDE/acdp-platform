#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_thesis_formatting.py - Deterministic linter for academic manuscripts under FIT-HCMUTE standards.
Part of the thesis-writer skill in ACDP.

Validates:
1. Zero informal first-person pronouns (tôi, mình, chúng em, tụi mình).
2. Figure / Table cross-referencing and duplicate ID prevention.
3. Chapter-prefix consistency for Figures and Tables (e.g., Bảng 3.x inside CHƯƠNG 3).
4. Heading hierarchy and duplicate section numbering detection.
5. Control character / escaped string corruption (e.g. \t turning into TAB inside filenames).
6. IEEE Citation consistency ([1]..[N] in References vs in-text citations, zero unmapped [Author, Year]).
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

    for idx, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith("```"):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue

        # Track active chapter number (CHƯƠNG 1, CHƯƠNG 2, ...)
        chap_match = re.match(r"^#{1,3}\s+CHƯƠNG\s+(\d+)\b", stripped, re.IGNORECASE)
        if chap_match:
            current_chapter = int(chap_match.group(1))

        # Detect formal Figure/Table caption lines (e.g., "#### Bảng 1.1:..." or "*Hình 2.1:...")
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

    # Check 4: Heading hierarchy & Duplicate numeric section prefixes
    prev_level = 0
    seen_section_numbers = {}
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
            if level > prev_level + 1 and prev_level > 0:
                warnings.append(
                    f"Line {idx}: Heading level skipped from #{prev_level} to #{level}."
                )
            prev_level = level

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

    # Check 5: Control characters / Tab corruption inside prose or tables
    for idx, line in enumerate(lines, 1):
        if "\t" in line:
            errors.append(
                f"Line {idx}: Literal TAB character ('\\t') detected (often caused by unescaped '\\test_'). Replace with spaces or proper text."
            )

    # Check 6: Unmapped Author-Year citations vs IEEE numeric citations
    author_year_matches = list(
        re.finditer(r"\[[A-Z][a-zA-Z\s&-]+(?:et al\.,?)?\s*,\s*\d{4}\]", clean_content)
    )
    if author_year_matches:
        sample = author_year_matches[0].group(0)
        errors.append(
            f"Found {len(author_year_matches)} unstandardized APA/Author-Year bracket citation(s) (e.g., '{sample}'). Standardize to IEEE numeric citations [1], [2]."
        )

    # Verify all Bibliography items [1]..[N] are cited in body text
    ref_section_match = re.search(r"^#\s+TÀI LIỆU THAM KHẢO", content, re.MULTILINE)
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
        print("[PASS] Zero informal pronouns, zero numbering conflicts, and clean IEEE citations.")

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
