#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Unit tests for repo-task-manager sync_tasks.py."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from sync_tasks import render_task_registry_md, validate_tasks_data


class TestSyncTasks(unittest.TestCase):
    def test_validate_and_render(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs" / "deliverables").mkdir(parents=True)
            (root / "docs" / "deliverables" / "sample.md").write_text("# Sample\n", encoding="utf-8")

            data = {
                "version": "1.0.0",
                "last_updated": "2026-11-22",
                "tasks": [
                    {
                        "id": "TASK-OPS-02",
                        "title": "External Feedback Form",
                        "cycle": "Cycle 10",
                        "scope": "KLTN (Phase 2)",
                        "layer": "Academic & Ops",
                        "task_type": "No-Code / External Integration",
                        "is_no_code": True,
                        "owner": "Hung & Duy",
                        "status": "done",
                        "priority": "low",
                        "problem_statement": "Use external form.",
                        "deliverables": ["docs/deliverables/sample.md"],
                        "updated_at": "2026-11-22",
                    }
                ],
            }
            errors = validate_tasks_data(data, root)
            self.assertEqual(errors, [])

            md = render_task_registry_md(data)
            self.assertIn("TASK-OPS-02", md)
            self.assertIn("*(No-Code)*", md)


if __name__ == "__main__":
    unittest.main()
