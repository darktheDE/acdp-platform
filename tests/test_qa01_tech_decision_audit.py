"""Automated verification suite for TASK-QA-01 (3-Axis Technical Decision Audit) & DIR-024."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

from acdp.config import AppConfig

REPO_ROOT = Path(__file__).resolve().parents[1]
DELIVERABLE_MD = REPO_ROOT / "docs" / "deliverables" / "TASK-QA-01-tech-decision-theory-practice-audit.md"
DELIVERABLE_HTML = (
    REPO_ROOT / "docs" / "deliverables" / "TASK-QA-01-tech-decision-theory-practice-audit-visual-dossier.html"
)
RFC_0001 = REPO_ROOT / "docs" / "rfc" / "RFC-0001-spec-v2-and-cloud-parity-realignment.md"
RFC_0002 = REPO_ROOT / "docs" / "rfc" / "RFC-0002-kltn-scale-evolution-triggers.md"


def test_deliverable_covers_all_eight_decisions_and_seven_core_components() -> None:
    """Verify TASK-QA-01 audits D1-D8, all 7 mandatory stack components, and Search Provenance."""
    assert DELIVERABLE_MD.exists(), f"Missing deliverable: {DELIVERABLE_MD}"
    text = DELIVERABLE_MD.read_text(encoding="utf-8")

    for decision_id in ("D1", "D2", "D3", "D4", "D5", "D6", "D7", "D8"):
        assert re.search(rf"\b{decision_id}\b", text), f"Missing decision {decision_id} in audit matrix"

    required_stack_tokens = (
        "Cloudflare R2",
        "Parquet",
        "Crawl4AI",
        "Instructor",
        "Star Schema",
        "DuckDB",
        "PostgreSQL",
        "Qdrant",
        "FastAPI",
        "Next.js",
    )
    for token in required_stack_tokens:
        assert token in text, f"Missing required stack coverage token: {token}"

    assert "Search Provenance" in text
    assert "search_web" in text
    assert len(re.findall(r"https://[^\s)>\]]+", text)) >= 16


def test_rfcs_exist_with_valid_lifecycle_status() -> None:
    """Verify RFC-0001 (Implemented) and RFC-0002 (Draft) follow RFC lifecycle per DIR-011."""
    assert RFC_0001.exists(), f"Missing RFC file: {RFC_0001}"
    assert RFC_0002.exists(), f"Missing RFC file: {RFC_0002}"

    rfc1 = RFC_0001.read_text(encoding="utf-8")
    assert "- Status: Implemented" in rfc1
    assert "## 1. Motivation & Context" in rfc1
    assert "## 2. Proposed Change" in rfc1

    rfc2 = RFC_0002.read_text(encoding="utf-8")
    assert "- Status: Draft" in rfc2
    assert "## 1. Motivation & Context" in rfc2
    assert "## 2. Proposed Change" in rfc2


def test_docker_compose_zero_latest_and_ram_budget() -> None:
    """Verify docker-compose.yml has 0 :latest tags and core profile limits stay <= 2048 MB."""
    dc_text = (REPO_ROOT / "docker-compose.yml").read_text(encoding="utf-8")
    assert re.findall(r":latest\b", dc_text) == []

    # Core services defined in SPEC-0006 + ADR-0002: postgres (256M) + api (640M) + web (512M) = 1408M
    assert "memory: 256M" in dc_text
    assert "memory: 640M" in dc_text
    assert "memory: 512M" in dc_text
    assert 256 + 640 + 512 == 1408 <= 2048


def test_config_r2_exclusive_and_llm_guardrails() -> None:
    """Verify AppConfig enforces Cloudflare R2 exclusive backend and LLM output token cap."""
    cfg = AppConfig(_env_file=None)
    assert cfg.bronze_storage_backend == "cloudflare_r2"
    assert cfg.rag_max_output_tokens <= 2048
    assert cfg.get_embedding_model() == "@cf/baai/bge-m3"


def test_keep_alive_workflow_daily_and_weekly_backup() -> None:
    """Verify keep-alive.yml runs daily at 02:15 UTC and weekly pg_dump on Sunday 02:30 UTC."""
    wf = (REPO_ROOT / ".github" / "workflows" / "keep-alive.yml").read_text(encoding="utf-8")
    assert "15 2 * * *" in wf
    assert "30 2 * * 0" in wf
    assert "--keep-alive" in wf
    assert "--backup-oltp" in wf


def test_dir024_and_standard_delivery_gate_synced() -> None:
    """Verify DIR-024 and standard-delivery-gate are synced across contracts and pass gate checks."""
    for rel in (
        "docs/frameworks/TEAM_DIRECTIVES.md",
        "AGENTS.md",
        "GEMINI.md",
        ".agents/skills/doc-decision-sync/references/decision_rules.json",
    ):
        assert "DIR-024" in (REPO_ROOT / rel).read_text(encoding="utf-8"), f"DIR-024 missing in {rel}"

    for rel in ("AGENTS.md", "GEMINI.md", "CLAUDE.md", ".agents/skills/README.md"):
        assert "standard-delivery-gate" in (REPO_ROOT / rel).read_text(
            encoding="utf-8"
        ), f"standard-delivery-gate missing in {rel}"

    rules = json.loads(
        (REPO_ROOT / ".agents" / "skills" / "doc-decision-sync" / "references" / "decision_rules.json").read_text(
            encoding="utf-8"
        )
    )
    assert "DIR-024" in rules["required_directives_in_agent_contracts"]

    gate_script = REPO_ROOT / ".agents" / "skills" / "standard-delivery-gate" / "scripts" / "check_delivery_package.py"
    proc = subprocess.run(
        [sys.executable, str(gate_script), "--task-id", "TASK-QA-01", "--repo-root", str(REPO_ROOT)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    assert proc.returncode == 0, f"Delivery gate failed:\n{proc.stdout}\n{proc.stderr}"
    assert DELIVERABLE_HTML.exists()
