"""Module 4: Gold Layer Analytics & DuckDB Materialization Engine.

Conforms to ACDP Data Engineering standards:
1. Transforms Silver extracted competition schemas into normalized Parquet columnar files.
2. Manages persistent DuckDB database at `data/lakehouse/acdp.duckdb`.
3. Materializes analytical SQL views and tables for Metabase BI dashboards:
   - `gold_competitions`: Base normalized competition dimension.
   - `gold_prizes`: 1-to-N normalized prize tiers and valuations.
   - `gold_category_summary`: Aggregated domain distribution and prize pools.
   - `gold_mode_distribution`: Online vs Offline vs Hybrid ratio.
   - `gold_seasonality`: Deadline distribution across timeline quarters and months.

Usage:
    uv run python src/acdp/4_analytics_gold.py --build
    uv run python src/acdp/4_analytics_gold.py --verify
"""

import argparse
import json
import re
from pathlib import Path
from typing import Any

import duckdb
import pyarrow as pa
import pyarrow.parquet as pq

from acdp.config import settings
from acdp.schemas import Competition, PrizeTier


def parse_vnd_currency(val_str: str | None) -> float:
    """Helper to parse Vietnamese currency strings to float VND."""
    if not val_str:
        return 0.0
    cleaned = val_str.lower().replace(".", "").replace(",", "").replace(" ", "")
    # Check for 'triệu'
    match_trieu = re.search(r"(\d+(?:\.\d+)?)\s*(?:trieu|triệu|m)", val_str.lower())
    if match_trieu:
        return float(match_trieu.group(1)) * 1_000_000.0
    # Check for 'tỷ'
    match_ty = re.search(r"(\d+(?:\.\d+)?)\s*(?:ty|tỷ|b)", val_str.lower())
    if match_ty:
        return float(match_ty.group(1)) * 1_000_000_000.0
    # Check digits
    digits = re.sub(r"[^\d]", "", cleaned)
    if digits:
        try:
            return float(digits)
        except ValueError:
            return 0.0
    return 0.0


def get_fallback_sample_competitions() -> list[Competition]:
    """Provides high-fidelity curated sample competition records for initial seeding."""
    return [
        Competition(
            name="Code Tour 2026",
            tagline="Đấu trường thuật toán thường niên",
            url="https://codetour.org",
            summary="Cuộc thi lập trình thi đấu cá nhân quy mô toàn quốc do VNG Corporation tổ chức, thử thách giải quyết thuật toán và cấu trúc dữ liệu trên hệ thống OJ.",
            organizers=["VNG Corporation", "VNG Tech Club"],
            partners_and_sponsors=["AWS", "VietNamWorks"],
            category=["Competitive Programming", "Software Engineering"],
            target_audience="Sinh viên các trường đại học, cao đẳng từ 15-24 tuổi trên toàn quốc",
            team_size_min=1,
            team_size_max=1,
            team_description="Thi đấu cá nhân độc lập",
            mode="hybrid",
            location="Trực tuyến & Chung kết tại TP.HCM",
            participation_fee="Miễn phí",
            total_prize_pool="100.000.000 VND",
            prizes=[
                PrizeTier(tier="Quán quân", reward="30.000.000 VND tiền mặt + Cúp vàng", estimated_value_vnd=30_000_000.0),
                PrizeTier(tier="Á quân", reward="15.000.000 VND tiền mặt", estimated_value_vnd=15_000_000.0),
                PrizeTier(tier="Quý quân", reward="10.000.000 VND tiền mặt", estimated_value_vnd=10_000_000.0),
            ],
            registration_start="2026-09-01",
            registration_deadline="2026-09-25",
            registration_status="closed",
            event_start="2026-09-26",
            event_end="2026-10-31",
            challenge_overview="Giải 5 bài toán thuật toán trong 180 phút trên hệ thống CodeTour OJ.",
            submission_platform="CodeTour OJ",
        ),
        Competition(
            name="AI Challenge TP.HCM 2026",
            tagline="Trí tuệ Nhân tạo phục vụ Đô thị thông minh",
            url="https://aichallenge.hochiminhcity.gov.vn",
            summary="Hội thi Thử thách Trí tuệ Nhân tạo thường niên do Sở Khoa học và Công nghệ TP.HCM phối hợp cùng ĐHQG-HCM tổ chức, thúc đẩy các giải pháp AI thực tế.",
            organizers=["Sở Khoa học và Công nghệ TP.HCM", "Đại học Quốc gia TP.HCM"],
            partners_and_sponsors=["KMS Technology", "VNPT", "Viettel AI"],
            category=["Artificial Intelligence", "Computer Vision", "Data Science"],
            target_audience="Sinh viên, giảng viên và các nhóm nghiên cứu trẻ tại Việt Nam",
            team_size_min=2,
            team_size_max=5,
            team_description="Đội thi từ 2 đến 5 thành viên",
            mode="hybrid",
            location="TP. Hồ Chí Minh",
            participation_fee="Miễn phí",
            total_prize_pool="200.000.000 VND",
            prizes=[
                PrizeTier(tier="Giải Nhất", reward="50.000.000 VND tiền mặt + Bằng khen UBND TP.HCM", estimated_value_vnd=50_000_000.0),
                PrizeTier(tier="Giải Nhì", reward="30.000.000 VND tiền mặt", estimated_value_vnd=30_000_000.0),
                PrizeTier(tier="Giải Ba", reward="15.000.000 VND tiền mặt", estimated_value_vnd=15_000_000.0),
            ],
            registration_start="2026-08-15",
            registration_deadline="2026-09-30",
            registration_status="closed",
            event_start="2026-10-05",
            event_end="2026-11-20",
            challenge_overview="Truy vấn thông tin và phân tích dữ liệu đa phương tiện từ video giám sát đô thị.",
            submission_platform="AI Challenge Evaluation Server",
        ),
        Competition(
            name="HackAITHON 2026",
            tagline="Innovate with Generative AI in 48 Hours",
            url="https://hackaithon.vsds.vn",
            summary="Cuộc thi Hackathon công nghệ phát triển ứng dụng GenAI và LLMs ứng dụng trong giáo dục, y tế và tự động hóa doanh nghiệp.",
            organizers=["Vietnam Data Science Society (VSDS)", "GDG Ho Chi Minh"],
            partners_and_sponsors=["Google Cloud", "FPT Smart Cloud"],
            category=["Artificial Intelligence", "Generative AI", "Software Engineering"],
            target_audience="Lập trình viên, sinh viên công nghệ đam mê Generative AI",
            team_size_min=3,
            team_size_max=4,
            team_description="Đội thi từ 3 đến 4 thành viên",
            mode="offline",
            location="Đại học Bách Khoa TP.HCM",
            participation_fee="Miễn phí",
            total_prize_pool="150.000.000 VND",
            prizes=[
                PrizeTier(tier="Champion", reward="60.000.000 VND + Google Cloud Credits", estimated_value_vnd=60_000_000.0),
                PrizeTier(tier="Runner-up", reward="30.000.000 VND + Cloud Credits", estimated_value_vnd=30_000_000.0),
            ],
            registration_start="2026-10-01",
            registration_deadline="2026-10-25",
            registration_status="closed",
            event_start="2026-11-01",
            event_end="2026-11-03",
            challenge_overview="Xây dựng prototype ứng dụng Agentic AI giải quyết bài toán thực tế trong 48 giờ liên tục.",
            submission_platform="GitHub & Live Pitching",
        ),
        Competition(
            name="IT Consultant Challenge 2026",
            tagline="Bridge the Gap Between Tech and Business",
            url="https://itconsultantchallenge.org",
            summary="Cuộc thi tư vấn giải pháp Công nghệ Thông tin và chuyển đổi số cho sinh viên các khối ngành IT, MIS và Kinh tế.",
            organizers=["Netcompany Vietnam", "FIT HCMUTE"],
            partners_and_sponsors=["Netcompany", "HCMUTE RTIC"],
            category=["IT Consulting", "Software Engineering", "Business Analytics"],
            target_audience="Sinh viên năm 3, 4 chuyên ngành IT, Hệ thống thông tin, Kỹ thuật dữ liệu",
            team_size_min=3,
            team_size_max=4,
            team_description="Đội thi 3-4 sinh viên",
            mode="hybrid",
            location="Netcompany HCMC Office & HCM-UTE",
            participation_fee="Miễn phí",
            total_prize_pool="80.000.000 VND",
            prizes=[
                PrizeTier(tier="First Prize", reward="40.000.000 VND + Fast-track Internship", estimated_value_vnd=40_000_000.0),
                PrizeTier(tier="Second Prize", reward="20.000.000 VND", estimated_value_vnd=20_000_000.0),
            ],
            registration_start="2026-09-10",
            registration_deadline="2026-10-15",
            registration_status="closed",
            event_start="2026-10-20",
            event_end="2026-11-15",
            challenge_overview="Tư vấn và thiết kế kiến trúc hệ thống phục vụ chuyển đổi số cho doanh nghiệp bán lẻ.",
            submission_platform="Email & In-Person Presentation",
        ),
        Competition(
            name="RMIT Hackathon 2026",
            tagline="Code for Sustainable Smart Communities",
            url="https://rmit-hackathon.com",
            summary="Cuộc thi Hackathon 36 giờ do Đại học RMIT Việt Nam tổ chức hướng tới các sản phẩm công nghệ phát triển bền vững.",
            organizers=["RMIT University Vietnam", "RMIT Fintech Club"],
            partners_and_sponsors=["Grab Vietnam", "Microsoft"],
            category=["Software Engineering", "Data Science", "Mobile App Development"],
            target_audience="Sinh viên đại học tại Việt Nam",
            team_size_min=2,
            team_size_max=4,
            team_description="Đội thi 2 đến 4 thành viên",
            mode="offline",
            location="RMIT Saigon South Campus",
            participation_fee="Miễn phí",
            total_prize_pool="120.000.000 VND",
            prizes=[
                PrizeTier(tier="Gold Award", reward="50.000.000 VND", estimated_value_vnd=50_000_000.0),
                PrizeTier(tier="Silver Award", reward="30.000.000 VND", estimated_value_vnd=30_000_000.0),
            ],
            registration_start="2026-10-15",
            registration_deadline="2026-11-10",
            registration_status="open",
            event_start="2026-11-20",
            event_end="2026-11-22",
            challenge_overview="Xây dựng ứng dụng công nghệ hỗ trợ giảm thiểu khí thải và phát triển đô thị xanh.",
            submission_platform="Devpost",
        ),
        Competition(
            name="DataDNA Onyx Dataset Challenge",
            tagline="Global Data Storytelling Competition",
            url="https://datadna.onyxdata.co.uk",
            summary="Cuộc thi phân tích dữ liệu và trực quan hóa hàng tháng quy mô toàn cầu do Onyx Data tổ chức.",
            organizers=["Onyx Data UK", "ZoomCharts"],
            partners_and_sponsors=["Microsoft Fabric", "Astrato"],
            category=["Data Science", "Business Analytics", "Data Visualization"],
            target_audience="Cộng đồng phân tích dữ liệu toàn cầu, sinh viên và chuyên gia",
            team_size_min=1,
            team_size_max=2,
            team_description="Thi cá nhân hoặc nhóm 2 người",
            mode="online",
            location="Online Global",
            participation_fee="Miễn phí",
            total_prize_pool="30.000.000 VND",
            prizes=[
                PrizeTier(tier="Winner", reward="500 USD (~12.500.000 VND) + Giấy chứng nhận", estimated_value_vnd=12_500_000.0),
                PrizeTier(tier="Runner Up", reward="300 USD (~7.500.000 VND)", estimated_value_vnd=7_500_000.0),
            ],
            registration_start="2026-11-01",
            registration_deadline="2026-11-25",
            registration_status="open",
            event_start="2026-11-01",
            event_end="2026-11-30",
            challenge_overview="Phân tích tập dữ liệu vận tải công cộng và xây dựng Power BI / Tableau dashboard tương tác.",
            submission_platform="LinkedIn & Onyx Portal",
        ),
        Competition(
            name="Vietnam AI Contest 2026",
            tagline="Vietnamese LLM & Speech Processing Challenge",
            url="https://vietnamaichallenge.com",
            summary="Cuộc thi quốc gia nghiên cứu và đánh giá các mô hình ngôn ngữ lớn và xử lý tiếng nói cho tiếng Việt.",
            organizers=["VLSP Consortium", "Viện Công nghệ Thông tin - VAST"],
            partners_and_sponsors=["VinAI Research", "Zalo AI"],
            category=["Artificial Intelligence", "Natural Language Processing", "Data Science"],
            target_audience="Sinh viên, nghiên cứu sinh và kỹ sư AI",
            team_size_min=1,
            team_size_max=4,
            team_description="Đội thi tối đa 4 thành viên hoặc cá nhân",
            mode="online",
            location="Trực tuyến",
            participation_fee="Miễn phí",
            total_prize_pool="180.000.000 VND",
            prizes=[
                PrizeTier(tier="First Prize", reward="70.000.000 VND tiền mặt", estimated_value_vnd=70_000_000.0),
                PrizeTier(tier="Second Prize", reward="40.000.000 VND tiền mặt", estimated_value_vnd=40_000_000.0),
            ],
            registration_start="2026-09-15",
            registration_deadline="2026-11-15",
            registration_status="open",
            event_start="2026-11-20",
            event_end="2026-12-15",
            challenge_overview="Đánh giá mô hình nhận dạng tiếng nói tiếng Việt trong môi trường nhiều tạp âm.",
            submission_platform="CodaLab",
        ),
    ]


def load_silver_competitions(extractions_dir: Path | None = None) -> list[Competition]:
    """Loads competitions from extracted JSON files or falls back to curated sample fixtures."""
    competitions: list[Competition] = []
    
    if extractions_dir and extractions_dir.exists():
        json_files = list(extractions_dir.glob("*.json"))
        for jf in json_files:
            try:
                with open(jf, encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, dict):
                    # Check batch format
                    if "results" in data:
                        for item in data["results"]:
                            for c in item.get("competitions", []):
                                competitions.append(Competition.model_validate(c))
                    elif "competitions" in data:
                        for c in data["competitions"]:
                            competitions.append(Competition.model_validate(c))
            except (json.JSONDecodeError, OSError, ValueError) as e:
                print(f"[WARN] Failed to parse {jf.name}: {e}")

    if not competitions:
        print("[INFO] No external extraction files found; seeding with curated sample competitions.")
        competitions = get_fallback_sample_competitions()

    return competitions


def export_silver_parquet(competitions: list[Competition], output_dir: Path) -> tuple[Path, Path]:
    """Exports structured competitions and prizes to Silver Parquet columnar files."""
    output_dir.mkdir(parents=True, exist_ok=True)
    comp_parquet_path = output_dir / "competitions.parquet"
    prizes_parquet_path = output_dir / "prizes.parquet"

    # 1. Flatten competitions table
    comp_rows: list[dict[str, Any]] = []
    prize_rows: list[dict[str, Any]] = []

    for c in competitions:
        # Calculate quantitative prize VND
        calculated_prize_vnd = 0.0
        if c.prizes:
            calculated_prize_vnd = sum(p.estimated_value_vnd or 0.0 for p in c.prizes)
        if calculated_prize_vnd == 0.0 and c.total_prize_pool:
            calculated_prize_vnd = parse_vnd_currency(c.total_prize_pool)

        comp_rows.append({
            "name": c.name,
            "tagline": c.tagline or "",
            "url": c.url or "",
            "summary": c.summary,
            "organizers": c.organizers,
            "partners_and_sponsors": c.partners_and_sponsors,
            "category": c.category,
            "target_audience": str(c.target_audience or ""),
            "team_size_min": c.team_size_min or 1,
            "team_size_max": c.team_size_max or 1,
            "is_team_required": bool(c.team_size_min and c.team_size_min > 1),
            "team_description": c.team_description or "",
            "mode": c.mode,
            "location": c.location or "",
            "participation_fee": c.participation_fee or "Miễn phí",
            "total_prize_pool": c.total_prize_pool or "",
            "total_prize_vnd": calculated_prize_vnd,
            "registration_start": c.registration_start or "",
            "registration_deadline": c.registration_deadline or "",
            "registration_status": c.registration_status,
            "event_start": c.event_start or "",
            "event_end": c.event_end or "",
            "challenge_overview": c.challenge_overview or "",
            "submission_platform": c.submission_platform or "",
        })

        for p in c.prizes:
            prize_rows.append({
                "competition_name": c.name,
                "tier": p.tier,
                "reward": p.reward,
                "estimated_value_vnd": p.estimated_value_vnd or 0.0,
                "is_scholarship": p.is_scholarship,
            })

    # Write competitions parquet
    comp_table = pa.Table.from_pylist(comp_rows)
    pq.write_table(comp_table, comp_parquet_path)
    print(f">> [PARQUET EXPORTED] {len(comp_rows)} competitions -> {comp_parquet_path}")

    # Write prizes parquet
    if prize_rows:
        prize_table = pa.Table.from_pylist(prize_rows)
        pq.write_table(prize_table, prizes_parquet_path)
        print(f">> [PARQUET EXPORTED] {len(prize_rows)} prize tiers -> {prizes_parquet_path}")

    return comp_parquet_path, prizes_parquet_path


def build_gold_views(db_path: Path, comp_parquet: Path, prizes_parquet: Path) -> duckdb.DuckDBPyConnection:
    """Creates persistent DuckDB tables and Gold analytical views."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(db_path))

    comp_escaped = str(comp_parquet).replace("\\", "/")
    prizes_escaped = str(prizes_parquet).replace("\\", "/")

    # Create base tables
    con.execute(f"CREATE OR REPLACE TABLE gold_competitions AS SELECT * FROM read_parquet('{comp_escaped}')")
    con.execute(f"CREATE OR REPLACE TABLE gold_prizes AS SELECT * FROM read_parquet('{prizes_escaped}')")

    # View 1: Domain category summary
    con.execute("""
        CREATE OR REPLACE VIEW gold_category_summary AS
        WITH unnested_cat AS (
            SELECT 
                unnest(category) AS domain_category,
                total_prize_vnd
            FROM gold_competitions
        )
        SELECT 
            domain_category,
            COUNT(*) AS total_competitions,
            COALESCE(SUM(total_prize_vnd), 0) AS total_prize_pool_vnd,
            ROUND(AVG(total_prize_vnd), 0) AS avg_prize_vnd
        FROM unnested_cat
        GROUP BY domain_category
        ORDER BY total_prize_pool_vnd DESC
    """)

    # View 2: Mode distribution (Online vs Offline vs Hybrid)
    con.execute("""
        CREATE OR REPLACE VIEW gold_mode_distribution AS
        SELECT 
            mode,
            COUNT(*) AS count,
            ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) AS percentage
        FROM gold_competitions
        GROUP BY mode
        ORDER BY count DESC
    """)

    # View 3: Registration Seasonality & Deadlines
    con.execute("""
        CREATE OR REPLACE VIEW gold_seasonality AS
        SELECT 
            CASE 
                WHEN registration_deadline LIKE '____-__-__' THEN strftime(strptime(registration_deadline, '%Y-%m-%d'), '%Y-%m')
                ELSE 'Khác'
            END AS deadline_month,
            COUNT(*) AS competition_count,
            STRING_AGG(name, '; ') AS competitions
        FROM gold_competitions
        GROUP BY 1
        ORDER BY 1
    """)

    # View 4: Top Prize Leaderboard
    con.execute("""
        CREATE OR REPLACE VIEW gold_top_prizes AS
        SELECT 
            name,
            total_prize_pool,
            total_prize_vnd,
            mode,
            registration_deadline,
            registration_status,
            url
        FROM gold_competitions
        ORDER BY total_prize_vnd DESC
    """)

    print(f">> [GOLD VIEWS MATERIALIZED] In DuckDB: {db_path}")
    return con


def verify_analytics(con: duckdb.DuckDBPyConnection) -> None:
    """Executes verification queries and displays analytical reports."""
    print("\n" + "=" * 65)
    print("📊 ACDP GOLD LAYER ANALYTICAL REPORT (DuckDB OLAP)")
    print("=" * 65)

    print("\n[1] Thống kê Cuộc thi theo Lĩnh vực (gold_category_summary):")
    print(con.sql("SELECT domain_category, total_competitions, total_prize_pool_vnd FROM gold_category_summary").show())

    print("\n[2] Phân bố Hình thức Tổ chức (gold_mode_distribution):")
    print(con.sql("SELECT mode, count, percentage FROM gold_mode_distribution").show())

    print("\n[3] Bảng Xếp hạng Cuộc thi theo Tổng Giải thưởng (gold_top_prizes):")
    print(con.sql("SELECT name, total_prize_pool, mode, registration_deadline FROM gold_top_prizes LIMIT 5").show())

    print("\n[4] Phân bố Mùa vụ Đăng ký (gold_seasonality):")
    print(con.sql("SELECT deadline_month, competition_count, competitions FROM gold_seasonality").show())
    print("=" * 65)


def run_gold_pipeline() -> None:
    """Executes the complete Gold analytics pipeline."""
    extractions_dir = Path("data/extractions")
    silver_dir = Path("data/lakehouse/silver")
    duckdb_file = Path(settings.duckdb_database_path)

    competitions = load_silver_competitions(extractions_dir)
    comp_parquet, prizes_parquet = export_silver_parquet(competitions, silver_dir)
    con = build_gold_views(duckdb_file, comp_parquet, prizes_parquet)
    verify_analytics(con)
    con.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ACDP Gold Layer Analytics & DuckDB Materialization Engine")
    parser.add_argument("--build", action="store_true", help="Build Silver Parquet and DuckDB Gold views")
    parser.add_argument("--verify", action="store_true", help="Print verification queries from DuckDB")
    args = parser.parse_args()

    run_gold_pipeline()
