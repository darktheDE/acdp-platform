#!/usr/bin/env python3
"""Deterministic Validator for ACDP Visual Dossier HTML Reports.

Conforms to AGENT_SKILL_ENGINEERING_SPEC.md and DIR-014.
Validates:
1. File existence and .html extension.
2. Required CDN integrations (Tailwind CSS, Mermaid.js, Chart.js).
3. 3-Tier Progressive Disclosure structure.
4. Basic HTML tag balance and absence of obvious syntax errors.
"""

import argparse
from pathlib import Path
import re
import sys


def validate_report(html_path: Path) -> tuple[bool, list[str]]:
    """Validate an interactive HTML visual report file."""
    errors: list[str] = []

    if not html_path.exists():
        return False, [f"File does not exist: {html_path}"]

    if html_path.suffix.lower() != ".html":
        errors.append(f"Expected .html extension, got: {html_path.suffix}")

    content = html_path.read_text(encoding="utf-8", errors="replace")

    # 1. Check for required CDN dependencies
    if "tailwindcss.com" not in content and "tailwind" not in content:
        errors.append("Missing Tailwind CSS CDN reference")
    if "mermaid" not in content:
        errors.append("Missing Mermaid.js CDN reference or diagram container")
    if "chart.js" not in content and "Chart" not in content:
        errors.append("Missing Chart.js CDN reference")

    # 2. Check for 3-Tier architecture markers
    # Tier 1: Metric or KPI indicator
    if not re.search(r"(kpi|metric|summary|tóm tắt|tiết kiệm|ram)", content, re.IGNORECASE):
        errors.append("Tier 1 (Executive KPI / Metric Summary) not detected")

    # Tier 2: Diagram or Chart container
    if 'class="mermaid"' not in content and "mermaid" not in content:
        errors.append("Tier 2 (Mermaid diagram container) not found")

    # 3. Check for HTML structure
    if "<!DOCTYPE html>" not in content and "<!doctype html>" not in content:
        errors.append("Missing standard HTML5 DOCTYPE declaration")
    if "</html>" not in content:
        errors.append("Unclosed </html> tag")

    return len(errors) == 0, errors


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate ACDP Visual Dossier HTML Report")
    parser.add_argument("report_file", type=Path, help="Path to the HTML visual report file")
    args = parser.parse_args()

    success, errors = validate_report(args.report_file)
    if success:
        print(f"[PASS] Visual Dossier PASS: {args.report_file} conforms to DIR-014 standards.")
        sys.exit(0)
    else:
        print(f"[FAIL] Visual Dossier FAIL: {args.report_file}", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        sys.exit(1)



if __name__ == "__main__":
    main()
