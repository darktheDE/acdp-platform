# HƯỚNG DẪN CẤU HÌNH VÀ ĐẨY DỮ LIỆU LÊN LAKEHOUSE R2
*(Tài liệu thực chiến dành cho Duy — Dự án ACDP)*

Bucket R2: `acdp-lakehouse` (Hưng đã tạo sẵn và đã đẩy dữ liệu mẫu lớp Đồng).  
Mục tiêu tài liệu: Hướng dẫn Duy thiết lập cấu hình trên máy cá nhân, kiểm tra kết nối và tự đẩy (push) dữ liệu các lớp Đồng, Bạc, Vàng lên R2.

---

## BƯỚC 1: CÀI ĐẶT THƯ VIỆN CẦN THIẾT

Mở terminal trong thư mục dự án và cài đặt các thư viện thao tác với Delta Lake và S3/R2:

```bash
uv add deltalake duckdb pyarrow python-dotenv boto3
```
*(Nếu dùng pip thông thường: `pip install deltalake duckdb pyarrow python-dotenv boto3`)*

---

## BƯỚC 2: CẤU HÌNH TỆP `.env` TRÊN MÁY DUY

Tạo hoặc mở tệp `.env` tại thư mục gốc của repository (tệp này đã có trong `.gitignore`, không lo bị đẩy lên GitHub).

Điền các thông số kết nối do Hưng cung cấp:

```env
# ==============================================================================
# CLOUDFLARE R2 CREDENTIALS (HƯNG CUNG CẤP)
# ==============================================================================
AWS_ENDPOINT_URL=https://<ACCOUNT_ID>.r2.cloudflarestorage.com
AWS_ACCESS_KEY_ID=<ACCESS_KEY_ID_DO_HUNG_GUI>
AWS_SECRET_ACCESS_KEY=<SECRET_ACCESS_KEY_DO_HUNG_GUI>
AWS_REGION=auto
AWS_ALLOW_HTTP=false

# Bắt buộc để delta-rs ghi file an toàn trên R2
AWS_S3_ALLOW_UNSAFE_RENAME=true

# Đường dẫn 3 phân tầng Lakehouse trên R2
BRONZE_STORAGE_URI=s3://acdp-lakehouse/bronze/events
SILVER_STORAGE_URI=s3://acdp-lakehouse/silver/competitions
GOLD_STORAGE_URI=s3://acdp-lakehouse/gold/marts
```

---

## BƯỚC 3: KIỂM TRA KẾT NỐI VÀ ĐỌC DỮ LIỆU LỚP ĐỒNG ĐÃ CÓ

Chạy đoạn mã Python kiểm tra xem máy Duy đã kết nối thành công và đọc được dữ liệu lớp Đồng mà Hưng đã đẩy lên hay chưa:

```python
import os
from deltalake import DeltaTable
from dotenv import load_dotenv

load_dotenv()

storage_options = {
    "AWS_ENDPOINT_URL": os.environ["AWS_ENDPOINT_URL"],
    "AWS_ACCESS_KEY_ID": os.environ["AWS_ACCESS_KEY_ID"],
    "AWS_SECRET_ACCESS_KEY": os.environ["AWS_SECRET_ACCESS_KEY"],
    "AWS_REGION": "auto",
    "AWS_S3_ALLOW_UNSAFE_RENAME": "true",
}

r2_bronze_uri = os.environ.get("BRONZE_STORAGE_URI", "s3://acdp-lakehouse/bronze/events")

print(f"[*] Đang kết nối tới R2: {r2_bronze_uri}")
dt = DeltaTable(r2_bronze_uri, storage_options=storage_options)
table = dt.to_pyarrow_table()

print(f"[+] Kết nối R2 thành công!")
print(f"[+] Số bản ghi lớp Đồng hiện có trên R2: {len(table)}")
print(f"[+] Schema các cột: {table.column_names}")
```

Nếu in ra số lượng bản ghi và danh sách cột (ví dụ: `raw_id`, `source_url`, `crawled_at`...), máy Duy đã kết nối R2 hoàn tất.

---

## BƯỚC 4: HƯỚNG DẪN DUY PUSH DỮ LIỆU LÊN R2

### 4.1. Đẩy dữ liệu Lớp Bạc (Silver Layer) — Nhiệm vụ trọng tâm của Duy

Sau khi Duy bóc tách thông tin và khởi tạo danh sách các thực thể `SilverCompetitionRecord` (Pydantic v2), Duy đẩy trực tiếp lên R2 bằng hàm sau:

```python
import os
import pyarrow as pa
from deltalake import write_deltalake
from dotenv import load_dotenv
from acdp.lakehouse.schema import SilverCompetitionRecord

load_dotenv()

storage_options = {
    "AWS_ENDPOINT_URL": os.environ["AWS_ENDPOINT_URL"],
    "AWS_ACCESS_KEY_ID": os.environ["AWS_ACCESS_KEY_ID"],
    "AWS_SECRET_ACCESS_KEY": os.environ["AWS_SECRET_ACCESS_KEY"],
    "AWS_REGION": "auto",
    "AWS_S3_ALLOW_UNSAFE_RENAME": "true",
}

def push_silver_records_to_r2(records: list[SilverCompetitionRecord]):
    """Chuyển đổi danh sách Pydantic Silver thành Arrow Table và đẩy lên R2."""
    if not records:
        print("[!] Không có bản ghi nào để đẩy.")
        return

    # 1. Chuyển đổi danh sách Pydantic sang dictionary
    data_dicts = [r.to_json_dict() for r in records]
    
    # 2. Tạo PyArrow Table
    arrow_table = pa.Table.from_pylist(data_dicts)
    
    r2_silver_uri = os.environ.get("SILVER_STORAGE_URI", "s3://acdp-lakehouse/silver/competitions")
    print(f"[*] Đang đẩy {len(records)} bản ghi Lớp Bạc lên R2: {r2_silver_uri}")
    
    # 3. Ghi nối tiếp (append) vào bảng Delta trên R2
    write_deltalake(
        r2_silver_uri,
        arrow_table,
        mode="append",
        storage_options=storage_options,
    )
    print("[+] Đẩy dữ liệu Lớp Bạc lên Cloudflare R2 thành công!")
```

---

### 4.2. Đẩy dữ liệu Lớp Đồng (Bronze Layer) — Nếu Duy có thêm nguồn cào mới

Nếu Duy thu thập thêm trang web thô và muốn đẩy trực tiếp vào Lớp Đồng:

```python
import os
import pyarrow as pa
from deltalake import write_deltalake
from dotenv import load_dotenv
from acdp.lakehouse.schema import BRONZE_ARROW_SCHEMA, BronzeRecord

load_dotenv()

storage_options = {
    "AWS_ENDPOINT_URL": os.environ["AWS_ENDPOINT_URL"],
    "AWS_ACCESS_KEY_ID": os.environ["AWS_ACCESS_KEY_ID"],
    "AWS_SECRET_ACCESS_KEY": os.environ["AWS_SECRET_ACCESS_KEY"],
    "AWS_REGION": "auto",
    "AWS_S3_ALLOW_UNSAFE_RENAME": "true",
}

def push_bronze_records_to_r2(records: list[BronzeRecord]):
    """Đẩy các bản ghi HTML thô nén Zstandard lên Tầng Đồng R2."""
    data_dicts = [r.model_dump() for r in records]
    arrow_table = pa.Table.from_pylist(data_dicts, schema=BRONZE_ARROW_SCHEMA)
    
    r2_bronze_uri = os.environ.get("BRONZE_STORAGE_URI", "s3://acdp-lakehouse/bronze/events")
    write_deltalake(
        r2_bronze_uri,
        arrow_table,
        mode="append",
        storage_options=storage_options,
    )
    print(f"[+] Đã đẩy {len(records)} bản ghi lên Lớp Đồng R2!")
```

---

### 4.3. Đẩy dữ liệu Lớp Vàng (Gold Layer) — Phục vụ phân tích OLAP

Khi tổng hợp bảng sự kiện hoặc bảng chiều từ Lớp Bạc, Duy dùng DuckDB đẩy trực tiếp tệp Parquet lên R2 mà không cần lưu trung gian:

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
    SET s3_use_ssl = true;
    SET s3_url_style = 'path';
""")

print("[*] Đang xuất bản Fact_Competitions lên Lớp Vàng R2...")
con.execute("""
    COPY (
        SELECT 
            competition_id,
            canonical_name,
            organizer_type,
            edition_year,
            total_prize_vnd,
            first_prize_vnd,
            min_team_size,
            max_team_size,
            registration_fee_vnd
        FROM delta_scan('s3://acdp-lakehouse/silver/competitions')
    ) TO 's3://acdp-lakehouse/gold/marts/fact_competitions.parquet' (FORMAT PARQUET);
""")
print("[+] Xuất bản Lớp Vàng thành công!")
```

---

## BƯỚC 5: TRUY VẤN NHANH DỮ LIỆU TỪ R2 BẰNG DUCKDB (KHÔNG TẢI TỆP)

Duy có thể viết truy vấn SQL trực tiếp trên mây từ máy cá nhân với tốc độ mili-giây:

```python
import os
import duckdb
from dotenv import load_dotenv

load_dotenv()

con = duckdb.connect()
con.execute("INSTALL httpfs; LOAD httpfs; INSTALL delta; LOAD delta;")

endpoint = os.environ["AWS_ENDPOINT_URL"].replace("https://", "")
con.execute(f"""
    SET s3_endpoint = '{endpoint}';
    SET s3_access_key_id = '{os.environ["AWS_ACCESS_KEY_ID"]}';
    SET s3_secret_access_key = '{os.environ["AWS_SECRET_ACCESS_KEY"]}';
    SET s3_use_ssl = true;
    SET s3_url_style = 'path';
""")

# Truy vấn dữ liệu thực tế trên R2
df = con.execute("""
    SELECT canonical_name, organizer_name, registration_deadline, total_prize_vnd
    FROM delta_scan('s3://acdp-lakehouse/silver/competitions')
    LIMIT 5;
""").df()

print(df)
```

---

## 3 NGUYÊN TẮC QUAN TRỌNG KHI LÀM VIỆC CHUNG

1. Bảo mật khóa truy cập: Không chia sẻ hoặc commit tệp `.env` lên GitHub dưới bất kỳ hình thức nào.
2. Chế độ ghi nối tiếp: Luôn sử dụng `mode="append"` khi đẩy dữ liệu để tránh ghi đè làm mất các bản ghi mà thành viên khác đã đẩy lên trước đó.
3. Cờ an toàn Delta Lake: Đảm bảo luôn bật `AWS_S3_ALLOW_UNSAFE_RENAME=true` trong môi trường để `delta-rs` hoàn tất giao dịch commit an toàn trên R2.
