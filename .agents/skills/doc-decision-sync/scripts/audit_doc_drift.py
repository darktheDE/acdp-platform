#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
audit_doc_drift.py - Deterministic Decision Sync, Drift & Internal Link Linter
Part of 'doc-decision-sync' skill (DIR-017).

Performs five deterministic governance checks across the ACDP repository:
1. DIRECTIVE-SYNC: Verifies TEAM_DIRECTIVES.md directives are accounted for and synced in AGENTS.md & GEMINI.md.
2. SKILL-REGISTRY-PARITY: Verifies every .agents/skills/<name>/SKILL.md is registered in all harness contracts.
3. CANONICAL-FACT-DRIFT: Scans docs against decision_rules.json for stale paths, versions, or contradictions.
4. INTERNAL-LINK-INTEGRITY: Verifies relative Markdown links resolve to existing files or directories on disk.
5. --impact <query>: Maps the 4-tier blast radius for any directive, keyword, or path across repository docs.
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
from urllib.parse import unquote

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

DEFAULT_RULES_PATH = Path(__file__).resolve().parent.parent / "references" / "decision_rules.json"

LINK_PATTERN = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
DIRECTIVE_ID_PATTERN = re.compile(r"\bDIR-(\d{3})\b")
SCHEME_PATTERN = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*:")
INLINE_CODE_PATTERN = re.compile(r"`[^`]*`")


@dataclass
class AuditFinding:
    check_id: str
    rule_id: str
    file_path: str
    line_number: int
    message: str


@dataclass
class ImpactHit:
    tier: str
    file_path: str
    line_number: int
    excerpt: str


def load_rules(rules_path: Path | None = None) -> dict[str, Any]:
    target = rules_path or DEFAULT_RULES_PATH
    with target.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def _expand_globs(root: Path, patterns: list[str]) -> list[Path]:
    matched: list[Path] = []
    seen: set[Path] = set()
    for pattern in patterns:
        raw_pattern = str(root / pattern)
        for hit in glob.glob(raw_pattern, recursive=True):
            p = Path(hit)
            if p.is_file() and p not in seen:
                seen.add(p)
                matched.append(p)
    return sorted(matched)


def _strip_code_from_lines(text: str) -> list[tuple[int, str]]:
    """Return (line_number, line_without_code) skipping fenced code blocks and inline code."""
    results: list[tuple[int, str]] = []
    in_fence = False
    fence_marker = ""
    for line_no, raw_line in enumerate(text.splitlines(), start=1):
        stripped = raw_line.strip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            marker = stripped[:3]
            if not in_fence:
                in_fence = True
                fence_marker = marker
            elif marker == fence_marker:
                in_fence = False
                fence_marker = ""
            continue
        if in_fence:
            continue
        cleaned = INLINE_CODE_PATTERN.sub("", raw_line)
        results.append((line_no, cleaned))
    return results


def _rel_posix(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def check_directive_sync(root: Path, rules: dict[str, Any]) -> tuple[list[AuditFinding], dict[str, Any]]:
    findings: list[AuditFinding] = []
    directives_file = root / rules.get("directive_source", "docs/frameworks/TEAM_DIRECTIVES.md")
    required_universal = list(rules.get("required_directives_in_agent_contracts", []))
    scoped = set(rules.get("scoped_directives", []))
    contract_files = list(rules.get("agent_contract_files", ["AGENTS.md", "GEMINI.md"]))

    defined_dirs: list[str] = []
    if not directives_file.exists():
        findings.append(
            AuditFinding(
                check_id="DIRECTIVE-SYNC",
                rule_id="DIR-SOURCE-MISSING",
                file_path=_rel_posix(directives_file, root),
                line_number=0,
                message="Canonical directive ledger TEAM_DIRECTIVES.md is missing.",
            )
        )
        return findings, {"defined_count": 0, "universal_count": len(required_universal)}

    content = _read_text(directives_file)
    defined_set = {f"DIR-{m}" for m in DIRECTIVE_ID_PATTERN.findall(content)}
    defined_dirs = sorted(defined_set)
    accounted_set = set(required_universal) | scoped

    for dir_id in defined_dirs:
        if dir_id not in accounted_set:
            findings.append(
                AuditFinding(
                    check_id="DIRECTIVE-SYNC",
                    rule_id="DIR-UNACCOUNTED",
                    file_path=_rel_posix(directives_file, root),
                    line_number=0,
                    message=(
                        f"{dir_id} exists in TEAM_DIRECTIVES.md but is not registered in "
                        "decision_rules.json (required_directives_in_agent_contracts or scoped_directives)."
                    ),
                )
            )

    for contract_rel in contract_files:
        contract_path = root / contract_rel
        if not contract_path.exists():
            findings.append(
                AuditFinding(
                    check_id="DIRECTIVE-SYNC",
                    rule_id="CONTRACT-MISSING",
                    file_path=contract_rel,
                    line_number=0,
                    message=f"Required agent contract file '{contract_rel}' does not exist.",
                )
            )
            continue
        contract_text = _read_text(contract_path)
        for dir_id in required_universal:
            if dir_id not in contract_text:
                findings.append(
                    AuditFinding(
                        check_id="DIRECTIVE-SYNC",
                        rule_id="DIR-CONTRACT-MISSING",
                        file_path=contract_rel,
                        line_number=0,
                        message=f"Universal directive {dir_id} is missing from {contract_rel}.",
                    )
                )

    meta = {
        "defined_count": len(defined_dirs),
        "universal_count": len(required_universal),
        "contracts_checked": len(contract_files),
    }
    return findings, meta


def discover_skills(root: Path) -> list[str]:
    skills_dir = root / ".agents" / "skills"
    if not skills_dir.is_dir():
        return []
    skills: list[str] = []
    for entry in sorted(skills_dir.iterdir()):
        if entry.is_dir() and (entry / "SKILL.md").is_file():
            skills.append(entry.name)
    return skills


def check_skill_registry_parity(root: Path, rules: dict[str, Any]) -> tuple[list[AuditFinding], dict[str, Any]]:
    findings: list[AuditFinding] = []
    skills = discover_skills(root)
    targets = list(rules.get("skill_registry_targets", []))

    for target_rel in targets:
        target_path = root / target_rel
        if not target_path.exists():
            findings.append(
                AuditFinding(
                    check_id="SKILL-REGISTRY-PARITY",
                    rule_id="REGISTRY-TARGET-MISSING",
                    file_path=target_rel,
                    line_number=0,
                    message=f"Skill registry file '{target_rel}' does not exist.",
                )
            )
            continue
        text = _read_text(target_path)
        for skill_name in skills:
            if skill_name not in text:
                findings.append(
                    AuditFinding(
                        check_id="SKILL-REGISTRY-PARITY",
                        rule_id="SKILL-UNREGISTERED",
                        file_path=target_rel,
                        line_number=0,
                        message=f"Skill '{skill_name}' exists on disk but is missing from {target_rel}.",
                    )
                )

    banner_cfg = rules.get("skill_count_banner")
    if banner_cfg:
        banner_file = root / banner_cfg["file"]
        if banner_file.exists():
            banner_text = _read_text(banner_file)
            banner_re = re.compile(banner_cfg["pattern"])
            for line_no, line in enumerate(banner_text.splitlines(), start=1):
                match = banner_re.search(line)
                if match:
                    stated_count = int(match.group(1))
                    if stated_count != len(skills):
                        findings.append(
                            AuditFinding(
                                check_id="CANONICAL-FACT-DRIFT",
                                rule_id=banner_cfg.get("rule_id", "DRIFT-004"),
                                file_path=banner_cfg["file"],
                                line_number=line_no,
                                message=(
                                    f"Skill count drift: '{banner_cfg['file']}' states {stated_count} "
                                    f"skills, but {len(skills)} exist under .agents/skills/."
                                ),
                            )
                        )

    return findings, {"skills_on_disk": len(skills), "targets_checked": len(targets)}


def check_canonical_fact_drift(root: Path, rules: dict[str, Any]) -> tuple[list[AuditFinding], dict[str, Any]]:
    findings: list[AuditFinding] = []
    drift_rules = list(rules.get("drift_rules", []))
    scanned_files: set[Path] = set()

    for rule in drift_rules:
        rule_id = rule["id"]
        pattern = re.compile(rule["pattern"])
        excludes = list(rule.get("exclude_if_line_contains", []))
        target_files = _expand_globs(root, list(rule.get("targets", [])))
        for file_path in target_files:
            scanned_files.add(file_path)
            text = _read_text(file_path)
            for line_no, raw_line in enumerate(text.splitlines(), start=1):
                if any(ex in raw_line for ex in excludes):
                    continue
                if pattern.search(raw_line):
                    findings.append(
                        AuditFinding(
                            check_id="CANONICAL-FACT-DRIFT",
                            rule_id=rule_id,
                            file_path=_rel_posix(file_path, root),
                            line_number=line_no,
                            message=rule["message"],
                        )
                    )

    return findings, {"rules_evaluated": len(drift_rules), "files_scanned": len(scanned_files)}


def _extract_relative_link_target(raw_target: str) -> str | None:
    target = raw_target.strip()
    if target.startswith("<") and ">" in target:
        target = target[1 : target.index(">")].strip()
    else:
        # Strip optional markdown link title: path "title" or path 'title'
        title_match = re.match(r'^([^\s]+)\s+["\'].*["\']$', target)
        if title_match:
            target = title_match.group(1)

    if not target or target.startswith("#"):
        return None
    if SCHEME_PATTERN.match(target):
        return None

    target_no_fragment = target.split("#", 1)[0].split("?", 1)[0].strip()
    if not target_no_fragment:
        return None
    return unquote(target_no_fragment)


def check_internal_markdown_links(root: Path, rules: dict[str, Any]) -> tuple[list[AuditFinding], dict[str, Any]]:
    findings: list[AuditFinding] = []
    scan_globs = list(rules.get("internal_link_scan_paths", []))
    files = _expand_globs(root, scan_globs)
    links_checked = 0

    for md_file in files:
        text = _read_text(md_file)
        for line_no, cleaned_line in _strip_code_from_lines(text):
            for match in LINK_PATTERN.finditer(cleaned_line):
                rel_target = _extract_relative_link_target(match.group(1))
                if rel_target is None:
                    continue
                links_checked += 1
                if rel_target.startswith("/"):
                    resolved = (root / rel_target.lstrip("/")).resolve()
                else:
                    resolved = (md_file.parent / rel_target).resolve()
                if not resolved.exists():
                    findings.append(
                        AuditFinding(
                            check_id="INTERNAL-LINK-INTEGRITY",
                            rule_id="BROKEN-REL-LINK",
                            file_path=_rel_posix(md_file, root),
                            line_number=line_no,
                            message=f"Broken relative link '{rel_target}' (resolved target does not exist).",
                        )
                    )

    return findings, {"files_scanned": len(files), "links_checked": links_checked}


def _classify_tier(rel_path: str, tier_map: dict[str, list[str]]) -> str:
    for tier_name, prefixes in tier_map.items():
        for prefix in prefixes:
            if rel_path == prefix or rel_path.startswith(prefix):
                return tier_name
    return "Tier 3 (Skills & Academic Outputs)"


def compute_blast_radius(root: Path, query: str, rules: dict[str, Any]) -> list[ImpactHit]:
    hits: list[ImpactHit] = []
    tier_map = dict(rules.get("tier_classification", {}))
    patterns = [
        "AGENTS.md",
        "GEMINI.md",
        "CLAUDE.md",
        ".cursorrules",
        "README.md",
        "docs/**/*.md",
        ".agents/skills/**/*.md",
    ]
    files = _expand_globs(root, patterns)
    query_re = re.compile(re.escape(query), re.IGNORECASE)

    for path in files:
        rel_path = _rel_posix(path, root)
        tier = _classify_tier(rel_path, tier_map)
        text = _read_text(path)
        for line_no, line in enumerate(text.splitlines(), start=1):
            if query_re.search(line):
                excerpt = line.strip()
                if len(excerpt) > 100:
                    excerpt = excerpt[:97] + "..."
                hits.append(
                    ImpactHit(
                        tier=tier,
                        file_path=rel_path,
                        line_number=line_no,
                        excerpt=excerpt,
                    )
                )
    return hits


def run_full_audit(root: Path, rules_path: Path | None = None) -> dict[str, Any]:
    rules = load_rules(rules_path)
    dir_findings, dir_meta = check_directive_sync(root, rules)
    skill_findings, skill_meta = check_skill_registry_parity(root, rules)
    drift_findings, drift_meta = check_canonical_fact_drift(root, rules)
    link_findings, link_meta = check_internal_markdown_links(root, rules)

    all_findings = dir_findings + skill_findings + drift_findings + link_findings
    return {
        "root": str(root.resolve()),
        "clean": len(all_findings) == 0,
        "violation_count": len(all_findings),
        "meta": {
            "directive_sync": dir_meta,
            "skill_registry_parity": skill_meta,
            "canonical_fact_drift": drift_meta,
            "internal_link_integrity": link_meta,
        },
        "findings": [asdict(f) for f in all_findings],
    }


def _print_impact_report(query: str, hits: list[ImpactHit]) -> None:
    print("=" * 80)
    print(f"[IMPACT SCAN] Query: \"{query}\" | Matches: {len(hits)}")
    print("=" * 80)
    if not hits:
        print("No repository documentation references found.")
        return

    grouped: dict[str, list[ImpactHit]] = {}
    for hit in hits:
        grouped.setdefault(hit.tier, []).append(hit)

    for tier_name, tier_hits in grouped.items():
        print(f"\n{tier_name} ({len(tier_hits)} hit(s)):")
        for hit in tier_hits:
            print(f"  - {hit.file_path}:{hit.line_number} -> {hit.excerpt}")


def _print_audit_report(report: dict[str, Any]) -> None:
    print("=" * 80)
    print("ACDP DOCUMENTATION DRIFT & DECISION SYNC AUDIT")
    print("=" * 80)
    findings = report["findings"]
    meta = report["meta"]

    by_check: dict[str, list[dict[str, Any]]] = {}
    for item in findings:
        by_check.setdefault(item["check_id"], []).append(item)

    checks = [
        (
            "DIRECTIVE-SYNC",
            f"{meta['directive_sync']['defined_count']} directives accounted for across "
            f"{meta['directive_sync']['contracts_checked']} agent contracts",
        ),
        (
            "SKILL-REGISTRY-PARITY",
            f"{meta['skill_registry_parity']['skills_on_disk']} skills on disk verified against "
            f"{meta['skill_registry_parity']['targets_checked']} registry targets",
        ),
        (
            "CANONICAL-FACT-DRIFT",
            f"{meta['canonical_fact_drift']['rules_evaluated']} drift rules evaluated across "
            f"{meta['canonical_fact_drift']['files_scanned']} files",
        ),
        (
            "INTERNAL-LINK-INTEGRITY",
            f"{meta['internal_link_integrity']['links_checked']} relative links checked across "
            f"{meta['internal_link_integrity']['files_scanned']} Markdown files",
        ),
    ]

    for check_id, summary_text in checks:
        check_errors = by_check.get(check_id, [])
        if not check_errors:
            print(f"[PASS] {check_id}: {summary_text}")
        else:
            for err in check_errors:
                loc = f"{err['file_path']}:{err['line_number']}" if err["line_number"] else err["file_path"]
                print(f"[FAIL] {check_id} [{err['rule_id']}]: {loc} -> {err['message']}")

    print("-" * 80)
    status = "CLEAN" if report["clean"] else "DRIFT DETECTED"
    print(f"Summary: {report['violation_count']} violation(s) found. Status: {status}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Deterministic Decision Sync, Drift & Internal Link Linter for ACDP"
    )
    parser.add_argument("--root", default=".", help="Repository root directory (default: .)")
    parser.add_argument("--rules", default=None, help="Optional path to decision_rules.json")
    parser.add_argument("--strict", action="store_true", help="Exit code 1 when any drift or broken link is found")
    parser.add_argument("--json", action="store_true", help="Emit structured JSON report")
    parser.add_argument("--impact", default=None, help="Scan 4-tier blast radius for a directive, version, or path")

    args = parser.parse_args()
    root = Path(args.root).resolve()
    rules_path = Path(args.rules).resolve() if args.rules else None

    if args.impact:
        rules = load_rules(rules_path)
        hits = compute_blast_radius(root, args.impact, rules)
        if args.json:
            print(json.dumps({"query": args.impact, "hits": [asdict(h) for h in hits]}, indent=2, ensure_ascii=False))
        else:
            _print_impact_report(args.impact, hits)
        return 0

    report = run_full_audit(root, rules_path)
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        _print_audit_report(report)

    if args.strict and not report["clean"]:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
