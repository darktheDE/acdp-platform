#!/usr/bin/env python3
"""
validate_ui_component.py - Automated deterministic validator for Next.js 15 & React 19 UI components.
Part of the frontend-designer skill in ACDP.
"""

import argparse
import re
import sys
from pathlib import Path


def validate_component(file_path: Path) -> int:
    if not file_path.exists():
        print(f"[FAIL] File not found: {file_path}")
        return 1

    content = file_path.read_text(encoding="utf-8")
    errors = []
    warnings = []

    # Check 1: React hook usage without 'use client'
    hook_patterns = [r"\buseState\b", r"\buseEffect\b", r"\buseRef\b", r"\buseMemo\b", r"\buseCallback\b", r"\buseRouter\b"]
    uses_hooks = any(re.search(p, content) for p in hook_patterns)
    has_use_client = content.strip().startswith("'use client'") or content.strip().startswith('"use client"')

    if uses_hooks and not has_use_client:
        errors.append("File uses React client hooks (useState/useEffect/etc.) but is missing the 'use client' directive at line 1.")

    # Check 2: Deprecated Tailwind v3 configuration references
    if "tailwind.config.js" in content:
        warnings.append("Reference to 'tailwind.config.js' detected. ACDP uses Tailwind CSS v4 CSS-first configuration.")

    # Check 3: Basic Accessibility - Images missing alt attribute
    img_tags = re.findall(r"<img\b[^>]*>", content)
    for img in img_tags:
        if "alt=" not in img:
            errors.append(f"Image tag missing 'alt' attribute for accessibility: {img[:60]}...")

    # Check 4: Button elements missing aria-label or accessible text
    button_tags = re.findall(r"<button\b[^>]*>(.*?)</button>", content, re.DOTALL)
    for btn in button_tags:
        if not btn.strip() and "aria-label" not in btn:
            warnings.append("Button element may be empty without an 'aria-label' or accessible inner text.")

    # Output results
    print(f"=== UI Component Validation Report: {file_path.name} ===")
    if errors:
        print(f"[FAIL] Found {len(errors)} critical error(s):")
        for e in errors:
            print(f"  - ERROR: {e}")
    else:
        print("[PASS] Zero critical structural errors detected.")

    if warnings:
        print(f"[WARN] Found {len(warnings)} warning(s):")
        for w in warnings:
            print(f"  - WARNING: {w}")

    return 1 if errors else 0


def main():
    parser = argparse.ArgumentParser(description="Validate Next.js 15 UI Component")
    parser.add_argument("--file", required=True, help="Path to .tsx or .html file")
    args = parser.parse_args()

    sys.exit(validate_component(Path(args.file)))


if __name__ == "__main__":
    main()
