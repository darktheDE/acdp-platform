#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_audit_doc_drift.py - Unit tests for audit_doc_drift.py
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from audit_doc_drift import (  # noqa: E402
    compute_blast_radius,
    load_rules,
    run_full_audit,
)


def _write(base: Path, rel: str, content: str) -> Path:
    target = base / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return target


def _create_clean_fixture_repo(root: Path) -> Path:
    rules = {
        "directive_source": "docs/frameworks/TEAM_DIRECTIVES.md",
        "agent_contract_files": ["AGENTS.md", "GEMINI.md"],
        "required_directives_in_agent_contracts": ["DIR-007", "DIR-016", "DIR-017"],
        "scoped_directives": ["DIR-001"],
        "skill_registry_targets": ["AGENTS.md", "GEMINI.md", "CLAUDE.md", ".agents/skills/README.md"],
        "skill_count_banner": {
            "file": ".agents/skills/README.md",
            "pattern": "Toàn bộ (\\d+) kỹ năng",
            "rule_id": "DRIFT-004",
        },
        "internal_link_scan_paths": [
            "AGENTS.md",
            "GEMINI.md",
            "CLAUDE.md",
            "README.md",
            "docs/**/*.md",
            ".agents/skills/**/*.md",
        ],
        "drift_rules": [
            {
                "id": "DRIFT-001",
                "description": "Deprecated path",
                "targets": ["docs/specs/*.md", "README.md", "AGENTS.md", "GEMINI.md"],
                "pattern": "src/acdp/lakehouse/",
                "exclude_if_line_contains": ["deprecated"],
                "message": "Deprecated lakehouse path",
            },
            {
                "id": "DRIFT-002",
                "description": "Outdated Next.js 15",
                "targets": ["AGENTS.md", "GEMINI.md", ".agents/skills/README.md"],
                "pattern": "Next\\.js 15(?!\\.5| Maintenance LTS)",
                "exclude_if_line_contains": [],
                "message": "Use Next.js 16",
            },
            {
                "id": "DRIFT-003",
                "description": "PostgreSQL exclusion contradiction",
                "targets": ["docs/specs/0001-system-foundation-spec.md"],
                "pattern": "SeaweedFS[^\\n]*PostgreSQL[^\\n]*excluded",
                "exclude_if_line_contains": [],
                "message": "PostgreSQL 18 is active for OLTP",
            },
        ],
        "tier_classification": {
            "Tier 0 (Decision Origins)": ["docs/frameworks/TEAM_DIRECTIVES.md"],
            "Tier 1 (Agent Contracts & Harness)": ["AGENTS.md", "GEMINI.md", "CLAUDE.md", ".agents/skills/README.md"],
            "Tier 2 (Technical Specs & Ledgers)": ["docs/specs/", "README.md"],
            "Tier 3 (Skills & Academic Outputs)": [".agents/skills/"],
        },
    }
    rules_path = _write(root, ".agents/skills/doc-decision-sync/references/decision_rules.json", json.dumps(rules))
    _write(root, ".agents/skills/doc-decision-sync/SKILL.md", "# doc-decision-sync\n")
    _write(
        root,
        "docs/frameworks/TEAM_DIRECTIVES.md",
        "| DIR-001 | ... |\n| DIR-007 | ... |\n| DIR-016 | ... |\n| DIR-017 | ... |\n",
    )
    _write(root, "AGENTS.md", "DIR-007 DIR-016 DIR-017 doc-decision-sync Next.js 16\n[Specs](./docs/specs/0001-system-foundation-spec.md)\n")
    _write(root, "GEMINI.md", "DIR-007 DIR-016 DIR-017 doc-decision-sync\n")
    _write(root, "CLAUDE.md", "doc-decision-sync\n")
    _write(root, ".agents/skills/README.md", "Toàn bộ 1 kỹ năng: doc-decision-sync\n")
    _write(root, "docs/specs/0001-system-foundation-spec.md", "# SPEC-0001\nUses PostgreSQL 18 OLTP and src/acdp/schemas.py\n")
    _write(root, "README.md", "# ACDP\n")
    return rules_path


class TestAuditDocDrift(unittest.TestCase):
    def test_clean_repository_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rules_path = _create_clean_fixture_repo(root)
            report = run_full_audit(root, rules_path)
            self.assertTrue(report["clean"], report["findings"])
            self.assertEqual(report["violation_count"], 0)

    def test_detects_missing_directive_in_contract_and_unaccounted_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rules_path = _create_clean_fixture_repo(root)
            _write(
                root,
                "docs/frameworks/TEAM_DIRECTIVES.md",
                "| DIR-001 | DIR-007 | DIR-016 | DIR-017 | DIR-018 |\n",
            )
            _write(root, "AGENTS.md", "DIR-007 DIR-017 doc-decision-sync\n")
            report = run_full_audit(root, rules_path)
            rule_ids = {f["rule_id"] for f in report["findings"]}
            self.assertIn("DIR-UNACCOUNTED", rule_ids)
            self.assertIn("DIR-CONTRACT-MISSING", rule_ids)

    def test_detects_unregistered_skill_and_count_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rules_path = _create_clean_fixture_repo(root)
            _write(root, ".agents/skills/new-skill/SKILL.md", "# new-skill\n")
            report = run_full_audit(root, rules_path)
            rule_ids = {f["rule_id"] for f in report["findings"]}
            self.assertIn("SKILL-UNREGISTERED", rule_ids)
            self.assertIn("DRIFT-004", rule_ids)

    def test_detects_canonical_fact_drift_rules(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rules_path = _create_clean_fixture_repo(root)
            _write(
                root,
                "docs/specs/0001-system-foundation-spec.md",
                "Schema at src/acdp/lakehouse/schema.py\nSeaweedFS, PostgreSQL, dbt-core are excluded.\n",
            )
            _write(root, "AGENTS.md", "DIR-007 DIR-016 DIR-017 doc-decision-sync Next.js 15 components\n")
            report = run_full_audit(root, rules_path)
            rule_ids = {f["rule_id"] for f in report["findings"]}
            self.assertIn("DRIFT-001", rule_ids)
            self.assertIn("DRIFT-002", rule_ids)
            self.assertIn("DRIFT-003", rule_ids)

    def test_detects_broken_relative_links_and_ignores_code_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rules_path = _create_clean_fixture_repo(root)
            _write(
                root,
                "docs/specs/0002-test.md",
                (
                    "# Spec\n"
                    "Valid anchor link: [Found](./0001-system-foundation-spec.md#section-1)\n"
                    "Broken link: [Ghost](./does-not-exist.md)\n"
                    "External link: [Docs](https://example.com/missing)\n"
                    "Inline code: `[Fake](./not-real.md)`\n"
                    "```markdown\n"
                    "[Template](./sample-missing.md)\n"
                    "```\n"
                ),
            )
            report = run_full_audit(root, rules_path)
            link_findings = [f for f in report["findings"] if f["check_id"] == "INTERNAL-LINK-INTEGRITY"]
            self.assertEqual(len(link_findings), 1)
            self.assertIn("does-not-exist.md", link_findings[0]["message"])

    def test_compute_blast_radius_groups_by_tier(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rules_path = _create_clean_fixture_repo(root)
            rules = load_rules(rules_path)
            hits = compute_blast_radius(root, "DIR-016", rules)
            tiers = {h.tier for h in hits}
            self.assertIn("Tier 0 (Decision Origins)", tiers)
            self.assertIn("Tier 1 (Agent Contracts & Harness)", tiers)


if __name__ == "__main__":
    unittest.main()
