"""Source registries, search patterns, and keyword filters for ACDP v2 Discovery."""

from __future__ import annotations

from dataclasses import dataclass

TRACKING_QUERY_PARAMS = frozenset(
    {
        "utm_source",
        "utm_medium",
        "utm_campaign",
        "utm_term",
        "utm_content",
        "fbclid",
        "gclid",
        "ref",
        "mc_cid",
        "mc_eid",
        "igshid",
    }
)

STATIC_ASSET_EXTENSIONS = (
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".svg",
    ".webp",
    ".ico",
    ".css",
    ".js",
    ".woff",
    ".woff2",
    ".ttf",
    ".zip",
    ".rar",
    ".mp4",
    ".mp3",
)

NOISE_KEYWORDS = (
    "lich-thi",
    "lịch thi",
    "de-cuong",
    "đề cương",
    "thoi-khoa-bieu",
    "thời khóa biểu",
    "diem-thi",
    "điểm thi",
    "tuyen-dung-nhan-su",
    "thcs",
    "tieu-hoc",
    "mam-non",
    "/tag/",
    "/tags/",
    "tong-ket",
    "tổng kết",
    "trao-giai",
    "trao giải",
    "dat-giai",
    "đạt giải",
    "be-mac",
    "bế mạc",
    "soi-noi",
    "sôi nổi",
    "phuong-an",
    "phương án",
    "/login",
    "/signin",
    "/signup",
    "/register-account",
    "/privacy",
    "/terms-of-service",
    "/cookie-policy",
)

RELEVANCE_KEYWORDS_HIGH = (
    "hackathon",
    "datathon",
    "ai challenge",
    "coding challenge",
    "cuộc thi",
    "cuoc-thi",
    "hội thi",
    "hoi-thi",
    "olympic",
    "icpc",
    "codetour",
    "dataforlife",
    "eureka",
)

RELEVANCE_KEYWORDS_MEDIUM = (
    "ai",
    "trí tuệ nhân tạo",
    "dữ liệu",
    "data science",
    "lập trình",
    "cntt",
    "công nghệ thông tin",
    "sinh viên",
    "students",
    "giải thưởng",
    "thể lệ",
    "prize",
    "2026",
    "2027",
)

TECH_DOMAIN_KEYWORDS = (
    "ai",
    "trí tuệ nhân tạo",
    "tri tue nhan tao",
    "dữ liệu",
    "du lieu",
    "data",
    "lập trình",
    "lap trinh",
    "cntt",
    "công nghệ",
    "cong nghe",
    "coding",
    "hackathon",
    "datathon",
    "icpc",
    "olp",
    "olympic",
    "makerthon",
    "tin học",
    "tin hoc",
    "phần mềm",
    "phan mem",
    "codetour",
    "dataforlife",
)

# Standardized Tier 2 search patterns (12 weekly queries = 48/month < 5% Free Tier)
DEFAULT_TIER2_QUERIES: list[tuple[str, str]] = [
    (
        "A_edu_vn_ai_data",
        'site:edu.vn ("phát động cuộc thi" OR "thể lệ cuộc thi" OR "hackathon") (CNTT OR AI OR "dữ liệu") 2026 -filetype:pdf -"lịch thi" -"đề cương"',
    ),
    (
        "A_edu_vn_olympic",
        'site:edu.vn ("olympic tin học" OR "lập trình sinh viên" OR "sáng tạo trẻ") 2026 -filetype:pdf',
    ),
    (
        "A_edu_vn_nckh",
        'site:edu.vn ("cuộc thi" OR "hội thi") ("khoa học dữ liệu" OR "trí tuệ nhân tạo" OR "an toàn thông tin") 2026',
    ),
    (
        "B_gov_vn_ai",
        'site:gov.vn ("cuộc thi" OR "hội thi" OR "giải thưởng") ("trí tuệ nhân tạo" OR "chuyển đổi số" OR "sáng tạo") 2026',
    ),
    (
        "B_gov_vn_hcm_hn",
        'site:gov.vn ("tin học trẻ" OR "AI Challenge" OR "khởi nghiệp đổi mới sáng tạo") 2026',
    ),
    (
        "C_enterprise_hackathon",
        '("hackathon" OR "datathon" OR "coding challenge") ("Vietnam" OR "TP.HCM" OR "Hà Nội") ("sinh viên" OR "students") 2026',
    ),
    (
        "C_enterprise_ai_vn",
        '("AI hackathon" OR "data challenge" OR "code tour") ("Việt Nam" OR "Vietnam") 2026',
    ),
    (
        "C_luma_devpost_vn",
        '(site:lu.ma OR site:devpost.com) ("hackathon" OR "buildathon" OR "AI") ("Vietnam" OR "Ho Chi Minh" OR "Hanoi") 2026',
    ),
    (
        "C_ybox_vn_contests",
        'site:ybox.vn ("cuộc thi" OR "hackathon" OR "datathon") (CNTT OR AI OR "dữ liệu" OR "lập trình") 2026',
    ),
    (
        "C_topdev_vnoi",
        '(site:topdev.vn OR site:vnoi.info) ("hackathon" OR "coding" OR "ICPC" OR "OLP") 2026',
    ),
    (
        "D_edu_pdf_rules",
        'site:edu.vn ("thể lệ" OR "quy chế" OR "kế hoạch") "cuộc thi" (CNTT OR AI OR "dữ liệu") 2026 filetype:pdf',
    ),
    (
        "D_gov_pdf_rules",
        'site:gov.vn ("thể lệ" OR "kế hoạch") ("cuộc thi" OR "hội thi") ("trí tuệ nhân tạo" OR "tin học") 2026 filetype:pdf',
    ),
]

DEFAULT_GDELT_QUERIES: list[str] = [
    "(hackathon OR datathon) vietnam",
    '("cuoc thi" OR "hoi thi") ("tri tue nhan tao" OR "du lieu" OR "lap trinh") vietnam',
]

DEFAULT_RSS_FEEDS: list[tuple[str, str]] = []

DEFAULT_SITEMAP_URLS: list[str] = [
    "https://ybox.vn/sitemap.xml",
]


@dataclass(frozen=True)
class HubSourceConfig:
    """Configuration for a public Vietnamese/event competition hub."""

    name: str
    url: str
    link_contains: tuple[str, ...] = ()


DEFAULT_VIETNAM_HUBS: list[HubSourceConfig] = [
    HubSourceConfig(name="ybox", url="https://ybox.vn/cuoc-thi", link_contains=("/cuoc-thi/", "/tin-tuyen-dung/")),
    HubSourceConfig(name="khoahoctre", url="https://khoahoctre.com.vn/", link_contains=("cuoc-thi", "hoi-thi", "giai-thuong", "eureka")),
    HubSourceConfig(name="vnoi", url="https://vnoi.info/", link_contains=("icpc", "olp", "contest", "ky-thi", "cuoc-thi")),
]

CURATED_SEED_URLS: list[str] = [
    "https://codetour.org/",
    "https://www.vietnamaichallenge.com/",
    "https://datadna.onyxdata.co.uk/challenges/",
    "https://itconsultantchallenge.org/vi",
    "https://rmit-hackathon.com/",
    "https://thucchien.ai/",
    "https://www.lotushack.org/",
    "https://dataforlife.vn/",
    "https://vietnamdatathon.com/",
    "https://challenge.zalo.ai/",
]
