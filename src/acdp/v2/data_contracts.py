"""TASK-DQ-03: Automated Data Contracts (ODCS v3.2.0) & WAP Quality Gate (ACDP v2).

Implements a three-tier Write-Audit-Publish (WAP) Circuit Breaker across Bronze, Silver,
and Gold layers using Pydantic v2 (Tier A row contracts) and DuckDB 1.5.6 vectorized SQL
assertions (Tier B set/table contracts and Tier C Silver-to-Gold invariants), governed by
``docs/contracts/acdp-silver-competition.odcs.yaml``.

Usage:
    uv run python -m acdp.v2.data_contracts --validate-odcs
    uv run python -m acdp.v2.data_contracts --audit-local tests/fixtures/dq03/valid_silver_batch.json
    uv run python -m acdp.v2.data_contracts --audit-local tests/fixtures/dq03/invalid_silver_batch.json
    uv run python -m acdp.v2.data_contracts --audit-r2 --no-fail-fast
    uv run python -m acdp.v2.data_contracts --benchmark
"""

from __future__ import annotations

import argparse
import io
import json
import re
import sys
import time
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any, Literal
from urllib.parse import urlparse

import duckdb
import pyarrow as pa
import pyarrow.parquet as pq
import yaml
from pydantic import BaseModel, Field

from acdp.config import settings
from acdp.v2.schemas import (
    Competition,
    clean_placeholder,
    compute_competition_key,
    normalize_canonical_url,
    parse_date_value,
)

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

DEFAULT_CONTRACT_PATH = (
    Path(__file__).resolve().parents[3] / "docs" / "contracts" / "acdp-silver-competition.odcs.yaml"
)
DEFAULT_REFERENCE_YEAR = 2026

BRONZE_KEY_PATTERN = re.compile(
    r"^bronze/([^/]+)/year=(\d{4})/month=(\d{2})/day=(\d{2})/(\d+)(\.html)?$"
)
HEX64_RE = re.compile(r"^[0-9a-f]{64}$")

ALLOWED_MODES = frozenset({"online", "offline", "hybrid", "unknown"})
ALLOWED_REG_STATUSES = frozenset({"open", "upcoming", "closed", "unknown"})
ALLOWED_ELIGIBILITY_LEVELS = frozenset({"undergraduate", "all_students", "open", "unknown"})
ALLOWED_CURRENCIES = frozenset({"VND", "USD", "OTHER"})
ALLOWED_PRIZE_TYPES = frozenset({"cash", "scholarship", "credits", "merch", "mixed"})

AGGREGATOR_HOSTS = frozenset(
    {
        "ybox.vn",
        "www.ybox.vn",
        "topdev.vn",
        "www.topdev.vn",
        "vnoi.info",
        "www.vnoi.info",
        "khoahoctre.com.vn",
        "www.khoahoctre.com.vn",
        "tuoitre.vn",
        "vnexpress.net",
        "thanhnien.vn",
        "kenh14.vn",
        "svvn.tienphong.vn",
    }
)
SOCIAL_OR_FORM_HOSTS = frozenset(
    {
        "facebook.com",
        "www.facebook.com",
        "fb.com",
        "m.facebook.com",
        "youtube.com",
        "www.youtube.com",
        "youtu.be",
        "tiktok.com",
        "www.tiktok.com",
        "instagram.com",
        "www.instagram.com",
        "linkedin.com",
        "www.linkedin.com",
        "zalo.me",
        "t.me",
        "x.com",
        "twitter.com",
        "forms.gle",
        "docs.google.com",
        "drive.google.com",
        "bit.ly",
        "tinyurl.com",
        "shorturl.at",
        "pinterest.com",
        "www.pinterest.com",
        "threads.net",
    }
)
NOISY_HOST_PREFIXES = (
    "tuyensinh.",
    "alumni.",
    "khcn.",
    "daotao.",
    "ctsv.",
    "tracuu.",
    "jst-",
    "vieclam.",
    "portal.",
)
NOISY_PATH_MARKERS = (
    "/admissions",
    "/msc-programmes",
    "/graduate-studies",
    "/tuyen-dung",
)
GENERIC_ROOT_ONLY_HOSTS = frozenset(
    {
        "mic.gov.vn",
        "www.mic.gov.vn",
        "moet.gov.vn",
        "www.moet.gov.vn",
        "most.gov.vn",
        "www.most.gov.vn",
    }
)
NON_TECH_EXCLUSION_TERMS = (
    "marketingarena",
    "marketing arena",
    "cuộc thi marketing",
    "truyền thông thương hiệu",
    "infographic",
    "vẽ tranh",
    "nông nghiệp",
    "agriculture",
    "bầu cử",
    "khởi nghiệp nông nghiệp",
    "ẩm thực",
    "thời trang",
    "hùng biện tiếng anh",
)
CORE_TECH_OVERRIDE_TERMS = (
    "hackathon",
    "datathon",
    "lập trình",
    "trí tuệ nhân tạo",
    "an toàn thông tin",
    "cybersecurity",
    "data science",
    "artificial intelligence",
)
SCHOOL_ONLY_TERMS = (
    "tiểu học",
    "tieu hoc",
    "thcs",
    "trung học cơ sở",
    "thpt",
    "trung học phổ thông",
    "tin học trẻ",
    "học sinh phổ thông",
    "mầm non",
)
STUDENT_POSITIVE_TERMS = (
    "sinh viên",
    "sinh vien",
    "đại học",
    "dai hoc",
    "cao đẳng",
    "cao dang",
    "university",
    "undergraduate",
    "postgraduate",
    "college",
    "students",
    "student",
    "học viện",
    "cử nhân",
)
NOT_FOUND_MARKERS = (
    "404 not found",
    "page not found",
    "không tìm thấy trang",
    "không tồn tại trang",
    "403 forbidden",
    "access denied",
    "cloudflare ray id",
)

EXPECTED_RULE_IDS: tuple[str, ...] = (
    "C01",
    "C02",
    "C03",
    "C04",
    "C05",
    "C06",
    "C07",
    "C08",
    "C09",
    "C10",
    "C11",
    "C12",
    "C13",
    "C14",
    "W01",
    "W02",
    "W03",
    "W04",
    "W05",
)


class ContractViolation(BaseModel):
    """Single data contract rule violation sample."""

    rule_id: str
    severity: Literal["CRITICAL", "WARNING"]
    record_key: str | None = None
    record_name: str | None = None
    field: str | None = None
    value: str | None = None
    message: str


class RuleResult(BaseModel):
    """Evaluation outcome for a single Data Contract rule."""

    rule_id: str
    name: str
    layer: str
    engine: str
    severity: Literal["CRITICAL", "WARNING"]
    status: Literal["PASS", "FAIL", "WARN", "SKIP"]
    failed_count: int = 0
    checked_count: int = 0
    duration_ms: float = 0.0
    sample_violations: list[ContractViolation] = Field(default_factory=list)


class QualityGateReport(BaseModel):
    """Aggregate pass/fail report across all evaluated contract rules."""

    gate_name: str
    contract_id: str = "urn:acdp:datacontract:silver-competitions"
    contract_version: str = "2.0.0"
    audited_at_utc: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    source_label: str = "unknown"
    reference_year: int = DEFAULT_REFERENCE_YEAR
    record_counts: dict[str, int] = Field(default_factory=dict)
    rules_total: int = 0
    rules_passed: int = 0
    critical_failed: int = 0
    warning_count: int = 0
    overall_status: Literal["PASS", "PASS_WITH_WARNINGS", "FAIL"] = "PASS"
    circuit_breaker_tripped: bool = False
    elapsed_ms: float = 0.0
    rules: list[RuleResult] = Field(default_factory=list)

    def to_console_table(self) -> str:
        """Format a deterministic human-readable CLI report table."""
        lines = [
            "=" * 84,
            f"DATA CONTRACT QUALITY GATE: {self.gate_name} ({self.source_label})",
            f"Contract: {self.contract_id} v{self.contract_version} | Ref Year: {self.reference_year} ({self.reference_year - 1}-{self.reference_year + 1})",
            f"Records : {self.record_counts} | Elapsed: {self.elapsed_ms:.2f} ms",
            "-" * 84,
            f"{'Rule':<6} {'Severity':<9} {'Layer':<17} {'Engine':<11} {'Failed/Chk':<12} {'Status':<6} {'Name'}",
            "-" * 84,
        ]
        for rule in self.rules:
            ratio = f"{rule.failed_count}/{rule.checked_count}"
            lines.append(
                f"{rule.rule_id:<6} {rule.severity:<9} {rule.layer:<17} {rule.engine:<11} {ratio:<12} {rule.status:<6} {rule.name}"
            )
            for v in rule.sample_violations[:3]:
                who = v.record_name or v.record_key or "batch"
                lines.append(f"       -> [{who}] {v.field or ''}: {v.message}")
        lines.extend(
            [
                "-" * 84,
                f"Summary : {self.rules_passed}/{self.rules_total} passed | "
                f"critical_failed={self.critical_failed} | warnings={self.warning_count} | "
                f"circuit_breaker_tripped={self.circuit_breaker_tripped} | OVERALL={self.overall_status}",
                "=" * 84,
            ]
        )
        return "\n".join(lines)

    def to_markdown_table(self) -> str:
        """Render rule results as a Markdown summary table."""
        rows = [
            "| Rule | Severity | Layer | Engine | Checked | Failed | Status |",
            "| :---: | :---: | :--- | :--- | :---: | :---: | :---: |",
        ]
        for r in self.rules:
            rows.append(
                f"| `{r.rule_id}` | `{r.severity}` | {r.layer} | {r.engine} | {r.checked_count} | {r.failed_count} | **`{r.status}`** |"
            )
        return "\n".join(rows)


class DataContractViolationError(RuntimeError):
    """Fail-fast circuit breaker exception raised when CRITICAL contract rules fail."""

    def __init__(self, report: QualityGateReport) -> None:
        self.report = report
        tripped = [f"{r.rule_id}({r.failed_count})" for r in report.rules if r.status == "FAIL"]
        detail_lines = [
            f"DataContractViolationError: Circuit breaker tripped on '{report.source_label}' "
            f"[{report.critical_failed} CRITICAL rule(s) failed: {', '.join(tripped)}]."
        ]
        for r in report.rules:
            if r.status == "FAIL":
                for sample in r.sample_violations[:2]:
                    detail_lines.append(
                        f"  - {r.rule_id} [{sample.record_name or sample.record_key or 'batch'}]: {sample.message}"
                    )
        super().__init__("\n".join(detail_lines))


def load_odcs_contract(path: Path = DEFAULT_CONTRACT_PATH) -> dict[str, Any]:
    """Load and parse the ODCS v3.2.0 YAML Data Contract specification."""
    if not path.exists():
        raise FileNotFoundError(f"ODCS contract file not found: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Invalid ODCS YAML root object in {path}")
    return data


def validate_odcs_contract_sync(path: Path = DEFAULT_CONTRACT_PATH) -> dict[str, Any]:
    """Validate ODCS v3.2.0 required blocks and rule-ID parity with the runtime gate."""
    contract = load_odcs_contract(path)
    missing_blocks = [
        k for k in ("apiVersion", "kind", "id", "name", "version", "status", "schema", "quality") if not contract.get(k)
    ]
    if missing_blocks:
        raise ValueError(f"ODCS contract missing mandatory top-level blocks: {missing_blocks}")
    if str(contract.get("kind")) != "DataContract":
        raise ValueError(f"Unexpected ODCS kind: {contract.get('kind')}")
    if not str(contract.get("apiVersion", "")).startswith("v3."):
        raise ValueError(f"Expected ODCS v3.x apiVersion, got: {contract.get('apiVersion')}")

    schema_names = {tbl.get("name") for tbl in contract.get("schema", []) if isinstance(tbl, dict)}
    expected_tables = {"competitions", "prizes", "timeline_stages"}
    if not expected_tables.issubset(schema_names):
        raise ValueError(f"ODCS schema missing tables: {sorted(expected_tables - schema_names)}")

    yaml_rules = {q.get("id"): q for q in contract.get("quality", []) if isinstance(q, dict) and q.get("id")}
    missing_rules = [rid for rid in EXPECTED_RULE_IDS if rid not in yaml_rules]
    if missing_rules:
        raise ValueError(f"ODCS quality block missing expected rules: {missing_rules}")

    return {
        "status": "ok",
        "path": str(path),
        "apiVersion": contract["apiVersion"],
        "id": contract["id"],
        "version": contract["version"],
        "tables": sorted(schema_names),
        "rules_count": len(yaml_rules),
        "rule_ids": [q["id"] for q in contract["quality"] if isinstance(q, dict) and q.get("id")],
    }


def _check_official_url_c02(url: str | None) -> str | None:
    """Return error reason if URL fails DIR-022 official website requirements (C02)."""
    if not url or not isinstance(url, str) or not url.strip():
        return "URL is empty or null"
    raw = url.strip()
    lower = raw.lower()
    if lower.startswith("urn:"):
        return f"Fallback URN is not an official HTTP(S) website: {raw}"
    parsed = urlparse(raw)
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.netloc or "." not in parsed.netloc:
        return f"Malformed HTTP(S) URL: {raw}"
    host = parsed.netloc.lower().split(":")[0]
    bare = host[4:] if host.startswith("www.") else host
    if host in AGGREGATOR_HOSTS or bare in AGGREGATOR_HOSTS:
        return f"Aggregator URL must be resolved to official website (DIR-022): {host}"
    if host in SOCIAL_OR_FORM_HOSTS or bare in SOCIAL_OR_FORM_HOSTS:
        return f"Social/form link is not an official competition website: {host}"
    return None


def _check_anti_noise_url_c03(url: str | None) -> str | None:
    """Return error reason if URL matches known DOM/banner noise patterns (C03)."""
    if not url or not isinstance(url, str):
        return None
    parsed = urlparse(url.strip())
    host = parsed.netloc.lower().split(":")[0]
    bare = host[4:] if host.startswith("www.") else host
    path_lower = (parsed.path or "").lower()

    for prefix in NOISY_HOST_PREFIXES:
        if bare.startswith(prefix):
            return f"Noisy university/portal subdomain '{prefix}' leaked into official URL: {url}"
    for marker in NOISY_PATH_MARKERS:
        if marker in path_lower:
            return f"Non-competition ad/admissions path '{marker}' in URL: {url}"
    if host in GENERIC_ROOT_ONLY_HOSTS and path_lower in {"", "/"}:
        return f"Generic ministry homepage root is not a dedicated competition URL: {url}"
    return None


def _check_scope_c08(name: str, url: str | None, summary: str, category: list[str], target_audience: str | None, challenge_overview: str | None) -> str | None:
    """Return error reason if competition violates DIR-022 student tech scope (C08)."""
    blob = " ".join(
        part for part in (name, url or "", summary, " ".join(category), target_audience or "", challenge_overview or "") if part
    ).lower()
    has_non_tech = any(term in blob for term in NON_TECH_EXCLUSION_TERMS)
    has_tech_override = any(term in blob for term in CORE_TECH_OVERRIDE_TERMS)
    if has_non_tech and not has_tech_override:
        return f"Non-tech competition excluded by DIR-022 scope: {name}"
    has_school = any(term in blob for term in SCHOOL_ONLY_TERMS)
    has_university = any(term in blob for term in STUDENT_POSITIVE_TERMS)
    if has_school and not has_university:
        return f"School-only (non-university) competition excluded by DIR-022 scope: {name}"
    return None


def validate_bronze_to_silver_handoff(
    bronze_key: str | None,
    source_url: str | None,
    clean_md: str,
) -> RuleResult:
    """Validate C12 Bronze-to-Silver handoff contract before LLM extraction."""
    t0 = time.perf_counter()
    violations: list[ContractViolation] = []
    if not bronze_key or not BRONZE_KEY_PATTERN.match(bronze_key.strip()):
        violations.append(
            ContractViolation(
                rule_id="C12",
                severity="CRITICAL",
                record_key=bronze_key,
                field="bronze_key",
                value=bronze_key,
                message=f"Invalid Bronze object key taxonomy: {bronze_key!r}",
            )
        )
    if not source_url or not (source_url.startswith("http://") or source_url.startswith("https://")):
        violations.append(
            ContractViolation(
                rule_id="C12",
                severity="CRITICAL",
                record_key=bronze_key,
                field="source_url",
                value=source_url,
                message=f"Invalid Bronze source_url: {source_url!r}",
            )
        )
    stripped_md = (clean_md or "").strip()
    if len(stripped_md) < 200:
        violations.append(
            ContractViolation(
                rule_id="C12",
                severity="CRITICAL",
                record_key=bronze_key,
                field="clean_md",
                value=str(len(stripped_md)),
                message=f"Clean Markdown too short ({len(stripped_md)} < 200 chars)",
            )
        )
    lower_md = stripped_md.lower()
    if len(stripped_md) < 1500 and any(m in lower_md for m in NOT_FOUND_MARKERS):
        violations.append(
            ContractViolation(
                rule_id="C12",
                severity="CRITICAL",
                record_key=bronze_key,
                field="clean_md",
                message="Clean Markdown matches HTTP 404/403 error stub",
            )
        )
    elapsed = round((time.perf_counter() - t0) * 1000, 3)
    return RuleResult(
        rule_id="C12",
        name="Bronze-to-Silver Handoff Guard",
        layer="bronze_to_silver",
        engine="pydantic",
        severity="CRITICAL",
        status="FAIL" if violations else "PASS",
        failed_count=len(violations),
        checked_count=1,
        duration_ms=elapsed,
        sample_violations=violations[:10],
    )


def _record_raw_field(item: Competition | dict[str, Any], field: str, default: Any = None) -> Any:
    if isinstance(item, dict):
        return item.get(field, default)
    return getattr(item, field, default)


def _safe_year(val: Any) -> int | None:
    if val is None:
        return None
    if isinstance(val, datetime):
        return val.year
    if isinstance(val, date):
        return val.year
    parsed = parse_date_value(val)
    return parsed.year if parsed else None


def _safe_date(val: Any) -> date | None:
    return parse_date_value(val)


def validate_silver_records_pydantic(
    competitions: list[Competition] | list[dict[str, Any]],
    reference_year: int = DEFAULT_REFERENCE_YEAR,
) -> list[RuleResult]:
    """Tier A: Evaluate row-level Pydantic & domain contract rules C01..C08."""
    min_year, max_year = reference_year - 1, reference_year + 1
    checked = len(competitions)
    buckets: dict[str, list[ContractViolation]] = {f"C0{i}": [] for i in range(1, 9)}
    timings: dict[str, float] = {f"C0{i}": 0.0 for i in range(1, 9)}

    t_start = time.perf_counter()
    for idx, comp in enumerate(competitions):
        if isinstance(comp, dict):
            raw_key = comp.get("competition_key")
            raw_name = comp.get("name")
            raw_url = comp.get("url")
            raw_summary = comp.get("summary")
            label_name = str(raw_name or f"row[{idx}]")
            comp_key = str(raw_key or "")
            if not comp_key and raw_url:
                comp_key = compute_competition_key(normalize_canonical_url(str(raw_url), label_name))
        else:
            raw_key = comp.competition_key
            raw_name = comp.name
            raw_url = comp.url
            raw_summary = comp.summary
            label_name = comp.name
            comp_key = comp.competition_key or ""

        # C01: Non-empty core required fields
        if not comp_key or not HEX64_RE.match(comp_key):
            buckets["C01"].append(
                ContractViolation(
                    rule_id="C01",
                    severity="CRITICAL",
                    record_key=comp_key or None,
                    record_name=label_name,
                    field="competition_key",
                    value=str(raw_key),
                    message="competition_key must be a 64-char SHA-256 hex digest",
                )
            )
        for fname, fval in (("name", raw_name), ("url", raw_url), ("summary", raw_summary)):
            cleaned = clean_placeholder(fval)
            if not cleaned or not isinstance(cleaned, str):
                buckets["C01"].append(
                    ContractViolation(
                        rule_id="C01",
                        severity="CRITICAL",
                        record_key=comp_key or None,
                        record_name=label_name,
                        field=fname,
                        value=str(fval),
                        message=f"Required field '{fname}' is null, blank, or placeholder",
                    )
                )

        # C02 & C03: Official URL & Anti-Noise URL guards
        url_str = str(raw_url).strip() if raw_url is not None else ""
        c02_err = _check_official_url_c02(url_str)
        if c02_err:
            buckets["C02"].append(
                ContractViolation(
                    rule_id="C02",
                    severity="CRITICAL",
                    record_key=comp_key or None,
                    record_name=label_name,
                    field="url",
                    value=url_str,
                    message=c02_err,
                )
            )
        c03_err = _check_anti_noise_url_c03(url_str)
        if c03_err:
            buckets["C03"].append(
                ContractViolation(
                    rule_id="C03",
                    severity="CRITICAL",
                    record_key=comp_key or None,
                    record_name=label_name,
                    field="url",
                    value=url_str,
                    message=c03_err,
                )
            )

        # C04: Strict Enum Domains
        mode_val = _record_raw_field(comp, "mode", "unknown")
        reg_status_val = _record_raw_field(comp, "registration_status", "unknown")
        elig_val = _record_raw_field(comp, "eligibility_level", "unknown")
        if mode_val not in ALLOWED_MODES:
            buckets["C04"].append(
                ContractViolation(
                    rule_id="C04",
                    severity="CRITICAL",
                    record_key=comp_key or None,
                    record_name=label_name,
                    field="mode",
                    value=str(mode_val),
                    message=f"Invalid mode '{mode_val}'; expected one of {sorted(ALLOWED_MODES)}",
                )
            )
        if reg_status_val not in ALLOWED_REG_STATUSES:
            buckets["C04"].append(
                ContractViolation(
                    rule_id="C04",
                    severity="CRITICAL",
                    record_key=comp_key or None,
                    record_name=label_name,
                    field="registration_status",
                    value=str(reg_status_val),
                    message=f"Invalid registration_status '{reg_status_val}'",
                )
            )
        if elig_val not in ALLOWED_ELIGIBILITY_LEVELS:
            buckets["C04"].append(
                ContractViolation(
                    rule_id="C04",
                    severity="CRITICAL",
                    record_key=comp_key or None,
                    record_name=label_name,
                    field="eligibility_level",
                    value=str(elig_val),
                    message=f"Invalid eligibility_level '{elig_val}'",
                )
            )

        raw_prizes = _record_raw_field(comp, "prizes", []) or []
        for p_idx, prize in enumerate(raw_prizes):
            p_curr = prize.get("currency", "VND") if isinstance(prize, dict) else prize.currency
            p_type = prize.get("prize_type", "cash") if isinstance(prize, dict) else prize.prize_type
            p_tier = prize.get("tier") if isinstance(prize, dict) else prize.tier
            if not clean_placeholder(p_tier):
                buckets["C01"].append(
                    ContractViolation(
                        rule_id="C01",
                        severity="CRITICAL",
                        record_key=comp_key or None,
                        record_name=label_name,
                        field=f"prizes[{p_idx}].tier",
                        value=str(p_tier),
                        message="PrizeTier.tier must be non-empty",
                    )
                )
            if p_curr not in ALLOWED_CURRENCIES:
                buckets["C04"].append(
                    ContractViolation(
                        rule_id="C04",
                        severity="CRITICAL",
                        record_key=comp_key or None,
                        record_name=label_name,
                        field=f"prizes[{p_idx}].currency",
                        value=str(p_curr),
                        message=f"Invalid prize currency '{p_curr}'",
                    )
                )
            if p_type not in ALLOWED_PRIZE_TYPES:
                buckets["C04"].append(
                    ContractViolation(
                        rule_id="C04",
                        severity="CRITICAL",
                        record_key=comp_key or None,
                        record_name=label_name,
                        field=f"prizes[{p_idx}].prize_type",
                        value=str(p_type),
                        message=f"Invalid prize_type '{p_type}'",
                    )
                )

            p_val = prize.get("estimated_value_vnd") if isinstance(prize, dict) else prize.estimated_value_vnd
            p_qty = prize.get("quantity", 1) if isinstance(prize, dict) else prize.quantity
            p_rank = prize.get("tier_rank", p_idx + 1) if isinstance(prize, dict) else prize.tier_rank
            if p_val is not None and float(p_val) < 0:
                buckets["C07"].append(
                    ContractViolation(
                        rule_id="C07",
                        severity="CRITICAL",
                        record_key=comp_key or None,
                        record_name=label_name,
                        field=f"prizes[{p_idx}].estimated_value_vnd",
                        value=str(p_val),
                        message="Prize estimated_value_vnd cannot be negative",
                    )
                )
            if p_qty is not None and int(p_qty) < 1:
                buckets["C07"].append(
                    ContractViolation(
                        rule_id="C07",
                        severity="CRITICAL",
                        record_key=comp_key or None,
                        record_name=label_name,
                        field=f"prizes[{p_idx}].quantity",
                        value=str(p_qty),
                        message="Prize quantity must be >= 1",
                    )
                )
            if p_rank is not None and int(p_rank) < 1:
                buckets["C07"].append(
                    ContractViolation(
                        rule_id="C07",
                        severity="CRITICAL",
                        record_key=comp_key or None,
                        record_name=label_name,
                        field=f"prizes[{p_idx}].tier_rank",
                        value=str(p_rank),
                        message="Prize tier_rank must be >= 1",
                    )
                )

        # C05 & C06: Temporal window [2025, 2027] & chronological ordering
        reg_start_d = _safe_date(_record_raw_field(comp, "registration_start_date") or _record_raw_field(comp, "registration_start"))
        reg_end_d = _safe_date(_record_raw_field(comp, "registration_deadline_date") or _record_raw_field(comp, "registration_deadline"))
        evt_start_d = _safe_date(_record_raw_field(comp, "event_start_date") or _record_raw_field(comp, "event_start"))
        evt_end_d = _safe_date(_record_raw_field(comp, "event_end_date") or _record_raw_field(comp, "event_end"))
        team_reg_d = _safe_date(_record_raw_field(comp, "team_registration_deadline_date") or _record_raw_field(comp, "team_registration_deadline"))

        for df_name, dt_val in (
            ("registration_start_date", reg_start_d),
            ("registration_deadline_date", reg_end_d),
            ("event_start_date", evt_start_d),
            ("event_end_date", evt_end_d),
            ("team_registration_deadline_date", team_reg_d),
        ):
            if dt_val is not None and not (min_year <= dt_val.year <= max_year):
                buckets["C05"].append(
                    ContractViolation(
                        rule_id="C05",
                        severity="CRITICAL",
                        record_key=comp_key or None,
                        record_name=label_name,
                        field=df_name,
                        value=dt_val.isoformat(),
                        message=f"Date {dt_val.isoformat()} outside allowed window [{min_year}, {max_year}]",
                    )
                )

        if reg_start_d and reg_end_d and reg_end_d < reg_start_d:
            buckets["C06"].append(
                ContractViolation(
                    rule_id="C06",
                    severity="CRITICAL",
                    record_key=comp_key or None,
                    record_name=label_name,
                    field="registration_deadline_date",
                    value=f"{reg_start_d} > {reg_end_d}",
                    message=f"registration_deadline_date ({reg_end_d}) < registration_start_date ({reg_start_d})",
                )
            )
        if evt_start_d and evt_end_d and evt_end_d < evt_start_d:
            buckets["C06"].append(
                ContractViolation(
                    rule_id="C06",
                    severity="CRITICAL",
                    record_key=comp_key or None,
                    record_name=label_name,
                    field="event_end_date",
                    value=f"{evt_start_d} > {evt_end_d}",
                    message=f"event_end_date ({evt_end_d}) < event_start_date ({evt_start_d})",
                )
            )

        raw_stages = _record_raw_field(comp, "timeline_stages", []) or []
        for s_idx, stage in enumerate(raw_stages):
            st_s = _safe_date(stage.get("start_date_iso") if isinstance(stage, dict) else stage.start_date_iso) or _safe_date(
                stage.get("start_date") if isinstance(stage, dict) else stage.start_date
            )
            st_e = _safe_date(stage.get("end_date_iso") if isinstance(stage, dict) else stage.end_date_iso) or _safe_date(
                stage.get("end_date") if isinstance(stage, dict) else stage.end_date
            )
            for s_field, s_dt in (("start_date_iso", st_s), ("end_date_iso", st_e)):
                if s_dt is not None and not (min_year <= s_dt.year <= max_year):
                    buckets["C05"].append(
                        ContractViolation(
                            rule_id="C05",
                            severity="CRITICAL",
                            record_key=comp_key or None,
                            record_name=label_name,
                            field=f"timeline_stages[{s_idx}].{s_field}",
                            value=s_dt.isoformat(),
                            message=f"Stage date {s_dt.isoformat()} outside [{min_year}, {max_year}]",
                        )
                    )
            if st_s and st_e and st_e < st_s:
                buckets["C06"].append(
                    ContractViolation(
                        rule_id="C06",
                        severity="CRITICAL",
                        record_key=comp_key or None,
                        record_name=label_name,
                        field=f"timeline_stages[{s_idx}].end_date_iso",
                        value=f"{st_s} > {st_e}",
                        message=f"Stage end_date ({st_e}) < start_date ({st_s})",
                    )
                )

        # C07: Numeric & team bounds
        tmin = _record_raw_field(comp, "team_size_min")
        tmax = _record_raw_field(comp, "team_size_max")
        if tmin is not None and (int(tmin) < 1 or int(tmin) > 20):
            buckets["C07"].append(
                ContractViolation(
                    rule_id="C07",
                    severity="CRITICAL",
                    record_key=comp_key or None,
                    record_name=label_name,
                    field="team_size_min",
                    value=str(tmin),
                    message=f"team_size_min={tmin} outside [1, 20]",
                )
            )
        if tmax is not None and (int(tmax) < 1 or int(tmax) > 20):
            buckets["C07"].append(
                ContractViolation(
                    rule_id="C07",
                    severity="CRITICAL",
                    record_key=comp_key or None,
                    record_name=label_name,
                    field="team_size_max",
                    value=str(tmax),
                    message=f"team_size_max={tmax} outside [1, 20]",
                )
            )
        if tmin is not None and tmax is not None and int(tmin) > int(tmax):
            buckets["C07"].append(
                ContractViolation(
                    rule_id="C07",
                    severity="CRITICAL",
                    record_key=comp_key or None,
                    record_name=label_name,
                    field="team_size_min/max",
                    value=f"{tmin} > {tmax}",
                    message=f"team_size_min ({tmin}) > team_size_max ({tmax})",
                )
            )
        total_vnd = _record_raw_field(comp, "total_prize_vnd")
        if total_vnd is not None and int(total_vnd) < 0:
            buckets["C07"].append(
                ContractViolation(
                    rule_id="C07",
                    severity="CRITICAL",
                    record_key=comp_key or None,
                    record_name=label_name,
                    field="total_prize_vnd",
                    value=str(total_vnd),
                    message="total_prize_vnd cannot be negative",
                )
            )

        # C08: DIR-022 Student Tech Scope Guard
        cats = _record_raw_field(comp, "category", []) or []
        if isinstance(cats, str):
            cats = [cats]
        c08_err = _check_scope_c08(
            name=str(raw_name or ""),
            url=url_str,
            summary=str(raw_summary or ""),
            category=[str(x) for x in cats],
            target_audience=str(_record_raw_field(comp, "target_audience") or ""),
            challenge_overview=str(_record_raw_field(comp, "challenge_overview") or ""),
        )
        if c08_err:
            buckets["C08"].append(
                ContractViolation(
                    rule_id="C08",
                    severity="CRITICAL",
                    record_key=comp_key or None,
                    record_name=label_name,
                    field="scope",
                    value=label_name,
                    message=c08_err,
                )
            )

    total_ms = round((time.perf_counter() - t_start) * 1000, 3)
    per_rule_ms = round(total_ms / 8.0, 3)
    rule_meta = {
        "C01": "Non-Empty Core Not-Null Contract",
        "C02": "Official Website URL Required (DIR-022)",
        "C03": "Anti-Noise Official URL Guard (E1)",
        "C04": "Strict Enum Domains",
        "C05": f"Temporal Window {min_year}-{max_year} (DIR-022)",
        "C06": "Chronological Date Ordering",
        "C07": "Numeric and Team Size Bounds",
        "C08": "Student Tech Scope Guard (DIR-022)",
    }
    results: list[RuleResult] = []
    for rid, rname in rule_meta.items():
        viols = buckets[rid]
        results.append(
            RuleResult(
                rule_id=rid,
                name=rname,
                layer="silver_row",
                engine="pydantic",
                severity="CRITICAL",
                status="FAIL" if viols else "PASS",
                failed_count=len(viols),
                checked_count=checked,
                duration_ms=timings[rid] or per_rule_ms,
                sample_violations=viols[:10],
            )
        )
    return results


def _run_sql_rule(
    con: duckdb.DuckDBPyConnection,
    rule_id: str,
    name: str,
    layer: str,
    severity: Literal["CRITICAL", "WARNING"],
    checked_count: int,
    count_sql: str,
    sample_sql: str | None = None,
    *,
    is_min_threshold: bool = False,
    min_value: int = 1,
) -> RuleResult:
    t0 = time.perf_counter()
    cnt_row = con.execute(count_sql).fetchone()
    metric = int(cnt_row[0] or 0) if cnt_row else 0
    if is_min_threshold:
        failed_count = 0 if metric >= min_value else 1
    else:
        failed_count = metric

    samples: list[ContractViolation] = []
    if failed_count > 0:
        if sample_sql:
            for row in con.execute(sample_sql).fetchall()[:10]:
                samples.append(
                    ContractViolation(
                        rule_id=rule_id,
                        severity=severity,
                        record_key=str(row[0]) if len(row) > 0 and row[0] is not None else None,
                        record_name=str(row[1]) if len(row) > 1 and row[1] is not None else None,
                        field=str(row[2]) if len(row) > 2 and row[2] is not None else None,
                        value=str(row[3]) if len(row) > 3 and row[3] is not None else None,
                        message=str(row[4]) if len(row) > 4 and row[4] is not None else f"{rule_id} assertion failed",
                    )
                )
        else:
            samples.append(
                ContractViolation(
                    rule_id=rule_id,
                    severity=severity,
                    message=f"{name}: observed count={metric}",
                )
            )

    if failed_count == 0:
        status: Literal["PASS", "FAIL", "WARN", "SKIP"] = "PASS"
    elif severity == "WARNING":
        status = "WARN"
    else:
        status = "FAIL"

    return RuleResult(
        rule_id=rule_id,
        name=name,
        layer=layer,
        engine="duckdb_sql",
        severity=severity,
        status=status,
        failed_count=failed_count,
        checked_count=checked_count,
        duration_ms=round((time.perf_counter() - t0) * 1000, 3),
        sample_violations=samples,
    )


def validate_silver_tables_duckdb(
    comp_table: pa.Table,
    prize_table: pa.Table,
    stage_table: pa.Table,
    reference_year: int = DEFAULT_REFERENCE_YEAR,
    min_records: int = 1,
) -> list[RuleResult]:
    """Tier B: Execute DuckDB vectorized SQL assertions over Silver Arrow/Parquet tables."""
    min_year, max_year = reference_year - 1, reference_year + 1
    n_comp = comp_table.num_rows
    n_prize = prize_table.num_rows
    n_stage = stage_table.num_rows

    con = duckdb.connect(":memory:")
    try:
        con.register("competitions", comp_table)
        con.register("prizes", prize_table)
        con.register("timeline_stages", stage_table)

        results: list[RuleResult] = []
        # C09: Non-empty batch volume
        results.append(
            _run_sql_rule(
                con,
                "C09",
                "Non-Empty Batch Volume Guard",
                "silver_table",
                "CRITICAL",
                n_comp,
                "SELECT COUNT(*) FROM competitions",
                is_min_threshold=True,
                min_value=min_records,
            )
        )

        # C10: Primary key uniqueness across all 3 Silver tables
        results.append(
            _run_sql_rule(
                con,
                "C10",
                "Primary Key Uniqueness Across Silver Tables",
                "silver_table",
                "CRITICAL",
                n_comp + n_prize + n_stage,
                """
                SELECT (
                    (SELECT COUNT(*) FROM (SELECT competition_key FROM competitions GROUP BY 1 HAVING COUNT(*) > 1))
                    + (SELECT COUNT(*) FROM (SELECT competition_key, tier_rank FROM prizes GROUP BY 1, 2 HAVING COUNT(*) > 1))
                    + (SELECT COUNT(*) FROM (SELECT competition_key, stage_order FROM timeline_stages GROUP BY 1, 2 HAVING COUNT(*) > 1))
                )
                """,
                """
                SELECT competition_key, MIN(name), 'competition_key', CAST(COUNT(*) AS VARCHAR),
                       'Duplicate competition_key in competitions'
                FROM competitions GROUP BY competition_key HAVING COUNT(*) > 1
                UNION ALL
                SELECT competition_key, MIN(competition_name), 'tier_rank', CAST(tier_rank AS VARCHAR),
                       'Duplicate (competition_key, tier_rank) in prizes'
                FROM prizes GROUP BY competition_key, tier_rank HAVING COUNT(*) > 1
                UNION ALL
                SELECT competition_key, MIN(competition_name), 'stage_order', CAST(stage_order AS VARCHAR),
                       'Duplicate (competition_key, stage_order) in timeline_stages'
                FROM timeline_stages GROUP BY competition_key, stage_order HAVING COUNT(*) > 1
                """,
            )
        )

        # C11: Silver Referential Integrity (0 orphan children)
        results.append(
            _run_sql_rule(
                con,
                "C11",
                "Silver Referential Integrity (Zero Orphan Children)",
                "silver_table",
                "CRITICAL",
                n_prize + n_stage,
                """
                SELECT (
                    (SELECT COUNT(*) FROM prizes p LEFT JOIN competitions c ON p.competition_key = c.competition_key WHERE c.competition_key IS NULL)
                    + (SELECT COUNT(*) FROM timeline_stages t LEFT JOIN competitions c ON t.competition_key = c.competition_key WHERE c.competition_key IS NULL)
                )
                """,
                """
                SELECT p.competition_key, p.competition_name, 'prizes.competition_key', p.tier,
                       'Orphan prize row has no parent in competitions'
                FROM prizes p LEFT JOIN competitions c ON p.competition_key = c.competition_key
                WHERE c.competition_key IS NULL
                UNION ALL
                SELECT t.competition_key, t.competition_name, 'timeline_stages.competition_key', t.stage_name,
                       'Orphan timeline stage row has no parent in competitions'
                FROM timeline_stages t LEFT JOIN competitions c ON t.competition_key = c.competition_key
                WHERE c.competition_key IS NULL
                """,
            )
        )

        # C01..C07 DuckDB verification over physical Parquet/Arrow columns
        results.append(
            _run_sql_rule(
                con,
                "C01_SQL",
                "Parquet Not-Null & Hex Key Assertion",
                "silver_table",
                "CRITICAL",
                n_comp,
                """
                SELECT COUNT(*) FROM competitions
                WHERE competition_key IS NULL OR NOT regexp_matches(competition_key, '^[0-9a-f]{64}$')
                   OR name IS NULL OR TRIM(name) = ''
                   OR url IS NULL OR TRIM(url) = ''
                   OR summary IS NULL OR TRIM(summary) = ''
                """,
                """
                SELECT competition_key, name, 'core_columns', url,
                       'Null/blank required column or malformed competition_key in Parquet'
                FROM competitions
                WHERE competition_key IS NULL OR NOT regexp_matches(competition_key, '^[0-9a-f]{64}$')
                   OR name IS NULL OR TRIM(name) = ''
                   OR url IS NULL OR TRIM(url) = ''
                   OR summary IS NULL OR TRIM(summary) = ''
                """,
            )
        )

        agg_sql_list = ", ".join(f"'{h}'" for h in sorted(AGGREGATOR_HOSTS | SOCIAL_OR_FORM_HOSTS))
        results.append(
            _run_sql_rule(
                con,
                "C02_SQL",
                "Parquet Official HTTP(S) Host Assertion",
                "silver_table",
                "CRITICAL",
                n_comp,
                f"""
                SELECT COUNT(*) FROM competitions
                WHERE NOT regexp_matches(LOWER(COALESCE(url, '')), '^https?://[^/]+\\.[^/]+')
                   OR LOWER(COALESCE(url, '')) LIKE 'urn:%'
                   OR regexp_extract(LOWER(COALESCE(url, '')), '^https?://([^/:?#]+)', 1) IN ({agg_sql_list})
                """,
                f"""
                SELECT competition_key, name, 'url', url,
                       'Non-official, URN, aggregator, or social URL in Parquet'
                FROM competitions
                WHERE NOT regexp_matches(LOWER(COALESCE(url, '')), '^https?://[^/]+\\.[^/]+')
                   OR LOWER(COALESCE(url, '')) LIKE 'urn:%'
                   OR regexp_extract(LOWER(COALESCE(url, '')), '^https?://([^/:?#]+)', 1) IN ({agg_sql_list})
                """,
            )
        )

        results.append(
            _run_sql_rule(
                con,
                "C04_SQL",
                "Parquet Enum Domain Assertion",
                "silver_table",
                "CRITICAL",
                n_comp + n_prize,
                """
                SELECT (
                    (SELECT COUNT(*) FROM competitions WHERE mode NOT IN ('online','offline','hybrid','unknown')
                       OR registration_status NOT IN ('open','upcoming','closed','unknown')
                       OR eligibility_level NOT IN ('undergraduate','all_students','open','unknown'))
                    + (SELECT COUNT(*) FROM prizes WHERE currency NOT IN ('VND','USD','OTHER')
                       OR prize_type NOT IN ('cash','scholarship','credits','merch','mixed'))
                )
                """,
                """
                SELECT competition_key, name, 'enum', CONCAT(mode, '|', registration_status, '|', eligibility_level),
                       'Invalid competition enum value in Parquet'
                FROM competitions
                WHERE mode NOT IN ('online','offline','hybrid','unknown')
                   OR registration_status NOT IN ('open','upcoming','closed','unknown')
                   OR eligibility_level NOT IN ('undergraduate','all_students','open','unknown')
                UNION ALL
                SELECT competition_key, competition_name, 'prize_enum', CONCAT(currency, '|', prize_type),
                       'Invalid prize enum value in Parquet'
                FROM prizes
                WHERE currency NOT IN ('VND','USD','OTHER')
                   OR prize_type NOT IN ('cash','scholarship','credits','merch','mixed')
                """,
            )
        )

        results.append(
            _run_sql_rule(
                con,
                "C05_SQL",
                f"Parquet Temporal Window {min_year}-{max_year} Assertion",
                "silver_table",
                "CRITICAL",
                n_comp + n_stage,
                f"""
                SELECT (
                    (SELECT COUNT(*) FROM competitions WHERE
                       (registration_start_date IS NOT NULL AND YEAR(registration_start_date) NOT BETWEEN {min_year} AND {max_year})
                       OR (registration_deadline_date IS NOT NULL AND YEAR(registration_deadline_date) NOT BETWEEN {min_year} AND {max_year})
                       OR (event_start_date IS NOT NULL AND YEAR(event_start_date) NOT BETWEEN {min_year} AND {max_year})
                       OR (event_end_date IS NOT NULL AND YEAR(event_end_date) NOT BETWEEN {min_year} AND {max_year})
                       OR (team_registration_deadline_date IS NOT NULL AND YEAR(team_registration_deadline_date) NOT BETWEEN {min_year} AND {max_year}))
                    + (SELECT COUNT(*) FROM timeline_stages WHERE
                       (start_date_iso IS NOT NULL AND YEAR(start_date_iso) NOT BETWEEN {min_year} AND {max_year})
                       OR (end_date_iso IS NOT NULL AND YEAR(end_date_iso) NOT BETWEEN {min_year} AND {max_year}))
                )
                """,
            )
        )

        # W01..W05 Soft SLAs (never trip circuit breaker)
        results.append(
            _run_sql_rule(
                con,
                "W01",
                "Soft SLA - Missing Registration Deadline Date",
                "silver_table",
                "WARNING",
                n_comp,
                "SELECT COUNT(*) FROM competitions WHERE registration_deadline_date IS NULL",
                "SELECT competition_key, name, 'registration_deadline_date', NULL, 'Missing registration_deadline_date' FROM competitions WHERE registration_deadline_date IS NULL",
            )
        )
        results.append(
            _run_sql_rule(
                con,
                "W02",
                "Soft SLA - Unknown Eligibility or Mode",
                "silver_table",
                "WARNING",
                n_comp,
                "SELECT COUNT(*) FROM competitions WHERE eligibility_level = 'unknown' OR mode = 'unknown'",
                "SELECT competition_key, name, 'eligibility_level/mode', CONCAT(eligibility_level, '/', mode), 'E3 soft debt: unknown eligibility or mode' FROM competitions WHERE eligibility_level = 'unknown' OR mode = 'unknown'",
            )
        )
        results.append(
            _run_sql_rule(
                con,
                "W03",
                "Soft SLA - Missing Advisor or Rules Metadata",
                "silver_table",
                "WARNING",
                n_comp,
                "SELECT COUNT(*) FROM competitions WHERE official_rules_url IS NULL OR organizer_contact IS NULL",
                "SELECT competition_key, name, 'official_rules_url/contact', NULL, 'Optional rules URL or organizer contact missing' FROM competitions WHERE official_rules_url IS NULL OR organizer_contact IS NULL",
            )
        )
        results.append(
            _run_sql_rule(
                con,
                "W04",
                "Soft SLA - Missing Bronze Lineage Metadata",
                "silver_table",
                "WARNING",
                n_comp,
                "SELECT COUNT(*) FROM competitions WHERE bronze_key IS NULL OR source_url IS NULL",
                "SELECT competition_key, name, 'bronze_key/source_url', NULL, 'Missing Bronze lineage reference (acceptable in unit fixtures)' FROM competitions WHERE bronze_key IS NULL OR source_url IS NULL",
            )
        )
        results.append(
            _run_sql_rule(
                con,
                "W05",
                "Soft SLA - Unquantified Prize Pool",
                "silver_table",
                "WARNING",
                n_comp,
                """
                SELECT COUNT(*) FROM competitions c
                WHERE c.total_prize_vnd = 0
                  AND NOT EXISTS (SELECT 1 FROM prizes p WHERE p.competition_key = c.competition_key)
                """,
                """
                SELECT c.competition_key, c.name, 'total_prize_vnd', '0', 'No quantified cash prize or prize tiers'
                FROM competitions c
                WHERE c.total_prize_vnd = 0
                  AND NOT EXISTS (SELECT 1 FROM prizes p WHERE p.competition_key = c.competition_key)
                """,
            )
        )
        return results
    finally:
        con.close()


def validate_silver_to_gold_gate(
    con: duckdb.DuckDBPyConnection,
    expected_silver_count: int,
) -> list[RuleResult]:
    """Tier C: Validate Gold Star Schema parity and prize conservation before publishing."""
    c13 = _run_sql_rule(
        con,
        "C13",
        "Gold Pre-Publish Row Parity & Null Guard",
        "silver_to_gold",
        "CRITICAL",
        expected_silver_count,
        f"""
        SELECT
            (CASE WHEN (SELECT COUNT(*) FROM dim_competition) != {expected_silver_count} THEN 1 ELSE 0 END)
            + (CASE WHEN (SELECT COUNT(*) FROM fact_competitions) != {expected_silver_count} THEN 1 ELSE 0 END)
            + (CASE WHEN (SELECT COUNT(*) FROM mart_competition_explorer) != {expected_silver_count} THEN 1 ELSE 0 END)
            + (SELECT COUNT(*) FROM dim_competition WHERE canonical_url IS NULL OR TRIM(canonical_url) = '' OR name IS NULL OR TRIM(name) = '')
        """,
    )
    c14 = _run_sql_rule(
        con,
        "C14",
        "Gold Bridge Weight & Prize Conservation Invariant",
        "silver_to_gold",
        "CRITICAL",
        expected_silver_count,
        """
        SELECT (
            (SELECT COUNT(*) FROM (
                SELECT competition_sk FROM bridge_competition_domain
                GROUP BY competition_sk HAVING ABS(SUM(allocation_weight) - 1.0) > 0.001
            ))
            + (SELECT CASE WHEN ABS(
                (SELECT COALESCE(total_prize_pool_vnd, 0) FROM mart_kpi_overview LIMIT 1)
                - (SELECT COALESCE(SUM(allocated_prize_vnd), 0) FROM mart_domain_analytics)
            ) > 1.0 THEN 1 ELSE 0 END)
        )
        """,
    )
    return [c13, c14]


def _merge_hybrid_and_sql_rules(
    tier_a: list[RuleResult],
    tier_b: list[RuleResult],
    tier_c: list[RuleResult] | None = None,
) -> list[RuleResult]:
    """Merge Tier A Pydantic results with Tier B/C DuckDB SQL assertions without duplicating C01..C07."""
    sql_suffix_map = {r.rule_id.replace("_SQL", ""): r for r in tier_b if r.rule_id.endswith("_SQL")}
    merged: list[RuleResult] = []
    for r_a in tier_a:
        r_sql = sql_suffix_map.get(r_a.rule_id)
        if r_sql is not None and r_sql.failed_count > 0 and r_a.failed_count == 0:
            merged.append(
                r_a.model_copy(
                    update={
                        "engine": "hybrid",
                        "status": "FAIL",
                        "failed_count": r_sql.failed_count,
                        "duration_ms": round(r_a.duration_ms + r_sql.duration_ms, 3),
                        "sample_violations": r_sql.sample_violations,
                    }
                )
            )
        else:
            merged.append(
                r_a.model_copy(
                    update={
                        "engine": "hybrid" if r_sql is not None else r_a.engine,
                        "duration_ms": round(r_a.duration_ms + (r_sql.duration_ms if r_sql else 0.0), 3),
                    }
                )
            )
    for r_b in tier_b:
        if not r_b.rule_id.endswith("_SQL"):
            merged.append(r_b)
    if tier_c:
        merged.extend(tier_c)
    return merged


def _build_gate_report(
    gate_name: str,
    source_label: str,
    reference_year: int,
    record_counts: dict[str, int],
    rules: list[RuleResult],
    elapsed_ms: float,
) -> QualityGateReport:
    critical_failed = sum(1 for r in rules if r.severity == "CRITICAL" and r.status == "FAIL")
    warning_count = sum(1 for r in rules if r.severity == "WARNING" and r.failed_count > 0)
    rules_passed = sum(1 for r in rules if r.status == "PASS")
    if critical_failed > 0:
        overall: Literal["PASS", "PASS_WITH_WARNINGS", "FAIL"] = "FAIL"
    elif warning_count > 0:
        overall = "PASS_WITH_WARNINGS"
    else:
        overall = "PASS"

    return QualityGateReport(
        gate_name=gate_name,
        source_label=source_label,
        reference_year=reference_year,
        record_counts=record_counts,
        rules_total=len(rules),
        rules_passed=rules_passed,
        critical_failed=critical_failed,
        warning_count=warning_count,
        overall_status=overall,
        circuit_breaker_tripped=critical_failed > 0,
        elapsed_ms=round(elapsed_ms, 3),
        rules=rules,
    )


def run_silver_quality_gate(
    competitions: list[Competition] | list[dict[str, Any]],
    comp_table: pa.Table,
    prize_table: pa.Table,
    stage_table: pa.Table,
    *,
    gate_name: str = "Silver WAP Quality Gate",
    source_label: str = "silver_batch",
    reference_year: int = DEFAULT_REFERENCE_YEAR,
    min_records: int = 1,
    fail_fast: bool = True,
) -> QualityGateReport:
    """Execute Tier A (Pydantic) + Tier B (DuckDB SQL) Silver Quality Gate and trip on CRITICAL failures."""
    t0 = time.perf_counter()
    tier_a = validate_silver_records_pydantic(competitions, reference_year=reference_year)
    tier_b = validate_silver_tables_duckdb(
        comp_table=comp_table,
        prize_table=prize_table,
        stage_table=stage_table,
        reference_year=reference_year,
        min_records=min_records,
    )
    rules = _merge_hybrid_and_sql_rules(tier_a, tier_b)
    report = _build_gate_report(
        gate_name=gate_name,
        source_label=source_label,
        reference_year=reference_year,
        record_counts={
            "competitions": comp_table.num_rows,
            "prizes": prize_table.num_rows,
            "timeline_stages": stage_table.num_rows,
        },
        rules=rules,
        elapsed_ms=(time.perf_counter() - t0) * 1000,
    )
    if fail_fast and report.circuit_breaker_tripped:
        raise DataContractViolationError(report)
    return report


def _build_arrow_tables_from_raw_dicts(
    raw_comps: list[dict[str, Any]],
    extra_orphan_prizes: list[dict[str, Any]] | None = None,
    extra_orphan_stages: list[dict[str, Any]] | None = None,
) -> tuple[pa.Table, pa.Table, pa.Table]:
    """Build Silver Arrow tables preserving intentionally corrupted enum/date/key values for negative testing."""
    comp_schema = pa.schema(
        [
            pa.field("competition_key", pa.string(), nullable=True),
            pa.field("name", pa.string(), nullable=True),
            pa.field("url", pa.string(), nullable=True),
            pa.field("summary", pa.string(), nullable=True),
            pa.field("eligibility_level", pa.string(), nullable=True),
            pa.field("mode", pa.string(), nullable=True),
            pa.field("registration_status", pa.string(), nullable=True),
            pa.field("team_size_min", pa.int32(), nullable=True),
            pa.field("team_size_max", pa.int32(), nullable=True),
            pa.field("total_prize_vnd", pa.int64(), nullable=True),
            pa.field("registration_start_date", pa.date32(), nullable=True),
            pa.field("registration_deadline_date", pa.date32(), nullable=True),
            pa.field("event_start_date", pa.date32(), nullable=True),
            pa.field("event_end_date", pa.date32(), nullable=True),
            pa.field("team_registration_deadline_date", pa.date32(), nullable=True),
            pa.field("official_rules_url", pa.string(), nullable=True),
            pa.field("organizer_contact", pa.string(), nullable=True),
            pa.field("source_url", pa.string(), nullable=True),
            pa.field("bronze_key", pa.string(), nullable=True),
        ]
    )
    prize_schema = pa.schema(
        [
            pa.field("competition_key", pa.string(), nullable=True),
            pa.field("competition_name", pa.string(), nullable=True),
            pa.field("tier_rank", pa.int32(), nullable=True),
            pa.field("tier", pa.string(), nullable=True),
            pa.field("reward", pa.string(), nullable=True),
            pa.field("quantity", pa.int32(), nullable=True),
            pa.field("currency", pa.string(), nullable=True),
            pa.field("prize_type", pa.string(), nullable=True),
            pa.field("estimated_value_vnd", pa.int64(), nullable=True),
            pa.field("is_scholarship", pa.bool_(), nullable=True),
        ]
    )
    stage_schema = pa.schema(
        [
            pa.field("competition_key", pa.string(), nullable=True),
            pa.field("competition_name", pa.string(), nullable=True),
            pa.field("stage_order", pa.int32(), nullable=True),
            pa.field("stage_name", pa.string(), nullable=True),
            pa.field("start_date_iso", pa.date32(), nullable=True),
            pa.field("end_date_iso", pa.date32(), nullable=True),
        ]
    )

    comp_rows: list[dict[str, Any]] = []
    prize_rows: list[dict[str, Any]] = []
    stage_rows: list[dict[str, Any]] = []

    for c in raw_comps:
        url_val = c.get("url")
        name_val = c.get("name") or ""
        comp_key = c.get("competition_key")
        if comp_key is None and url_val:
            comp_key = compute_competition_key(normalize_canonical_url(str(url_val), str(name_val)))
        comp_rows.append(
            {
                "competition_key": comp_key,
                "name": c.get("name"),
                "url": url_val,
                "summary": c.get("summary"),
                "eligibility_level": c.get("eligibility_level", "unknown"),
                "mode": c.get("mode", "unknown"),
                "registration_status": c.get("registration_status", "unknown"),
                "team_size_min": c.get("team_size_min"),
                "team_size_max": c.get("team_size_max"),
                "total_prize_vnd": int(c.get("total_prize_vnd") or 0),
                "registration_start_date": parse_date_value(c.get("registration_start_date") or c.get("registration_start")),
                "registration_deadline_date": parse_date_value(c.get("registration_deadline_date") or c.get("registration_deadline")),
                "event_start_date": parse_date_value(c.get("event_start_date") or c.get("event_start")),
                "event_end_date": parse_date_value(c.get("event_end_date") or c.get("event_end")),
                "team_registration_deadline_date": parse_date_value(
                    c.get("team_registration_deadline_date") or c.get("team_registration_deadline")
                ),
                "official_rules_url": c.get("official_rules_url"),
                "organizer_contact": c.get("organizer_contact"),
                "source_url": c.get("source_url"),
                "bronze_key": c.get("bronze_key"),
            }
        )
        for idx, p in enumerate(c.get("prizes") or [], start=1):
            prize_rows.append(
                {
                    "competition_key": p.get("competition_key", comp_key),
                    "competition_name": name_val,
                    "tier_rank": p.get("tier_rank", idx),
                    "tier": p.get("tier"),
                    "reward": p.get("reward", ""),
                    "quantity": p.get("quantity", 1),
                    "currency": p.get("currency", "VND"),
                    "prize_type": p.get("prize_type", "cash"),
                    "estimated_value_vnd": int(p.get("estimated_value_vnd") or 0),
                    "is_scholarship": bool(p.get("is_scholarship", False)),
                }
            )
        for idx, st in enumerate(c.get("timeline_stages") or [], start=1):
            stage_rows.append(
                {
                    "competition_key": st.get("competition_key", comp_key),
                    "competition_name": name_val,
                    "stage_order": st.get("stage_order", idx),
                    "stage_name": st.get("stage_name"),
                    "start_date_iso": parse_date_value(st.get("start_date_iso") or st.get("start_date")),
                    "end_date_iso": parse_date_value(st.get("end_date_iso") or st.get("end_date")),
                }
            )

    for p in extra_orphan_prizes or []:
        prize_rows.append(
            {
                "competition_key": p.get("competition_key", "0" * 64),
                "competition_name": p.get("competition_name", "Orphan Contest"),
                "tier_rank": p.get("tier_rank", 1),
                "tier": p.get("tier", "Orphan Tier"),
                "reward": p.get("reward", "10M"),
                "quantity": p.get("quantity", 1),
                "currency": p.get("currency", "VND"),
                "prize_type": p.get("prize_type", "cash"),
                "estimated_value_vnd": int(p.get("estimated_value_vnd") or 10_000_000),
                "is_scholarship": bool(p.get("is_scholarship", False)),
            }
        )
    for st in extra_orphan_stages or []:
        stage_rows.append(
            {
                "competition_key": st.get("competition_key", "0" * 64),
                "competition_name": st.get("competition_name", "Orphan Contest"),
                "stage_order": st.get("stage_order", 1),
                "stage_name": st.get("stage_name", "Orphan Round"),
                "start_date_iso": parse_date_value(st.get("start_date_iso") or st.get("start_date")),
                "end_date_iso": parse_date_value(st.get("end_date_iso") or st.get("end_date")),
            }
        )

    return (
        pa.Table.from_pylist(comp_rows, schema=comp_schema),
        pa.Table.from_pylist(prize_rows, schema=prize_schema),
        pa.Table.from_pylist(stage_rows, schema=stage_schema),
    )


def _arrow_tables_to_raw_dicts(
    comp_table: pa.Table,
    prize_table: pa.Table,
    stage_table: pa.Table,
) -> list[dict[str, Any]]:
    """Reconstruct competition dicts with nested prizes & timeline_stages from Parquet tables."""
    prizes_by_key: dict[str, list[dict[str, Any]]] = {}
    for row in prize_table.to_pylist():
        prizes_by_key.setdefault(str(row.get("competition_key") or ""), []).append(row)
    stages_by_key: dict[str, list[dict[str, Any]]] = {}
    for row in stage_table.to_pylist():
        stages_by_key.setdefault(str(row.get("competition_key") or ""), []).append(row)

    records: list[dict[str, Any]] = []
    for row in comp_table.to_pylist():
        ckey = str(row.get("competition_key") or "")
        item = dict(row)
        item["prizes"] = prizes_by_key.get(ckey, [])
        item["timeline_stages"] = stages_by_key.get(ckey, [])
        records.append(item)
    return records


def audit_local_source(
    path: Path,
    *,
    reference_year: int = DEFAULT_REFERENCE_YEAR,
    fail_fast: bool = True,
) -> QualityGateReport:
    """Audit either a local Silver Parquet directory or a JSON batch fixture offline."""
    if not path.exists():
        raise FileNotFoundError(f"Audit source path does not exist: {path}")

    if path.is_dir():
        comp_table = pq.read_table(path / "competitions.parquet")
        prize_table = pq.read_table(path / "prizes.parquet")
        stage_table = pq.read_table(path / "timeline_stages.parquet")
        raw_records = _arrow_tables_to_raw_dicts(comp_table, prize_table, stage_table)
        return run_silver_quality_gate(
            raw_records,
            comp_table,
            prize_table,
            stage_table,
            gate_name="Local Silver Parquet Quality Gate",
            source_label=str(path),
            reference_year=reference_year,
            fail_fast=fail_fast,
        )

    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict) and "competitions" in payload:
        raw_comps = list(payload["competitions"])
        orphan_prizes = list(payload.get("extra_orphan_prizes") or [])
        orphan_stages = list(payload.get("extra_orphan_stages") or [])
    elif isinstance(payload, list):
        raw_comps = list(payload)
        orphan_prizes = []
        orphan_stages = []
    else:
        raise ValueError(f"Unsupported JSON fixture structure in {path}")

    comp_table, prize_table, stage_table = _build_arrow_tables_from_raw_dicts(
        raw_comps,
        extra_orphan_prizes=orphan_prizes,
        extra_orphan_stages=orphan_stages,
    )
    return run_silver_quality_gate(
        raw_comps,
        comp_table,
        prize_table,
        stage_table,
        gate_name="Local Fixture Data Contract Gate",
        source_label=str(path).replace("\\", "/"),
        reference_year=reference_year,
        fail_fast=fail_fast,
    )


def audit_r2_silver_and_gold(
    *,
    reference_year: int = DEFAULT_REFERENCE_YEAR,
    fail_fast: bool = False,
) -> QualityGateReport:
    """Perform non-destructive read-only audit of Silver and Gold Parquet tables on Cloudflare R2."""
    if not settings.bucket_name:
        raise RuntimeError("BUCKET_NAME is required in .env to audit Cloudflare R2.")
    t0 = time.perf_counter()
    bucket = settings.bucket_name.strip().strip("/")
    s3 = settings.create_r2_client()

    comp_raw = s3.get_object(Bucket=bucket, Key="silver/competitions.parquet")["Body"].read()
    prize_raw = s3.get_object(Bucket=bucket, Key="silver/prizes.parquet")["Body"].read()
    stage_raw = s3.get_object(Bucket=bucket, Key="silver/timeline_stages.parquet")["Body"].read()

    comp_table = pq.read_table(io.BytesIO(comp_raw))
    prize_table = pq.read_table(io.BytesIO(prize_raw))
    stage_table = pq.read_table(io.BytesIO(stage_raw))
    raw_records = _arrow_tables_to_raw_dicts(comp_table, prize_table, stage_table)

    tier_a = validate_silver_records_pydantic(raw_records, reference_year=reference_year)
    tier_b = validate_silver_tables_duckdb(
        comp_table,
        prize_table,
        stage_table,
        reference_year=reference_year,
        min_records=1,
    )

    con = duckdb.connect(":memory:")
    try:
        settings.configure_duckdb_r2(con)
        for entity in (
            "dim_competition",
            "fact_competitions",
            "mart_competition_explorer",
            "mart_kpi_overview",
            "mart_domain_analytics",
            "bridge_competition_domain",
        ):
            con.execute(f"CREATE OR REPLACE VIEW {entity} AS SELECT * FROM read_parquet('s3://{bucket}/gold/{entity}.parquet')")
        tier_c = validate_silver_to_gold_gate(con, expected_silver_count=comp_table.num_rows)
        gold_dim_cnt = int(con.execute("SELECT COUNT(*) FROM dim_competition").fetchone()[0])
    finally:
        con.close()

    rules = _merge_hybrid_and_sql_rules(tier_a, tier_b, tier_c)
    report = _build_gate_report(
        gate_name="Live Cloudflare R2 Silver+Gold Audit (Read-Only)",
        source_label=f"s3://{bucket}/silver+gold",
        reference_year=reference_year,
        record_counts={
            "silver_competitions": comp_table.num_rows,
            "silver_prizes": prize_table.num_rows,
            "silver_timeline_stages": stage_table.num_rows,
            "gold_dim_competition": gold_dim_cnt,
        },
        rules=rules,
        elapsed_ms=(time.perf_counter() - t0) * 1000,
    )
    if fail_fast and report.circuit_breaker_tripped:
        raise DataContractViolationError(report)
    return report


def run_cli_benchmark(sizes: tuple[int, ...] = (10, 24, 500)) -> dict[str, Any]:
    """Measure Tier A (Pydantic) vs Tier B (DuckDB SQL) latency across batch sizes."""
    results: list[dict[str, Any]] = []
    for n in sizes:
        comps = [
            Competition(
                name=f"Benchmark AI Challenge 2026 #{i}",
                url=f"https://ai-bench-{i}.edu.vn",
                summary="Cuộc thi Trí tuệ Nhân tạo và Khoa học Dữ liệu dành cho sinh viên đại học.",
                organizers=["HCM-UTE FIT"],
                category=["Artificial Intelligence", "Data Science"],
                mode="hybrid",
                eligibility_level="undergraduate",
                registration_status="open",
                registration_start="2026-09-01",
                registration_deadline="2026-10-15",
                event_start="2026-10-20",
                event_end="2026-11-20",
                team_size_min=1,
                team_size_max=4,
                total_prize_pool="50.000.000 VND",
            )
            for i in range(n)
        ]
        comp_rows = [
            {
                "competition_key": c.competition_key,
                "name": c.name,
                "url": c.url,
                "summary": c.summary,
                "eligibility_level": c.eligibility_level,
                "mode": c.mode,
                "registration_status": c.registration_status,
                "team_size_min": c.team_size_min,
                "team_size_max": c.team_size_max,
                "total_prize_vnd": 50_000_000,
                "registration_start_date": c.registration_start_date,
                "registration_deadline_date": c.registration_deadline_date,
                "event_start_date": c.event_start_date,
                "event_end_date": c.event_end_date,
                "team_registration_deadline_date": None,
                "official_rules_url": "https://ai-bench.edu.vn/rules.pdf",
                "organizer_contact": "contact@hcmute.edu.vn",
                "source_url": c.url,
                "bronze_key": f"bronze/ai-bench-{i}.edu.vn/year=2026/month=11/day=28/1795850000.html",
            }
            for i, c in enumerate(comps)
        ]
        comp_tbl, prize_tbl, stage_tbl = _build_arrow_tables_from_raw_dicts(comp_rows)

        t0 = time.perf_counter()
        validate_silver_records_pydantic(comps, reference_year=DEFAULT_REFERENCE_YEAR)
        tier_a_ms = (time.perf_counter() - t0) * 1000

        t1 = time.perf_counter()
        validate_silver_tables_duckdb(comp_tbl, prize_tbl, stage_tbl, reference_year=DEFAULT_REFERENCE_YEAR)
        tier_b_ms = (time.perf_counter() - t1) * 1000

        results.append(
            {
                "records": n,
                "tier_a_pydantic_ms": round(tier_a_ms, 2),
                "tier_b_duckdb_ms": round(tier_b_ms, 2),
                "total_ms": round(tier_a_ms + tier_b_ms, 2),
            }
        )
    return {"benchmark_sizes": list(sizes), "measurements": results}


def _save_report_json(report: QualityGateReport, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(report.model_dump_json(indent=2), encoding="utf-8")
    print(f"Saved quality gate report -> {path}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="ACDP v2 Data Contract & Quality Gate CLI (TASK-DQ-03)")
    parser.add_argument("--validate-odcs", action="store_true", help="Validate ODCS v3.2.0 YAML contract & rule sync")
    parser.add_argument("--audit-local", type=Path, default=None, help="Audit local Parquet dir or JSON fixture")
    parser.add_argument("--audit-r2", action="store_true", help="Read-only audit of live Cloudflare R2 Silver+Gold")
    parser.add_argument("--audit-fixtures", action="store_true", help="Run both valid and invalid DQ-03 fixtures")
    parser.add_argument("--benchmark", action="store_true", help="Measure Tier A vs Tier B validation latency")
    parser.add_argument("--reference-year", type=int, default=DEFAULT_REFERENCE_YEAR, help="Anchor year for [year-1, year+1]")
    parser.add_argument("--no-fail-fast", action="store_true", help="Return exit code 0 even if critical rules fail")
    parser.add_argument("--save-report", type=Path, default=None, help="Optional path to save JSON report")
    args = parser.parse_args(argv)

    if args.validate_odcs:
        res = validate_odcs_contract_sync()
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return 0

    if args.benchmark:
        bench = run_cli_benchmark()
        print(json.dumps(bench, ensure_ascii=False, indent=2))
        return 0

    if args.audit_fixtures:
        fixtures_dir = Path(__file__).resolve().parents[3] / "tests" / "fixtures" / "dq03"
        valid_rep = audit_local_source(fixtures_dir / "valid_silver_batch.json", reference_year=args.reference_year, fail_fast=False)
        invalid_rep = audit_local_source(fixtures_dir / "invalid_silver_batch.json", reference_year=args.reference_year, fail_fast=False)
        print(valid_rep.to_console_table())
        print(invalid_rep.to_console_table())
        return 0 if (not valid_rep.circuit_breaker_tripped and invalid_rep.circuit_breaker_tripped) else 1

    if args.audit_local is not None:
        report = audit_local_source(
            args.audit_local,
            reference_year=args.reference_year,
            fail_fast=False,
        )
        print(report.to_console_table())
        if args.save_report is not None:
            _save_report_json(report, args.save_report)
        if report.circuit_breaker_tripped and not args.no_fail_fast:
            print(f"[CIRCUIT BREAKER TRIPPED] Exiting with code 1 ({report.critical_failed} CRITICAL rule(s) failed).")
            return 1
        return 0

    if args.audit_r2:
        report = audit_r2_silver_and_gold(
            reference_year=args.reference_year,
            fail_fast=False,
        )
        print(report.to_console_table())
        if args.save_report is not None:
            _save_report_json(report, args.save_report)
        if report.circuit_breaker_tripped and not args.no_fail_fast:
            print(f"[CIRCUIT BREAKER TRIPPED] Exiting with code 1 ({report.critical_failed} CRITICAL rule(s) failed).")
            return 1
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
