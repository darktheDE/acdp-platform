# HƯỚNG DẪN CẤU HÌNH VÀ ĐỒNG BỘ DỮ LIỆU TRÊN CLOUDFLARE R2 (QUY MÔ TỐI GIẢN 5–10 CUỘC THI)
*(Tài liệu thực chiến dành cho Duy & Hưng — Giai đoạn Tiểu luận chuyên ngành ACDP)*

Bucket R2: `acdp-lakehouse`.  
Mục tiêu tài liệu: Hướng dẫn thiết lập cấu hình và đồng bộ dữ liệu theo **Phương án Tối giản nhất (DIR-015)** cho tập **5–10 cuộc thi mẫu** trong giai đoạn Tiểu luận chuyên ngành (TLCN):
- **Tầng Bronze**: Cào văn bản Markdown sạch bằng `Crawl4AI` và đẩy trực tiếp lên R2 bằng `boto3` (`src/acdp/1_crawl_to_bronze.py`), **không nén nhị phân Zstandard**.
- **Tầng Silver**: Đọc văn bản Markdown từ R2 (hoặc `data/raw/markdown/`), dùng `instructor` bóc tách thành thực thể Pydantic v2 `SilverCompetitionRecord` (`src/acdp/2_instruction.py`) và lưu dưới dạng tệp Parquet / JSON chuẩn.
- **Tầng Gold / Truy vấn**: Dùng **DuckDB** đọc trực tiếp tệp Parquet / JSON từ R2 hoặc Local.

---

## BƯỚC 1: ĐỒNG BỘ MÔI TRƯỜNG PYTHON BẰNG `uv`

Mở terminal tại thư mục gốc của dự án và đồng bộ các gói phụ thuộc đã khai báo trong `pyproject.toml`:

```bash
uv sync
```

---

## BƯỚC 2: CẤU HÌNH TỆP `.env`

Tạo hoặc mở tệp `.env` tại thư mục gốc của repository (tệp này đã có trong `.gitignore`, tuyệt đối không đẩy lên GitHub):

```env
# ==============================================================================
# CLOUDFLARE R2 CREDENTIALS
# ==============================================================================
BUCKET_NAME=acdp-lakehouse
AWS_ENDPOINT_URL=https://<ACCOUNT_ID>.r2.cloudflarestorage.com
AWS_ACCESS_KEY_ID=<ACCESS_KEY_ID>
AWS_SECRET_ACCESS_KEY=<SECRET_ACCESS_KEY>
AWS_REGION=auto
AWS_ALLOW_HTTP=false
AWS_S3_ALLOW_UNSAFE_RENAME=true

# Đường dẫn lưu trữ
BRONZE_STORAGE_BACKEND=cloudflare_r2
BRONZE_STORAGE_URI=s3://acdp-lakehouse/bronze
SILVER_STORAGE_URI=s3://acdp-lakehouse/silver
GOLD_STORAGE_URI=s3://acdp-lakehouse/gold
```

---

## BƯỚC 3: THU THẬP VÀ ĐẨY DỮ LIỆU MARKDOWN LÊN TẦNG BRONZE R2 (`1_crawl_to_bronze.py`)

Với quy mô 5–10 cuộc thi của giai đoạn TLCN, hệ thống sử dụng trực tiếp kịch bản [`src/acdp/1_crawl_to_bronze.py`](../../src/acdp/1_crawl_to_bronze.py) để cào nội dung văn bản Markdown (`text/markdown; charset=utf-8`) và đẩy thẳng lên R2 qua `boto3`:

```python
import os
from datetime import datetime
from urllib.parse import urlparse
import boto3
from dotenv import load_dotenv

load_dotenv()

s3_client = boto3.client(
    service_name="s3",
    endpoint_url=os.getenv("AWS_ENDPOINT_URL"),
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name="auto",
)

def upload_to_bronze(md_content: str, source_url: str) -> str:
    """Đẩy trực tiếp văn bản Markdown nguyên bản (UTF-8) của cuộc thi lên tầng Bronze R2."""
    now = datetime.now()
    dm_name = urlparse(source_url).netloc or source_url

    bronze_key = (
        f"bronze/{dm_name}"
        f"/year={now.year}/month={now.strftime('%m')}/day={now.strftime('%d')}/"
        f"{int(now.timestamp())}"
    )

    s3_client.put_object(
        Bucket=os.getenv("BUCKET_NAME", "acdp-lakehouse"),
        Key=bronze_key,
        Body=md_content.encode("utf-8"),
        ContentType="text/markdown; charset=utf-8",
        Metadata={"source": dm_name, "layer": "bronze"},
    )
    print(f"[+] Đã đẩy nội dung {dm_name} lên Bronze R2: {bronze_key}")
    return bronze_key
```

---

## BƯỚC 4: TRÍCH XUẤT VÀ ĐẨY DỮ LIỆU LÊN TẦNG SILVER R2 (`2_instruction.py`)

Sau khi dùng `instructor` bóc tách 5–10 file Markdown thành danh sách các thực thể `SilverCompetitionRecord` (Pydantic v2), chuyển đổi trực tiếp sang tệp Parquet và đẩy lên tầng Silver R2:

```python
import io
import os
import boto3
import pyarrow as pa
import pyarrow.parquet as pq
from dotenv import load_dotenv
from acdp.lakehouse.schema import SilverCompetitionRecord

load_dotenv()

def push_silver_records_to_r2(records: list[SilverCompetitionRecord]) -> None:
    """Chuyển danh sách SilverCompetitionRecord thành file Parquet gọn nhẹ trên R2."""
    if not records:
        return

    data_dicts = [r.to_json_dict() for r in records]
    arrow_table = pa.Table.from_pylist(data_dicts)

    buffer = io.BytesIO()
    pq.write_table(arrow_table, buffer)
    buffer.seek(0)

    s3_client = boto3.client(
        service_name="s3",
        endpoint_url=os.getenv("AWS_ENDPOINT_URL"),
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        region_name="auto",
    )

    bucket = os.getenv("BUCKET_NAME", "acdp-lakehouse")
    silver_key = "silver/competitions.parquet"
    s3_client.put_object(
        Bucket=bucket,
        Key=silver_key,
        Body=buffer.getvalue(),
        ContentType="application/octet-stream",
    )
    print(f"[+] Đã đẩy {len(records)} cuộc thi chuẩn hóa lên s3://{bucket}/{silver_key}")
```

---

## BƯỚC 5: TRUY VẤN PHÂN TÍCH TRỰC TIẾP BẰNG DUCKDB (TẦNG SILVER & GOLD)

Với 5–10 cuộc thi đã chuẩn hóa trong tệp Parquet trên R2 (hoặc lưu cục bộ tại `data/lakehouse/silver/competitions.parquet`), **DuckDB** đọc và phân tích trực tiếp trong vài mili-giây mà không cần cài đặt PostgreSQL hay cụm máy chủ:

```python
import os
import duckdb
from dotenv import load_dotenv

load_dotenv()

con = duckdb.connect()
con.execute("INSTALL httpfs; LOAD httpfs;")

endpoint = os.environ["AWS_ENDPOINT_URL"].replace("https://", "")
con.execute(f"""
    SET s3_endpoint = '{endpoint}';
    SET s3_access_key_id = '{os.environ["AWS_ACCESS_KEY_ID"]}';
    SET s3_secret_access_key = '{os.environ["AWS_SECRET_ACCESS_KEY"]}';
    SET s3_region = 'auto';
    SET s3_use_ssl = true;
    SET s3_url_style = 'path';
""")

bucket = os.getenv("BUCKET_NAME", "acdp-lakehouse")
df = con.execute(f"""
    SELECT 
        canonical_name,
        organizer_name,
        registration_deadline,
        total_prize_vnd,
        registration_link
    FROM read_parquet('s3://{bucket}/silver/competitions.parquet')
    ORDER BY total_prize_vnd DESC;
""").df()

print(df)
```

---

## 3 NGUYÊN TẮC QUAN TRỌNG TRONG GIAI ĐOẠN TLCN (5–10 CUỘC THI)

1. **Giữ kiến trúc tối giản**: Ở quy mô 5–10 cuộc thi ($\sim 1\text{ MB}$), lưu văn bản Markdown (`UTF-8`) nguyên bản ở tầng Bronze và tệp Parquet ở tầng Silver để dễ dàng kiểm tra bằng mắt thường và gỡ lỗi nhanh.
2. **Bảo mật khóa truy cập**: Tuyệt đối không chia sẻ hoặc commit tệp `.env` lên GitHub.
3. **Tái lập kiểm thử**: Luôn giữ bản sao của 7 cuộc thi mẫu trong `data/raw/markdown/` để có thể chạy thử nghiệm cục bộ ngay cả khi không có kết nối mạng.
