#!/usr/bin/env python3
"""Unit tests for check_delivery_package.py (DIR-024 Standard Delivery Gate)."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from check_delivery_package import validate_delivery_package  # noqa: E402


class TestStandardDeliveryGate(unittest.TestCase):
    """Verify deterministic 7-pillar enforcement on synthetic task packages."""

    def _create_complete_fixture(self, root: Path) -> None:
        (root / "docs" / "tasks").mkdir(parents=True)
        (root / "docs" / "deliverables").mkdir(parents=True)
        (root / "tests").mkdir(parents=True)

        (root / "tests" / "test_sample_task.py").write_text("def test_ok():\n    assert True\n", encoding="utf-8")

        html_doc = root / "docs" / "deliverables" / "TASK-DEMO-01-sample-visual-dossier.html"
        html_doc.write_text(
            "<!DOCTYPE html><html><head><script src='https://cdn.tailwindcss.com'></script>"
            "<script src='https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js'></script>"
            "<script src='https://cdn.jsdelivr.net/npm/chart.js'></script></head>"
            "<body><div class='mermaid'>flowchart LR\nA-->B</div></body></html>",
            encoding="utf-8",
        )

        md_doc = root / "docs" / "deliverables" / "TASK-DEMO-01-sample.md"
        md_doc.write_text(
            "# DELIVERABLE: Sample Task\n\n"
            "## 2. Benchmarks & Quantitative Evidence\n\n"
            "| Metric | Value |\n| :--- | :--- |\n| Query Latency | 18.5 ms |\n\n"
            "## 3. Manual Test & Advisor Demo Runbook\n\n"
            "```powershell\nuv run pytest tests/test_sample_task.py -q\n```\n\n"
            "Captured Output:\n\n"
            "```text\n1 passed in 0.12s\n```\n\n"
            "## 4. Search Provenance & References\n\n"
            "| Query | URL |\n| :--- | :--- |\n"
            "| `duckdb benchmark` | https://duckdb.org/ |\n",
            encoding="utf-8",
        )

        tasks_json = {
            "tasks": [
                {
                    "id": "TASK-DEMO-01",
                    "deliverables": [
                        "docs/deliverables/TASK-DEMO-01-sample.md",
                        "docs/deliverables/TASK-DEMO-01-sample-visual-dossier.html",
                        "tests/test_sample_task.py",
                    ],
                }
            ]
        }
        (root / "docs" / "tasks" / "tasks-data.json").write_text(
            json.dumps(tasks_json, indent=2), encoding="utf-8"
        )

    def test_complete_package_passes_all_seven_pillars(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._create_complete_fixture(root)
            ok, passed, errors = validate_delivery_package(root, task_id="TASK-DEMO-01")
            self.assertTrue(ok, f"Expected PASS, got errors: {errors}")
            self.assertEqual(len(passed), 7)
            self.assertEqual(errors, [])

    def test_missing_html_dossier_fails_pillar_3(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._create_complete_fixture(root)
            (root / "docs" / "deliverables" / "TASK-DEMO-01-sample-visual-dossier.html").unlink()
            ok, _, errors = validate_delivery_package(root, task_id="TASK-DEMO-01")
            self.assertFalse(ok)
            self.assertTrue(any("Pillar 3 FAIL" in e for e in errors))

    def test_missing_search_provenance_fails_pillar_4(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._create_complete_fixture(root)
            md_doc = root / "docs" / "deliverables" / "TASK-DEMO-01-sample.md"
            md_doc.write_text(
                "# DELIVERABLE: Sample\n\n"
                "## 2. Benchmarks\n\n| M | V |\n| :--- | :--- |\n| Latency | 10 ms |\n\n"
                "## 3. Manual Test & Demo Runbook\n\n"
                "```powershell\nuv run pytest tests/test_sample_task.py\n```\n\n"
                "```text\n1 passed\n```\n",
                encoding="utf-8",
            )
            ok, _, errors = validate_delivery_package(root, task_id="TASK-DEMO-01")
            self.assertFalse(ok)
            self.assertTrue(any("Pillar 4 FAIL" in e for e in errors))

    def test_placeholder_token_fails_pillar_7(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._create_complete_fixture(root)
            md_doc = root / "docs" / "deliverables" / "TASK-DEMO-01-sample.md"
            md_doc.write_text(md_doc.read_text(encoding="utf-8") + "\nPending output: TBD\n", encoding="utf-8")
            ok, _, errors = validate_delivery_package(root, task_id="TASK-DEMO-01")
            self.assertFalse(ok)
            self.assertTrue(any("Pillar 7 FAIL" in e for e in errors))


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestStandardDeliveryGate)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(0 if result.wasSuccessful() else 1)
