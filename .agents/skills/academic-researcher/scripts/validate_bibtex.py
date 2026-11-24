#!/usr/bin/env python3
"""
validate_bibtex.py - Deterministic BibTeX syntax and completeness validator.
Part of the academic-researcher skill in ACDP.
"""

import argparse
import re
import sys
from pathlib import Path


def validate_bibtex(file_path: Path) -> int:
    if not file_path.exists():
        print(f"[FAIL] BibTeX file not found: {file_path}")
        return 1

    content = file_path.read_text(encoding="utf-8")
    errors = []
    warnings = []

    # Find all entries: @type{key, ...}
    entries = re.findall(r"@([a-zA-Z]+)\s*\{\s*([^,]+),", content)
    if not entries:
        errors.append("No valid BibTeX entries found in file.")
        print(f"[FAIL] {errors[0]}")
        return 1

    keys_seen = set()
    for entry_type, key in entries:
        key = key.strip()
        if key in keys_seen:
            errors.append(f"Duplicate citation key detected: '{key}'")
        keys_seen.add(key)

        # Check key convention: author + year + keyword
        if not re.match(r"^[a-zA-Z]+[0-9]{4}[a-zA-Z0-9_\-]+$", key):
            warnings.append(f"Citation key '{key}' does not follow '[author][YYYY][keyword]' convention.")

    # Split into individual entry blocks
    raw_blocks = re.split(r"(?=@(?:article|inproceedings|book|misc|techreport)\s*\{)", content)
    for block in raw_blocks:
        block = block.strip()
        if not block.startswith("@"):
            continue

        match = re.match(r"@([a-zA-Z]+)\s*\{\s*([^,]+),", block)
        if not match:
            continue

        entry_type = match.group(1).lower()
        key = match.group(2).strip()

        # Check required fields
        required_fields = ["author", "title", "year"]
        if entry_type == "article":
            required_fields.append("journal")
        elif entry_type == "inproceedings":
            required_fields.append("booktitle")

        for field in required_fields:
            pattern = rf"\b{field}\s*=\s*[\"\{{]"
            if not re.search(pattern, block, re.IGNORECASE):
                errors.append(f"Entry '{key}' (@{entry_type}) missing required field '{field}'.")

        # Check for unescaped special characters
        if re.search(r"[^\\]&", block):
            warnings.append(f"Entry '{key}' contains unescaped '&'. Use '\\&'.")

    # Report results
    print(f"=== BibTeX Validation Report: {file_path.name} ({len(entries)} entries) ===")
    if errors:
        print(f"[FAIL] Found {len(errors)} error(s):")
        for e in errors:
            print(f"  - ERROR: {e}")
    else:
        print(f"[PASS] All {len(entries)} BibTeX entries are syntactically valid.")

    if warnings:
        print(f"[WARN] Found {len(warnings)} warning(s):")
        for w in warnings:
            print(f"  - WARNING: {w}")

    return 1 if errors else 0


def main():
    parser = argparse.ArgumentParser(description="Validate BibTeX Library")
    parser.add_argument("--file", required=True, help="Path to .bib file")
    args = parser.parse_args()

    sys.exit(validate_bibtex(Path(args.file)))


if __name__ == "__main__":
    main()
