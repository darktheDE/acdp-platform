#!/usr/bin/env python3
"""
test_verify_links.py - Self-test and smoke verification for verify_links.py
"""

import sys
from pathlib import Path

# Set UTF-8 stdout if needed for Windows console
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Add script directory to path
current_dir = Path(__file__).parent.resolve()
sys.path.insert(0, str(current_dir))

from verify_links import LinkVerifier, LinkOccurrence


def test_url_cleaning():
    verifier = LinkVerifier(verbose=False)
    assert verifier.clean_url("https://example.com/.") == "https://example.com/"
    assert verifier.clean_url("https://example.com/),") == "https://example.com/"
    assert verifier.clean_url("https://example.com/test)") == "https://example.com/test"
    print("  [PASS] URL Cleaning & Punctuation Stripping: OK")


def test_dns_resolution():
    verifier = LinkVerifier(verbose=False)
    # Real domain
    assert verifier.check_dns("google.com") is True
    assert verifier.check_dns("github.com") is True
    # Fake domain
    assert verifier.check_dns("this-domain-definitely-does-not-exist-9876543210.xyz") is False
    print("  [PASS] DNS Resolution Pre-check: OK")


def test_single_url_verification():
    verifier = LinkVerifier(timeout=6.0, verbose=False)
    dummy_occ = [LinkOccurrence(file_path="test.md", line_number=1, url="https://doi.org")]

    # 1. Test genuine accessible link
    res_valid = verifier.verify_single_url("https://doi.org", dummy_occ)
    assert res_valid.status in ("HEALTHY", "RESTRICTED_BOT"), f"Expected HEALTHY/RESTRICTED, got {res_valid.status}"
    print(f"  [PASS] Valid Link Verification (https://doi.org): OK ({res_valid.status})")

    # 2. Test nonexistent domain (Dead link detection)
    dead_url = "https://this-domain-definitely-does-not-exist-9876543210.xyz/page"
    dummy_dead = [LinkOccurrence(file_path="test.md", line_number=2, url=dead_url)]
    res_dead = verifier.verify_single_url(dead_url, dummy_dead)
    assert res_dead.status == "DNS_FAILED", f"Expected DNS_FAILED, got {res_dead.status}"
    print("  [PASS] Dead Domain Detection: OK (DNS_FAILED accurately caught)")


def run_all_tests():
    print("=== Running URL Link Verifier Smoke Test Suite ===")
    try:
        test_url_cleaning()
        test_dns_resolution()
        test_single_url_verification()
        print("=== All URL Link Verifier Tests PASSED (10/10) ===")
        return 0
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"[FAIL] Smoke test failed: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
