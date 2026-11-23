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


def slugify(text: str) -> str:
    """Convert arbitrary Unicode/Vietnamese text to lowercase URL-safe ASCII slug."""
    normalized = unicodedata.normalize("NFKD", text.replace("đ", "d").replace("Đ", "D"))
    ascii_only = normalized.encode("ascii", "ignore").decode("ascii").lower()
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_only).strip("-")
    return slug or "unknown"


def normalize_canonical_url(url: str | None, fallback_name: str = "") -> str:
    """Normalize URL by enforcing https, lowercase host, no tracking query or trailing slash."""
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
    path = parsed.path.rstrip("/") or ""

    filtered_query = [
        (k, v)
        for k, v in parse_qsl(parsed.query, keep_blank_values=True)
        if not k.lower().startswith("utm_") and k.lower() != "fbclid"
    ]
    query_str = urlencode(filtered_query)
    return urlunparse((scheme, netloc, path, "", query_str, ""))


def compute_competition_key(canonical_url: str) -> str:
    """Compute immutable 64-char SHA-256 natural key from canonical URL."""
    return hashlib.sha256(canonical_url.encode("utf-8")).hexdigest()


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

    vn_match = re.match(r"^(\d{1,2})[/\-](\d{1,2})[/\-](\d{4})$", s)
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

    # Lineage & Audit Metadata (G6)
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
        """Deterministically populate ISO dates, team individual flag, and competition_key."""
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

        if not self.competition_key:
            canonical = normalize_canonical_url(self.url, self.name)
            self.competition_key = compute_competition_key(canonical)

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
