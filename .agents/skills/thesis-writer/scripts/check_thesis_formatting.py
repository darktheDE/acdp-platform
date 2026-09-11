#!/usr/bin/env python3
"""
check_thesis_formatting.py - Deterministic linter for academic manuscripts under FIT-HCMUTE standards.
Part of the thesis-writer skill in ACDP.
"""

import argparse
import re
import sys
from pathlib import Path


def check_formatting(file_path: Path) -> int:
    if not file_path.exists():
        print(f"[FAIL] Manuscript file not found: {file_path}")
        return 1

    content = file_path.read_text(encoding="utf-8")
    errors = []
    warnings = []

    # Check 1: Informal pronouns in Vietnamese
    informal_pronouns = [r"\btôi\b", r"\bmình\b", r"\bchúng em\b", r"\btụi mình\b"]
    for p in informal_pronouns:
        matches = list(re.finditer(p, content, re.IGNORECASE))
        if matches:
            errors.append(f"Found {len(matches)} instance(s) of informal pronoun '{p}'. Use 'Nhóm nghiên cứu' or passive voice.")

    # Check 2: Figure / Table cross-references
    # Detect figures like "Hình 1.1", "Bảng 2.1"
    figures = set(re.findall(r"(?:Hình|Bảng)\s+([0-9]+\.[0-9]+)", content))
    for fig in figures:
        # Check if cited in the text (e.g. "trong Hình X.Y" or "tại Bảng X.Y")
        pattern = rf"(?:trong|tại|theo|như)\s+(?:Hình|Bảng)\s+{re.escape(fig)}"
        if not re.search(pattern, content, re.IGNORECASE):
            warnings.append(f"Figure/Table '{fig}' defined but may not be explicitly referenced in narrative text.")

    # Check 3: Heading hierarchy (no skipping levels like # straight to ###)
    lines = content.splitlines()
    prev_level = 0
    for idx, line in enumerate(lines, 1):
        if line.startswith("#"):
            level = len(line.split()[0])
            if level > prev_level + 1 and prev_level > 0:
                warnings.append(f"Line {idx}: Heading level skipped from #{prev_level} to #{level}.")
            prev_level = level

    # Report
    print(f"=== FIT-HCMUTE Thesis Manuscript Report: {file_path.name} ===")
    if errors:
        print(f"[FAIL] Found {len(errors)} stylistic error(s):")
        for e in errors:
            print(f"  - ERROR: {e}")
    else:
        print("[PASS] Zero informal pronouns detected. Academic tone is preserved.")

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
