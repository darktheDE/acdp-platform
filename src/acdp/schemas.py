"""Pydantic schemas for extracting structured academic competition data from bronze layer markdown.

Designed for LLM extraction via Instructor (Ollama, Gemini, OpenAI, Claude).
Conforms to ACDP Data Engineering standards (Pydantic v2, OLAP dimensions for DuckDB/Delta Lake).
"""

from typing import Literal, Optional, Union
from pydantic import BaseModel, Field, field_validator


def clean_placeholder(v: any) -> any:
    """Chuyển đổi các chuỗi giả định của LLM thành None chuẩn."""
    if isinstance(v, str):
        v_strip = v.strip()
        v_lower = v_strip.lower()
        if v_lower in {"none", "n/a", "null", "not specified", "unknown", "tbd"} or (
            "no " in v_lower and "mentioned" in v_lower
        ):
            return None
        return v_strip
    return v


class PrizeTier(BaseModel):
    """Detailed prize category and rewards."""

    tier: str = Field(
        ...,
        description="Tên hạng giải thưởng (vd: Quán quân / First Place, Á quân 1, Top 5, Winner, v.v.)",
    )
    reward: str = Field(
        ...,
        description="Mô tả phần thưởng (tiền mặt, quà tặng, voucher, học bổng, phần mềm)",
    )
    estimated_value_vnd: Optional[float] = Field(
        default=None,
        description="Ước tính giá trị quy đổi sang VNĐ (nếu có để phục vụ phân tích định lượng)",
    )
    is_scholarship: bool = Field(
        default=False,
        description="Đánh dấu giải thưởng có phải là học bổng đào tạo/khóa học hay không",
    )

    @field_validator("tier", "reward", mode="before")
    @classmethod
    def clean_fields(cls, v):
        cleaned = clean_placeholder(v)
        return cleaned if cleaned is not None else ""


class TimelineStage(BaseModel):
    """Detailed stage or round in the competition timeline."""

    stage_name: str = Field(
        ...,
        description="Tên vòng thi / giai đoạn (vd: Vòng 1: Discover, Vòng 2: Build, Chung kết & Demo, Warm-up)",
    )
    start_date: Optional[str] = Field(
        default=None,
        description="Ngày bắt đầu vòng thi (định dạng DD/MM/YYYY hoặc YYYY-MM-DD)",
    )
    end_date: Optional[str] = Field(
        default=None,
        description="Hạn nộp bài hoặc ngày kết thúc vòng thi (định dạng DD/MM/YYYY hoặc YYYY-MM-DD)",
    )
    description: Optional[str] = Field(
        default=None,
        description="Mục tiêu hoặc yêu cầu của vòng thi (vd: nộp proposal, xây dựng MVP, demo pitching)",
    )

    @field_validator("start_date", "end_date", "description", mode="before")
    @classmethod
    def clean_stage_dates(cls, v):
        return clean_placeholder(v)


class Competition(BaseModel):
    """Normalized schema representing a single academic or technical competition.
    
    Provides >10 quantitative and categorical dimensions for OLAP Data Marts in DuckDB.
    """

    name: str = Field(
        ...,
        description="Tên chính thức của cuộc thi (vd: IT Consultant Challenge 2026, RMIT Hackathon 2026)",
    )
    tagline: Optional[str] = Field(
        default=None,
        description="Khẩu hiệu, chủ đề hoặc theme của mùa thi (vd: Prompt to Production, Secure. Generate. Include.)",
    )
    url: Optional[str] = Field(
        default=None,
        description="Đường dẫn URL chính thức của cuộc thi hoặc trang đích đăng ký",
    )
    summary: str = Field(
        ...,
        description="Tóm tắt ngắn gọn 2-3 câu về nội dung, mục tiêu và ý nghĩa của cuộc thi",
    )
    organizers: list[str] = Field(
        default_factory=list,
        description="Danh sách các đơn vị tổ chức chính (Trường Đại học, Doanh nghiệp, Tổ chức/Câu lạc bộ)",
    )
    partners_and_sponsors: list[str] = Field(
        default_factory=list,
        description="Danh sách các đơn vị tài trợ, đối tác đồng hành, đơn vị bảo trợ truyền thông",
    )
    category: list[str] = Field(
        default_factory=list,
        description="Lĩnh vực / chuyên môn (vd: Artificial Intelligence, Data Science, Software Engineering, IT Consulting, Cybersecurity, Competitive Programming)",
    )
    target_audience: Optional[Union[str, list[str]]] = Field(
        default=None,
        description="Đối tượng dự thi hướng tới (vd: Sinh viên ĐH/CĐ, Tech Freshers, Data Enthusiasts)",
    )
    team_size_min: Optional[int] = Field(
        default=None,
        description="Số lượng thành viên tối thiểu mỗi đội (1 nếu cho phép thi cá nhân)",
    )
    team_size_max: Optional[int] = Field(
        default=None,
        description="Số lượng thành viên tối đa mỗi đội (1 nếu chỉ thi cá nhân)",
    )
    team_description: Optional[str] = Field(
        default=None,
        description="Mô tả quy định về thành viên hoặc đội thi (vd: Mỗi đội 3 thành viên, Đội 4 sinh viên)",
    )
    mode: Literal["online", "offline", "hybrid", "unknown"] = Field(
        default="unknown",
        description="Hình thức tổ chức cuộc thi: 'online', 'offline', 'hybrid', hoặc 'unknown'",
    )
    location: Optional[str] = Field(
        default=None,
        description="Địa điểm tổ chức nếu diễn ra offline/hybrid (vd: Trực tiếp tại RMIT TP.HCM & Hà Nội, Netcompany HCMC)",
    )
    participation_fee: Optional[str] = Field(
        default="Miễn phí",
        description="Lệ phí tham gia (Miễn phí / Free, hoặc chi tiết số tiền)",
    )
    total_prize_pool: Optional[str] = Field(
        default=None,
        description="Tổng giá trị giải thưởng công bố (vd: Hơn 300 triệu VNĐ, Up to VND 100M)",
    )
    prizes: list[PrizeTier] = Field(
        default_factory=list,
        description="Danh sách cơ cấu giải thưởng chi tiết và học bổng",
    )
    registration_start: Optional[str] = Field(
        default=None,
        description="Ngày bắt đầu mở cổng đăng ký",
    )
    registration_deadline: Optional[str] = Field(
        default=None,
        description="Hạn chót nộp hồ sơ hoặc đăng ký dự thi",
    )
    registration_status: Literal["open", "upcoming", "closed", "unknown"] = Field(
        default="unknown",
        description="Tình trạng đăng ký hiện tại (open, upcoming, closed, unknown)",
    )
    event_start: Optional[str] = Field(
        default=None,
        description="Ngày khai mạc hoặc bắt đầu sự kiện",
    )
    event_end: Optional[str] = Field(
        default=None,
        description="Ngày kết thúc hoặc vòng chung kết",
    )
    timeline_stages: list[TimelineStage] = Field(
        default_factory=list,
        description="Danh sách các vòng thi, mốc thời gian hoặc chặng đua",
    )
    challenge_overview: Optional[str] = Field(
        default=None,
        description="Mô tả tóm tắt đề bài, thử thách kỹ thuật hoặc bài toán cần giải quyết",
    )
    submission_platform: Optional[str] = Field(
        default=None,
        description="Nền tảng hoặc hình thức nộp bài (vd: Kaggle, Google Forms, GitHub, Nộp qua website)",
    )

    @field_validator("target_audience", mode="before")
    @classmethod
    def normalize_target_audience(cls, v):
        if isinstance(v, list):
            return ", ".join(str(item) for item in v if item)
        return clean_placeholder(v)

    @field_validator("category", "organizers", "partners_and_sponsors", mode="before")
    @classmethod
    def ensure_list_of_strings(cls, v):
        """Bảo đảm trường list[str] luôn hợp lệ dù LLM trả về str hay list hay None."""
        if v is None:
            return []
        if isinstance(v, str):
            cleaned = clean_placeholder(v)
            if not cleaned:
                return []
            if "," in cleaned:
                return [item.strip() for item in cleaned.split(",") if item.strip()]
            if ";" in cleaned:
                return [item.strip() for item in cleaned.split(";") if item.strip()]
            return [cleaned]
        if isinstance(v, list):
            res = []
            for item in v:
                if isinstance(item, str):
                    c = clean_placeholder(item)
                    if c:
                        res.append(c)
                elif item is not None:
                    res.append(str(item))
            return res
        return []

    @field_validator("prizes", "timeline_stages", mode="before")
    @classmethod
    def ensure_list_items(cls, v):
        """Chống lỗi khi LLM trả về None thay vì mảng rỗng."""
        if v is None:
            return []
        return v

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
        mode="before",
    )
    @classmethod
    def clean_string_placeholders(cls, v):
        return clean_placeholder(v)


class CompetitionExtractionResult(BaseModel):
    """Top-level container returned by LLM Instructor extraction.
    
    Handles documents with single competitions, multiple competitions (e.g. contest portals),
    or invalid/empty documents with no competitions.
    """

    is_competition: bool = Field(
        default=True,
        description="True nếu văn bản chứa thông tin về cuộc thi học thuật/kỹ thuật hợp lệ; False nếu văn bản trống, lỗi 404, hoặc không liên quan.",
    )
    reasoning: Optional[str] = Field(
        default=None,
        description="Giải thích ngắn gọn lý do tài liệu có hoặc không chứa cuộc thi",
    )
    competitions: list[Competition] = Field(
        default_factory=list,
        description="Danh sách các cuộc thi trích xuất được. Nếu chỉ có một cuộc thi, trả về danh sách 1 phần tử. Nếu không có, để trống.",
    )

    @field_validator("is_competition", mode="before")
    @classmethod
    def normalize_is_competition(cls, v):
        if isinstance(v, str):
            return v.strip().lower() in {"true", "1", "yes", "co"}
        if isinstance(v, bool):
            return v
        return bool(v)

    @field_validator("competitions", mode="before")
    @classmethod
    def ensure_competitions_list(cls, v):
        if v is None:
            return []
        if isinstance(v, dict):
            return [v]
        return v
