#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sync_tasks.py - Deterministic In-Repo Task Registry & Portal Synchronizer.
Part of 'repo-task-manager' skill (DIR-018).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

VALID_SCOPES = {"TLCN (Phase 1)", "KLTN (Phase 2)", "TLCN -> KLTN"}
VALID_STATUSES = {"todo", "in_progress", "review", "done"}
VALID_LAYERS = {
    "Discovery",
    "Bronze",
    "Silver",
    "Gold",
    "Serving & Web",
    "Cloud & Infra",
    "Academic & Ops",
}
REQUIRED_FIELDS = {
    "id",
    "title",
    "cycle",
    "scope",
    "layer",
    "task_type",
    "is_no_code",
    "owner",
    "status",
    "priority",
    "problem_statement",
    "deliverables",
    "updated_at",
}

STATUS_BADGE = {
    "done": "✅ Done",
    "in_progress": "🔄 In Progress",
    "review": "👀 Peer Review",
    "todo": "⏳ Todo",
}

EMBED_START = "/*__ACDP_TASKS_START__*/"
EMBED_END = "/*__ACDP_TASKS_END__*/"


def load_tasks_data(json_path: Path) -> dict[str, Any]:
    with json_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def validate_tasks_data(data: dict[str, Any], repo_root: Path) -> list[str]:
    errors: list[str] = []
    tasks = data.get("tasks")
    if not isinstance(tasks, list):
        return ["Top-level 'tasks' must be a list."]

    seen_ids: set[str] = set()
    for idx, task in enumerate(tasks):
        tid = task.get("id", f"<index-{idx}>")
        if tid in seen_ids:
            errors.append(f"Duplicate task id: {tid}")
        seen_ids.add(tid)

        missing = REQUIRED_FIELDS - set(task.keys())
        if missing:
            errors.append(f"{tid}: missing required fields {sorted(missing)}")

        if task.get("scope") not in VALID_SCOPES:
            errors.append(f"{tid}: invalid scope '{task.get('scope')}'")
        if task.get("status") not in VALID_STATUSES:
            errors.append(f"{tid}: invalid status '{task.get('status')}'")
        if task.get("layer") not in VALID_LAYERS:
            errors.append(f"{tid}: invalid layer '{task.get('layer')}'")
        if not isinstance(task.get("is_no_code"), bool):
            errors.append(f"{tid}: 'is_no_code' must be boolean")

        if task.get("status") == "done":
            for rel in task.get("deliverables", []):
                target = (repo_root / rel).resolve()
                if not target.exists():
                    errors.append(f"{tid}: done task references missing deliverable '{rel}'")

    return errors


def render_task_registry_md(data: dict[str, Any], repo_root: Path | None = None) -> str:
    tasks = data.get("tasks", [])
    done_count = sum(1 for t in tasks if t.get("status") == "done")
    tlcn_count = sum(1 for t in tasks if "TLCN" in t.get("scope", ""))
    kltn_count = sum(1 for t in tasks if "KLTN" in t.get("scope", ""))

    lines = [
        "# In-repo task registry & deliverables ledger",
        "",
        "This ledger is auto-generated from [`tasks-data.json`](./tasks-data.json) and synchronized with the interactive portal [`index.html`](./index.html) per **DIR-018**.",
        "",
        f"- **Total tasks**: `{len(tasks)}` (`{done_count}` completed)",
        f"- **Scope distribution**: `{tlcn_count}` TLCN (Phase 1) | `{kltn_count}` KLTN (Phase 2)",
        f"- **Last updated**: `{data.get('last_updated', '2026-11-22')}`",
        "",
        "---",
        "",
        "## Master task registry",
        "",
        "| Task ID | Cycle | Scope | Layer | Title | Owner | Deliverables | Status |",
        "| :---: | :---: | :---: | :---: | :--- | :---: | :--- | :---: |",
    ]

    for t in tasks:
        no_code_tag = " *(No-Code)*" if t.get("is_no_code") else ""
        delivs = t.get("deliverables") or []
        if delivs:
            rendered_delivs = []
            for d in delivs:
                label = Path(d).name or d
                if repo_root is not None and (repo_root / d).exists():
                    rendered_delivs.append(f"[`{label}`](../../{d})")
                else:
                    rendered_delivs.append(f"`{d}`")
            deliv_links = ", ".join(rendered_delivs)
        else:
            deliv_links = "-"
        badge = STATUS_BADGE.get(t.get("status", "todo"), t.get("status", "todo"))
        title_clean = t.get("title", "").replace("|", "\\|")
        lines.append(
            f"| **{t['id']}** | {t['cycle']} | {t['scope']} | {t['layer']} | "
            f"{title_clean}{no_code_tag} | {t['owner']} | {deliv_links} | {badge} |"
        )

    lines.extend([
        "",
        "---",
        "",
        "## Synchronization commands",
        "",
        "```powershell",
        "uv run python .agents/skills/repo-task-manager/scripts/sync_tasks.py --sync",
        "uv run python .agents/skills/repo-task-manager/scripts/sync_tasks.py --validate",
        "```",
        "",
    ])
    return "\n".join(lines)


def embed_json_in_html(html_path: Path, data: dict[str, Any]) -> bool:
    if not html_path.exists():
        return False
    content = html_path.read_text(encoding="utf-8")
    pattern = re.compile(
        re.escape(EMBED_START) + r".*?" + re.escape(EMBED_END),
        re.DOTALL,
    )
    if not pattern.search(content):
        return False
    payload = json.dumps(data, ensure_ascii=False, indent=2)
    replacement = f"{EMBED_START}\nwindow.__ACDP_TASKS_DATA__ = {payload};\n{EMBED_END}"
    updated = pattern.sub(lambda _: replacement, content, count=1)
    html_path.write_text(updated, encoding="utf-8")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate and sync ACDP in-repo task registry.")
    parser.add_argument("--root", default=".", help="Repository root path")
    parser.add_argument("--validate", action="store_true", help="Validate tasks-data.json")
    parser.add_argument("--sync", action="store_true", help="Regenerate task-registry.md and embed JSON in index.html")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    json_path = root / "docs" / "tasks" / "tasks-data.json"
    md_path = root / "docs" / "tasks" / "task-registry.md"
    html_path = root / "docs" / "tasks" / "index.html"

    if not json_path.exists():
        print(f"[ERROR] Missing {json_path}")
        return 1

    data = load_tasks_data(json_path)
    errors = validate_tasks_data(data, root)
    if errors:
        for err in errors:
            print(f"[FAIL] {err}")
        return 1

    print(f"[PASS] Validated {len(data.get('tasks', []))} tasks in tasks-data.json.")

    if args.sync:
        md_content = render_task_registry_md(data, root)
        md_path.write_text(md_content, encoding="utf-8")
        print(f"[SYNC] Wrote {md_path.relative_to(root)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
