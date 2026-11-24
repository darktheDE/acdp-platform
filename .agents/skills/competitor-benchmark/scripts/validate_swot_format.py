#!/usr/bin/env python3
"""
validate_swot_format.py - Deterministic format validator for competitor benchmarks and SWOT matrices.
Part of the competitor-benchmark skill in ACDP.
"""

import argparse
import re
import sys
from pathlib import Path


def validate_benchmark(file_path: Path) -> int:
    if not file_path.exists():
        print(f"[FAIL] File not found: {file_path}")
        return 1

    content = file_path.read_text(encoding="utf-8")
    errors = []
    warnings = []

    # Check 1: 5-Dimensional Matrix Dimensions
    required_dimensions = [
        "Data Ingestion",
        "Rulebook",
        "Team",
        "Faculty",
        "Analytics",
    ]
    for dim in required_dimensions:
        if not re.search(rf"\b{dim}\b", content, re.IGNORECASE):
            errors.append(f"Missing core comparison dimension: '{dim}'")

    # Check 2: Key Competitor Names
    required_competitors = ["Devpost", "Unstop"]
    for comp in required_competitors:
        if comp not in content:
            warnings.append(f"Primary competitor '{comp}' is not explicitly evaluated in text.")

    # Check 3: SWOT Quadrants
    swot_quadrants = ["Strengths", "Weaknesses", "Opportunities", "Threats"]
    for quad in swot_quadrants:
        if not re.search(rf"###?\s*{quad}", content, re.IGNORECASE):
            errors.append(f"Missing SWOT quadrant: '{quad}'")

    # Check 4: Bullet point quality (no empty or 1-word bullets)
    bullets = re.findall(r"^-\s+(.+)$", content, re.MULTILINE)
    for b in bullets:
        if len(b.strip().split()) < 3:
            warnings.append(f"Potentially vague bullet point detected: '{b}'")

    # Report
    print(f"=== Competitor Benchmark Report: {file_path.name} ===")
    if errors:
        print(f"[FAIL] Found {len(errors)} structural error(s):")
        for e in errors:
            print(f"  - ERROR: {e}")
    else:
        print("[PASS] Benchmark document satisfies all structural and SWOT requirements.")

    if warnings:
        print(f"[WARN] Found {len(warnings)} warning(s):")
        for w in warnings:
            print(f"  - WARNING: {w}")

    return 1 if errors else 0


def main():
    parser = argparse.ArgumentParser(description="Validate Competitor Benchmark Document")
    parser.add_argument("--file", required=True, help="Path to benchmark markdown file")
    args = parser.parse_args()

    sys.exit(validate_benchmark(Path(args.file)))


if __name__ == "__main__":
    main()
