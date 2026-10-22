"""Data contracts and schemas for the Bronze Lakehouse layer.

Includes Pydantic v2 validation models and PyArrow schemas for Delta Lake.
"""

from datetime import datetime, timezone
import hashlib
import json
from typing import Any
import uuid

from pydantic import BaseModel, Field
import pyarrow as pa


class BronzeRecord(BaseModel):
    """Pydantic model representing an immutable raw web ingestion record."""

    raw_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique identifier for the raw crawl event",
    )
    source_url: str = Field(..., description="Target source URL crawled")
    source_domain: str = Field(..., description="Root domain of the target source (e.g. codetour.org)")
    crawled_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp of crawl event in UTC",
    )
    http_status: int = Field(default=200, description="HTTP response status code")
    content_type: str = Field(default="text/html", description="MIME content type")
    content_hash: str = Field(
        ...,
        description="SHA-256 cryptographic hash of uncompressed content for deduplication",
    )
    raw_html_bytes: bytes = Field(
        ...,
        description="Zstandard-compressed raw binary payload",
    )
    metadata_json: str = Field(
        default="{}",
        description="JSON string containing crawler metadata, HTTP headers, and context",
    )

    @classmethod
    def create(
        cls,
        source_url: str,
        source_domain: str,
        raw_html: str,
        compress_fn: Any,
        http_status: int = 200,
        content_type: str = "text/html",
        metadata: dict[str, Any] | None = None,
        crawled_at: datetime | None = None,
    ) -> "BronzeRecord":
        """Factory method to construct a BronzeRecord with automatic hashing and compression."""
        raw_bytes_uncompressed = raw_html.encode("utf-8")
        content_hash = hashlib.sha256(raw_bytes_uncompressed).hexdigest()
        compressed_bytes = compress_fn(raw_html)
        metadata_str = json.dumps(metadata or {}, ensure_ascii=False)

        return cls(
            source_url=source_url,
            source_domain=source_domain,
            crawled_at=crawled_at or datetime.now(timezone.utc),
            http_status=http_status,
            content_type=content_type,
            content_hash=content_hash,
            raw_html_bytes=compressed_bytes,
            metadata_json=metadata_str,
        )


# PyArrow Schema for Delta Lake table persistence
BRONZE_ARROW_SCHEMA = pa.schema([
    pa.field("raw_id", pa.string(), nullable=False),
    pa.field("source_url", pa.string(), nullable=False),
    pa.field("source_domain", pa.string(), nullable=False),
    pa.field("crawled_at", pa.timestamp("us", tz="UTC"), nullable=False),
    pa.field("http_status", pa.int32(), nullable=False),
    pa.field("content_type", pa.string(), nullable=False),
    pa.field("content_hash", pa.string(), nullable=False),
    pa.field("raw_html_bytes", pa.binary(), nullable=False),
    pa.field("metadata_json", pa.string(), nullable=True),
])


class PrizeItem(BaseModel):
    """Specific prize tier within a competition."""

    rank_name: str = Field(..., description="Tên hạng giải: Nhất, Nhì, Ba, Khuyến khích...")
    amount_vnd: int = Field(default=0, ge=0, description="Giá trị giải thưởng quy đổi VND")
    quantity: int = Field(default=1, ge=1, description="Số lượng suất giải")
    description: str = Field(default="", description="Chi tiết hiện vật hoặc quyền lợi kèm theo")


class SilverCompetitionRecord(BaseModel):
    """Pydantic v2 model representing a validated, structured, and deduplicated competition entity.

    Serves as the central data contract for the Silver Lakehouse Layer.
    """

    # 1. Identity & Provenance
    competition_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Định danh duy nhất UUID của thực thể cuộc thi tại tầng Silver",
    )
    canonical_name: str = Field(..., description="Tên chuẩn mực chính thức của cuộc thi")
    slug: str = Field(..., description="URL-friendly slug (ví dụ: code-tour-2026)")
    aliases: list[str] = Field(default_factory=list, description="Các tên gọi tương đương hoặc tên viết tắt")
    source_urls: list[str] = Field(
        default_factory=list,
        description="Danh sách các đường dẫn URL nguồn đã thu thập được",
    )
    primary_source: str = Field(..., description="URL nguồn có độ tin cậy cao nhất (Website BTC)")
    registration_link: str | None = Field(
        default=None,
        description="Đường dẫn trực tiếp tới cổng hoặc biểu mẫu đăng ký dự thi (Google Form, Portal...)",
    )
    raw_bronze_id: str | None = Field(default=None, description="Khóa ngoại liên kết tới bản ghi gốc Bronze raw_id")

    # 2. Organizer Dimension
    organizer_name: str = Field(..., description="Đơn vị chủ trì hoặc tổ chức chính")
    organizer_type: str = Field(
        default="enterprise",
        description="Phân loại đơn vị: 'enterprise', 'university', 'government', 'student_association', 'international'",
    )
    co_organizers: list[str] = Field(default_factory=list, description="Các đơn vị đồng tổ chức hoặc tài trợ chính")

    # 3. Temporal Dimension (Thời gian & Mùa vụ)
    edition_year: int = Field(default=2026, description="Năm tổ chức mùa giải")
    registration_start_date: str | None = Field(default=None, description="Ngày mở cổng đăng ký (YYYY-MM-DD)")
    registration_deadline: str | None = Field(default=None, description="Hạn chót đăng ký chính thức (YYYY-MM-DD)")
    event_start_date: str | None = Field(default=None, description="Ngày khởi tranh hoặc thi vòng đầu (YYYY-MM-DD)")
    event_end_date: str | None = Field(default=None, description="Ngày bế mạc hoặc chung kết (YYYY-MM-DD)")
    is_deadline_extended: bool = Field(default=False, description="Cờ đánh dấu hạn chót đã từng được gia hạn")
    season_quarter: str | None = Field(default=None, description="Quý diễn ra cuộc thi: 'Q1', 'Q2', 'Q3', 'Q4'")

    # 4. Domain & Category Dimension (Lĩnh vực & Kỹ năng)
    domain_categories: list[str] = Field(
        default_factory=list,
        description="Danh mục lĩnh vực: 'Algorithmic Coding', 'AI/ML', 'Data Engineering', 'Web/Mobile', 'Cybersecurity', 'Scientific Research'",
    )
    technical_tags: list[str] = Field(
        default_factory=list,
        description="Từ khóa kỹ thuật: 'Python', 'C++', 'PyTorch', 'SQL', 'NLP', 'Computer Vision'...",
    )
    competition_level: str = Field(
        default="national",
        description="Quy mô giải đấu: 'university', 'city', 'regional', 'national', 'international'",
    )

    # 5. Constraint & Eligibility Dimension (Điều kiện dự thi)
    target_audience: str = Field(default="", description="Đối tượng sinh viên hoặc giới hạn độ tuổi")
    min_team_size: int = Field(default=1, ge=1, le=20, description="Số lượng thành viên tối thiểu mỗi đội")
    max_team_size: int = Field(default=1, ge=1, le=20, description="Số lượng thành viên tối đa mỗi đội")
    is_individual_allowed: bool = Field(default=True, description="Cho phép cá nhân thi đấu độc lập")
    eligible_universities: list[str] = Field(
        default_factory=list,
        description="Danh sách trường đại học đủ điều kiện (để trống nếu dành cho toàn quốc)",
    )
    registration_fee_vnd: int = Field(default=0, ge=0, description="Lệ phí tham gia tính theo VND (0 là miễn phí)")

    # 6. Financial & Prize Dimension (Tài chính & Cơ cấu giải thưởng)
    total_prize_vnd: int = Field(default=0, ge=0, description="Tổng giá trị giải thưởng quy đổi VND")
    first_prize_vnd: int = Field(default=0, ge=0, description="Giá trị giải Nhất/Quán quân quy đổi VND")
    prizes: list[PrizeItem] = Field(default_factory=list, description="Chi tiết các hạng giải thưởng")

    # 7. Knowledge & RAG Rules Dimension (Tri thức thể lệ phục vụ RAG)
    summary_description: str = Field(default="", description="Tóm tắt ngắn gọn mục đích và nội dung cuộc thi")
    rules_document_url: str | None = Field(default=None, description="Đường dẫn tải tài liệu điều lệ hoặc file thể lệ PDF")
    rules_text_content: str | None = Field(default=None, description="Toàn văn thể lệ đã bóc tách phục vụ phân đoạn RAG")
    submission_format: str | None = Field(default=None, description="Hình thức nộp bài: GitHub, Slide, Báo cáo, Code trực tuyến")
    contact_email: str | None = Field(default=None, description="Email ban tổ chức liên hệ giải đáp thắc mắc")

    # 8. Auditing & Deduplication
    extraction_timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Thời điểm thực hiện trích xuất dữ liệu lớp Silver",
    )
    confidence_score: float = Field(default=1.0, ge=0.0, le=1.0, description="Điểm tin cậy của thuật toán trích xuất LLM")
    dedup_fingerprint: str = Field(default="", description="Mã băm đại diện so khớp khử trùng lặp sự kiện đa nguồn")

    def generate_fingerprint(self) -> str:
        """Generate deterministic fingerprint for entity resolution based on title, year, and organizer."""
        norm_title = "".join(self.canonical_name.lower().split())
        norm_org = "".join(self.organizer_name.lower().split())
        raw_key = f"{norm_title}::{self.edition_year}::{norm_org}"
        return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()

    def to_json_dict(self) -> dict[str, Any]:
        """Serialize entity to JSON-compatible dictionary."""
        return json.loads(self.model_dump_json())

