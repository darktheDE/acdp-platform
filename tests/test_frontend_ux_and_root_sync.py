"""Automated verification tests for Frontend UI/UX hygiene, use-case features, and root file synchronization (TASK-HF-01)."""

from __future__ import annotations

import json
import re
from pathlib import Path

import yaml
from dotenv import dotenv_values

from acdp.api.main import app

ROOT = Path(__file__).resolve().parents[1]
WEB_DIR = ROOT / "apps" / "web"

PUBLIC_UI_FILES: tuple[Path, ...] = (
    WEB_DIR / "app" / "layout.tsx",
    WEB_DIR / "app" / "error.tsx",
    WEB_DIR / "app" / "page.tsx",
    WEB_DIR / "app" / "competitions" / "page.tsx",
    WEB_DIR / "app" / "competitions" / "[key]" / "page.tsx",
    WEB_DIR / "app" / "dashboard" / "page.tsx",
    WEB_DIR / "app" / "copilot" / "page.tsx",
    WEB_DIR / "app" / "bookmarks" / "page.tsx",
    WEB_DIR / "app" / "login" / "page.tsx",
    WEB_DIR / "components" / "brand" / "AcdpLogo.tsx",
    WEB_DIR / "components" / "layout" / "AppShell.tsx",
    WEB_DIR / "components" / "layout" / "TopNav.tsx",
    WEB_DIR / "components" / "competitions" / "BookmarkButton.tsx",
    WEB_DIR / "components" / "competitions" / "CompetitionCard.tsx",
    WEB_DIR / "components" / "competitions" / "FilterSidebar.tsx",
    WEB_DIR / "components" / "copilot" / "CopilotWorkspace.tsx",
    WEB_DIR / "components" / "charts" / "DomainBarChart.tsx",
    WEB_DIR / "components" / "charts" / "ModeDonutChart.tsx",
    WEB_DIR / "components" / "charts" / "OrganizerRanking.tsx",
    WEB_DIR / "components" / "charts" / "SeasonalityChart.tsx",
)

FORBIDDEN_PUBLIC_UI_PATTERNS: tuple[str, ...] = (
    r"Medallion\s+Lakehouse",
    r"Star\s+Schema",
    r"PostgreSQL\s*18",
    r"\bDuckDB\b",
    r"\bQdrant\b",
    r"saved_competitions",
    r"mart_competition_explorer",
    r"bridge_competition_organizer",
    r"allocation_weight",
    r"OWASP\s+LLM10",
    r"DIR-\d{3}",
    r"FastAPI\s+Gateway",
    r"HCM-UTE\s+Data\s+Lakehouse",
    r"Grounded\s+RAG",
    r"RAG\s+Copilot",
    r"17\s+(?:nguồn|cuộc\s+thi)",
    r"read_only=True",
)


def test_public_frontend_has_no_internal_tech_or_method_jargon() -> None:
    """Ensure student-facing UI files never leak backend DB tables, stack names, or internal directives."""
    violations: list[str] = []
    for path in PUBLIC_UI_FILES:
        text = path.read_text(encoding="utf-8")
        for pattern in FORBIDDEN_PUBLIC_UI_PATTERNS:
            if re.search(pattern, text, flags=re.IGNORECASE):
                violations.append(f"{path.relative_to(ROOT)} matched /{pattern}/")
    assert not violations, "Internal jargon leaked on public UI:\n" + "\n".join(violations)


def test_admin_frontend_security_and_swagger_route() -> None:
    """Ensure /admin avoids env-var/milestone leaks and calls authenticated /api/v1/admin/docs."""
    admin_text = (WEB_DIR / "app" / "admin" / "page.tsx").read_text(encoding="utf-8")
    assert "ADMIN_EMAILS" not in admin_text
    assert "Gate G5/G6" not in admin_text
    assert "/api/v1/admin/docs" in admin_text
    assert 'window.open(`${baseUrl}/docs`' not in admin_text


def test_frontend_use_case_ux_enhancements() -> None:
    """Verify student discovery, filtering, detail brief, and contextual copilot use cases."""
    home_text = (WEB_DIR / "app" / "page.tsx").read_text(encoding="utf-8")
    assert 'action="/competitions"' in home_text
    assert "QUICK_FILTERS" in home_text
    assert "CompetitionCard" in home_text

    filter_text = (WEB_DIR / "components" / "competitions" / "FilterSidebar.tsx").read_text(encoding="utf-8")
    assert 'name="status"' in filter_text
    assert 'name="sort"' in filter_text

    detail_text = (WEB_DIR / "app" / "competitions" / "[key]" / "page.tsx").read_text(encoding="utf-8")
    assert "comp.target_audience" in detail_text
    assert "comp.challenge_overview" in detail_text
    assert "/copilot?" in detail_text

    copilot_page_text = (WEB_DIR / "app" / "copilot" / "page.tsx").read_text(encoding="utf-8")
    assert "buildCompetitionScopes" in copilot_page_text


def test_root_openapi_env_compose_and_readme_are_synced() -> None:
    """Verify openapi.json, .env.example, .env.dev, docker-compose.yml, and README.md match the current codebase."""
    live_paths = set(app.openapi()["paths"].keys())
    disk_openapi = json.loads((ROOT / "openapi.json").read_text(encoding="utf-8"))
    disk_paths = set(disk_openapi["paths"].keys())
    assert live_paths == disk_paths, f"openapi.json drift: missing={live_paths - disk_paths}, extra={disk_paths - live_paths}"

    for env_name in (".env.example", ".env.dev"):
        env_map = dotenv_values(ROOT / env_name)
        assert env_map.get("GROQ_CHAT_MODEL") == "qwen/qwen3.8-27b", f"{env_name} GROQ_CHAT_MODEL out of sync"
        assert (
            env_map.get("OPENROUTER_CHAT_MODEL") == "google/gemma-4-31b-it:free"
        ), f"{env_name} OPENROUTER_CHAT_MODEL out of sync"

    compose = yaml.safe_load((ROOT / "docker-compose.yml").read_text(encoding="utf-8"))
    api_env = compose["services"]["api"]["environment"]
    for required_key in ("GROQ_API_KEY", "OPENROUTER_API_KEY", "ADMIN_EMAILS", "SUPABASE_DIRECT_URL"):
        assert required_key in api_env, f"docker-compose.yml api missing {required_key}"

    readme_text = (ROOT / "README.md").read_text(encoding="utf-8")
    for required_ref in (
        "src/acdp/v2/discovery.py",
        "src/acdp/v2/bronze_crawl.py",
        "src/acdp/v2/silver_transform.py",
        "src/acdp/v2/gold_star_schema.py",
        "src/acdp/v2/rag_ingest.py",
        "src/acdp/v2/cloud_ops.py",
        "scripts/seed_local_users.py",
        ".github/workflows/keep-alive.yml",
    ):
        assert required_ref in readme_text, f"README.md missing reference to {required_ref}"
