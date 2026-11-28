"""TASK-DQ-02: Silver Layer Golden Dataset & Field-Level Accuracy Evaluation Harness (ACDP v2).

Evaluates the Hybrid Deterministic Sandwich + LLM Silver extraction pipeline against
a versioned, manually grounded Golden Dataset (`docs/experiments/data/silver-golden-dataset-v1.json`).

Implements 3-axis empirical verification:
1. Per-field Precision, Recall, F1, Exact Match (EM), and nullable TP/FP/FN/TN accounting
   across 3 criticality tiers (Tier 1 Critical, Tier 2 Operational, Tier 3 Nested/Advisor).
2. Deterministic Parser vs. Hybrid Silver Pipeline attribution on identical Bronze HTML inputs.
3. 5-Class Error Taxonomy (`E1_HTML_PARSER_NOISE`, `E2_DATE_NORMALIZER`,
   `E3_PROMPT_SCHEMA_DRIFT`, `E4_DYNAMIC_SPA_INCOMPLETE`, `E5_SEMANTIC_HALLUCINATION_OR_OMISSION`).
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import sys
from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any, Literal
from urllib.parse import urlparse

import pyarrow.parquet as pq
from pydantic import BaseModel, Field

from acdp.config import settings
from acdp.v2.schemas import normalize_canonical_url, parse_date_value
from acdp.v2.silver_transform import (
    extract_deterministic_signals,
    html_to_clean_markdown,
    is_html_payload,
    split_bronze_pages,
)

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

DEFAULT_GOLDEN_PATH = Path("docs/experiments/data/silver-golden-dataset-v1.json")

ErrorCategory = Literal[
    "E1_HTML_PARSER_NOISE",
    "E2_DATE_NORMALIZER",
    "E3_PROMPT_SCHEMA_DRIFT",
    "E4_DYNAMIC_SPA_INCOMPLETE",
    "E5_SEMANTIC_HALLUCINATION_OR_OMISSION",
]


class GoldenPrize(BaseModel):
    """Expected prize tier inside the Golden Dataset."""

    tier: str
    reward: str = ""
    estimated_value_vnd: float | None = None
    currency: str = "VND"


class GoldenStage(BaseModel):
    """Expected timeline stage inside the Golden Dataset."""

    stage_name: str
    start_date_iso: str | None = None
    end_date_iso: str | None = None


class GoldenGroundTruth(BaseModel):
    """Ground-truth fields covering Tier 1, Tier 2, and Tier 3 Silver attributes."""

    url: str | None = None
    registration_deadline_date: str | None = None
    event_start_date: str | None = None
    event_end_date: str | None = None
    total_prize_vnd: float | None = None
    total_prize_pool: str | None = None
    team_size_min: int | None = None
    team_size_max: int | None = None
    is_individual_allowed: bool | None = None
    name: str
    mode: str = "unknown"
    participation_fee: str | None = None
    organizers: list[str] = Field(default_factory=list)
    category: list[str] = Field(default_factory=list)
    eligibility_level: str = "unknown"
    target_audience: str | None = None
    prizes: list[GoldenPrize] = Field(default_factory=list)
    timeline_stages: list[GoldenStage] = Field(default_factory=list)
    official_rules_url: str | None = None
    organizer_contact: str | None = None
    requires_advisor: bool | None = None


class GoldenCase(BaseModel):
    """Single manually annotated competition record grounded against Bronze/Markdown."""

    case_id: str
    stratum: str
    domain: str
    bronze_key: str
    silver_markdown_key: str
    source_url: str
    expected_in_scope: bool = True
    ground_truth: GoldenGroundTruth
    evidence_snippets: dict[str, str] = Field(default_factory=dict)
    annotation_notes: str = ""


class GoldenDataset(BaseModel):
    """Versioned, hash-verified Golden Dataset contract."""

    dataset_version: str
    schema_version: str
    created_at: str
    scope: str
    annotators: list[str]
    annotation_guidelines: str
    content_sha256: str
    cases: list[GoldenCase]


@dataclass(frozen=True)
class FieldSpec:
    """Evaluation specification for one Silver schema field."""

    name: str
    tier: Literal["Tier 1: Critical", "Tier 2: Operational", "Tier 3: Nested & Advisor"]
    matcher: str
    target_f1: float
    target_em: float
    description: str


FIELD_SPECS: tuple[FieldSpec, ...] = (
    # Tier 1: Critical student-facing accuracy
    FieldSpec("url", "Tier 1: Critical", "exact_url", 0.90, 0.90, "Canonical official website URL"),
    FieldSpec("registration_deadline_date", "Tier 1: Critical", "exact_date", 0.90, 0.90, "ISO registration deadline"),
    FieldSpec("event_start_date", "Tier 1: Critical", "exact_date", 0.85, 0.85, "ISO event start date"),
    FieldSpec("event_end_date", "Tier 1: Critical", "exact_date", 0.85, 0.85, "ISO event end date"),
    FieldSpec("total_prize_vnd", "Tier 1: Critical", "numeric_tol_5pct", 0.85, 0.80, "Total prize pool in VND (±5%)"),
    FieldSpec("total_prize_pool", "Tier 1: Critical", "token_f1_065", 0.85, 0.60, "Published prize headline string"),
    FieldSpec("team_size_min", "Tier 1: Critical", "exact_int", 0.90, 0.90, "Minimum members per team"),
    FieldSpec("team_size_max", "Tier 1: Critical", "exact_int", 0.90, 0.90, "Maximum members per team"),
    FieldSpec("is_individual_allowed", "Tier 1: Critical", "exact_bool", 0.90, 0.90, "Individual participation flag"),
    # Tier 2: Operational filtering & matching
    FieldSpec("name", "Tier 2: Operational", "token_f1_085", 0.95, 0.80, "Official competition name"),
    FieldSpec("mode", "Tier 2: Operational", "exact_enum", 0.85, 0.85, "Delivery mode (online/offline/hybrid)"),
    FieldSpec("participation_fee", "Tier 2: Operational", "normalized_fee", 0.90, 0.90, "Free vs paid participation fee"),
    FieldSpec("organizers", "Tier 2: Operational", "set_f1", 0.80, 0.60, "Organizing institutions list"),
    FieldSpec("category", "Tier 2: Operational", "set_f1", 0.80, 0.40, "Technical domain tags"),
    FieldSpec("eligibility_level", "Tier 2: Operational", "exact_enum", 0.80, 0.80, "Structured eligibility level (G2)"),
    FieldSpec("target_audience", "Tier 2: Operational", "token_f1_055", 0.80, 0.30, "Target participant description"),
    # Tier 3: Nested arrays & Advisor screen fields (G4, G5, G8)
    FieldSpec("prizes", "Tier 3: Nested & Advisor", "bipartite_prizes", 0.80, 0.40, "Prize tiers array (Bipartite F1)"),
    FieldSpec("timeline_stages", "Tier 3: Nested & Advisor", "bipartite_stages", 0.80, 0.40, "Timeline stages array (Bipartite F1)"),
    FieldSpec("official_rules_url", "Tier 3: Nested & Advisor", "exact_url", 0.70, 0.70, "Official rules/handbook URL (G4)"),
    FieldSpec("organizer_contact", "Tier 3: Nested & Advisor", "exact_email", 0.70, 0.70, "Official organizer email (G4)"),
    FieldSpec("requires_advisor", "Tier 3: Nested & Advisor", "exact_bool", 0.70, 0.70, "Faculty advisor requirement (G4)"),
)


@dataclass
class FieldMetricSummary:
    """Precision, Recall, F1, Exact Match, and error counts for a single Silver field."""

    field: str
    tier: str
    matcher: str
    tp: int
    fp: int
    fn: int
    tn: int
    em_hits: int
    total_cases: int
    precision: float
    recall: float
    f1: float
    exact_match_rate: float
    target_f1: float
    target_em: float
    meets_f1_target: bool
    meets_em_target: bool


@dataclass
class ErrorInstance:
    """Single logged extraction mismatch attributed to one root-cause error class."""

    case_id: str
    domain: str
    field: str
    tier: str
    error_class: ErrorCategory
    gt_value: Any
    pred_value: Any
    det_value: Any
    note: str


@dataclass
class SilverEvaluationReport:
    """Complete TASK-DQ-02 evaluation report ready for JSON export and Markdown rendering."""

    evaluated_at_utc: str
    dataset_version: str
    dataset_sha256: str
    total_golden_cases: int
    total_silver_parquet_rows: int
    field_metrics: list[FieldMetricSummary]
    tier_summaries: dict[str, dict[str, float | int]]
    deterministic_vs_hybrid: list[dict[str, Any]]
    before_vs_after_postfix: dict[str, Any]
    error_taxonomy_counts: dict[str, int]
    error_instances: list[ErrorInstance] = field(default_factory=list)


def compute_cases_sha256(cases: list[dict[str, Any]] | list[GoldenCase]) -> str:
    """Compute canonical SHA-256 fingerprint over Golden Dataset cases."""
    serializable = [
        c.model_dump(mode="json") if isinstance(c, GoldenCase) else c
        for c in cases
    ]
    payload = json.dumps(serializable, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def load_golden_dataset(path: Path = DEFAULT_GOLDEN_PATH, *, verify_hash: bool = True) -> GoldenDataset:
    """Load and verify the versioned Golden Dataset JSON."""
    raw = json.loads(path.read_text(encoding="utf-8"))
    dataset = GoldenDataset.model_validate(raw)
    if verify_hash:
        expected_sha = compute_cases_sha256(raw["cases"])
        if dataset.content_sha256 != expected_sha:
            raise ValueError(
                f"Golden Dataset SHA-256 mismatch: expected {expected_sha}, found {dataset.content_sha256}"
            )
    return dataset


def _normalize_url_key(url: str | None) -> str | None:
    if not url or not str(url).strip():
        return None
    canon = normalize_canonical_url(str(url).strip())
    if canon.startswith("urn:acdp:"):
        return None
    parsed = urlparse(canon)
    host = parsed.netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    path = parsed.path.rstrip("/")
    query = f"?{parsed.query}" if parsed.query else ""
    return f"{host}{path}{query}"


def _normalize_date_str(val: Any) -> str | None:
    parsed = parse_date_value(val)
    return parsed.isoformat() if parsed else None


def _normalize_tokens(text: str) -> list[str]:
    expanded = re.sub(r"(\d+)\s*m\+?\b", r"\1 million", text.lower(), flags=re.IGNORECASE)
    expanded = re.sub(r"\b(?:hơn|over|trên)\b", "over", expanded)
    return re.findall(r"\w+", expanded, flags=re.UNICODE)


def _token_f1(a: str, b: str) -> float:
    toks_a = _normalize_tokens(a)
    toks_b = _normalize_tokens(b)
    if not toks_a and not toks_b:
        return 1.0
    if not toks_a or not toks_b:
        return 0.0
    common = sum((Counter(toks_a) & Counter(toks_b)).values())
    if common == 0:
        return 0.0
    p = common / len(toks_b)
    r = common / len(toks_a)
    return (2 * p * r) / (p + r)


def _norm_fee_bucket(val: Any) -> tuple[str, float | None] | None:
    if val is None or not str(val).strip():
        return None
    low = str(val).strip().lower()
    if any(k in low for k in ("miễn phí", "free", "0 đ", "0đ", "không thu phí")):
        return ("free", 0.0)
    digits = re.sub(r"[^\d]", "", low)
    amount = float(digits) if digits else None
    return ("paid", amount)


def _is_missing_field_value(field_name: str, val: Any) -> bool:
    if val is None:
        return True
    if isinstance(val, str):
        s = val.strip()
        if not s:
            return True
        if field_name in {"mode", "eligibility_level", "registration_status"} and s.lower() == "unknown":
            return True
        return False
    if isinstance(val, (list, tuple, dict)):
        return len(val) == 0
    if field_name == "total_prize_vnd":
        try:
            return float(val) <= 0.0
        except (TypeError, ValueError):
            return True
    return False


def _items_similar(a: str, b: str) -> bool:
    na = " ".join(_normalize_tokens(a))
    nb = " ".join(_normalize_tokens(b))
    if not na or not nb:
        return False
    if na == nb or na in nb or nb in na:
        return True
    return _token_f1(a, b) >= 0.60


def _score_set_list(gt_list: list[str], pred_list: list[str]) -> tuple[bool, bool, float]:
    """Compare string lists using case-folded substring/token bipartite matching."""
    if not gt_list and not pred_list:
        return True, True, 1.0
    if not gt_list or not pred_list:
        return False, False, 0.0

    matched_pred: set[int] = set()
    tp = 0
    for g in gt_list:
        for idx, p in enumerate(pred_list):
            if idx in matched_pred:
                continue
            if _items_similar(g, p):
                matched_pred.add(idx)
                tp += 1
                break
    prec = tp / len(pred_list)
    rec = tp / len(gt_list)
    f1 = (2 * prec * rec) / (prec + rec) if (prec + rec) > 0 else 0.0
    exact = tp == len(gt_list) == len(pred_list)
    return f1 >= 0.65, exact, f1


def _prize_similarity(gt_p: dict[str, Any], pred_p: dict[str, Any]) -> float:
    tier_sim = _token_f1(str(gt_p.get("tier") or ""), str(pred_p.get("tier") or ""))
    gt_val = gt_p.get("estimated_value_vnd")
    pred_val = pred_p.get("estimated_value_vnd")
    if gt_val and pred_val and float(gt_val) > 0:
        rel = abs(float(pred_val) - float(gt_val)) / float(gt_val)
        val_sim = 1.0 if rel <= 0.05 else max(0.0, 1.0 - rel)
        return 0.6 * tier_sim + 0.4 * val_sim
    rew_sim = _token_f1(str(gt_p.get("reward") or ""), str(pred_p.get("reward") or ""))
    return 0.7 * tier_sim + 0.3 * rew_sim


def _stage_similarity(gt_s: dict[str, Any], pred_s: dict[str, Any]) -> float:
    name_sim = _token_f1(str(gt_s.get("stage_name") or ""), str(pred_s.get("stage_name") or ""))
    gt_start = _normalize_date_str(gt_s.get("start_date_iso"))
    pred_start = _normalize_date_str(pred_s.get("start_date_iso"))
    gt_end = _normalize_date_str(gt_s.get("end_date_iso"))
    pred_end = _normalize_date_str(pred_s.get("end_date_iso"))

    date_checks = 0
    date_hits = 0
    if gt_start or pred_start:
        date_checks += 1
        if gt_start == pred_start:
            date_hits += 1
    if gt_end or pred_end:
        date_checks += 1
        if gt_end == pred_end:
            date_hits += 1

    if date_checks == 0:
        return name_sim
    date_sim = date_hits / date_checks
    return 0.55 * name_sim + 0.45 * date_sim


def score_bipartite_array(
    gt_items: list[dict[str, Any]],
    pred_items: list[dict[str, Any]],
    sim_fn: Any,
    threshold: float = 0.55,
) -> tuple[int, int, int, bool]:
    """Order-insensitive greedy bipartite matching returning (tp, fp, fn, case_exact)."""
    if not gt_items and not pred_items:
        return 0, 0, 0, True

    candidates: list[tuple[float, int, int]] = []
    for gi, g in enumerate(gt_items):
        for pi, p in enumerate(pred_items):
            sim = float(sim_fn(g, p))
            if sim >= threshold:
                candidates.append((sim, gi, pi))
    candidates.sort(key=lambda x: x[0], reverse=True)

    used_g: set[int] = set()
    used_p: set[int] = set()
    tp = 0
    for _sim, gi, pi in candidates:
        if gi in used_g or pi in used_p:
            continue
        used_g.add(gi)
        used_p.add(pi)
        tp += 1

    fp = len(pred_items) - tp
    fn = len(gt_items) - tp
    case_exact = fp == 0 and fn == 0
    return tp, fp, fn, case_exact


def compare_scalar_field(spec: FieldSpec, gt_val: Any, pred_val: Any) -> tuple[bool, bool]:
    """Return (is_match, is_exact_match) for two non-missing scalar/list field values."""
    m = spec.matcher
    if m == "exact_url":
        ng = _normalize_url_key(gt_val)
        np_ = _normalize_url_key(pred_val)
        ok = bool(ng and np_ and ng == np_)
        return ok, ok
    if m == "exact_date":
        dg = _normalize_date_str(gt_val)
        dp = _normalize_date_str(pred_val)
        ok = bool(dg and dp and dg == dp)
        return ok, ok
    if m == "exact_int":
        try:
            ok = int(gt_val) == int(pred_val)
            return ok, ok
        except (TypeError, ValueError):
            return False, False
    if m == "exact_bool":
        ok = bool(gt_val) is bool(pred_val)
        return ok, ok
    if m == "exact_enum":
        ok = str(gt_val).strip().lower() == str(pred_val).strip().lower()
        return ok, ok
    if m == "exact_email":
        ok = str(gt_val).strip().lower() == str(pred_val).strip().lower()
        return ok, ok
    if m == "numeric_tol_5pct":
        try:
            gv = float(gt_val)
            pv = float(pred_val)
            if gv <= 0:
                return False, False
            rel = abs(pv - gv) / gv
            return rel <= 0.05, abs(pv - gv) < 1.0
        except (TypeError, ValueError):
            return False, False
    if m == "normalized_fee":
        fg = _norm_fee_bucket(gt_val)
        fp_ = _norm_fee_bucket(pred_val)
        ok = bool(fg and fp_ and fg == fp_)
        return ok, ok
    if m.startswith("token_f1_"):
        thresh = int(m.split("_")[-1]) / 100.0
        sg = " ".join(str(gt_val).strip().split())
        sp = " ".join(str(pred_val).strip().split())
        exact = sg.lower() == sp.lower()
        f1 = _token_f1(sg, sp)
        return f1 >= thresh, exact
    if m == "set_f1":
        ok, exact, _ = _score_set_list(list(gt_val or []), list(pred_val or []))
        return ok, exact
    ok = gt_val == pred_val
    return ok, ok


def classify_error_cause(
    case: GoldenCase,
    field_name: str,
    gt_val: Any,
    pred_val: Any,
    pred_record: dict[str, Any],
    det_signals: dict[str, Any],
) -> tuple[ErrorCategory, str]:
    """Attribute a field-level mismatch to one of the 5 structured Error Taxonomy classes."""
    if field_name == "url":
        if not case.expected_in_scope or gt_val is None:
            return (
                "E1_HTML_PARSER_NOISE",
                f"Aggregator/media post lacked official site, yet HTML link scorer picked '{pred_val}'.",
            )
        return (
            "E1_HTML_PARSER_NOISE",
            f"HTML link scorer selected '{pred_val}' (likely header/nav/sidebar link) instead of '{gt_val}'.",
        )

    if field_name == "official_rules_url":
        if gt_val is None and pred_val:
            return (
                "E1_HTML_PARSER_NOISE",
                f"Parser captured unrelated header/footer PDF '{pred_val}'.",
            )
        return (
            "E5_SEMANTIC_HALLUCINATION_OR_OMISSION",
            f"Rules link '{gt_val}' present in HTML/nav was omitted (pred={pred_val}).",
        )

    if field_name.endswith("_date"):
        raw_field = field_name[: -len("_date")]
        raw_val = pred_record.get(raw_field)
        if raw_val and pred_val is None:
            return (
                "E2_DATE_NORMALIZER",
                f"Raw date '{raw_val}' extracted by LLM, but persisted Silver ISO field '{field_name}' is None.",
            )
        if case.domain in {"codetour.org", "ybox.vn"} and (gt_val is None or pred_val != gt_val):
            if case.domain == "ybox.vn":
                return (
                    "E5_SEMANTIC_HALLUCINATION_OR_OMISSION",
                    f"40KB noisy social feed pushed real event date past 16KB prompt truncation; LLM hallucinated '{pred_val}'.",
                )
            return (
                "E4_DYNAMIC_SPA_INCOMPLETE",
                f"SPA DOM did not expose date cleanly (gt={gt_val}, pred={pred_val}).",
            )
        return (
            "E5_SEMANTIC_HALLUCINATION_OR_OMISSION",
            f"Date mismatch or omission on '{field_name}' (gt={gt_val}, pred={pred_val}).",
        )

    if field_name in {"eligibility_level", "requires_advisor", "organizer_contact"}:
        if _is_missing_field_value(field_name, pred_val):
            return (
                "E3_PROMPT_SCHEMA_DRIFT",
                f"R2 Silver JSON snapshot predates Schema v2 prompt fields ({field_name}={pred_val!r}).",
            )
        return (
            "E5_SEMANTIC_HALLUCINATION_OR_OMISSION",
            f"Schema v2 field mismatch (gt={gt_val}, pred={pred_val}).",
        )

    if field_name in {"team_size_min", "team_size_max", "is_individual_allowed"} and case.domain == "www.vietnamaichallenge.com":
        return (
            "E4_DYNAMIC_SPA_INCOMPLETE",
            "FAQ accordion collapsed team-size answer in rendered DOM.",
        )

    if case.domain == "ybox.vn" and field_name in {"total_prize_vnd", "total_prize_pool", "prizes", "timeline_stages"}:
        return (
            "E5_SEMANTIC_HALLUCINATION_OR_OMISSION",
            f"Prompt truncation at 16KB due to ybox feed noise caused hallucinated/mismatched '{field_name}'.",
        )

    if field_name in {"total_prize_vnd", "total_prize_pool"} and pred_record.get("prizes"):
        return (
            "E5_SEMANTIC_HALLUCINATION_OR_OMISSION",
            f"Prize tiers present, but total VND/pool miscomputed or omitted (gt={gt_val}, pred={pred_val}; det_prizes={det_signals.get('detected_prizes')}).",
        )

    return (
        "E5_SEMANTIC_HALLUCINATION_OR_OMISSION",
        f"Semantic extraction error on '{field_name}' (gt={gt_val!r}, pred={pred_val!r}).",
    )


def _compute_prf(tp: int, fp: int, fn: int) -> tuple[float, float, float]:
    prec = round(tp / (tp + fp), 4) if (tp + fp) > 0 else (1.0 if fn == 0 else 0.0)
    rec = round(tp / (tp + fn), 4) if (tp + fn) > 0 else (1.0 if fp == 0 else 0.0)
    f1 = round((2 * prec * rec) / (prec + rec), 4) if (prec + rec) > 0 else 0.0
    return prec, rec, f1


def evaluate_predictions(
    dataset: GoldenDataset,
    predictions_by_bronze_key: dict[str, dict[str, Any]],
    det_signals_by_bronze_key: dict[str, dict[str, Any]] | None = None,
    *,
    total_silver_rows: int = 0,
    postfix_sim: dict[str, Any] | None = None,
) -> SilverEvaluationReport:
    """Evaluate Silver records against the Golden Dataset across all 21 fields."""
    det_map = det_signals_by_bronze_key or {}
    field_metrics: list[FieldMetricSummary] = []
    error_instances: list[ErrorInstance] = []
    err_counter: Counter[str] = Counter()

    for spec in FIELD_SPECS:
        tp = fp = fn = tn = em_hits = 0
        total_cases = len(dataset.cases)

        for case in dataset.cases:
            gt_dict = case.ground_truth.model_dump(mode="json")
            pred_rec = predictions_by_bronze_key.get(case.bronze_key, {})
            det_sig = det_map.get(case.bronze_key, {})
            gt_val = gt_dict.get(spec.name)
            pred_val = pred_rec.get(spec.name)

            if spec.matcher in {"bipartite_prizes", "bipartite_stages"}:
                sim_fn = _prize_similarity if spec.matcher == "bipartite_prizes" else _stage_similarity
                gt_items = list(gt_val or [])
                pred_items = list(pred_val or [])
                c_tp, c_fp, c_fn, c_exact = score_bipartite_array(gt_items, pred_items, sim_fn)
                tp += c_tp
                fp += c_fp
                fn += c_fn
                if not gt_items and not pred_items:
                    tn += 1
                if c_exact:
                    em_hits += 1
                else:
                    e_cls, e_note = classify_error_cause(case, spec.name, gt_items, pred_items, pred_rec, det_sig)
                    err_counter[e_cls] += 1
                    error_instances.append(
                        ErrorInstance(
                            case_id=case.case_id,
                            domain=case.domain,
                            field=spec.name,
                            tier=spec.tier,
                            error_class=e_cls,
                            gt_value=f"{len(gt_items)} items",
                            pred_value=f"{len(pred_items)} items (tp={c_tp}, fp={c_fp}, fn={c_fn})",
                            det_value=None,
                            note=e_note,
                        )
                    )
                continue

            gt_miss = _is_missing_field_value(spec.name, gt_val)
            pred_miss = _is_missing_field_value(spec.name, pred_val)

            if gt_miss and pred_miss:
                tn += 1
                em_hits += 1
            elif gt_miss and not pred_miss:
                fp += 1
                e_cls, e_note = classify_error_cause(case, spec.name, gt_val, pred_val, pred_rec, det_sig)
                err_counter[e_cls] += 1
                error_instances.append(
                    ErrorInstance(
                        case_id=case.case_id,
                        domain=case.domain,
                        field=spec.name,
                        tier=spec.tier,
                        error_class=e_cls,
                        gt_value=gt_val,
                        pred_value=pred_val,
                        det_value=det_sig.get(spec.name),
                        note=e_note,
                    )
                )
            elif not gt_miss and pred_miss:
                fn += 1
                e_cls, e_note = classify_error_cause(case, spec.name, gt_val, pred_val, pred_rec, det_sig)
                err_counter[e_cls] += 1
                error_instances.append(
                    ErrorInstance(
                        case_id=case.case_id,
                        domain=case.domain,
                        field=spec.name,
                        tier=spec.tier,
                        error_class=e_cls,
                        gt_value=gt_val,
                        pred_value=pred_val,
                        det_value=det_sig.get(spec.name),
                        note=e_note,
                    )
                )
            else:
                matched, exact = compare_scalar_field(spec, gt_val, pred_val)
                if matched:
                    tp += 1
                    if exact:
                        em_hits += 1
                else:
                    fp += 1
                    fn += 1
                    e_cls, e_note = classify_error_cause(case, spec.name, gt_val, pred_val, pred_rec, det_sig)
                    err_counter[e_cls] += 1
                    error_instances.append(
                        ErrorInstance(
                            case_id=case.case_id,
                            domain=case.domain,
                            field=spec.name,
                            tier=spec.tier,
                            error_class=e_cls,
                            gt_value=gt_val,
                            pred_value=pred_val,
                            det_value=det_sig.get(spec.name),
                            note=e_note,
                        )
                    )

        prec, rec, f1 = _compute_prf(tp, fp, fn)
        em_rate = round(em_hits / total_cases, 4) if total_cases > 0 else 0.0
        field_metrics.append(
            FieldMetricSummary(
                field=spec.name,
                tier=spec.tier,
                matcher=spec.matcher,
                tp=tp,
                fp=fp,
                fn=fn,
                tn=tn,
                em_hits=em_hits,
                total_cases=total_cases,
                precision=prec,
                recall=rec,
                f1=f1,
                exact_match_rate=em_rate,
                target_f1=spec.target_f1,
                target_em=spec.target_em,
                meets_f1_target=f1 >= spec.target_f1,
                meets_em_target=em_rate >= spec.target_em,
            )
        )

    tier_summaries: dict[str, dict[str, float | int]] = {}
    for tier_name in ("Tier 1: Critical", "Tier 2: Operational", "Tier 3: Nested & Advisor"):
        t_rows = [m for m in field_metrics if m.tier == tier_name]
        t_tp = sum(m.tp for m in t_rows)
        t_fp = sum(m.fp for m in t_rows)
        t_fn = sum(m.fn for m in t_rows)
        t_prec, t_rec, t_f1 = _compute_prf(t_tp, t_fp, t_fn)
        t_em = round(sum(m.exact_match_rate for m in t_rows) / len(t_rows), 4) if t_rows else 0.0
        tier_summaries[tier_name] = {
            "field_count": len(t_rows),
            "micro_precision": t_prec,
            "micro_recall": t_rec,
            "micro_f1": t_f1,
            "macro_em": t_em,
            "fields_meeting_f1_target": sum(1 for m in t_rows if m.meets_f1_target),
        }

    det_vs_hybrid = evaluate_deterministic_vs_hybrid(dataset, predictions_by_bronze_key, det_map, field_metrics)

    return SilverEvaluationReport(
        evaluated_at_utc=datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        dataset_version=dataset.dataset_version,
        dataset_sha256=dataset.content_sha256,
        total_golden_cases=len(dataset.cases),
        total_silver_parquet_rows=total_silver_rows,
        field_metrics=field_metrics,
        tier_summaries=tier_summaries,
        deterministic_vs_hybrid=det_vs_hybrid,
        before_vs_after_postfix=postfix_sim or {},
        error_taxonomy_counts=dict(sorted(err_counter.items())),
        error_instances=error_instances,
    )


def evaluate_deterministic_vs_hybrid(
    dataset: GoldenDataset,
    predictions_by_bronze_key: dict[str, dict[str, Any]],
    det_map: dict[str, dict[str, Any]],
    hybrid_metrics: list[FieldMetricSummary],
) -> list[dict[str, Any]]:
    """Compare pure Deterministic Parser vs Hybrid Silver Pipeline on shared fields."""
    hybrid_by_field = {m.field: m for m in hybrid_metrics}
    shared_fields = [
        ("url", "exact_url"),
        ("mode", "exact_enum"),
        ("participation_fee", "normalized_fee"),
        ("team_size_min", "exact_int"),
        ("team_size_max", "exact_int"),
        ("official_rules_url", "exact_url"),
        ("registration_deadline_date", "det_date_presence"),
    ]
    rows: list[dict[str, Any]] = []
    for field_name, _matcher_kind in shared_fields:
        tp = fp = fn = tn = em = 0
        for case in dataset.cases:
            gt_val = case.ground_truth.model_dump(mode="json").get(field_name)
            det_sig = det_map.get(case.bronze_key, {})
            if field_name == "registration_deadline_date":
                det_dates = {_normalize_date_str(d) for d in (det_sig.get("detected_dates") or [])}
                det_dates.discard(None)
                gt_d = _normalize_date_str(gt_val)
                if gt_d is None:
                    tn += 1
                    em += 1
                elif gt_d in det_dates:
                    tp += 1
                    em += 1
                else:
                    fn += 1
                continue

            det_val = det_sig.get(field_name)
            gt_miss = _is_missing_field_value(field_name, gt_val)
            det_miss = _is_missing_field_value(field_name, det_val)
            if gt_miss and det_miss:
                tn += 1
                em += 1
            elif gt_miss and not det_miss:
                fp += 1
            elif not gt_miss and det_miss:
                fn += 1
            else:
                spec = next(s for s in FIELD_SPECS if s.name == field_name)
                matched, exact = compare_scalar_field(spec, gt_val, det_val)
                if matched:
                    tp += 1
                    if exact:
                        em += 1
                else:
                    fp += 1
                    fn += 1

        dp, dr, df1 = _compute_prf(tp, fp, fn)
        dem = round(em / len(dataset.cases), 4) if dataset.cases else 0.0
        hm = hybrid_by_field[field_name]
        rows.append(
            {
                "field": field_name,
                "det_precision": dp,
                "det_recall": dr,
                "det_f1": df1,
                "det_em": dem,
                "hybrid_precision": hm.precision,
                "hybrid_recall": hm.recall,
                "hybrid_f1": hm.f1,
                "hybrid_em": hm.exact_match_rate,
                "f1_delta_hybrid_minus_det": round(hm.f1 - df1, 4),
            }
        )
    return rows


def _extract_det_dict_from_bronze(bronze_key: str, domain: str, raw_html: str) -> dict[str, Any]:
    is_html = is_html_payload(raw_html, "html" if bronze_key.endswith(".html") else "markdown")
    pages = split_bronze_pages(raw_html, domain) if is_html else [(f"https://{domain}/", raw_html)]
    clean_md = html_to_clean_markdown(pages) if is_html else raw_html
    sig = extract_deterministic_signals(pages=pages, clean_md=clean_md, source_domain=domain, is_html=is_html)
    return {
        "url": sig.canonical_official_url or None,
        "mode": sig.detected_mode,
        "participation_fee": sig.detected_fee,
        "team_size_min": sig.detected_team_bounds[0],
        "team_size_max": sig.detected_team_bounds[1],
        "official_rules_url": sig.official_rules_urls[0] if sig.official_rules_urls else None,
        "detected_dates": sig.detected_dates,
        "detected_prizes": sig.detected_prizes,
    }


def evaluate_from_r2(
    dataset_path: Path = DEFAULT_GOLDEN_PATH,
    s3_client: Any | None = None,
    bucket_name: str | None = None,
) -> SilverEvaluationReport:
    """Load Golden Dataset and evaluate live Cloudflare R2 Bronze + Silver Parquet."""
    dataset = load_golden_dataset(dataset_path)
    client = s3_client or settings.create_r2_client()
    bucket = bucket_name or settings.bucket_name

    comp_rows = pq.read_table(io.BytesIO(client.get_object(Bucket=bucket, Key="silver/competitions.parquet")["Body"].read())).to_pylist()
    prize_rows = pq.read_table(io.BytesIO(client.get_object(Bucket=bucket, Key="silver/prizes.parquet")["Body"].read())).to_pylist()
    stage_rows = pq.read_table(io.BytesIO(client.get_object(Bucket=bucket, Key="silver/timeline_stages.parquet")["Body"].read())).to_pylist()

    prizes_by_ck: dict[str, list[dict[str, Any]]] = {}
    for p in prize_rows:
        prizes_by_ck.setdefault(str(p.get("competition_key")), []).append(p)
    stages_by_ck: dict[str, list[dict[str, Any]]] = {}
    for s in stage_rows:
        stages_by_ck.setdefault(str(s.get("competition_key")), []).append(
            {k: (v.isoformat() if isinstance(v, (date, datetime)) else v) for k, v in s.items()}
        )

    pred_by_bk: dict[str, dict[str, Any]] = {}
    for r in comp_rows:
        bk = str(r.get("bronze_key") or "")
        ck = str(r.get("competition_key") or "")
        norm_row = {k: (v.isoformat() if isinstance(v, (date, datetime)) else v) for k, v in r.items()}
        norm_row["prizes"] = prizes_by_ck.get(ck, [])
        norm_row["timeline_stages"] = stages_by_ck.get(ck, [])
        pred_by_bk[bk] = norm_row

    det_by_bk: dict[str, dict[str, Any]] = {}
    for case in dataset.cases:
        raw_html = client.get_object(Bucket=bucket, Key=case.bronze_key)["Body"].read().decode("utf-8", errors="replace")
        det_by_bk[case.bronze_key] = _extract_det_dict_from_bronze(case.bronze_key, case.domain, raw_html)

    # Simulate Option A deterministic date re-parsing & updated link resolver without mutating R2
    postfix_preds: dict[str, dict[str, Any]] = {}
    for bk, rec in pred_by_bk.items():
        cloned = dict(rec)
        for df in ("registration_deadline", "event_start", "event_end", "team_registration_deadline"):
            iso_key = f"{df}_date"
            if cloned.get(iso_key) is None and cloned.get(df):
                parsed = parse_date_value(cloned[df])
                if parsed:
                    cloned[iso_key] = parsed.isoformat()
        postfix_preds[bk] = cloned

    report = evaluate_predictions(
        dataset=dataset,
        predictions_by_bronze_key=pred_by_bk,
        det_signals_by_bronze_key=det_by_bk,
        total_silver_rows=len(comp_rows),
    )

    # Compare deterministic date re-parse & updated link extraction vs baseline
    postfix_report = evaluate_predictions(
        dataset=dataset,
        predictions_by_bronze_key=postfix_preds,
        det_signals_by_bronze_key=det_by_bk,
        total_silver_rows=len(comp_rows),
    )
    baseline_by_f = {m.field: m for m in report.field_metrics}
    postfix_by_f = {m.field: m for m in postfix_report.field_metrics}
    det_by_f = {d["field"]: d for d in postfix_report.deterministic_vs_hybrid}

    report.before_vs_after_postfix = {
        "registration_deadline_date_hybrid": {
            "before_f1": baseline_by_f["registration_deadline_date"].f1,
            "before_em": baseline_by_f["registration_deadline_date"].exact_match_rate,
            "after_f1": postfix_by_f["registration_deadline_date"].f1,
            "after_em": postfix_by_f["registration_deadline_date"].exact_match_rate,
        },
        "deterministic_url": {
            "f1": det_by_f["url"]["det_f1"],
            "em": det_by_f["url"]["det_em"],
            "precision": det_by_f["url"]["det_precision"],
            "recall": det_by_f["url"]["det_recall"],
        },
        "deterministic_official_rules_url": {
            "f1": det_by_f["official_rules_url"]["det_f1"],
            "em": det_by_f["official_rules_url"]["det_em"],
            "precision": det_by_f["official_rules_url"]["det_precision"],
            "recall": det_by_f["official_rules_url"]["det_recall"],
        },
    }
    return report


def _save_report_to_r2(s3_client: Any, bucket_name: str, report: SilverEvaluationReport) -> str:
    ts = int(datetime.now(UTC).timestamp())
    key = f"silver/_validation/dq02_eval_{ts}.json"
    s3_client.put_object(
        Bucket=bucket_name,
        Key=key,
        Body=json.dumps(asdict(report), ensure_ascii=False, indent=2).encode("utf-8"),
        ContentType="application/json; charset=utf-8",
        Metadata={"layer": "silver", "task": "TASK-DQ-02", "dataset_version": report.dataset_version},
    )
    return key


def print_report_summary(report: SilverEvaluationReport) -> None:
    print("================ SILVER GOLDEN DATASET EVALUATION (TASK-DQ-02) ================")
    print(f"Dataset Version : {report.dataset_version} (sha256={report.dataset_sha256[:16]}...)")
    print(f"Golden Cases    : {report.total_golden_cases} | Live Silver Parquet Rows: {report.total_silver_parquet_rows}")
    print("-" * 79)
    print(f"{'Field':<28} {'Tier':<12} {'P':>6} {'R':>6} {'F1':>6} {'EM':>6} {'TP/FP/FN/TN':>13} {'Gate':>6}")
    print("-" * 79)
    for m in report.field_metrics:
        tier_short = m.tier.split(":")[0]
        counts = f"{m.tp}/{m.fp}/{m.fn}/{m.tn}"
        gate = "PASS" if m.meets_f1_target else "GAP"
        print(
            f"{m.field:<28} {tier_short:<12} {m.precision:>6.2f} {m.recall:>6.2f} "
            f"{m.f1:>6.2f} {m.exact_match_rate:>6.2f} {counts:>13} {gate:>6}"
        )
    print("-" * 79)
    for tier_name, stats in report.tier_summaries.items():
        print(
            f"{tier_name:<25} -> Micro P={stats['micro_precision']:.3f} R={stats['micro_recall']:.3f} "
            f"F1={stats['micro_f1']:.3f} | Macro EM={stats['macro_em']:.3f} "
            f"| Target Pass: {stats['fields_meeting_f1_target']}/{stats['field_count']}"
        )
    print("-" * 79)
    print("Error Taxonomy Counts:", json.dumps(report.error_taxonomy_counts, ensure_ascii=False))
    if report.before_vs_after_postfix:
        print("Deterministic / Post-Fix Snapshot:", json.dumps(report.before_vs_after_postfix, ensure_ascii=False))
    print("===============================================================================")


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="ACDP v2 Silver Golden Dataset Evaluation CLI (TASK-DQ-02)")
    parser.add_argument("--evaluate-r2", action="store_true", help="Evaluate live Cloudflare R2 Bronze + Silver Parquet.")
    parser.add_argument("--dataset", type=Path, default=DEFAULT_GOLDEN_PATH, help="Path to Golden Dataset JSON.")
    parser.add_argument("--save-json", type=Path, default=None, help="Save structured evaluation report JSON locally.")
    parser.add_argument("--save-r2-report", action="store_true", help="Upload evaluation report JSON to silver/_validation/.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    if not args.evaluate_r2:
        print("Specify --evaluate-r2 to execute Golden Dataset evaluation against Cloudflare R2.")
        return 1

    report = evaluate_from_r2(dataset_path=args.dataset)
    print_report_summary(report)

    if args.save_json:
        args.save_json.parent.mkdir(parents=True, exist_ok=True)
        args.save_json.write_text(
            json.dumps(asdict(report), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"Saved evaluation JSON -> {args.save_json}")

    if args.save_r2_report:
        s3 = settings.create_r2_client()
        r2_key = _save_report_to_r2(s3, settings.bucket_name, report)
        print(f"Uploaded R2 evaluation report -> s3://{settings.bucket_name}/{r2_key}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
