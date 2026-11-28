"""Pydantic v2 Silver Layer Schemas (ACDP Schema v2 — TASK-SLV-04).

Addresses all Silver schema gaps (G1–G7) audited in TASK-SLV-02 while preserving
100% backward compatibility with v1 extraction JSON payloads on Cloudflare R2:
- G1: Deterministic ISO 8601 `date` fields alongside raw display date strings.
- G2: Structured eligibility fields (`is_individual_allowed`, `eligibility_level`, `allowed_majors`).
- G3: `required_skills` list for student profile/team matching.
- G4: Advisor-outreach fields (`official_rules_url`, `organizer_contact`, `requires_advisor`, `team_registration_deadline`).
- G5: Rich `PrizeTier` (`tier_rank`, `quantity`, `currency`, `prize_type`).
- G6: Lineage & audit metadata (`competition_key`, `source_url`, `bronze_key`, `extracted_at`, `extractor_model`, `schema_version`).
- G7: Strict rejection of empty/placeholder `PrizeTier` entries instead of coercing `None -> ""`.
"""

from __future__ import annotations

import hashlib
import re
import unicodedata
from datetime import date, datetime
from typing import Any, Literal
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from pydantic import BaseModel, Field, field_validator, model_validator


def clean_placeholder(v: Any) -> Any:
    """Convert LLM placeholder strings ('N/A', 'none', 'unknown', 'tbd', etc.) to None."""
    if isinstance(v, str):
        v_strip = v.strip()
        if not v_strip:
            return None
        v_lower = v_strip.lower()
        if v_lower in {"none", "n/a", "null", "not specified", "unknown", "tbd", "nil"} or (
            "no " in v_lower and "mentioned" in v_lower
        ):
            return None
        return v_strip
    return v


def fold_vietnamese(text: str) -> str:
    """Fold Vietnamese text to lowercase ASCII with punctuation collapsed to single spaces."""
    if not text:
        return ""
    normalized = unicodedata.normalize("NFKD", text.replace("đ", "d").replace("Đ", "D"))
    ascii_only = normalized.encode("ascii", "ignore").decode("ascii").lower()
    cleaned = re.sub(r"[^a-z0-9]+", " ", ascii_only)
    return re.sub(r"\s+", " ", cleaned).strip()


def slugify(text: str) -> str:
    """Convert arbitrary Unicode/Vietnamese text to lowercase URL-safe ASCII slug."""
    folded = fold_vietnamese(text)
    slug = re.sub(r"\s+", "-", folded).strip("-")
    return slug or "unknown"


_URL_TRACKING_PARAMS = frozenset(
    {
        "fbclid",
        "gclid",
        "ref",
        "igshid",
        "mc_cid",
        "mc_eid",
    }
)
_ROOT_BOILERPLATE_PATHS = frozenset(
    {
        "/trang-chu",
        "/home",
        "/index.html",
        "/index.htm",
        "/index.php",
        "/vi",
        "/en",
    }
)


def normalize_canonical_url(url: str | None, fallback_name: str = "") -> str:
    """Normalize URL per RFC 3986 §6: https, lowercase host, no www., no tracking query/root boilerplate."""
    if not url or not url.strip():
        return f"urn:acdp:name:{slugify(fallback_name)}"

    raw = url.strip()
    if "://" not in raw:
        raw = f"https://{raw}"

    parsed = urlparse(raw)
    if not parsed.netloc:
        return f"urn:acdp:name:{slugify(fallback_name)}"

    scheme = "https"
    netloc = parsed.netloc.lower()
    if netloc.endswith(":80") or netloc.endswith(":443"):
        netloc = netloc.rsplit(":", 1)[0]
    if netloc.startswith("www."):
        netloc = netloc[4:]

    path = parsed.path.rstrip("/") or ""
    if path.lower() in _ROOT_BOILERPLATE_PATHS:
        path = ""

    filtered_query = sorted(
        (k, v)
        for k, v in parse_qsl(parsed.query, keep_blank_values=False)
        if not k.lower().startswith("utm_") and k.lower() not in _URL_TRACKING_PARAMS
    )
    query_str = urlencode(filtered_query)
    return urlunparse((scheme, netloc, path, "", query_str, ""))


def compute_competition_key(canonical_url: str, season_year: int | None = None) -> str:
    """Compute immutable 64-char SHA-256 key from canonical URL, scoped by season_year on evergreen domains."""
    key_input = canonical_url
    if season_year is not None and not canonical_url.startswith("urn:"):
        year_str = str(season_year)
        if not re.search(rf"(?<!\d){re.escape(year_str)}(?!\d)", canonical_url):
            key_input = f"{canonical_url}#season={year_str}"
    return hashlib.sha256(key_input.encode("utf-8")).hexdigest()


ORGANIZER_ALIAS_MAP: dict[str, str] = {
    "vinuniversity": "vinuni",
    "truong dai hoc vinuni": "vinuni",
    "dai hoc vinuni": "vinuni",
    "vinuni": "vinuni",
    "vintelligence": "vinuni",
    "vng": "vng",
    "vng corporation": "vng",
    "cong ty co phan vng": "vng",
    "zalo": "zalo",
    "zalo ai": "zalo",
    "rmit": "rmit",
    "rmit university": "rmit",
    "rmit university vietnam": "rmit",
    "rmit vietnam": "rmit",
    "rmit vietnam fintech club": "rmit",
    "rmit student club program": "rmit",
    "dai hoc quoc gia ha noi": "vnu_hanoi",
    "dhqghn": "vnu_hanoi",
    "truong dai hoc cong nghe dhqghn": "vnu_hanoi",
    "dai hoc quoc gia thanh pho ho chi minh": "vnu_hcm",
    "dhqg hcm": "vnu_hcm",
    "truong dai hoc cong nghe thong tin dhqg hcm": "uit",
    "truong dai hoc cong nghe thong tin": "uit",
    "uit": "uit",
    "hust": "hust",
    "hbac": "hust",
    "hbac hust business analytics club": "hust",
    "truong kinh te dhbk ha noi": "hust",
    "dai hoc bach khoa ha noi": "hust",
    "hcmute": "hcmute",
    "hcm ute": "hcmute",
    "fit hcmute": "hcmute",
    "fit hcm ute": "hcmute",
    "truong dai hoc su pham ky thuat tp hcm": "hcmute",
    "truong dai hoc cong nghe ky thuat tp hcm": "hcmute",
    "ton duc thang university": "tdtu",
    "ton duc thang university faculty of information technology": "tdtu",
    "truong dai hoc ton duc thang": "tdtu",
    "fpt": "fpt",
    "fpt university": "fpt",
    "dai hoc fpt": "fpt",
    "naver": "naver",
    "naver viet nam": "naver",
    "naver vietnam": "naver",
    "bo cong an": "mps_vn",
    "so khoa hoc va cong nghe tp hcm": "dost_hcm",
    "hoi tin hoc thanh pho": "hca",
    "qualcomm": "qualcomm",
    "qualcomm technologies": "qualcomm",
    "onyx data": "onyx_data",
    "netcompany": "netcompany",
    "netcompany vietnam": "netcompany",
    "code mely": "code_mely",
    "trung tam doi moi sang tao quoc gia": "nic",
    "nic": "nic",
    "tap doan meta": "meta",
    "meta": "meta",
    "ai for vietnam": "aiv",
    "to chuc ai for vietnam": "aiv",
    "hiep hoi du lieu quoc gia": "nda",
    "trung tam du lieu quoc gia": "ndc",
    "dai truyen hinh viet nam": "vtv",
    "haui": "haui",
    "dai hoc cong nghiep ha noi": "haui",
    "ntt": "nttu",
    "truong dai hoc nguyen tat thanh": "nttu",
    "khoa cong nghe thong tin truong dai hoc nguyen tat thanh": "nttu",
    "lotushacks": "lotushacks",
    "hackharvard": "hackharvard",
    "cuc so huu tri tue": "ipvietnam",
    "bo khoa hoc va cong nghe": "most_vn",
    "bao vnexpress": "vnexpress",
}

_FRAMING_PREFIX_RE = re.compile(
    r"^(?:cuoc thi|hoi thi|dau truong|giai dau|san choi|chuong trinh|thong bao|khoi dong|chung ket)\s+"
)
_GENERIC_DOMAIN_PREFIX_RE = re.compile(
    r"^(?:khoa hoc du lieu|tri tue nhan tao|an toan thong tin|lap trinh|cong nghe thong tin)\s+"
)
_MONTH_MAP: dict[str, int] = {
    "january": 1,
    "jan": 1,
    "thang 1": 1,
    "thang 01": 1,
    "february": 2,
    "feb": 2,
    "thang 2": 2,
    "thang 02": 2,
    "march": 3,
    "mar": 3,
    "thang 3": 3,
    "thang 03": 3,
    "april": 4,
    "apr": 4,
    "thang 4": 4,
    "thang 04": 4,
    "may": 5,
    "thang 5": 5,
    "thang 05": 5,
    "june": 6,
    "jun": 6,
    "thang 6": 6,
    "thang 06": 6,
    "july": 7,
    "jul": 7,
    "thang 7": 7,
    "thang 07": 7,
    "august": 8,
    "aug": 8,
    "thang 8": 8,
    "thang 08": 8,
    "september": 9,
    "sep": 9,
    "sept": 9,
    "thang 9": 9,
    "thang 09": 9,
    "october": 10,
    "oct": 10,
    "thang 10": 10,
    "november": 11,
    "nov": 11,
    "thang 11": 11,
    "december": 12,
    "dec": 12,
    "thang 12": 12,
}


def canonicalize_organizers(organizers: list[str]) -> list[str]:
    """Map noisy Vietnamese/English organizer strings to canonical entity tokens."""
    canonical: list[str] = []
    seen: set[str] = set()
    for raw in organizers:
        folded = fold_vietnamese(raw)
        if not folded:
            continue
        mapped = ORGANIZER_ALIAS_MAP.get(folded)
        if not mapped:
            # Substring fallback for parenthetical / multi-part organizer strings
            for alias_key, target in ORGANIZER_ALIAS_MAP.items():
                if len(alias_key) >= 5 and alias_key in folded:
                    mapped = target
                    break
        token = mapped or slugify(folded)
        if token not in seen:
            seen.add(token)
            canonical.append(token)
    return canonical


def extract_season_year(
    name: str,
    url: str | None = None,
    *,
    event_start_date: date | None = None,
    registration_deadline_date: date | None = None,
    registration_start_date: date | None = None,
    event_end_date: date | None = None,
    timeline_dates: list[date | None] | None = None,
    tagline: str | None = None,
    summary: str | None = None,
) -> int | None:
    """Extract competition edition/season year using deterministic priority cascade."""
    year_re = re.compile(r"(?<!\d)(202\d|2030)(?!\d)")

    name_years = [int(y) for y in year_re.findall(name or "")]
    if name_years:
        return name_years[-1]

    if url:
        parsed_u = urlparse(url)
        url_body = f"{parsed_u.netloc}{parsed_u.path}"
        url_years = [int(y) for y in year_re.findall(url_body)]
        if url_years:
            return url_years[-1]

    for dt in (
        event_start_date,
        registration_deadline_date,
        registration_start_date,
        event_end_date,
        *(timeline_dates or []),
    ):
        if dt is not None and 2020 <= dt.year <= 2030:
            return dt.year

    for text_field in (tagline or "", summary or ""):
        found = sorted({int(y) for y in year_re.findall(text_field)})
        if len(found) == 1:
            return found[0]
        if found:
            return found[0]
    return None


def extract_season_month(name: str, url: str | None = None) -> int | None:
    """Extract explicit month identifier for monthly recurring challenges (e.g. DataDNA)."""
    combined = f"{fold_vietnamese(name)} {fold_vietnamese(url or '')}".strip()
    for token, month_num in _MONTH_MAP.items():
        if re.search(rf"\b{re.escape(token)}\b", combined):
            return month_num
    return None


def extract_edition_number(name: str) -> int | None:
    """Extract explicit ordinal edition/season number ('mùa 3', 'season 4', 'lần thứ 2')."""
    folded = fold_vietnamese(name)
    match = re.search(r"\b(?:mua|season|edition|lan thu)\s*(\d{1,2})\b", folded)
    if match:
        return int(match.group(1))
    return None


def normalize_competition_name(name: str) -> tuple[str, str]:
    """Return (full_normalized_name, core_name_slug) invariant to framing words, locations, and year/edition."""
    raw = (name or "").strip()
    if not raw:
        return ("", "unknown")

    def _clean_segment(seg: str) -> str:
        f = fold_vietnamese(seg)
        f = re.sub(r"\bviet nam\b", "vietnam", f)
        f = re.sub(r"\b(thanh pho ho chi minh|tp hcm|ho chi minh city|tphcm)\b", "tphcm", f)
        return re.sub(r"\s+", " ", f).strip()

    full_norm = _clean_segment(raw)
    # Split thematic subtitles (e.g. "Datathon 2026: The Gridbreaker" -> "Datathon 2026")
    head = re.split(r"[:–|]|\s+-\s+", raw, maxsplit=1)[0].strip() or raw
    core = _clean_segment(head)

    # Strip year, month, and ordinal edition markers from core
    core = re.sub(r"\b(?:mua|season|edition|lan thu)\s*\d{1,2}\b", " ", core)
    core = re.sub(r"\b(?:nam\s*)?20[2-3]\d\b", " ", core)
    for m_tok in _MONTH_MAP:
        core = re.sub(rf"\b{re.escape(m_tok)}\b", " ", core)
    core = re.sub(r"\btoan quoc\b", " ", core)
    core = re.sub(r"\s+", " ", core).strip()

    # Strip framing boilerplate iteratively
    while True:
        updated = _FRAMING_PREFIX_RE.sub("", core).strip()
        if updated == core:
            break
        core = updated

    # Strip generic domain descriptor only when a distinct brand token remains
    stripped_domain = _GENERIC_DOMAIN_PREFIX_RE.sub("", core).strip()
    if stripped_domain and len(stripped_domain) >= 4:
        core = stripped_domain

    # If a parenthetical short brand exists alongside long Vietnamese framing, e.g., "... (AI Challenge) tphcm",
    # fold outer/inner cleanly into slug
    core = re.sub(r"\s+", " ", core).strip()
    core_slug = re.sub(r"\s+", "-", core).strip("-") or slugify(full_norm)
    return full_norm, core_slug


def build_natural_key(
    name: str,
    organizers: list[str],
    url: str | None,
    season_year: int | None,
    *,
    season_month: int | None = None,
    official_domain: str | None = None,
) -> tuple[str, str]:
    """Build deterministic composite natural key and its 64-char SHA-256 digest."""
    _, core_slug = normalize_competition_name(name)
    canon_orgs = canonicalize_organizers(organizers)
    primary_org = canon_orgs[0] if canon_orgs else "unknown-org"
    domain_part = (official_domain or "").strip().lower()
    if not domain_part and url:
        canon_u = normalize_canonical_url(url, name)
        if not canon_u.startswith("urn:"):
            domain_part = urlparse(canon_u).netloc
    domain_part = domain_part or "no-domain"
    year_part = str(season_year) if season_year is not None else "unknown-year"
    parts = [core_slug, primary_org, year_part, domain_part]
    if season_month is not None:
        parts.append(f"{season_month:02d}")
    natural_key = "|".join(parts)
    return natural_key, hashlib.sha256(natural_key.encode("utf-8")).hexdigest()


def parse_date_value(raw: Any) -> date | None:
    """Parse ISO YYYY-MM-DD, Vietnamese DD/MM/YYYY, and MM/YYYY strings into Python date."""
    if raw is None:
        return None
    if isinstance(raw, datetime):
        return raw.date()
    if isinstance(raw, date):
        return raw
    if not isinstance(raw, str):
        return None

    s = clean_placeholder(raw)
    if not s:
        return None

    lower = s.lower()
    if any(tok in lower for tok in ("tbd", "rolling", "liên tục", "hàng tháng", "unknown", "n/a")):
        return None

    iso_match = re.match(r"^(\d{4})-(\d{1,2})-(\d{1,2})(?:[T\s].*)?$", s)
    if iso_match:
        try:
            return date(int(iso_match.group(1)), int(iso_match.group(2)), int(iso_match.group(3)))
        except ValueError:
            return None

    # Handle exact DD/MM/YYYY as well as date strings decorated with time prefixes/suffixes
    # e.g. "17/07/2026 – 11:00", "11:00, 17/07/2026", "23:59 ngày 15/06/2026"
    vn_match = re.match(r"^(\d{1,2})[/\-](\d{1,2})[/\-](\d{4})(?:[\s,–\-]+(?:\d{1,2}:\d{2}|lúc\s*\d{1,2}:\d{2}).*)?$", s)
    if not vn_match and re.search(r"\b\d{1,2}:\d{2}\b", s):
        vn_match = re.search(r"\b(\d{1,2})[/\-](\d{1,2})[/\-](\d{4})\b", s)
    if vn_match:
        try:
            return date(int(vn_match.group(3)), int(vn_match.group(2)), int(vn_match.group(1)))
        except ValueError:
            return None

    my_match = re.match(r"^(?:tháng\s*)?(\d{1,2})[/\-](\d{4})$", lower)
    if my_match:
        try:
            return date(int(my_match.group(2)), int(my_match.group(1)), 1)
        except ValueError:
            return None

    ym_match = re.match(r"^(\d{4})[/\-](\d{1,2})$", s)
    if ym_match:
        try:
            return date(int(ym_match.group(1)), int(ym_match.group(2)), 1)
        except ValueError:
            return None

    return None


def _clean_string_list(v: Any) -> list[str]:
    """Ensure list[str] is valid even if LLM returns str, None, or mixed items."""
    if v is None:
        return []
    if isinstance(v, str):
        cleaned = clean_placeholder(v)
        if not cleaned:
            return []
        if "," in cleaned:
            return [item.strip() for item in cleaned.split(",") if clean_placeholder(item)]
        if ";" in cleaned:
            return [item.strip() for item in cleaned.split(";") if clean_placeholder(item)]
        return [cleaned]
    if isinstance(v, list):
        res: list[str] = []
        for item in v:
            if isinstance(item, str):
                c = clean_placeholder(item)
                if c:
                    res.append(c)
            elif item is not None:
                res.append(str(item))
        return res
    return []


class PrizeTier(BaseModel):
    """Detailed prize category and rewards (Schema v2 — G5, G7)."""

    tier: str = Field(
        ...,
        description="Tên hạng giải thưởng (vd: Quán quân / First Place, Á quân 1, Top 5, Winner)",
    )
    reward: str = Field(
        default="",
        description="Mô tả phần thưởng (tiền mặt, quà tặng, voucher, học bổng, phần mềm)",
    )
    tier_rank: int | None = Field(
        default=None,
        ge=1,
        description="Thứ hạng tường minh của giải thưởng (1, 2, 3...)",
    )
    quantity: int = Field(
        default=1,
        ge=1,
        description="Số lượng suất giải ở hạng này (mặc định 1)",
    )
    currency: Literal["VND", "USD", "OTHER"] = Field(
        default="VND",
        description="Đơn vị tiền tệ chính của phần thưởng ('VND', 'USD', 'OTHER')",
    )
    prize_type: Literal["cash", "scholarship", "credits", "merch", "mixed"] = Field(
        default="cash",
        description="Loại phần thưởng ('cash', 'scholarship', 'credits', 'merch', 'mixed')",
    )
    estimated_value_vnd: float | None = Field(
        default=None,
        ge=0,
        description="Ước tính giá trị quy đổi sang VNĐ cho 1 suất giải (nếu có)",
    )
    is_scholarship: bool = Field(
        default=False,
        description="Đánh dấu giải thưởng có phải là học bổng đào tạo/khóa học hay không",
    )

    @field_validator("tier", mode="before")
    @classmethod
    def validate_tier_non_empty(cls, v: Any) -> str:
        """G7: Reject None or placeholder strings instead of coercing to empty string."""
        cleaned = clean_placeholder(v)
        if not cleaned or not isinstance(cleaned, str):
            raise ValueError("PrizeTier.tier must be a non-empty string.")
        return cleaned

    @field_validator("reward", mode="before")
    @classmethod
    def clean_reward(cls, v: Any) -> str:
        cleaned = clean_placeholder(v)
        return str(cleaned) if cleaned is not None else ""

    @field_validator("quantity", mode="before")
    @classmethod
    def normalize_quantity(cls, v: Any) -> int:
        if v is None:
            return 1
        try:
            parsed = int(v)
            return max(parsed, 1)
        except (TypeError, ValueError):
            return 1

    @field_validator("currency", mode="before")
    @classmethod
    def normalize_currency(cls, v: Any) -> str:
        if not isinstance(v, str):
            return "VND"
        upper = v.strip().upper()
        if upper in {"VND", "VNĐ", "DONG"}:
            return "VND"
        if upper in {"USD", "USDT", "USDC", "$"}:
            return "USD"
        return "OTHER" if upper else "VND"

    @field_validator("prize_type", mode="before")
    @classmethod
    def normalize_prize_type(cls, v: Any) -> str:
        if not isinstance(v, str):
            return "cash"
        lower = v.strip().lower()
        if lower in {"cash", "scholarship", "credits", "merch", "mixed"}:
            return lower
        return "cash"


class TimelineStage(BaseModel):
    """Detailed stage or round in the competition timeline (Schema v2 — G1, G8)."""

    stage_name: str = Field(
        ...,
        description="Tên vòng thi / giai đoạn (vd: Vòng 1: Discover, Vòng 2: Build, Chung kết & Demo)",
    )
    start_date: str | None = Field(
        default=None,
        description="Ngày bắt đầu vòng thi dạng chuỗi gốc (DD/MM/YYYY hoặc YYYY-MM-DD)",
    )
    end_date: str | None = Field(
        default=None,
        description="Hạn nộp bài hoặc ngày kết thúc vòng thi dạng chuỗi gốc",
    )
    start_date_iso: date | None = Field(
        default=None,
        description="Ngày bắt đầu vòng thi chuẩn hóa ISO 8601 (DATE)",
    )
    end_date_iso: date | None = Field(
        default=None,
        description="Ngày kết thúc vòng thi chuẩn hóa ISO 8601 (DATE)",
    )
    description: str | None = Field(
        default=None,
        description="Mục tiêu hoặc yêu cầu của vòng thi",
    )

    @field_validator("stage_name", mode="before")
    @classmethod
    def clean_stage_name(cls, v: Any) -> str:
        cleaned = clean_placeholder(v)
        if not cleaned or not isinstance(cleaned, str):
            raise ValueError("TimelineStage.stage_name must be non-empty.")
        return cleaned

    @field_validator("start_date", "end_date", "description", mode="before")
    @classmethod
    def clean_stage_fields(cls, v: Any) -> Any:
        return clean_placeholder(v)

    @field_validator("start_date_iso", "end_date_iso", mode="before")
    @classmethod
    def parse_stage_iso_dates(cls, v: Any) -> date | None:
        return parse_date_value(v)

    @model_validator(mode="after")
    def populate_iso_dates(self) -> TimelineStage:
        if self.start_date_iso is None and self.start_date:
            self.start_date_iso = parse_date_value(self.start_date)
        if self.end_date_iso is None and self.end_date:
            self.end_date_iso = parse_date_value(self.end_date)
        return self


class Competition(BaseModel):
    """Normalized Silver Schema v2 representing a single academic/technical competition."""

    # Identity & Core Metadata
    competition_key: str | None = Field(
        default=None,
        description="Khóa tự nhiên SHA-256 (64 ký tự) của canonical URL",
    )
    name: str = Field(
        ...,
        description="Tên chính thức của cuộc thi (vd: IT Consultant Challenge 2026)",
    )
    tagline: str | None = Field(
        default=None,
        description="Khẩu hiệu hoặc chủ đề của mùa thi",
    )
    url: str | None = Field(
        default=None,
        description="Đường dẫn URL chính thức của cuộc thi",
    )
    summary: str = Field(
        ...,
        description="Tóm tắt ngắn gọn 2-3 câu về nội dung, mục tiêu và ý nghĩa của cuộc thi",
    )
    organizers: list[str] = Field(
        default_factory=list,
        description="Danh sách đơn vị tổ chức chính",
    )
    partners_and_sponsors: list[str] = Field(
        default_factory=list,
        description="Danh sách đơn vị tài trợ, đối tác đồng hành",
    )
    category: list[str] = Field(
        default_factory=list,
        description="Lĩnh vực / chuyên môn (Artificial Intelligence, Data Science, Cybersecurity, ...)",
    )
    target_audience: str | list[str] | None = Field(
        default=None,
        description="Đối tượng dự thi hướng tới",
    )

    # Team & Eligibility (G2, G3)
    team_size_min: int | None = Field(
        default=None,
        description="Số lượng thành viên tối thiểu mỗi đội",
    )
    team_size_max: int | None = Field(
        default=None,
        description="Số lượng thành viên tối đa mỗi đội",
    )
    team_description: str | None = Field(
        default=None,
        description="Mô tả quy định về đội thi",
    )
    is_individual_allowed: bool | None = Field(
        default=None,
        description="G2: Cho phép thí sinh đăng ký thi cá nhân (1 người) hay không",
    )
    eligibility_level: Literal["undergraduate", "all_students", "open", "unknown"] = Field(
        default="unknown",
        description="G2: Bậc đối tượng ('undergraduate', 'all_students', 'open', 'unknown')",
    )
    allowed_majors: list[str] = Field(
        default_factory=list,
        description="G2: Các chuyên ngành được ưu tiên/cho phép (vd: CNTT, KTDL, AI)",
    )
    required_skills: list[str] = Field(
        default_factory=list,
        description="G3: Kỹ năng/công nghệ đề bài yêu cầu (Python, SQL, React, PyTorch, ...)",
    )

    # Mode, Fee & Prizes
    mode: Literal["online", "offline", "hybrid", "unknown"] = Field(
        default="unknown",
        description="Hình thức tổ chức: 'online', 'offline', 'hybrid', hoặc 'unknown'",
    )
    location: str | None = Field(
        default=None,
        description="Địa điểm tổ chức nếu offline/hybrid",
    )
    participation_fee: str | None = Field(
        default="Miễn phí",
        description="Lệ phí tham gia",
    )
    total_prize_pool: str | None = Field(
        default=None,
        description="Tổng giá trị giải thưởng công bố",
    )
    prizes: list[PrizeTier] = Field(
        default_factory=list,
        description="Danh sách cơ cấu giải thưởng chi tiết và học bổng",
    )

    # Timeline & ISO Dates (G1)
    registration_start: str | None = Field(default=None, description="Ngày mở cổng đăng ký (raw)")
    registration_deadline: str | None = Field(default=None, description="Hạn chót đăng ký (raw)")
    registration_status: Literal["open", "upcoming", "closed", "unknown"] = Field(
        default="unknown",
        description="Tình trạng đăng ký (open, upcoming, closed, unknown)",
    )
    event_start: str | None = Field(default=None, description="Ngày bắt đầu sự kiện (raw)")
    event_end: str | None = Field(default=None, description="Ngày kết thúc sự kiện (raw)")
    registration_start_date: date | None = Field(default=None, description="G1: Ngày mở đăng ký ISO DATE")
    registration_deadline_date: date | None = Field(default=None, description="G1: Hạn chót đăng ký ISO DATE")
    event_start_date: date | None = Field(default=None, description="G1: Ngày bắt đầu sự kiện ISO DATE")
    event_end_date: date | None = Field(default=None, description="G1: Ngày kết thúc sự kiện ISO DATE")
    timeline_stages: list[TimelineStage] = Field(
        default_factory=list,
        description="Danh sách các vòng thi, mốc thời gian",
    )

    # Challenge & Lecturer Screen Fields (G4)
    challenge_overview: str | None = Field(default=None, description="Mô tả tóm tắt đề bài/bài toán")
    submission_platform: str | None = Field(default=None, description="Nền tảng nộp bài")
    official_rules_url: str | None = Field(
        default=None,
        description="G4: Đường dẫn thể lệ chính thức (.pdf/.docx hoặc trang thể lệ)",
    )
    organizer_contact: str | None = Field(
        default=None,
        description="G4: Email hoặc kênh liên hệ chính thức của Ban Tổ Chức",
    )
    requires_advisor: bool | None = Field(
        default=None,
        description="G4: Cuộc thi có yêu cầu Giảng viên hướng dẫn (GVHD) hay không",
    )
    team_registration_deadline: str | None = Field(
        default=None,
        description="G4: Hạn chốt danh sách đội thi / nộp đơn xin GVHD (raw)",
    )
    team_registration_deadline_date: date | None = Field(
        default=None,
        description="G4: Hạn chốt đội thi chuẩn hóa ISO DATE",
    )

    # Lineage, Entity Resolution & Audit Metadata (G6 + TASK-DQ-04)
    season_year: int | None = Field(default=None, description="DQ-04: Năm mùa giải chuẩn hóa (2025-2027)")
    natural_key: str | None = Field(
        default=None,
        description="DQ-04: Khóa tự nhiên nghiệp vụ (core_name|primary_org|season_year|official_domain)",
    )
    merged_source_urls: list[str] = Field(
        default_factory=list,
        description="DQ-04: Danh sách URL nguồn đã gộp về thực thể chuẩn",
    )
    source_url: str | None = Field(default=None, description="G6: URL nguồn đã cào ở Bronze")
    bronze_key: str | None = Field(default=None, description="G6: Object key trên R2 Bronze")
    extracted_at: datetime | None = Field(default=None, description="G6: Thời điểm trích xuất UTC")
    extractor_model: str | None = Field(default=None, description="G6: Tên model LLM trích xuất")
    schema_version: str = Field(default="2.0", description="G6: Phiên bản Silver Schema")

    @field_validator("target_audience", mode="before")
    @classmethod
    def normalize_target_audience(cls, v: Any) -> Any:
        if isinstance(v, list):
            cleaned = [str(clean_placeholder(item)) for item in v if clean_placeholder(item)]
            return ", ".join(cleaned) if cleaned else None
        return clean_placeholder(v)

    @field_validator(
        "category",
        "organizers",
        "partners_and_sponsors",
        "allowed_majors",
        "required_skills",
        "merged_source_urls",
        mode="before",
    )
    @classmethod
    def ensure_list_of_strings(cls, v: Any) -> list[str]:
        return _clean_string_list(v)

    @field_validator("prizes", mode="before")
    @classmethod
    def filter_invalid_prizes(cls, v: Any) -> list[Any]:
        """G7: Drop empty/placeholder PrizeTier dicts instead of persisting empty rows."""
        if v is None:
            return []
        if not isinstance(v, list):
            return []
        valid_items: list[Any] = []
        for item in v:
            if isinstance(item, dict):
                tier_cleaned = clean_placeholder(item.get("tier"))
                if not tier_cleaned:
                    continue
                valid_items.append(item)
            elif item is not None:
                valid_items.append(item)
        return valid_items

    @field_validator("timeline_stages", mode="before")
    @classmethod
    def ensure_timeline_list(cls, v: Any) -> list[Any]:
        if v is None:
            return []
        if not isinstance(v, list):
            return []
        valid_items: list[Any] = []
        for item in v:
            if isinstance(item, dict):
                if not clean_placeholder(item.get("stage_name")):
                    continue
                valid_items.append(item)
            elif item is not None:
                valid_items.append(item)
        return valid_items

    @field_validator("eligibility_level", mode="before")
    @classmethod
    def normalize_eligibility_level(cls, v: Any) -> str:
        if not isinstance(v, str):
            return "unknown"
        lower = v.strip().lower()
        if lower in {"undergraduate", "all_students", "open", "unknown"}:
            return lower
        if any(k in lower for k in ("đại học", "cử nhân", "undergrad")):
            return "undergraduate"
        if any(k in lower for k in ("sinh viên", "học viên", "student")):
            return "all_students"
        if any(k in lower for k in ("mở rộng", "công khai", "tất cả", "open")):
            return "open"
        return "unknown"

    @field_validator(
        "tagline",
        "url",
        "location",
        "participation_fee",
        "total_prize_pool",
        "registration_start",
        "registration_deadline",
        "event_start",
        "event_end",
        "challenge_overview",
        "submission_platform",
        "team_description",
        "official_rules_url",
        "organizer_contact",
        "team_registration_deadline",
        "source_url",
        "bronze_key",
        "extractor_model",
        mode="before",
    )
    @classmethod
    def clean_string_placeholders(cls, v: Any) -> Any:
        return clean_placeholder(v)

    @field_validator(
        "registration_start_date",
        "registration_deadline_date",
        "event_start_date",
        "event_end_date",
        "team_registration_deadline_date",
        mode="before",
    )
    @classmethod
    def parse_iso_dates(cls, v: Any) -> date | None:
        return parse_date_value(v)

    @model_validator(mode="after")
    def enrich_deterministic_fields(self) -> Competition:
        """Deterministically populate ISO dates, season_year, natural_key, and season-scoped competition_key."""
        if self.registration_start_date is None and self.registration_start:
            self.registration_start_date = parse_date_value(self.registration_start)
        if self.registration_deadline_date is None and self.registration_deadline:
            self.registration_deadline_date = parse_date_value(self.registration_deadline)
        if self.event_start_date is None and self.event_start:
            self.event_start_date = parse_date_value(self.event_start)
        if self.event_end_date is None and self.event_end:
            self.event_end_date = parse_date_value(self.event_end)
        if self.team_registration_deadline_date is None and self.team_registration_deadline:
            self.team_registration_deadline_date = parse_date_value(self.team_registration_deadline)

        if self.is_individual_allowed is None and self.team_size_min is not None:
            self.is_individual_allowed = self.team_size_min <= 1

        if self.season_year is None:
            timeline_dates = [
                d
                for st in self.timeline_stages
                for d in (st.start_date_iso, st.end_date_iso)
            ]
            self.season_year = extract_season_year(
                self.name,
                self.url,
                event_start_date=self.event_start_date,
                registration_deadline_date=self.registration_deadline_date,
                registration_start_date=self.registration_start_date,
                event_end_date=self.event_end_date,
                timeline_dates=timeline_dates,
                tagline=self.tagline,
                summary=self.summary,
            )

        if not self.natural_key:
            s_month = extract_season_month(self.name, self.url)
            self.natural_key, _ = build_natural_key(
                self.name,
                self.organizers,
                self.url,
                self.season_year,
                season_month=s_month,
            )

        if not self.merged_source_urls:
            initial_urls: list[str] = []
            seen_canon: set[str] = set()
            for candidate_u in (self.source_url, self.url):
                if candidate_u and candidate_u.strip():
                    u_str = candidate_u.strip()
                    u_canon = normalize_canonical_url(u_str)
                    if u_canon not in seen_canon:
                        seen_canon.add(u_canon)
                        initial_urls.append(u_str)
            self.merged_source_urls = initial_urls

        if not self.competition_key:
            canonical = normalize_canonical_url(self.url, self.name)
            self.competition_key = compute_competition_key(canonical, season_year=self.season_year)

        for idx, prize in enumerate(self.prizes, start=1):
            if prize.tier_rank is None:
                prize.tier_rank = idx

        return self


class CompetitionExtractionResult(BaseModel):
    """Top-level container returned by LLM Instructor extraction (Schema v2)."""

    is_competition: bool = Field(
        default=True,
        description="True nếu văn bản chứa thông tin cuộc thi CNTT/AI/Dữ liệu/Bảo mật/Lập trình hợp lệ; False nếu không.",
    )
    reasoning: str | None = Field(
        default=None,
        description="Giải thích ngắn gọn lý do tài liệu có hoặc không chứa cuộc thi",
    )
    competitions: list[Competition] = Field(
        default_factory=list,
        description="Danh sách các cuộc thi trích xuất được.",
    )

    @field_validator("is_competition", mode="before")
    @classmethod
    def normalize_is_competition(cls, v: Any) -> bool:
        if isinstance(v, str):
            return v.strip().lower() in {"true", "1", "yes", "co", "có"}
        if isinstance(v, bool):
            return v
        return bool(v)

    @field_validator("competitions", mode="before")
    @classmethod
    def ensure_competitions_list(cls, v: Any) -> list[Any]:
        if v is None:
            return []
        if isinstance(v, dict):
            return [v]
        return v
