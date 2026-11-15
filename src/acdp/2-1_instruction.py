from duckdb import query
from instructor.v2.core import response_model
from jinja2.bccache import Bucket
import boto3
import instructor
import os
from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv()

class Competition(BaseModel):
    url: str = Field(description="Tên miền trang web chứa thông tin cuộc thi")
    name: str = Field(description="Tên cuộc thi")
    content: str = Field(description="Nội dung cuộc thi")

SYSTEM_PROMPT = """Bạn là chuyên gia Kỹ thuật Dữ liệu (Data Engineer) phụ trách bóc tách thông tin có cấu trúc từ tài liệu Markdown của các cuộc thi học thuật, tin học, AI và khoa học dữ liệu.

Nhiệm vụ của bạn: Phân tích nội dung Markdown thô được cào từ các trang web cuộc thi (tiếng Việt hoặc tiếng Anh).
"""

# LOAD ENV
LLM_PROVIDER = os.getenv("LLM_PROVIDER")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
BUCKET_NAME = os.getenv("BUCKET_NAME")
AWS_ENDPOINT_URL = os.getenv("AWS_ENDPOINT_URL")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")

client = instructor.from_provider(LLM_PROVIDER)

# READ FILES FROM BUCKET
s3_client = boto3.client(
    service_name="s3",
    endpoint_url=AWS_ENDPOINT_URL,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name="auto"
)

paginator = s3_client.get_paginator("list_objects_v2")

pages = paginator.paginate(
    Bucket=BUCKET_NAME,
    Prefix="bronze/"
)

for p in pages:
    if 'Contents' not in p: continue

    for item in p['Contents']:
        file_key = item['Key']

        response = s3_client.get_object(Bucket=BUCKET_NAME, Key=file_key)
        print("="*50)
        for competition in response['Body'].iter_lines():
            com = competition.decode("utf-8", errors="replace")
# PHẦN ĐỌC DỮ LIỆU TỪ BUCKET ĐÃ KẾT THÚC
# TIẾP THEO LÀ TẠO BASE MODEL VÀ ĐƯA DỮ LIỆU VÀO INSTRUCTOR ĐỂ TRÍCH XUẤT SCHEMA
# TẠO STRUCTURED OUTPUT             
            extract_com = client.create(
                response_model=Competition,
                messages = [
                    {'role': 'system', 'content': SYSTEM_PROMPT},
                    {'role': 'user', 'content': com}
                ]
            )
            print(extract_com)