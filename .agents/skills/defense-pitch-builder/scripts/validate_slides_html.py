#!/usr/bin/env python3
"""
validate_slides_html.py - Deterministic HTML slide deck structure and offline readiness validator.
Part of the defense-pitch-builder skill in ACDP.
"""

import argparse
import re
import sys
from pathlib import Path


def validate_slides(file_path: Path) -> int:
    if not file_path.exists():
        print(f"[FAIL] File not found: {file_path}")
        return 1

    content = file_path.read_text(encoding="utf-8")
    errors = []
    warnings = []

    # Check 1: Slide containers
    slides = re.findall(r'<div\b[^>]*class=["\'][^"\']*\bslide\b[^"\']*["\']', content, re.IGNORECASE)
    if not slides:
        # Check alternative Marp or section tags
        slides = re.findall(r'<section\b', content, re.IGNORECASE)

    if not slides:
        errors.append("No slide elements (<div class='slide'> or <section>) detected in HTML deck.")
    else:
        print(f"[INFO] Detected {len(slides)} presentation slides.")

    # Check 2: Keyboard navigation script
    if "ArrowRight" not in content and "keydown" not in content:
        errors.append("Missing keyboard navigation listener ('ArrowRight' / 'keydown') for slide navigation.")

    # Check 3: External CDN dependencies (offline reliability check)
    external_links = re.findall(r'(?:src|href)=["\']https?://[^"\']+["\']', content)
    cdn_links = [l for l in external_links if "cdn" in l.lower() or "unpkg" in l.lower() or "cdnjs" in l.lower()]
    if cdn_links:
        warnings.append(f"External CDN dependencies found ({len(cdn_links)}). For offline defense safety, embed styles directly.")

    # Check 4: Slide count constraint (academic defense is typically 8-15 slides)
    if len(slides) > 20:
        warnings.append(f"Slide count ({len(slides)}) may exceed the standard 12-minute defense time budget.")

    # Report
    print(f"=== HTML Slide Deck Report: {file_path.name} ===")
    if errors:
        print(f"[FAIL] Found {len(errors)} critical error(s):")
        for e in errors:
            print(f"  - ERROR: {e}")
    else:
        print("[PASS] Slide deck structure and navigation scripts are valid.")

    if warnings:
        print(f"[WARN] Found {len(warnings)} warning(s):")
        for w in warnings:
            print(f"  - WARNING: {w}")

    return 1 if errors else 0


def main():
    parser = argparse.ArgumentParser(description="Validate HTML Slide Deck")
    parser.add_argument("--file", required=True, help="Path to presentation HTML file")
    args = parser.parse_args()

    sys.exit(validate_slides(Path(args.file)))


if __name__ == "__main__":
    main()
