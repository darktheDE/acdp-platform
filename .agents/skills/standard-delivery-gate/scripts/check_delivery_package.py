#!/usr/bin/env python3
"""Deterministic 7-Pillar Standard Delivery Package Gate (DIR-024).

Validates that a completed ACDP task satisfies all 7 pillars of DIR-024:
1. Primary Markdown deliverable exists and is registered in docs/tasks/tasks-data.json.
2. Quantitative benchmark / measured evidence table is present.
3. Companion Single-File Interactive HTML Visual Dossier exists with Tailwind, Mermaid, and Chart.js.
4. Search Provenance / External References section contains search queries and https:// URLs.
5. Associated automated pytest suite (tests/test_*.py) exists on disk.
6. Manual Test / Advisor Demo Runbook section includes runnable CLI commands and captured outputs.
7. Zero forbidden placeholder tokens (TBD, insert output here, TODO: fill).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

FORBIDDEN_PLACEHOLDERS = (
    "insert output here",
    "todo: fill",
    "to be determined",
    "[placeholder]",
)

BENCHMARK_HEADING_RE = re.compile(
    r"^#{1,4}\s+.*(?:benchmark|metric|evidence|đo lường|đo đạc|chỉ số|kiểm chứng thực nghiệm).*$",
    re.IGNORECASE | re.MULTILINE,
)
PROVENANCE_HEADING_RE = re.compile(
    r"^#{1,4}\s+.*(?:search provenance|provenance|tham khảo|nhật ký truy vấn|references).*$",
    re.IGNORECASE | re.MULTILINE,
)
RUNBOOK_HEADING_RE = re.compile(
    r"^#{1,4}\s+.*(?:manual test|demo|runbook|hướng dẫn chạy|kiểm thử thủ công|triển khai).*$",
    re.IGNORECASE | re.MULTILINE,
)
TEST_PATH_RE = re.compile(r"tests/(?:api/)?test_[a-zA-Z0-9_]+\.py")
CLI_COMMAND_RE = re.compile(r"(?:uv run|pytest|python|docker|npm|npx)\s+[^\n]+")
FENCED_BLOCK_RE = re.compile(r"```[a-zA-Z0-9_-]*\n[\s\S]*?\n```")


def _extract_section(content: str, heading_pattern: re.Pattern[str]) -> str:
    """Return text from the matched heading until the next top-level (## ) heading."""
    match = heading_pattern.search(content)
    if not match:
        return ""
    start = match.start()
    next_h2 = re.search(r"\n##\s+", content[match.end() :])
    end = match.end() + next_h2.start() if next_h2 else len(content)
    return content[start:end]


def validate_delivery_package(
    repo_root: Path,
    task_id: str | None = None,
    deliverable_path: Path | None = None,
) -> tuple[bool, list[str], list[str]]:
    """Validate all 7 pillars of DIR-024 for a task or explicit deliverable markdown."""
    passed: list[str] = []
    errors: list[str] = []

    task_entry: dict | None = None
    deliverables: list[str] = []

    if task_id:
        tasks_json = repo_root / "docs" / "tasks" / "tasks-data.json"
        if not tasks_json.exists():
            return False, [], [f"Missing task registry JSON: {tasks_json}"]
        data = json.loads(tasks_json.read_text(encoding="utf-8"))
        for item in data.get("tasks", []):
            if item.get("id") == task_id:
                task_entry = item
                break
        if task_entry is None:
            return False, [], [f"Task ID '{task_id}' not found in docs/tasks/tasks-data.json"]
        deliverables = list(task_entry.get("deliverables", []))
        if deliverable_path is None:
            md_candidates = [
                p for p in deliverables if p.endswith(".md") and "deliverables/" in p.replace("\\", "/")
            ]
            if not md_candidates:
                errors.append(f"Pillar 1 FAIL: {task_id} has no primary .md deliverable in docs/deliverables/")
            else:
                deliverable_path = repo_root / md_candidates[0]

    if deliverable_path is None or not deliverable_path.exists():
        errors.append(f"Pillar 1 FAIL: Primary deliverable markdown not found: {deliverable_path}")
        return False, passed, errors

    content = deliverable_path.read_text(encoding="utf-8", errors="replace")
    passed.append(f"Pillar 1 PASS: Primary deliverable located ({deliverable_path.name})")

    # Pillar 2: Quantitative Benchmark / Evidence Table
    bench_section = _extract_section(content, BENCHMARK_HEADING_RE)
    has_table = bool(re.search(r"\|.*\|.*\n\|[\s:|-]+\|", bench_section or content))
    has_numbers = bool(re.search(r"\b\d+(?:\.\d+)?\s*(?:ms|s|MB|GB|%|cases|tests|links|URLs|USD)?\b", bench_section))
    if bench_section and has_table and has_numbers:
        passed.append("Pillar 2 PASS: Quantitative benchmark table detected")
    else:
        errors.append("Pillar 2 FAIL: Missing dedicated Benchmark/Metrics section with quantitative markdown table")

    # Pillar 3: Companion Visual Dossier HTML
    html_candidates: list[Path] = []
    if deliverables:
        html_candidates.extend(repo_root / p for p in deliverables if p.endswith(".html"))
    expected_html = deliverable_path.with_name(f"{deliverable_path.stem}-visual-dossier.html")
    if expected_html not in html_candidates:
        html_candidates.append(expected_html)
    html_path = next((p for p in html_candidates if p.exists()), None)
    if html_path is None:
        errors.append(f"Pillar 3 FAIL: Companion visual dossier HTML not found (expected {expected_html.name})")
    else:
        html_text = html_path.read_text(encoding="utf-8", errors="replace")
        missing_cdn = [
            name
            for name, token in (("Tailwind", "tailwind"), ("Mermaid", "mermaid"), ("Chart.js", "chart"))
            if token.lower() not in html_text.lower()
        ]
        if missing_cdn:
            errors.append(f"Pillar 3 FAIL: Visual dossier {html_path.name} missing {', '.join(missing_cdn)}")
        else:
            passed.append(f"Pillar 3 PASS: Visual dossier verified ({html_path.name})")

    # Pillar 4: Search Provenance & Verified External References
    prov_section = _extract_section(content, PROVENANCE_HEADING_RE)
    has_urls = len(re.findall(r"https?://[^\s)\]>]+", prov_section)) >= 1
    has_query_ref = bool(re.search(r"(?:search_web|truy vấn|query)", prov_section, re.IGNORECASE))
    if prov_section and has_urls and has_query_ref:
        passed.append("Pillar 4 PASS: Search provenance queries and external URLs present")
    else:
        errors.append(
            "Pillar 4 FAIL: Missing Search Provenance / References section with explicit search queries and https:// URLs"
        )

    # Pillar 5: Automated Test Suite on Disk
    test_candidates: list[Path] = []
    for p in deliverables:
        if p.replace("\\", "/").startswith("tests/") and p.endswith(".py"):
            test_candidates.append(repo_root / p)
    for match in TEST_PATH_RE.findall(content):
        candidate = repo_root / match
        if candidate not in test_candidates:
            test_candidates.append(candidate)
    existing_tests = [p for p in test_candidates if p.exists()]
    if existing_tests:
        passed.append(f"Pillar 5 PASS: Automated test suite found ({existing_tests[0].name})")
    else:
        errors.append("Pillar 5 FAIL: No existing tests/test_*.py suite linked in deliverable or tasks-data.json")

    # Pillar 6: Manual Test, CLI Deployment Runbook & Captured Outputs
    runbook_section = _extract_section(content, RUNBOOK_HEADING_RE)
    fenced_blocks = FENCED_BLOCK_RE.findall(runbook_section)
    has_cli = bool(CLI_COMMAND_RE.search(runbook_section))
    has_output_marker = bool(
        re.search(r"(?:output|kết quả|passed|clean|pass|exit code|status)", runbook_section, re.IGNORECASE)
    )
    if runbook_section and len(fenced_blocks) >= 2 and has_cli and has_output_marker:
        passed.append("Pillar 6 PASS: Manual test & advisor demo runbook with CLI commands and captured outputs present")
    else:
        errors.append(
            "Pillar 6 FAIL: Manual Test / Demo Runbook must include runnable CLI commands and captured real output blocks"
        )

    # Pillar 7: Zero Forbidden Placeholders
    lowered = content.lower()
    found_placeholders = [tok for tok in FORBIDDEN_PLACEHOLDERS if tok in lowered]
    tbd_matches = re.findall(r"\bTBD\b", content)
    if found_placeholders or tbd_matches:
        errors.append(
            f"Pillar 7 FAIL: Forbidden placeholder tokens found ({found_placeholders or tbd_matches})"
        )
    else:
        passed.append("Pillar 7 PASS: Zero forbidden placeholders detected")

    return len(errors) == 0, passed, errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate DIR-024 7-Pillar Standard Delivery Package")
    parser.add_argument("--task-id", type=str, help="Task ID in docs/tasks/tasks-data.json (e.g. TASK-QA-01)")
    parser.add_argument("--deliverable", type=Path, help="Optional explicit path to primary .md deliverable")
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[4],
        help="Repository root directory",
    )
    args = parser.parse_args()

    if not args.task_id and not args.deliverable:
        parser.error("Provide --task-id or --deliverable")

    ok, passed, errors = validate_delivery_package(
        repo_root=args.repo_root.resolve(),
        task_id=args.task_id,
        deliverable_path=args.deliverable.resolve() if args.deliverable else None,
    )

    print("=" * 72)
    print(f"DIR-024 STANDARD DELIVERY GATE ({args.task_id or args.deliverable})")
    print("=" * 72)
    for line in passed:
        print(f"[PASS] {line}")
    for err in errors:
        print(f"[FAIL] {err}")
    print("-" * 72)
    print(f"Summary: {len(passed)} passed, {len(errors)} failed. Status: {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
