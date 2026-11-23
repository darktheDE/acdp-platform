"""Module 2: Instruction & Information Extraction using Instructor and Pydantic (Cloudflare R2 Exclusive).

Reads raw markdown files stored in the Bronze layer of Cloudflare R2 bucket,
applies the standardized competition Pydantic schema, and uploads structured
JSON extractions directly to the Silver layer on Cloudflare R2 (Zero Local Persistence).

Incorporates:
- Few-Shot Prompting derived from real Bronze layer crawled data (October 31, 2026).
- Scoped Latest-Date Extraction: by default extracts only the latest snapshot of each domain
  for the target crawl date, keeping older crawl snapshots preserved as historical archives.
"""

import json
import os
import re
import sys
from collections import defaultdict
from datetime import datetime

import instructor
from dotenv import find_dotenv, load_dotenv

# Ensure UTF-8 output encoding on Windows consoles
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Load environment variables (.env in workspace root or current directory)
load_dotenv(find_dotenv(usecwd=True))

try:
    from acdp.config import settings
    from acdp.schemas import CompetitionExtractionResult
except ModuleNotFoundError:
    from config import settings  # type: ignore
    from schemas import CompetitionExtractionResult  # type: ignore

BUCKET_NAME = settings.bucket_name
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama/qwen2.5:7b")
# Cấu hình context window cho Ollama (mặc định 8192 token để đủ chứa prompt ~5k token mà vẫn tối ưu tốc độ CPU)
OLLAMA_NUM_CTX = int(os.getenv("OLLAMA_NUM_CTX", "8192"))

SYSTEM_PROMPT = """Bạn là chuyên gia Kỹ thuật Dữ liệu (Data Engineer) phụ trách bóc tách thông tin có cấu trúc từ tài liệu Markdown của các cuộc thi học thuật, tin học, AI và khoa học dữ liệu.

Nhiệm vụ của bạn:
1. Phân tích nội dung Markdown thô được cào từ các trang web cuộc thi (tiếng Việt hoặc tiếng Anh).
2. Xác định xem văn bản có chứa thông tin cuộc thi học thuật/kỹ thuật hợp lệ hay không (`is_competition`).
   - Nếu trang rỗng, lỗi 404, hoặc chỉ chứa thanh điều hướng không có thể lệ cụ thể: gán `is_competition = False` và để danh sách `competitions = []`.
   - Nếu trang chứa một hoặc nhiều cuộc thi cụ thể: gán `is_competition = True` và trích xuất danh sách các cuộc thi vào `competitions`.
3. Bóc tách chi tiết các chiều dữ liệu định lượng và định tính:
   - Tên cuộc thi (`name`), chủ đề (`tagline`), tóm tắt (`summary`).
   - Đơn vị tổ chức (`organizers`), đối tác/tài trợ (`partners_and_sponsors`).
   - Lĩnh vực (`category`), đối tượng (`target_audience`), quy mô đội (`team_size_min`, `team_size_max`, `team_description`).
   - Hình thức thi (`mode`: 'online', 'offline', 'hybrid') và địa điểm (`location`).
   - Lệ phí (`participation_fee`), tổng giá trị giải thưởng (`total_prize_pool`), cơ cấu giải chi tiết (`prizes`).
   - Thời gian đăng ký (`registration_start`, `registration_deadline`), tình trạng tiếp nhận đơn (`registration_status`: 'open', 'upcoming', 'closed').
   - Lịch trình các vòng thi (`timeline_stages`).
   - Tóm tắt thử thách/đề bài (`challenge_overview`) và nền tảng nộp bài (`submission_platform`).
4. Nguyên tắc dữ liệu nghiêm ngặt:
   - Nếu trường thông tin không có trong văn bản, gán `None` (hoặc `[]` cho mảng).
   - Tuyệt đối không điền các chuỗi giữ chỗ như 'N/A', 'None', 'Not specified', 'No fee mentioned'.
5. RÀNG BUỘC BẮT BUỘC về `competitions`:
   - Nếu `is_competition = True`, trường `competitions` BẮT BUỘC chứa ít nhất 1 phần tử với `name` và `summary` đã điền.
   - NGHIÊM CẤM trả về `is_competition = True` kèm `competitions = []`. Nếu không trích xuất được chi tiết đầy đủ, hãy điền tối thiểu `name` và `summary` dựa trên thông tin đã đọc được."""


# ==============================================================================
# FEW-SHOT EXAMPLES (Trích xuất từ dữ liệu thực tế ngày 31/10/2026 trên Bronze)
# ==============================================================================

FEW_SHOT_MESSAGES = [
    # --------------------------------------------------------------------------
    # MẪU 1: Cuộc thi Hackathon AI tiếng Việt, quy mô quốc gia, thi offline
    # Nguồn gốc: bronze/www.vietnamaichallenge.com/year=2026/month=10/day=31/...
    # --------------------------------------------------------------------------
    {
        "role": "user",
        "content": (
            "Source Domain / URL: www.vietnamaichallenge.com\n\n"
            "Nội dung Markdown cần trích xuất:\n\n"
            "# \"TRAIN\"SFORMATION - Một sứ mệnh. 48 giờ kiến tạo tương lai.\n"
            "Hackathon 100% AI-native đầu tiên tại Việt Nam giải bài toán thật từ doanh nghiệp. "
            "Quy tụ các builder trên quy mô toàn quốc, tranh tài 17-19 THÁNG 7/2026 | FPT TOWER, HÀ NỘI.\n"
            "TỔNG GIÁ TRỊ GIẢI THƯỞNG HIỆN TẠI HƠN 2 TỶ VNĐ.\n"
            "- Giải nhất: $10,000 Tiền mặt, Bằng khen của TW Đoàn TNCS Hồ Chí Minh, cơ hội nghiên cứu tại Thụy Điển.\n"
            "- Giải nhì: $5,000 Tiền mặt, Bằng khen TW Đoàn.\n"
            "- Giải ba: $1,000 Tiền mặt, Bằng khen TW Đoàn.\n"
            "- Giải đặc biệt PyTorch Award: $5,000 Cash.\n"
            "Chủ đề thử thách: Ngân hàng & Tài chính, Y tế & Sức khỏe, Giáo dục, Phòng chống thiên tai, SME AI Agent.\n"
            "Đồng tổ chức: NIC (Trung tâm Đổi mới Sáng tạo Quốc gia), AI for Vietnam Foundation.\n"
            "Nhà tài trợ: SHB (Kim cương), AI Singapore, FPT AI Factory (Vàng), SOTATEK, AVSE Global (Bạc).\n"
            "Hạn chót đăng ký: 11:00, 17/07/2026. Lễ khai mạc: 17/07/2026. Demo Day: 19/07/2026.\n"
            "Đối tượng: Arena chào đón sinh viên, lập trình viên, chuyên viên data science và startup builder.\n"
            "Phí tham gia: Miễn phí hoàn toàn."
        ),
    },
    {
        "role": "assistant",
        "content": (
            '{\n'
            '  "is_competition": true,\n'
            '  "reasoning": "Văn bản chứa đầy đủ thông tin về cuộc thi Vietnam AI Innovation Challenge 2026 với thể lệ, giải thưởng và thời gian cụ thể.",\n'
            '  "competitions": [\n'
            '    {\n'
            '      "name": "Vietnam AI Innovation Challenge 2026",\n'
            '      "tagline": "\\"TRAIN\\"SFORMATION - Một sứ mệnh. 48 giờ kiến tạo tương lai",\n'
            '      "url": "https://www.vietnamaichallenge.com",\n'
            '      "summary": "Hackathon 100% AI-native kéo dài 48 giờ tại Việt Nam giải quyết các bài toán thực tế của doanh nghiệp trong ngân hàng, y tế, giáo dục và thiên tai.",\n'
            '      "organizers": [\n'
            '        "Trung tâm Đổi mới Sáng tạo Quốc gia (NIC)",\n'
            '        "AI for Vietnam Foundation (AIV)"\n'
            '      ],\n'
            '      "partners_and_sponsors": [\n'
            '        "SHB",\n'
            '        "AI Singapore",\n'
            '        "FPT AI Factory",\n'
            '        "SOTATEK",\n'
            '        "AVSE Global",\n'
            '        "TW Đoàn TNCS Hồ Chí Minh"\n'
            '      ],\n'
            '      "category": [\n'
            '        "Artificial Intelligence",\n'
            '        "Generative AI",\n'
            '        "Hackathon"\n'
            '      ],\n'
            '      "target_audience": "Sinh viên, lập trình viên, chuyên viên data science và startup builder",\n'
            '      "team_size_min": null,\n'
            '      "team_size_max": null,\n'
            '      "team_description": null,\n'
            '      "mode": "offline",\n'
            '      "location": "Toà nhà FPT Tower, 10 Phạm Văn Bạch, Cầu Giấy, Hà Nội",\n'
            '      "participation_fee": "Miễn phí",\n'
            '      "total_prize_pool": "Hơn 2 tỷ VNĐ",\n'
            '      "prizes": [\n'
            '        {\n'
            '          "tier": "Giải nhất",\n'
            '          "reward": "$10,000 tiền mặt, Bằng khen TW Đoàn TNCS Hồ Chí Minh, cơ hội nghiên cứu tại Thụy Điển",\n'
            '          "estimated_value_vnd": 250000000.0,\n'
            '          "is_scholarship": false\n'
            '        },\n'
            '        {\n'
            '          "tier": "Giải nhì",\n'
            '          "reward": "$5,000 tiền mặt, Bằng khen TW Đoàn",\n'
            '          "estimated_value_vnd": 125000000.0,\n'
            '          "is_scholarship": false\n'
            '        },\n'
            '        {\n'
            '          "tier": "Giải ba",\n'
            '          "reward": "$1,000 tiền mặt, Bằng khen TW Đoàn",\n'
            '          "estimated_value_vnd": 25000000.0,\n'
            '          "is_scholarship": false\n'
            '        },\n'
            '        {\n'
            '          "tier": "PyTorch Award",\n'
            '          "reward": "$5,000 tiền mặt",\n'
            '          "estimated_value_vnd": 125000000.0,\n'
            '          "is_scholarship": false\n'
            '        }\n'
            '      ],\n'
            '      "registration_start": null,\n'
            '      "registration_deadline": "17/07/2026",\n'
            '      "registration_status": "closed",\n'
            '      "event_start": "17/07/2026",\n'
            '      "event_end": "19/07/2026",\n'
            '      "timeline_stages": [\n'
            '        {\n'
            '          "stage_name": "Giai đoạn 1: Khởi động",\n'
            '          "start_date": "28/05/2026",\n'
            '          "end_date": "17/07/2026",\n'
            '          "description": "Mở đơn đăng ký và chuỗi workshop bổ trợ kỹ năng thực chiến"\n'
            '        },\n'
            '        {\n'
            '          "stage_name": "Giai đoạn 2: Đấu trường AI (Hackathon 48h)",\n'
            '          "start_date": "17/07/2026",\n'
            '          "end_date": "19/07/2026",\n'
            '          "description": "Phát triển sản phẩm liên tục 48 giờ và Demo Day trao giải tại FPT Tower"\n'
            '        }\n'
            '      ],\n'
            '      "challenge_overview": "Ứng dụng AI giải quyết bài toán thật trong Ngân hàng, Y tế, Giáo dục, Phòng chống thiên tai và Năng suất SME",\n'
            '      "submission_platform": "Website ban tổ chức"\n'
            '    }\n'
            '  ]\n'
            '}'
        ),
    },
    # --------------------------------------------------------------------------
    # MẪU 2: Cuộc thi tiếng Anh, đa quốc gia, giới hạn đội 4 người, thi Kaggle
    # Nguồn gốc: bronze/rmit-hackathon.com/year=2026/month=10/day=31/...
    # --------------------------------------------------------------------------
    {
        "role": "user",
        "content": (
            "Source Domain / URL: rmit-hackathon.com\n\n"
            "Nội dung Markdown cần trích xuất:\n\n"
            "# RMIT Hackathon 2026\n"
            "Theme: Security × Generative AI × Low-Resource Languages. Secure. Generate. Include.\n"
            "Organiser: School of Computing Technologies, RMIT University.\n"
            "University Partner: Taylor’s University (Malaysia). Industry Challenge Sponsor: Tide.\n"
            "Industry Partners: DesignLive Technologies, Katalon, Orange Logic Vietnam.\n"
            "Eligibility: Each team must consist of four students. Open to undergraduate and postgraduate students.\n"
            "Participation: All team members must be present at one venue: Melbourne campus, Saigon South campus, "
            "Hanoi campus, or Taylor's University Lakeside campus. Registration fee: Free of charge.\n"
            "Platform: Kaggle, hosted by SkywardAI Labs.\n"
            "Timeline: Registrations closed 13 October 2026. Event dates: 22–23 October 2026.\n"
            "Prize: Up to VND 100M total prize value."
        ),
    },
    {
        "role": "assistant",
        "content": (
            '{\n'
            '  "is_competition": true,\n'
            '  "reasoning": "Tài liệu chứa thông tin chi tiết về cuộc thi RMIT Hackathon 2026.",\n'
            '  "competitions": [\n'
            '    {\n'
            '      "name": "RMIT Hackathon 2026",\n'
            '      "tagline": "Security × Generative AI × Low-Resource Languages",\n'
            '      "url": "https://rmit-hackathon.com",\n'
            '      "summary": "Cuộc thi lập trình đa quốc gia kết nối 3 chủ đề an toàn bảo mật, GenAI và xử lý ngôn ngữ ít tài nguyên tại các campus của RMIT và Taylor\'s University.",\n'
            '      "organizers": [\n'
            '        "School of Computing Technologies, RMIT University"\n'
            '      ],\n'
            '      "partners_and_sponsors": [\n'
            '        "Taylor’s University",\n'
            '        "Tide",\n'
            '        "DesignLive Technologies",\n'
            '        "Katalon",\n'
            '        "Orange Logic Vietnam"\n'
            '      ],\n'
            '      "category": [\n'
            '        "Cybersecurity",\n'
            '        "Generative AI",\n'
            '        "Natural Language Processing"\n'
            '      ],\n'
            '      "target_audience": "Sinh viên đại học và sau đại học đang theo học",\n'
            '      "team_size_min": 4,\n'
            '      "team_size_max": 4,\n'
            '      "team_description": "Mỗi đội bắt buộc gồm đúng 4 thành viên",\n'
            '      "mode": "offline",\n'
            '      "location": "RMIT Melbourne, RMIT Nam Sài Gòn, RMIT Hà Nội, và Taylor\'s University (Malaysia)",\n'
            '      "participation_fee": "Miễn phí",\n'
            '      "total_prize_pool": "Up to VND 100M",\n'
            '      "prizes": [\n'
            '        {\n'
            '          "tier": "Tổng giải thưởng",\n'
            '          "reward": "Tổng giá trị giải thưởng và quà tặng lên đến 100 triệu VNĐ",\n'
            '          "estimated_value_vnd": 100000000.0,\n'
            '          "is_scholarship": false\n'
            '        }\n'
            '      ],\n'
            '      "registration_start": null,\n'
            '      "registration_deadline": "13/10/2026",\n'
            '      "registration_status": "closed",\n'
            '      "event_start": "22/10/2026",\n'
            '      "event_end": "23/10/2026",\n'
            '      "timeline_stages": [\n'
            '        {\n'
            '          "stage_name": "Warm-up task",\n'
            '          "start_date": null,\n'
            '          "end_date": null,\n'
            '          "description": "Khởi động và làm quen nền tảng mã nguồn mở"\n'
            '        },\n'
            '        {\n'
            '          "stage_name": "Two Challenges",\n'
            '          "start_date": "22/10/2026",\n'
            '          "end_date": "23/10/2026",\n'
            '          "description": "Hai thử thách chính trên Kaggle kết nối 3 chủ đề trọng tâm"\n'
            '        }\n'
            '      ],\n'
            '      "challenge_overview": "Tìm kiếm và khắc phục lỗ hổng trong hệ thống AI, giảm thiểu ảo giác mô hình và phát triển GenAI cho ngôn ngữ hiếm",\n'
            '      "submission_platform": "Kaggle (SkywardAI Labs)"\n'
            '    }\n'
            '  ]\n'
            '}'
        ),
    },
    # --------------------------------------------------------------------------
    # MẪU 3 (Negative Case): Trang rỗng, lỗi 404, hoặc chỉ có thanh Menu navbar
    # Nguồn gốc: bronze/codetour.org/... hoặc bronze/hackaithon.vsds.vn/...
    # --------------------------------------------------------------------------
    {
        "role": "user",
        "content": (
            "Source Domain / URL: codetour.org\n\n"
            "Nội dung Markdown cần trích xuất:\n\n"
            "[ ![Code Tour](logo.svg)](https://codetour.org/)\n"
            "[Kỳ thi](https://codetour.org/contest)\n"
            "[Tin tức](https://codetour.org/news)\n"
            "[Xếp hạng](https://codetour.org/ranking)\n"
            "[ĐĂNG NHẬP](https://codetour.org/auth/login) [ĐĂNG KÝ](https://codetour.org/auth/register)\n"
            "## Không tìm thấy\n"
            "[← Về trang trước](https://codetour.org/)\n"
            "Copyright © 2022 VNG Corporation. All rights reserved."
        ),
    },
    {
        "role": "assistant",
        "content": (
            '{\n'
            '  "is_competition": false,\n'
            '  "reasoning": "Tài liệu chỉ bao gồm thanh điều hướng trang web hoặc thông báo lỗi 404 không tìm thấy trang, không chứa mô tả thể lệ, mốc thời gian hay giải thưởng của cuộc thi cụ thể nào.",\n'
            '  "competitions": []\n'
            '}'
        ),
    },
]


def clean_markdown_content(raw_md: str, max_chars: int = 16000) -> str:
    """Loại bỏ nhiễu, link ảnh rác và tin tức ngoài lề khỏi Markdown trước khi đưa vào LLM."""
    if not raw_md:
        return ""

    # 1. Loại bỏ các thẻ ảnh Markdown ![alt](url) và SVG dài dòng
    text = re.sub(r"!\[.*?\]\(.*?\)", "", raw_md)

    # 2. Loại bỏ các liên kết rác dạng [Icon](url) đứng một mình
    text = re.sub(r"\[\s*\]\(.*?\)", "", text)

    # 3. Rút gọn nhiều dòng trống liên tiếp thành tối đa 2 dòng trống
    text = re.sub(r"\n{3,}", "\n\n", text)

    # 4. Nếu văn bản ngắn (dưới max_chars), giữ nguyên toàn bộ
    if len(text) <= max_chars:
        return text.strip()

    # 5. Nếu văn bản quá dài (như file aichallenge 116k ký tự):
    # Chỉ giữ lại các đoạn văn có chứa từ khóa liên quan đến cuộc thi
    keywords = [
        "cuộc thi", "hội thi", "thể lệ", "giải thưởng", "thời gian",
        "hạn chót", "đăng ký", "đối tượng", "vòng thi", "vòng 1", "vòng 2",
        "chung kết", "prize", "deadline", "timeline", "challenge", "hackathon",
        "organizer", "eligibility", "submission"
    ]

    paragraphs = text.split("\n\n")
    relevant_paragraphs = []

    for p in paragraphs:
        p_lower = p.lower()
        if any(kw in p_lower for kw in keywords) or p.strip().startswith(("#", "###")):
            relevant_paragraphs.append(p)

    filtered_text = "\n\n".join(relevant_paragraphs)
    return filtered_text[:max_chars].strip()


def parse_bronze_key(fkey: str):
    """Phân rã key bronze/<domain>/year=<year>/month=<month>/day=<day>/<timestamp>."""
    pattern = r"^bronze/([^/]+)/year=(\d{4})/month=(\d{2})/day=(\d{2})/(\d+)$"
    match = re.match(pattern, fkey)
    if match:
        domain, year, month, day, ts = match.groups()
        return {
            "domain": domain,
            "date": f"{year}-{month}-{day}",
            "timestamp": int(ts),
            "key": fkey,
        }
    return None


def extract_competition_from_markdown(
    client, raw_markdown: str, source_domain: str = ""
) -> CompetitionExtractionResult:
    """Uses Instructor + LLM with Few-Shot prompting to extract structured competition data.

    FIX num_ctx: Instructor với provider Ollama sử dụng OpenAI client bên dưới.
    OpenAI client không chấp nhận tham số 'options' trực tiếp trong create(),
    mà phải truyền qua 'extra_body={"options": {"num_ctx": ...}}'.
    """
    # Tiền lọc Markdown trước khi đưa vào prompt
    cleaned_md = clean_markdown_content(raw_markdown)

    raw_messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        *FEW_SHOT_MESSAGES,
        {
            "role": "user",
            "content": f"Source Domain / URL: {source_domain}\n\nNội dung Markdown cần trích xuất:\n\n{cleaned_md}",
        },
    ]

    messages = list(raw_messages)

    extra_kwargs = {}
    if "ollama" in LLM_PROVIDER.lower():
        extra_kwargs["extra_body"] = {"options": {"num_ctx": OLLAMA_NUM_CTX}}

    chosen_model = os.getenv("LLM_MODEL") or os.getenv("LLM_PROVIDER") or "gemma-4-31b-it"
    if "/" in chosen_model:
        chosen_model = chosen_model.split("/")[-1]

    extraction: CompetitionExtractionResult = client.chat.completions.create(
        model=chosen_model,
        response_model=CompetitionExtractionResult,
        messages=messages,
        max_retries=1,
        **extra_kwargs,
    )
    return extraction


def upload_to_silver(
    s3_client,
    record: dict,
    domain: str,
    crawl_date: str,
    timestamp: int,
) -> str:
    """Upload bản ghi Silver JSON đã trích xuất thẳng lên Cloudflare R2 (không lưu local)."""
    safe_domain = re.sub(r"[^\w\-.]", "_", domain)
    parts = crawl_date.split("-")
    if len(parts) == 3:
        year, month, day = parts
    else:
        now = datetime.now()
        year, month, day = str(now.year), now.strftime("%m"), now.strftime("%d")

    silver_key = f"silver/extractions/{safe_domain}/year={year}/month={month}/day={day}/{timestamp}.json"
    s3_client.put_object(
        Bucket=BUCKET_NAME,
        Key=silver_key,
        Body=json.dumps(record, ensure_ascii=False, indent=2).encode("utf-8"),
        ContentType="application/json; charset=utf-8",
        Metadata={"source": domain, "layer": "silver", "crawl_date": crawl_date},
    )
    print(f">> [R2 SILVER UPLOADED] s3://{BUCKET_NAME}/{silver_key}")
    return silver_key


def process_bronze_bucket(
    run_llm: bool = False,
    target_date: str | None = None,
    process_all_dates: bool = False,
    dry_run: bool = False,
) -> list[dict]:
    """Quét dữ liệu tầng Bronze trên R2 theo cơ chế Scoped Latest Snapshot và đẩy Silver JSON lên R2.

    Quy tắc:
    1. Giữ nguyên 100% lịch sử các ngày cào trên bucket.
    2. Chỉ trích xuất tệp của ngày mục tiêu (mặc định: ngày cào mới nhất).
    3. Nếu 1 domain được cào nhiều lần trong cùng một ngày, chỉ trích xuất tệp có timestamp mới nhất.
    4. Upload kết quả trích xuất schema trực tiếp lên tầng Silver trên Cloudflare R2 (Zero Local Persistence).

    Args:
        run_llm: Nếu True, gọi LLM qua Instructor để trích xuất schema.
        target_date: Chuỗi ngày cần trích xuất định dạng 'YYYY-MM-DD'.
        process_all_dates: Nếu True, bỏ qua lọc ngày và quét toàn bộ lịch sử.
        dry_run: Nếu True, chỉ in kết quả trích xuất mà không đẩy object lên R2.
    """
    client = None
    if run_llm:
        gemini_key = os.getenv("GEMINI_API_KEY")
        if gemini_key and "your_gemini" not in gemini_key:
            from openai import OpenAI
            model_display = os.getenv("LLM_MODEL") or LLM_PROVIDER
            print(f"Initializing Instructor client with Gemini OpenAI endpoint (Model: {model_display}) ...")
            raw_client = OpenAI(
                base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
                api_key=gemini_key,
                timeout=45.0,
            )
            client = instructor.from_openai(raw_client, mode=instructor.Mode.JSON)
        elif "ollama" in LLM_PROVIDER.lower():
            print(f"Initializing Instructor client with Ollama provider: {LLM_PROVIDER} ...")
            client = instructor.from_provider(LLM_PROVIDER, mode=instructor.Mode.JSON)
        else:
            print(f"Initializing Instructor client with provider: {LLM_PROVIDER} ...")
            client = instructor.from_provider(LLM_PROVIDER)

    valid_crawl_items = []
    skipped_metadata_count = 0

    if not BUCKET_NAME:
        raise RuntimeError("BUCKET_NAME is not configured in .env. Cloudflare R2 bucket connection is required.")

    s3_client = settings.create_r2_client()
    print(f"Connecting to Cloudflare R2 Bucket: {BUCKET_NAME} (Strict Cloud Mode - Zero Fallback)")
    paginator = s3_client.get_paginator("list_objects_v2")
    pages = paginator.paginate(Bucket=BUCKET_NAME, Prefix="bronze/")

    # 1. Thu thập và phân loại toàn bộ tệp trong Bronze
    for p in pages:
        if "Contents" not in p:
            continue

        for item in p["Contents"]:
            fkey = item["Key"]
            if fkey.endswith("/"):
                continue

            # Bỏ qua metadata của Delta Lake (_delta_log), parquet data files và tệp hệ thống ẩn
            if (
                "_delta_log" in fkey
                or "/_" in fkey
                or fkey.startswith("_")
                or fkey.endswith((".parquet", ".crc", ".json"))
                or "part-" in fkey
            ):
                skipped_metadata_count += 1
                continue

            parsed = parse_bronze_key(fkey)
            if parsed:
                parsed["size"] = item.get("Size", 0)
                parsed["last_modified"] = item.get("LastModified")
                valid_crawl_items.append(parsed)

    if not valid_crawl_items:
        print(">> [INFO] Không tìm thấy tệp cào hợp lệ nào trong bucket.")
        return

    # 2. Xác định ngày mục tiêu cần trích xuất
    available_dates = sorted(list({x["date"] for x in valid_crawl_items}))
    
    if process_all_dates:
        selected_items = valid_crawl_items
        active_scope_desc = "TOÀN BỘ LỊCH SỬ (ALL DATES)"
        chosen_date = "all_dates"
    else:
        if target_date:
            if target_date not in available_dates:
                print(f">> [WARNING] Ngày '{target_date}' không có dữ liệu cào. Các ngày khả dụng: {available_dates}")
                return
            chosen_date = target_date
        else:
            # Tự động chọn ngày hôm nay; nếu hôm nay chưa cào thì lấy ngày cào mới nhất trên bucket
            today = datetime.now().strftime("%Y-%m-%d")
            chosen_date = today if today in available_dates else available_dates[-1]

        active_scope_desc = f"NGÀY MỤC TIÊU: {chosen_date}"
        selected_items = [x for x in valid_crawl_items if x["date"] == chosen_date]

    # 3. Gom nhóm theo domain và CHỈ LẤY BẢN MỚI NHẤT TRONG NGÀY (Deduplication within date)
    domain_groups = defaultdict(list)
    for it in selected_items:
        domain_groups[it["domain"]].append(it)

    final_queue = []
    historical_skipped_count = len(valid_crawl_items) - len(domain_groups)

    for _dom, items in sorted(domain_groups.items()):
        # Lấy file có timestamp lớn nhất
        latest_item = max(items, key=lambda x: x["timestamp"])
        final_queue.append(latest_item)

    print("\n" + "=" * 60)
    print(f"PIPELINE EXTRACTION SCOPE: {active_scope_desc}")
    print(f"Tổng số tệp trong Bronze: {len(valid_crawl_items)}")
    print(f"Số domain duy nhất cần trích xuất (Latest Snapshot): {len(final_queue)}")
    print(f"Số tệp lịch sử cũ được bảo lưu (Skipped from LLM): {historical_skipped_count}")
    print(f"Số tệp metadata/Delta log đã bỏ qua: {skipped_metadata_count}")
    print(f"Đích lưu Silver JSON trên R2: s3://{BUCKET_NAME}/silver/extractions/")
    print("=" * 60)

    # 4. Thực thi trích xuất LLM trên tập snapshot đã lọc
    processed_count = 0
    empty_count = 0
    successful_extractions = []

    for item in final_queue:
        fkey = item["key"]
        file_size = item["size"]

        print("\n--------------------------------------------------")
        print(f"Processing Target: {item['domain']} ({fkey})")
        print(f">> File Size: {file_size} bytes | Date: {item['date']} | Timestamp: {item['timestamp']}")

        if file_size == 0:
            print(">> [SKIP] Empty file (0 bytes).")
            empty_count += 1
            continue

        if item.get("is_local"):
            with open(item["key"], encoding="utf-8") as f:
                raw_markdown = f.read()
        else:
            response = s3_client.get_object(Bucket=BUCKET_NAME, Key=fkey)
            raw_markdown = response["Body"].read().decode("utf-8", errors="replace")

        if not raw_markdown.strip():
            print(">> [SKIP] Content contains only whitespace.")
            empty_count += 1
            continue

        processed_count += 1
        cleaned_md = clean_markdown_content(raw_markdown)
        print(f">> Raw Content Length: {len(raw_markdown)} chars -> Cleaned: {len(cleaned_md)} chars")
        print(f">> Preview: {cleaned_md[:150].strip()}...")

        if run_llm and client:
            print(">> Running Instructor LLM extraction with Few-Shot prompting (Mode: JSON)...")
            try:
                result = extract_competition_from_markdown(
                    client=client,
                    raw_markdown=raw_markdown,
                    source_domain=item["domain"],
                )
                print(f">> Extraction Status: is_competition={result.is_competition}")
                print(f">> Extracted Competitions: {len(result.competitions)}")
                print(result.model_dump_json(indent=2))

                # Gói bản ghi schema kèm thông tin nguồn (provenance/lineage metadata)
                record = {
                    "_metadata": {
                        "source_domain": item["domain"],
                        "source_key": item["key"],
                        "crawl_date": item["date"],
                        "crawl_timestamp": item["timestamp"],
                        "extracted_at": datetime.now().isoformat(),
                        "raw_markdown_length": len(raw_markdown),
                        "cleaned_markdown_length": len(cleaned_md),
                    },
                    **result.model_dump(mode="json"),
                }
                successful_extractions.append(record)

                # Đẩy ngay tệp JSON đơn lẻ của domain này lên tầng Silver trên Cloudflare R2
                if dry_run:
                    print(f">> [DRY-RUN] Bỏ qua upload R2 cho domain '{item['domain']}'.")
                else:
                    upload_to_silver(
                        s3_client=s3_client,
                        record=record,
                        domain=item["domain"],
                        crawl_date=item["date"],
                        timestamp=item["timestamp"],
                    )

            except Exception as e:
                print(f">> [ERROR] Extraction failed for domain '{item['domain']}': {e}")
                raise e
        else:
            print(">> [READY] Filtered & Schema ready. Set run_llm=True (hoặc truyền --extract) để gọi LLM & đẩy lên R2.")

    # 5. Đẩy manifest tổng hợp batch lên tầng Silver trên Cloudflare R2
    if successful_extractions and not dry_run:
        timestamp_now = int(datetime.now().timestamp())
        batch_key = f"silver/batches/extractions_{chosen_date}_{timestamp_now}.json"
        batch_payload = {
            "metadata": {
                "extraction_date": chosen_date,
                "generated_at": datetime.now().isoformat(),
                "total_targets": len(final_queue),
                "successful_extractions": len(successful_extractions),
                "competitions_found": sum(
                    len(r.get("competitions", [])) for r in successful_extractions
                ),
            },
            "results": successful_extractions,
        }

        s3_client.put_object(
            Bucket=BUCKET_NAME,
            Key=batch_key,
            Body=json.dumps(batch_payload, ensure_ascii=False, indent=2).encode("utf-8"),
            ContentType="application/json; charset=utf-8",
            Metadata={"layer": "silver", "extraction_date": chosen_date},
        )
        print(
            f"\n>> [R2 BATCH UPLOADED] Đã đẩy manifest tổng hợp ({len(successful_extractions)} domain) "
            f"lên: s3://{BUCKET_NAME}/{batch_key}"
        )

    print("\n" + "=" * 60)
    print(
        f"Extraction Batch Summary: Processed {processed_count} latest files, "
        f"extracted {len(successful_extractions)} successfully, "
        f"skipped {empty_count} empty files."
    )
    if successful_extractions and not dry_run:
        print(f"Silver JSON đã được đồng bộ trực tiếp lên: s3://{BUCKET_NAME}/silver/extractions/")
    print("=" * 60)
    return successful_extractions


if __name__ == "__main__":
    execute_extraction = "--extract" in sys.argv or os.getenv("EXECUTE_LLM", "0") == "1"
    process_all = "--all" in sys.argv
    dry_run_flag = "--dry-run" in sys.argv

    # Trích xuất tham số dòng lệnh
    target_date_arg = None

    for i, arg in enumerate(sys.argv):
        if arg.startswith("--date="):
            target_date_arg = arg.split("=", 1)[1]
        elif arg == "--date" and i + 1 < len(sys.argv):
            target_date_arg = sys.argv[i + 1]

    process_bronze_bucket(
        run_llm=execute_extraction,
        target_date=target_date_arg,
        process_all_dates=process_all,
        dry_run=dry_run_flag,
    )
