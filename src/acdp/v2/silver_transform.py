"""TASK-SLV-03: Silver Layer Hybrid Deterministic Sandwich & Clean Markdown (ACDP v2).

Implements decisions from TASK-BRZ-01, TASK-SLV-01, DIR-021, and DIR-022:
1. Reads Raw Rendered HTML (`*.html` with ACDP_PAGE_BOUNDARY) and backward-compatible
   legacy `.md` objects from Cloudflare R2 `bronze/`.
2. Runs Crawl4AI `DefaultMarkdownGenerator()` in RAM (0 ms browser) to generate
   Clean Markdown and uploads accepted competitions to `silver/markdown/`.
3. Executes Deterministic Extract (JSON-LD, og:*, canonical URL, outbound official
   links, optional .pdf/.docx rulebooks, regex hints) + DIR-022 Scope Gate
   (IT/AI/Data/Security/Coding, University Students, year in [current ± 1],
   official website required, media-partner deduplication) BEFORE calling
   Bounded LLM (Instructor).
4. Validates LLM output with Pydantic v2, applies post-LLM scope & canonical URL
   guards, and uploads Silver JSONs (`silver/extractions/`), batch manifest
   (`silver/batches/`), and transformation audit report (`silver/_reports/`) to R2.
"""

from __future__ import annotations

import argparse
import html as html_lib
import json
import os
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from urllib.parse import parse_qsl, urlencode, urljoin, urlparse, urlunparse

import instructor
from bs4 import BeautifulSoup
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
from dotenv import find_dotenv, load_dotenv

from acdp.config import settings
from acdp.v2.data_contracts import (
    DataContractViolationError,
    _build_gate_report,
    validate_bronze_to_silver_handoff,
    validate_silver_records_pydantic,
)
from acdp.v2.schemas import Competition, CompetitionExtractionResult

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv(find_dotenv(usecwd=True))

BUCKET_NAME = settings.bucket_name
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini/gemini-3.5-flash-lite")
OLLAMA_NUM_CTX = int(os.getenv("OLLAMA_NUM_CTX", "8192"))
DEFAULT_REFERENCE_YEAR = 2026

BRONZE_KEY_PATTERN = re.compile(
    r"^bronze/([^/]+)/year=(\d{4})/month=(\d{2})/day=(\d{2})/(\d+)(\.html)?$"
)
PAGE_BOUNDARY_RE = re.compile(
    r'<!--\s*ACDP_PAGE_BOUNDARY\s+url="([^"]*)"\s*-->'
)

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
MEDIA_NEWS_PATH_MARKERS = (
    "/tin-tuc/",
    "/bai-viet/",
    "/thong-bao/",
    "/su-kien/",
    "/news/",
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
TRACKING_PARAMS = frozenset(
    {
        "utm_source",
        "utm_medium",
        "utm_campaign",
        "utm_term",
        "utm_content",
        "fbclid",
        "gclid",
        "ref",
        "igshid",
    }
)

TECH_BOUNDARY_WORDS = frozenset({"ai", "it", "cntt", "data", "ml", "dl", "nlp", "cv", "iot", "ctf", "icpc", "olp"})
TECH_POSITIVE_TERMS = (
    "ai",
    "trí tuệ nhân tạo",
    "tri tue nhan tao",
    "artificial intelligence",
    "machine learning",
    "deep learning",
    "data science",
    "khoa học dữ liệu",
    "data analytics",
    "dữ liệu",
    "cntt",
    "công nghệ thông tin",
    "information technology",
    "lập trình",
    "lap trinh",
    "programming",
    "coding",
    "software",
    "phần mềm",
    "hackathon",
    "datathon",
    "makerthon",
    "cybersecurity",
    "an toàn thông tin",
    "an ninh mạng",
    "ctf",
    "icpc",
    "olympic tin học",
    "it",
    "generative ai",
    "genai",
    "llm",
    "mạng máy tính",
    "truyền thông dữ liệu",
    "kaggle",
    "algorithm",
    "thuật toán",
    "data analytics",
    "business intelligence",
    "power bi",
    "datadna",
)
NON_TECH_EXCLUSION_TERMS = (
    "marketingarena",
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
NOT_FOUND_MARKERS = (
    "404 not found",
    "page not found",
    "không tìm thấy trang",
    "không tồn tại trang",
    "403 forbidden",
    "access denied",
    "cloudflare ray id",
)

SYSTEM_PROMPT = """Bạn là chuyên gia Kỹ thuật Dữ liệu (Data Engineer) phụ trách bóc tách thông tin có cấu trúc từ tài liệu Clean Markdown và ngữ cảnh tất định (JSON-LD, OpenGraph, Regex) của các cuộc thi học thuật CNTT, AI, Khoa học Dữ liệu, An toàn Thông tin và Lập trình dành cho sinh viên.

Nhiệm vụ của bạn:
1. Kiểm tra ngữ cảnh và nội dung Clean Markdown để xác định xem đây có phải cuộc thi CNTT/AI/Dữ liệu/Bảo mật/Lập trình hợp lệ (`is_competition`) hay không.
   - Nếu là trang lỗi 404, điều hướng rỗng, hoặc không phải cuộc thi công nghệ: gán `is_competition = False` và `competitions = []`.
2. Tận dụng phần `Ngữ cảnh tất định đã trích xuất` (canonical URL, JSON-LD, og:*, ngày tháng, giải thưởng, thể lệ) để điền chính xác và tập trung suy luận vào các trường ngữ nghĩa:
   - `name`, `tagline`, `summary` (2-3 câu ngắn gọn).
   - `url`: Ưu tiên dùng URL trang web chính thức của cuộc thi nếu có trong ngữ cảnh tất định.
   - `organizers`, `partners_and_sponsors`, `category`, `target_audience`.
   - `team_size_min`, `team_size_max`, `team_description`, `is_individual_allowed`, `eligibility_level` ('undergraduate', 'all_students', 'open', 'unknown'), `allowed_majors`, `required_skills`.
   - `mode` ('online', 'offline', 'hybrid', 'unknown'), `location`.
   - `participation_fee`, `total_prize_pool`, `prizes` (kèm `quantity`, `currency`, `prize_type`).
   - `registration_start`, `registration_deadline`, `registration_status` ('open', 'upcoming', 'closed', 'unknown'), `event_start`, `event_end`, `timeline_stages`.
   - `challenge_overview`, `submission_platform`, `official_rules_url`, `organizer_contact`, `requires_advisor`, `team_registration_deadline`.
3. Nguyên tắc nghiêm ngặt:
   - Không có thông tin -> `None` (hoặc `[]`). Tuyệt đối không dùng 'N/A', 'None', 'Not specified', 'Unknown'.
   - Nếu `is_competition = True`, `competitions` bắt buộc có ít nhất 1 phần tử với `name` và `summary` đầy đủ."""


@dataclass
class DeterministicSignals:
    """Structured metadata extracted deterministically from Raw HTML and Clean Markdown."""

    source_domain: str
    source_url: str
    is_html: bool
    page_urls: list[str] = field(default_factory=list)
    canonical_url: str = ""
    canonical_official_url: str = ""
    is_media_or_aggregator: bool = False
    has_official_website: bool = False
    title: str = ""
    og_title: str = ""
    og_description: str = ""
    og_site_name: str = ""
    h1_title: str = ""
    json_ld: dict[str, Any] = field(default_factory=dict)
    official_rules_urls: list[str] = field(default_factory=list)
    candidate_official_urls: list[str] = field(default_factory=list)
    detected_dates: list[str] = field(default_factory=list)
    detected_years: list[int] = field(default_factory=list)
    detected_prizes: list[str] = field(default_factory=list)
    detected_team_bounds: tuple[int | None, int | None] = (None, None)
    detected_mode: str = "unknown"
    detected_fee: str | None = None

    def to_context_dict(self) -> dict[str, Any]:
        return {
            "source_domain": self.source_domain,
            "source_url": self.source_url,
            "canonical_official_url": self.canonical_official_url or None,
            "is_media_or_aggregator": self.is_media_or_aggregator,
            "title": self.og_title or self.title or self.h1_title or None,
            "description": self.og_description or None,
            "site_name": self.og_site_name or None,
            "json_ld": self.json_ld or None,
            "official_rules_urls": self.official_rules_urls[:5],
            "detected_dates": self.detected_dates[:10],
            "detected_years": self.detected_years,
            "detected_prizes": self.detected_prizes[:6],
            "detected_team_size": {
                "min": self.detected_team_bounds[0],
                "max": self.detected_team_bounds[1],
            },
            "detected_mode": self.detected_mode,
            "detected_fee": self.detected_fee,
        }


@dataclass
class ScopeDecision:
    """Result of deterministic DIR-022 scope & canonical deduplication gate."""

    accepted: bool
    reason: str
    canonical_official_url: str = ""
    merged_into_official_key: str | None = None


def normalize_url(raw_url: str | None) -> str:
    """Normalize HTTP(S) URL by lowering host, stripping tracking query params and fragments."""
    if not raw_url or not isinstance(raw_url, str):
        return ""
    stripped = raw_url.strip()
    if not stripped:
        return ""
    if "://" not in stripped and "." in stripped and not stripped.startswith("/"):
        stripped = f"https://{stripped}"
    parsed = urlparse(stripped)
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.netloc:
        return ""
    scheme = parsed.scheme.lower()
    netloc = parsed.netloc.lower()
    if netloc.endswith(":80") and scheme == "http":
        netloc = netloc[:-3]
    elif netloc.endswith(":443") and scheme == "https":
        netloc = netloc[:-4]
    cleaned_params = [
        (k, v)
        for k, v in parse_qsl(parsed.query, keep_blank_values=False)
        if k.lower() not in TRACKING_PARAMS and not k.lower().startswith("utm_")
    ]
    query = urlencode(sorted(cleaned_params))
    path = parsed.path or "/"
    if path != "/" and path.endswith("/"):
        path = path.rstrip("/")
    return urlunparse((scheme, netloc, path, "", query, ""))


def _canonical_domain(url: str) -> str:
    host = urlparse(url).netloc.lower()
    return host[4:] if host.startswith("www.") else host


def parse_bronze_key(fkey: str) -> dict[str, Any] | None:
    """Parse bronze/<domain>/year=<Y>/month=<M>/day=<D>/<ts>[.html]."""
    match = BRONZE_KEY_PATTERN.match(fkey)
    if not match:
        return None
    domain, year, month, day, ts, ext = match.groups()
    return {
        "key": fkey,
        "domain": domain,
        "date": f"{year}-{month}-{day}",
        "timestamp": int(ts),
        "format": "html" if ext == ".html" else "markdown",
    }


def is_html_payload(raw_content: str, key_format: str = "html") -> bool:
    """Detect whether a Bronze object contains HTML (with optional boundary) or legacy Markdown."""
    if key_format == "html":
        return True
    sample = raw_content.lstrip()[:400].lower()
    return (
        sample.startswith("<!doctype")
        or sample.startswith("<html")
        or "<!-- acdp_page_boundary" in sample
    )


def split_bronze_pages(raw_content: str, fallback_domain: str) -> list[tuple[str, str]]:
    """Split multi-page Bronze HTML packaged with ACDP_PAGE_BOUNDARY into (url, html) pairs."""
    matches = list(PAGE_BOUNDARY_RE.finditer(raw_content))
    if not matches:
        fallback_url = f"https://{fallback_domain}/"
        return [(fallback_url, raw_content.strip())]

    pages: list[tuple[str, str]] = []
    for idx, m in enumerate(matches):
        page_url = html_lib.unescape(m.group(1)).strip() or f"https://{fallback_domain}/"
        start = m.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(raw_content)
        chunk = raw_content[start:end].strip()
        if chunk:
            pages.append((page_url, chunk))
    return pages or [(f"https://{fallback_domain}/", raw_content.strip())]


def clean_markdown_text(raw_md: str) -> str:
    """Remove markdown image/SVG clutter, empty links, anchor links, and duplicate lines."""
    if not raw_md:
        return ""
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", raw_md)
    text = re.sub(r"\[\s*\]\([^)]*\)", "", text)
    text = re.sub(r"\[([^\]]+)\]\(#[^)]*\)", r"\1", text)
    text = re.sub(r"data:image/[^;\s]+;base64,[A-Za-z0-9+/=]+", "", text)

    seen_long_lines: set[str] = set()
    lines: list[str] = []
    for line in text.splitlines():
        key = line.strip()
        if key and len(key) > 35 and key in seen_long_lines:
            continue
        if key and len(key) > 35:
            seen_long_lines.add(key)
        lines.append(line)

    cleaned = "\n".join(lines)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def html_to_clean_markdown(
    pages: list[tuple[str, str]],
    md_generator: DefaultMarkdownGenerator | None = None,
) -> str:
    """Convert one or more (url, html) pages into Clean Markdown strictly in RAM."""
    generator = md_generator or DefaultMarkdownGenerator(
        options={"ignore_images": True, "body_width": 0}
    )
    sections: list[str] = []
    for page_url, page_html in pages:
        result = generator.generate_markdown(
            input_html=page_html,
            base_url=page_url,
            citations=False,
        )
        raw_md = getattr(result, "raw_markdown", "") or ""
        cleaned = clean_markdown_text(raw_md)
        if not cleaned:
            continue
        if len(pages) > 1:
            sections.append(f"<!-- source_page: {page_url} -->\n{cleaned}")
        else:
            sections.append(cleaned)
    return "\n\n---\n\n".join(sections).strip()


def build_bounded_llm_markdown(clean_md: str, max_chars: int = 16000) -> str:
    """Bound Clean Markdown length for LLM prompt without losing high-signal paragraphs."""
    if len(clean_md) <= max_chars:
        return clean_md
    keywords = (
        "cuộc thi",
        "hội thi",
        "thể lệ",
        "giải thưởng",
        "thời gian",
        "hạn chót",
        "đăng ký",
        "đối tượng",
        "vòng",
        "chung kết",
        "prize",
        "deadline",
        "timeline",
        "challenge",
        "hackathon",
        "datathon",
        "organizer",
        "eligibility",
        "submission",
        "team",
        "đội",
    )
    paragraphs = clean_md.split("\n\n")
    selected = [
        p
        for p in paragraphs
        if p.strip().startswith(("#", "- ", "* ")) or any(kw in p.lower() for kw in keywords)
    ]
    bounded = "\n\n".join(selected) if selected else clean_md
    return bounded[:max_chars].strip()


def _extract_json_ld_summary(soup: BeautifulSoup) -> dict[str, Any]:
    """Extract Schema.org Event/Hackathon/Competition properties from JSON-LD scripts."""
    summary: dict[str, Any] = {}
    for script in soup.find_all("script", attrs={"type": re.compile(r"application/ld\+json", re.I)}):
        raw = (script.string or script.get_text() or "").strip()
        if not raw:
            continue
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            continue

        nodes: list[dict[str, Any]] = []
        stack: list[Any] = [payload]
        while stack:
            curr = stack.pop()
            if isinstance(curr, list):
                stack.extend(curr)
            elif isinstance(curr, dict):
                if "@graph" in curr and isinstance(curr["@graph"], list):
                    stack.extend(curr["@graph"])
                nodes.append(curr)

        for node in nodes:
            raw_type = node.get("@type", "")
            types = [raw_type] if isinstance(raw_type, str) else list(raw_type or [])
            joined_types = " ".join(str(t).lower() for t in types)
            is_event = any(k in joined_types for k in ("event", "hackathon", "competition", "contest"))
            if is_event or ("startDate" in node and "name" in node):
                for key in ("name", "description", "startDate", "endDate", "url", "sameAs"):
                    if node.get(key) and key not in summary:
                        summary[key] = node[key]
                org = node.get("organizer")
                if isinstance(org, dict) and org.get("name"):
                    summary.setdefault("organizer", org["name"])
                elif isinstance(org, list):
                    org_names = [o.get("name") for o in org if isinstance(o, dict) and o.get("name")]
                    if org_names:
                        summary.setdefault("organizer", org_names)
                loc = node.get("location")
                if isinstance(loc, dict) and (loc.get("name") or loc.get("address")):
                    summary.setdefault("location", loc.get("name") or loc.get("address"))
                elif isinstance(loc, str) and loc.strip():
                    summary.setdefault("location", loc.strip())
    return summary


def is_media_or_aggregator_url(url: str) -> bool:
    """Return True if URL is a third-party competition aggregator or news/media-partner post."""
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    path = parsed.path.lower()
    if host in AGGREGATOR_HOSTS:
        return True
    if any(marker in path for marker in MEDIA_NEWS_PATH_MARKERS):
        return True
    return False


def _score_official_link(
    href_norm: str,
    anchor_text: str,
    source_domain: str,
) -> int:
    """Score an outbound link as a potential Canonical Official Competition Website."""
    parsed = urlparse(href_norm)
    host = parsed.netloc.lower()
    bare_host = _canonical_domain(href_norm)
    bare_src = source_domain[4:] if source_domain.startswith("www.") else source_domain

    if not host or bare_host == bare_src or bare_host.endswith(f".{bare_src}") or bare_src.endswith(f".{bare_host}"):
        return -100
    if host in SOCIAL_OR_FORM_HOSTS or host in AGGREGATOR_HOSTS or any(
        bare_host == agg or bare_host.endswith(f".{agg}") for agg in AGGREGATOR_HOSTS
    ):
        return -100
    # Ignore generic university/gov sibling portals and non-competition subdomains/paths
    if any(
        bare_host.startswith(prefix)
        for prefix in ("tuyensinh.", "alumni.", "khcn.", "daotao.", "ctsv.", "tracuu.", "jst-", "vieclam.", "portal.")
    ):
        return -100
    path_lower = parsed.path.lower()
    if any(tok in path_lower for tok in ("/admissions", "/msc-programmes", "/graduate-studies", "/tuyen-dung")):
        return -100
    if any(path_lower.endswith(ext) for ext in (".png", ".jpg", ".jpeg", ".svg", ".css", ".js", ".pdf", ".docx")):
        return -50

    score = 10
    text_lower = anchor_text.lower()
    if any(kw in text_lower for kw in ("website chính thức", "trang chủ", "official website", "official site", "landing page", "trang web cuộc thi")):
        score += 40
    elif any(kw in text_lower for kw in ("thông tin chi tiết", "chi tiết cuộc thi", "đăng ký", "thể lệ", "tại đây", "website", "portal")):
        score += 20
    if any(tok in bare_host for tok in ("hackathon", "datathon", "challenge", "codetour", "thucchien", "arena", "dataforlife", "olympic", "contest", "aisc")):
        score += 30
    if path_lower in {"", "/"}:
        score += 10
    return score


RULES_PAGE_KEYWORDS = (
    "thể lệ",
    "the le",
    "regulations",
    "rules & regulations",
    "rules of ",
    "official rules",
    "handbook",
)
RULES_URL_MARKERS = ("/the-le", "/regulations", "/rules", "the-le", "rules-of-")
NON_RULES_BLACKLIST = (
    "quy chế dân chủ",
    "nội quy cơ quan",
    "bảo đảm an toàn thông tin",
    "chính sách bảo mật",
    "điều khoản sử dụng",
    "privacy",
    "terms of service",
    "nq_hdt",
    "noi_quy",
)
NOISY_CONTAINER_MARKERS = (
    "rpa__media",
    "slick-slide",
    "sidebar",
    "navbar",
    "footer",
    "related-posts",
    "breadcrumb",
)


def _prune_layout_noise(soup: BeautifulSoup) -> BeautifulSoup:
    """Return a cloned BeautifulSoup with nav/header/footer/aside/ad-banners removed."""
    cloned = BeautifulSoup(str(soup), "html.parser")
    for tag in cloned.find_all(["nav", "header", "footer", "aside"]):
        tag.decompose()
    for elem in list(cloned.find_all(class_=True)):
        if getattr(elem, "attrs", None) is None:
            continue
        cls_text = " ".join(str(c) for c in (elem.get("class") or [])).lower()
        if any(marker in cls_text for marker in NOISY_CONTAINER_MARKERS):
            elem.decompose()
    return cloned


def _is_competition_rules_link(abs_url: str, anchor_text: str) -> bool:
    """Identify dedicated rulebook PDFs or official rules/handbook pages while rejecting unrelated policies."""
    path_lower = urlparse(abs_url).path.lower()
    text_lower = anchor_text.lower().strip()
    combined = f"{text_lower} {path_lower}"
    if any(bad in combined for bad in NON_RULES_BLACKLIST):
        return False
    if path_lower.endswith((".pdf", ".docx", ".doc")):
        return True
    if any(kw in text_lower for kw in RULES_PAGE_KEYWORDS) or any(m in path_lower for m in RULES_URL_MARKERS):
        return urlparse(abs_url).netloc.lower() not in SOCIAL_OR_FORM_HOSTS
    return False


def _extract_links_from_soup(
    soup: BeautifulSoup,
    base_url: str,
    source_domain: str,
) -> tuple[list[str], list[str]]:
    """Extract candidate official website URLs (main content only) and official rules URLs."""
    scored_official: list[tuple[int, str]] = []
    rulebook_urls: list[str] = []

    main_soup = _prune_layout_noise(soup)
    # Fallback to full soup only if document has no non-landmark links (e.g. minimal HTML fixtures)
    scan_soup = main_soup if main_soup.find("a", href=True) else soup

    for a in scan_soup.find_all("a", href=True):
        raw_href = str(a["href"]).strip()
        if not raw_href or raw_href.startswith(("#", "mailto:", "tel:", "javascript:")):
            continue
        abs_url = normalize_url(urljoin(base_url, raw_href))
        if not abs_url:
            continue
        path_lower = urlparse(abs_url).path.lower()
        anchor_text = a.get_text(" ", strip=True)

        if path_lower.endswith((".pdf", ".docx", ".doc")):
            if _is_competition_rules_link(abs_url, anchor_text) and abs_url not in rulebook_urls:
                rulebook_urls.append(abs_url)
            continue

        score = _score_official_link(abs_url, anchor_text, source_domain)
        if score > 0:
            scored_official.append((score, abs_url))

    # Dedicated rules links (/the-le, /regulations, Handbook) may live in top nav or body
    for a in soup.find_all("a", href=True):
        raw_href = str(a["href"]).strip()
        if not raw_href or raw_href.startswith(("#", "mailto:", "tel:", "javascript:")):
            continue
        abs_url = normalize_url(urljoin(base_url, raw_href))
        if not abs_url:
            continue
        path_lower = urlparse(abs_url).path.lower()
        if path_lower.endswith((".pdf", ".docx", ".doc")):
            continue
        anchor_text = a.get_text(" ", strip=True)
        if _is_competition_rules_link(abs_url, anchor_text) and abs_url not in rulebook_urls:
            rulebook_urls.append(abs_url)

    scored_official.sort(key=lambda item: item[0], reverse=True)
    dedup_official: list[str] = []
    seen: set[str] = set()
    for _, url in scored_official:
        if url not in seen:
            seen.add(url)
            dedup_official.append(url)
    return dedup_official, rulebook_urls


def _extract_regex_hints(clean_md: str) -> dict[str, Any]:
    """Extract deterministic dates, years, prizes, team size, mode, and fee hints from Markdown."""
    dates = re.findall(r"\b(?:\d{1,2}/\d{1,2}/20\d{2}|20\d{2}-\d{2}-\d{2})\b", clean_md)
    years = sorted({int(y) for y in re.findall(r"\b(20[2-3]\d)\b", clean_md)})
    prizes = re.findall(
        r"(?:\$?\s*\d[\d.,]*\s*(?:tỷ|triệu|tr|million|M|USD|VNĐ|VND)\b|\$\s*\d[\d.,]+)",
        clean_md,
        flags=re.IGNORECASE,
    )

    team_min: int | None = None
    team_max: int | None = None
    range_match = re.search(
        r"(?:đội|team|nhóm)\s*(?:từ\s*)?(\d{1,2})\s*[-–đến]+\s*(\d{1,2})\s*(?:thành viên|sinh viên|người|members?)",
        clean_md,
        flags=re.IGNORECASE,
    )
    if range_match:
        a, b = int(range_match.group(1)), int(range_match.group(2))
        if 1 <= a <= b <= 20:
            team_min, team_max = a, b
    else:
        exact_match = re.search(
            r"(?:each team must consist of|mỗi đội(?: gồm)?|đội thi)\s*(\d{1,2})\s*(?:thành viên|sinh viên|người|students?|members?)",
            clean_md,
            flags=re.IGNORECASE,
        )
        if exact_match:
            val = int(exact_match.group(1))
            if 1 <= val <= 20:
                team_min = team_max = val

    lower = clean_md.lower()
    has_online = any(k in lower for k in ("online", "trực tuyến"))
    has_offline = any(k in lower for k in ("offline", "trực tiếp", "tại campus", "tại hà nội", "tại tp.hcm"))
    if "hybrid" in lower or (has_online and has_offline):
        mode = "hybrid"
    elif has_offline:
        mode = "offline"
    elif has_online:
        mode = "online"
    else:
        mode = "unknown"

    fee: str | None = None
    if any(k in lower for k in ("miễn phí", "free of charge", "không thu phí", "0 đ", "free entry")):
        fee = "Miễn phí"

    return {
        "dates": list(dict.fromkeys(dates)),
        "years": years,
        "prizes": list(dict.fromkeys(p.strip() for p in prizes)),
        "team_bounds": (team_min, team_max),
        "mode": mode,
        "fee": fee,
    }


def extract_deterministic_signals(
    pages: list[tuple[str, str]],
    clean_md: str,
    source_domain: str,
    is_html: bool = True,
) -> DeterministicSignals:
    """Run Stage 1 deterministic extraction over Raw HTML pages and Clean Markdown."""
    primary_url = normalize_url(pages[0][0]) if pages else f"https://{source_domain}/"
    signals = DeterministicSignals(
        source_domain=source_domain,
        source_url=primary_url,
        is_html=is_html,
        page_urls=[normalize_url(u) or u for u, _ in pages],
    )

    if is_html:
        all_official_candidates: list[str] = []
        all_rules: list[str] = []
        is_primary_aggregator = is_media_or_aggregator_url(primary_url)
        for idx, (page_url, page_html) in enumerate(pages):
            soup = BeautifulSoup(page_html, "html.parser")
            if idx == 0:
                if soup.title and soup.title.string:
                    signals.title = soup.title.string.strip()
                h1 = soup.find("h1")
                if h1:
                    signals.h1_title = h1.get_text(" ", strip=True)
                canon_tag = soup.find("link", attrs={"rel": lambda v: v and "canonical" in v})
                if canon_tag and canon_tag.get("href"):
                    signals.canonical_url = normalize_url(urljoin(page_url, str(canon_tag["href"])))

                for prop, attr_name in (
                    ("og:title", "og_title"),
                    ("og:description", "og_description"),
                    ("og:site_name", "og_site_name"),
                ):
                    meta = soup.find("meta", attrs={"property": prop})
                    if meta and meta.get("content"):
                        setattr(signals, attr_name, str(meta["content"]).strip())
                if not signals.og_description:
                    desc_meta = soup.find("meta", attrs={"name": re.compile(r"^description$", re.I)})
                    if desc_meta and desc_meta.get("content"):
                        signals.og_description = str(desc_meta["content"]).strip()
                if not signals.canonical_url:
                    og_url = soup.find("meta", attrs={"property": "og:url"})
                    if og_url and og_url.get("content"):
                        signals.canonical_url = normalize_url(str(og_url["content"]))

            ld_data = _extract_json_ld_summary(soup)
            for k, v in ld_data.items():
                signals.json_ld.setdefault(k, v)

            # For aggregators/media news posts, only scan the primary article page (idx == 0)
            # so adaptive-crawled feed/sidebar pages cannot pollute official link candidates.
            if is_primary_aggregator and idx > 0:
                continue

            cand_official, cand_rules = _extract_links_from_soup(soup, page_url, source_domain)
            for u in cand_official:
                if u not in all_official_candidates:
                    all_official_candidates.append(u)
            for r in cand_rules:
                if r not in all_rules:
                    all_rules.append(r)

        signals.candidate_official_urls = all_official_candidates
        signals.official_rules_urls = all_rules

    base_source = signals.canonical_url or signals.source_url
    signals.is_media_or_aggregator = is_media_or_aggregator_url(base_source)
    base_host = _canonical_domain(base_source) if base_source else ""
    is_third_party_aggregator = base_host in AGGREGATOR_HOSTS

    if signals.is_media_or_aggregator:
        ld_url = normalize_url(str(signals.json_ld.get("url") or ""))
        if ld_url and not is_media_or_aggregator_url(ld_url) and urlparse(ld_url).netloc.lower() not in SOCIAL_OR_FORM_HOSTS:
            signals.canonical_official_url = ld_url
            signals.has_official_website = True
        elif signals.candidate_official_urls:
            signals.canonical_official_url = signals.candidate_official_urls[0]
            signals.has_official_website = True
        elif not is_third_party_aggregator and (base_host.endswith(".edu.vn") or base_host.endswith(".gov.vn")):
            # Official university/government announcement without a separate microsite serves as its own official URL
            signals.canonical_official_url = base_source
            signals.has_official_website = bool(base_source)
        else:
            signals.canonical_official_url = ""
            signals.has_official_website = False
    else:
        signals.canonical_official_url = base_source
        signals.has_official_website = bool(base_source)

    regex_hints = _extract_regex_hints(clean_md)
    signals.detected_dates = regex_hints["dates"]
    signals.detected_years = regex_hints["years"]
    signals.detected_prizes = regex_hints["prizes"]
    signals.detected_team_bounds = regex_hints["team_bounds"]
    signals.detected_mode = regex_hints["mode"]
    signals.detected_fee = regex_hints["fee"]
    return signals


def _contains_tech_term(text_lower: str) -> bool:
    for term in TECH_POSITIVE_TERMS:
        if term in TECH_BOUNDARY_WORDS:
            if re.search(rf"\b{re.escape(term)}\b", text_lower):
                return True
        elif term in text_lower:
            return True
    return False


def _has_school_only_audience(text_lower: str) -> bool:
    has_school = any(term in text_lower for term in SCHOOL_ONLY_TERMS)
    has_university = any(term in text_lower for term in STUDENT_POSITIVE_TERMS)
    return has_school and not has_university


def evaluate_pre_llm_scope(
    signals: DeterministicSignals,
    clean_md: str,
    known_official_domains: set[str] | None = None,
    reference_year: int = DEFAULT_REFERENCE_YEAR,
) -> ScopeDecision:
    """Stage 2 Deterministic Gate enforcing DIR-022 scope and media-partner deduplication."""
    if not clean_md or len(clean_md.strip()) < 200:
        return ScopeDecision(accepted=False, reason="empty_or_too_short")

    combined_text = " ".join(
        part
        for part in (
            signals.source_domain,
            signals.source_url,
            signals.og_title,
            signals.title,
            signals.h1_title,
            signals.og_description,
            clean_md[:12000],
        )
        if part
    )
    lower = combined_text.lower()

    if any(marker in lower for marker in NOT_FOUND_MARKERS) and len(clean_md) < 1500:
        return ScopeDecision(accepted=False, reason="http_error_or_404_page")

    # 1. Official website requirement & Media-partner resolution (DIR-022)
    if not signals.has_official_website or not signals.canonical_official_url:
        return ScopeDecision(accepted=False, reason="no_official_website")

    if signals.is_media_or_aggregator and known_official_domains:
        resolved_domain = _canonical_domain(signals.canonical_official_url)
        if resolved_domain in known_official_domains:
            return ScopeDecision(
                accepted=False,
                reason="media_partner_merged_to_official",
                canonical_official_url=signals.canonical_official_url,
                merged_into_official_key=resolved_domain,
            )

    # 2. Domain Relevance Gate (IT / AI / Data / Security / Coding)
    has_tech = _contains_tech_term(lower)
    has_non_tech_marker = any(term in lower for term in NON_TECH_EXCLUSION_TERMS)
    if not has_tech or (has_non_tech_marker and not any(k in lower for k in ("hackathon", "datathon", "lập trình", "trí tuệ nhân tạo", "an toàn thông tin"))):
        return ScopeDecision(accepted=False, reason="out_of_scope_non_tech")

    # 3. University Student Gate
    if _has_school_only_audience(lower):
        return ScopeDecision(accepted=False, reason="out_of_scope_non_university")

    # 4. Temporal Window Gate: [reference_year - 1, reference_year + 1]
    min_year, max_year = reference_year - 1, reference_year + 1
    if signals.detected_years:
        in_window = [y for y in signals.detected_years if min_year <= y <= max_year]
        if not in_window:
            return ScopeDecision(accepted=False, reason="out_of_scope_year")

    return ScopeDecision(
        accepted=True,
        reason="accepted",
        canonical_official_url=signals.canonical_official_url,
    )


def build_llm_user_prompt(signals: DeterministicSignals, clean_md: str) -> str:
    """Build bounded user prompt injecting deterministic context before Clean Markdown."""
    bounded_md = build_bounded_llm_markdown(clean_md, max_chars=16000)
    context_json = json.dumps(signals.to_context_dict(), ensure_ascii=False, indent=2)
    return (
        f"Source Domain: {signals.source_domain}\n"
        f"Canonical Official URL: {signals.canonical_official_url or signals.source_url}\n\n"
        f"Ngữ cảnh tất định đã trích xuất (JSON-LD / og:* / Regex):\n```json\n{context_json}\n```\n\n"
        f"Nội dung Clean Markdown cần bóc tách:\n\n{bounded_md}"
    )


def _create_instructor_client():
    """Initialize Instructor client (Gemini OpenAI-compatible endpoint, Ollama, or LiteLLM)."""
    gemini_key = settings.gemini_api_key or settings.google_api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if gemini_key and "your_gemini" not in gemini_key:
        from openai import OpenAI

        raw_client = OpenAI(
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
            api_key=gemini_key,
            timeout=45.0,
        )
        return instructor.from_openai(raw_client, mode=instructor.Mode.JSON)
    if "ollama" in LLM_PROVIDER.lower():
        return instructor.from_provider(LLM_PROVIDER, mode=instructor.Mode.JSON)
    return instructor.from_provider(LLM_PROVIDER)


def extract_competition_hybrid(
    client: Any,
    signals: DeterministicSignals,
    clean_md: str,
) -> CompetitionExtractionResult:
    """Run Stage 3 Bounded LLM extraction via Instructor + Pydantic v2."""
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": build_llm_user_prompt(signals, clean_md)},
    ]
    extra_kwargs: dict[str, Any] = {}
    if "ollama" in LLM_PROVIDER.lower():
        extra_kwargs["extra_body"] = {"options": {"num_ctx": OLLAMA_NUM_CTX}}

    chosen_model = os.getenv("LLM_MODEL") or settings.get_chat_model() or "gemini-3.5-flash-lite"
    if "/" in chosen_model:
        chosen_model = chosen_model.split("/")[-1]

    return client.chat.completions.create(
        model=chosen_model,
        response_model=CompetitionExtractionResult,
        messages=messages,
        max_retries=2,
        **extra_kwargs,
    )


def apply_post_llm_guards(
    result: CompetitionExtractionResult,
    signals: DeterministicSignals,
    reference_year: int = DEFAULT_REFERENCE_YEAR,
) -> CompetitionExtractionResult:
    """Stage 4 deterministic post-LLM validation, canonical URL enforcement, and scope re-check."""
    if not result.is_competition or not result.competitions:
        return CompetitionExtractionResult(
            is_competition=False,
            reasoning=result.reasoning or "No valid competition extracted.",
            competitions=[],
        )

    min_year, max_year = reference_year - 1, reference_year + 1
    filtered: list[Competition] = []
    for comp in result.competitions:
        resolved_url = normalize_url(comp.url) or signals.canonical_official_url
        if is_media_or_aggregator_url(resolved_url) and signals.canonical_official_url:
            resolved_url = signals.canonical_official_url
        if not resolved_url or is_media_or_aggregator_url(resolved_url):
            continue

        text_blob = " ".join(
            [
                comp.name,
                comp.summary,
                " ".join(comp.category),
                str(comp.target_audience or ""),
                comp.challenge_overview or "",
            ]
        ).lower()

        if not _contains_tech_term(text_blob):
            continue
        if _has_school_only_audience(text_blob):
            continue

        date_text = " ".join(
            str(d)
            for d in (
                comp.registration_start,
                comp.registration_deadline,
                comp.event_start,
                comp.event_end,
                comp.name,
            )
            if d
        )
        comp_years = [int(y) for y in re.findall(r"\b(20[2-3]\d)\b", date_text)]
        if comp_years and not any(min_year <= y <= max_year for y in comp_years):
            continue

        default_rules_url = signals.official_rules_urls[0] if signals.official_rules_urls else None
        filtered.append(
            comp.model_copy(
                update={
                    "url": resolved_url,
                    "source_url": comp.source_url or signals.source_url,
                    "official_rules_url": comp.official_rules_url or default_rules_url,
                }
            )
        )

    return CompetitionExtractionResult(
        is_competition=bool(filtered),
        reasoning=result.reasoning,
        competitions=filtered,
    )


def _upload_silver_markdown(
    s3_client: Any,
    bucket_name: str,
    clean_md: str,
    domain: str,
    crawl_date: str,
    timestamp: int,
    source_url: str,
    canonical_url: str,
    bronze_key: str,
) -> str:
    """Upload Clean Markdown to s3://<bucket>/silver/markdown/.../*.md."""
    safe_domain = re.sub(r"[^\w\-.]", "_", domain)
    year, month, day = crawl_date.split("-")
    md_key = f"silver/markdown/{safe_domain}/year={year}/month={month}/day={day}/{timestamp}.md"
    s3_client.put_object(
        Bucket=bucket_name,
        Key=md_key,
        Body=clean_md.encode("utf-8"),
        ContentType="text/markdown; charset=utf-8",
        Metadata={
            "layer": "silver",
            "source": domain,
            "source_url": source_url[:512],
            "canonical_url": canonical_url[:512],
            "crawl_date": crawl_date,
            "crawl_timestamp": str(timestamp),
            "bronze_key": bronze_key[:512],
        },
    )
    return md_key


def _upload_silver_extraction(
    s3_client: Any,
    bucket_name: str,
    record: dict[str, Any],
    domain: str,
    crawl_date: str,
    timestamp: int,
) -> str:
    """Upload Silver JSON extraction compatible with 4_analytics_gold.py."""
    safe_domain = re.sub(r"[^\w\-.]", "_", domain)
    year, month, day = crawl_date.split("-")
    silver_key = f"silver/extractions/{safe_domain}/year={year}/month={month}/day={day}/{timestamp}.json"
    s3_client.put_object(
        Bucket=bucket_name,
        Key=silver_key,
        Body=json.dumps(record, ensure_ascii=False, indent=2).encode("utf-8"),
        ContentType="application/json; charset=utf-8",
        Metadata={"source": domain, "layer": "silver", "crawl_date": crawl_date},
    )
    return silver_key


def _select_bronze_snapshots(
    s3_client: Any,
    bucket_name: str,
    target_date: str | None = None,
    process_all_dates: bool = False,
) -> tuple[str, list[dict[str, Any]]]:
    """List Bronze objects and deduplicate same-(domain, source_url) crawls by latest timestamp."""
    paginator = s3_client.get_paginator("list_objects_v2")
    raw_items: list[dict[str, Any]] = []
    for page in paginator.paginate(Bucket=bucket_name, Prefix="bronze/"):
        for obj in page.get("Contents", []):
            fkey = obj["Key"]
            if obj.get("Size", 0) == 0 or fkey.endswith("/"):
                continue
            parsed = parse_bronze_key(fkey)
            if parsed:
                parsed["size"] = obj.get("Size", 0)
                raw_items.append(parsed)

    if not raw_items:
        return "", []

    available_dates = sorted({it["date"] for it in raw_items})
    if process_all_dates:
        chosen_date = "all_dates"
        selected = raw_items
    else:
        if target_date:
            if target_date not in available_dates:
                raise ValueError(f"Ngày '{target_date}' không có dữ liệu Bronze. Khả dụng: {available_dates}")
            chosen_date = target_date
        else:
            today = datetime.now(UTC).strftime("%Y-%m-%d")
            chosen_date = today if today in available_dates else available_dates[-1]
        selected = [it for it in raw_items if it["date"] == chosen_date]

    # Read content once and group by (domain, primary_source_url) so distinct URLs on an aggregator
    # (e.g. multiple ybox.vn posts) are preserved while duplicate crawls of the same URL collapse.
    grouped: dict[tuple[str, str], dict[str, Any]] = {}
    for it in selected:
        resp = s3_client.get_object(Bucket=bucket_name, Key=it["key"])
        body_text = resp["Body"].read().decode("utf-8", errors="replace")
        is_html = is_html_payload(body_text, it["format"])
        pages = split_bronze_pages(body_text, it["domain"]) if is_html else [(f"https://{it['domain']}/", body_text)]
        first_url = normalize_url(pages[0][0]) or f"https://{it['domain']}/"
        group_key = (it["domain"], first_url)

        existing = grouped.get(group_key)
        if existing is None or (it["timestamp"], it["format"] == "html") > (
            existing["timestamp"],
            existing["format"] == "html",
        ):
            grouped[group_key] = {
                **it,
                "raw_text": body_text,
                "is_html": is_html,
                "pages": pages,
                "source_url": first_url,
            }

    return chosen_date, sorted(grouped.values(), key=lambda x: (x["domain"], x["timestamp"]))


def run_silver_transform(
    run_llm: bool = False,
    target_date: str | None = None,
    process_all_dates: bool = False,
    dry_run: bool = False,
    max_items: int = 0,
    reference_year: int = DEFAULT_REFERENCE_YEAR,
    strict_gate: bool = False,
) -> dict[str, Any]:
    """Execute Hybrid Deterministic Sandwich Silver transformation over R2 Bronze."""
    if not settings.bucket_name:
        raise RuntimeError("BUCKET_NAME is required in .env for Cloudflare R2 access.")

    s3_client = settings.create_r2_client()
    chosen_date, snapshots = _select_bronze_snapshots(
        s3_client=s3_client,
        bucket_name=settings.bucket_name,
        target_date=target_date,
        process_all_dates=process_all_dates,
    )
    if not snapshots:
        print(">> [INFO] Không tìm thấy snapshot Bronze hợp lệ.")
        return {"chosen_date": chosen_date, "total_snapshots": 0, "accepted": 0, "dropped": 0}

    if max_items > 0:
        snapshots = snapshots[:max_items]

    md_generator = DefaultMarkdownGenerator(options={"ignore_images": True, "body_width": 0})

    # Pre-pass 1: Deterministic extraction & Clean Markdown in RAM for all snapshots
    prepared: list[dict[str, Any]] = []
    known_official_domains: set[str] = set()
    for snap in snapshots:
        if snap["is_html"]:
            clean_md = html_to_clean_markdown(snap["pages"], md_generator=md_generator)
        else:
            clean_md = clean_markdown_text(snap["raw_text"])

        signals = extract_deterministic_signals(
            pages=snap["pages"],
            clean_md=clean_md,
            source_domain=snap["domain"],
            is_html=snap["is_html"],
        )
        if not signals.is_media_or_aggregator and signals.canonical_official_url:
            known_official_domains.add(_canonical_domain(signals.canonical_official_url))

        prepared.append({"snap": snap, "clean_md": clean_md, "signals": signals})

    client = _create_instructor_client() if (run_llm and not dry_run) else None
    accepted_records: list[dict[str, Any]] = []
    seen_canonical_urls: set[str] = set()
    audit_entries: list[dict[str, Any]] = []
    drop_counts: dict[str, int] = defaultdict(int)
    uploaded_md_keys: list[str] = []
    uploaded_json_keys: list[str] = []
    contract_gate_failures = 0

    for item in prepared:
        snap = item["snap"]
        clean_md: str = item["clean_md"]
        signals: DeterministicSignals = item["signals"]

        handoff_rule = validate_bronze_to_silver_handoff(snap["key"], snap["source_url"], clean_md)
        if strict_gate and handoff_rule.status == "FAIL":
            handoff_report = _build_gate_report(
                gate_name="Bronze-to-Silver Handoff Gate",
                source_label=snap["key"],
                reference_year=reference_year,
                record_counts={"snapshots": 1},
                rules=[handoff_rule],
                elapsed_ms=handoff_rule.duration_ms,
            )
            raise DataContractViolationError(handoff_report)

        decision = evaluate_pre_llm_scope(
            signals=signals,
            clean_md=clean_md,
            known_official_domains=known_official_domains,
            reference_year=reference_year,
        )
        if not decision.accepted:
            drop_counts[decision.reason] += 1
            audit_entries.append(
                {
                    "domain": snap["domain"],
                    "source_url": snap["source_url"],
                    "bronze_key": snap["key"],
                    "status": "dropped_pre_llm",
                    "reason": decision.reason,
                    "canonical_official_url": decision.canonical_official_url or None,
                    "merged_into": decision.merged_into_official_key,
                }
            )
            print(f">> [DROP:{decision.reason}] {snap['source_url']}")
            continue

        if run_llm and client is not None:
            raw_result = extract_competition_hybrid(client, signals, clean_md)
            guarded = apply_post_llm_guards(raw_result, signals, reference_year=reference_year)
            if not guarded.is_competition or not guarded.competitions:
                drop_counts["post_llm_scope_or_empty"] += 1
                audit_entries.append(
                    {
                        "domain": snap["domain"],
                        "source_url": snap["source_url"],
                        "bronze_key": snap["key"],
                        "status": "dropped_post_llm",
                        "reason": "post_llm_scope_or_empty",
                    }
                )
                print(f">> [DROP:post_llm_scope] {snap['source_url']}")
                continue

            unique_comps: list[Competition] = []
            for comp in guarded.competitions:
                canon = normalize_url(comp.url) or decision.canonical_official_url
                if canon in seen_canonical_urls:
                    continue
                seen_canonical_urls.add(canon)
                unique_comps.append(comp)

            if not unique_comps:
                drop_counts["canonical_url_duplicate"] += 1
                continue

            row_rules = validate_silver_records_pydantic(unique_comps, reference_year=reference_year)
            failed_row_rules = [r for r in row_rules if r.status == "FAIL"]
            if failed_row_rules:
                contract_gate_failures += 1
                if strict_gate:
                    row_report = _build_gate_report(
                        gate_name="Silver Extraction Row Contract Gate",
                        source_label=snap["key"],
                        reference_year=reference_year,
                        record_counts={"competitions": len(unique_comps)},
                        rules=row_rules,
                        elapsed_ms=sum(r.duration_ms for r in row_rules),
                    )
                    raise DataContractViolationError(row_report)

            final_result = guarded.model_copy(update={"competitions": unique_comps})
            record = {
                "_metadata": {
                    "source_domain": snap["domain"],
                    "source_url": snap["source_url"],
                    "canonical_official_url": unique_comps[0].url,
                    "source_key": snap["key"],
                    "crawl_date": snap["date"],
                    "crawl_timestamp": snap["timestamp"],
                    "extracted_at": datetime.now(UTC).isoformat(),
                    "raw_length": len(snap["raw_text"]),
                    "clean_markdown_length": len(clean_md),
                    "pipeline_version": "v2_deterministic_sandwich",
                },
                "_deterministic": signals.to_context_dict(),
                **final_result.model_dump(mode="json"),
            }
            accepted_records.append(record)

            md_key = _upload_silver_markdown(
                s3_client=s3_client,
                bucket_name=settings.bucket_name,
                clean_md=clean_md,
                domain=snap["domain"],
                crawl_date=snap["date"],
                timestamp=snap["timestamp"],
                source_url=snap["source_url"],
                canonical_url=unique_comps[0].url or decision.canonical_official_url,
                bronze_key=snap["key"],
            )
            json_key = _upload_silver_extraction(
                s3_client=s3_client,
                bucket_name=settings.bucket_name,
                record=record,
                domain=snap["domain"],
                crawl_date=snap["date"],
                timestamp=snap["timestamp"],
            )
            uploaded_md_keys.append(md_key)
            uploaded_json_keys.append(json_key)
            audit_entries.append(
                {
                    "domain": snap["domain"],
                    "source_url": snap["source_url"],
                    "canonical_official_url": unique_comps[0].url,
                    "bronze_key": snap["key"],
                    "silver_md_key": md_key,
                    "silver_json_key": json_key,
                    "status": "extracted",
                    "competitions_count": len(unique_comps),
                }
            )
            print(f">> [OK] {snap['domain']} -> {len(unique_comps)} comp(s) | md={md_key}")
        else:
            audit_entries.append(
                {
                    "domain": snap["domain"],
                    "source_url": snap["source_url"],
                    "canonical_official_url": decision.canonical_official_url,
                    "bronze_key": snap["key"],
                    "status": "ready_for_llm",
                    "raw_chars": len(snap["raw_text"]),
                    "clean_md_chars": len(clean_md),
                    "json_ld_present": bool(signals.json_ld),
                    "rules_urls_count": len(signals.official_rules_urls),
                }
            )
            print(
                f">> [READY] {snap['domain']} ({len(snap['raw_text']):,} -> {len(clean_md):,} chars) "
                f"| official={decision.canonical_official_url}"
            )

    ts_now = int(datetime.now(UTC).timestamp())
    if accepted_records and not dry_run:
        batch_key = f"silver/batches/extractions_{chosen_date}_{ts_now}.json"
        batch_payload = {
            "metadata": {
                "extraction_date": chosen_date,
                "generated_at": datetime.now(UTC).isoformat(),
                "total_targets": len(snapshots),
                "successful_extractions": len(accepted_records),
                "competitions_found": sum(len(r.get("competitions", [])) for r in accepted_records),
            },
            "results": accepted_records,
        }
        s3_client.put_object(
            Bucket=settings.bucket_name,
            Key=batch_key,
            Body=json.dumps(batch_payload, ensure_ascii=False, indent=2).encode("utf-8"),
            ContentType="application/json; charset=utf-8",
            Metadata={"layer": "silver", "extraction_date": chosen_date},
        )

    summary = {
        "chosen_date": chosen_date,
        "total_snapshots": len(snapshots),
        "ready_or_accepted": sum(1 for e in audit_entries if e["status"] in {"extracted", "ready_for_llm"}),
        "dropped": sum(drop_counts.values()),
        "drop_breakdown": dict(drop_counts),
        "uploaded_markdown_count": len(uploaded_md_keys),
        "uploaded_json_count": len(uploaded_json_keys),
        "contract_gate_failures": contract_gate_failures,
        "entries": audit_entries,
    }
    if not dry_run and (accepted_records or run_llm):
        report_key = f"silver/_reports/silver_transform_{chosen_date}_{ts_now}.json"
        s3_client.put_object(
            Bucket=settings.bucket_name,
            Key=report_key,
            Body=json.dumps(summary, ensure_ascii=False, indent=2).encode("utf-8"),
            ContentType="application/json; charset=utf-8",
            Metadata={"layer": "silver", "type": "audit_report"},
        )

    print("\n" + "=" * 64)
    print(
        f"Silver Transform ({chosen_date}): snapshots={summary['total_snapshots']} | "
        f"accepted/ready={summary['ready_or_accepted']} | dropped={summary['dropped']} {dict(drop_counts)}"
    )
    print("=" * 64)
    return summary


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="ACDP v2 Silver Hybrid Deterministic Sandwich & Clean Markdown"
    )
    parser.add_argument("--extract", action="store_true", help="Run Bounded LLM extraction and upload Silver outputs")
    parser.add_argument("--date", type=str, default=None, help="Target Bronze crawl date (YYYY-MM-DD)")
    parser.add_argument("--all", action="store_true", help="Process all historical Bronze dates")
    parser.add_argument("--dry-run", action="store_true", help="Run deterministic stages without calling LLM or writing R2")
    parser.add_argument("--max-items", type=int, default=0, help="Optional cap on snapshots to process")
    parser.add_argument("--reference-year", type=int, default=DEFAULT_REFERENCE_YEAR, help="Anchor year for [year-1, year+1] scope")
    parser.add_argument("--strict-gate", action="store_true", help="Fail-fast on Bronze-to-Silver or Silver row contract violations")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)
    run_llm = args.extract or os.getenv("EXECUTE_LLM", "0") == "1"
    run_silver_transform(
        run_llm=run_llm,
        target_date=args.date,
        process_all_dates=args.all,
        dry_run=args.dry_run,
        max_items=args.max_items,
        reference_year=args.reference_year,
        strict_gate=args.strict_gate,
    )


if __name__ == "__main__":
    main()
