"""Module 3: RAG Chatbot MVP (LangChain + Qdrant + Gradio).

Flow:
    1. Đọc snapshot mới nhất của từng domain theo ngày cào trên R2 (tầng Bronze).
    2. Làm sạch Markdown và chia chunk bằng SemanticChunker.
    3. Embedding (Ollama qwen3-embedding:4b) và upsert vào Qdrant.
    4. Retriever (MMR) cung cấp ngữ cảnh cho prompt.
    5. Lưu lịch sử hội thoại theo từng session (list các message).
    6. Gradio ChatInterface để kiểm thử tương tác.

Cách chạy (từ thư mục src/acdp):
    python 3_chatbot_mvp.py --ingest                 # nạp dữ liệu ngày cào mới nhất vào Qdrant
    python 3_chatbot_mvp.py --ingest --date 2026-11-03
    python 3_chatbot_mvp.py                          # mở Gradio chatbot
    python 3_chatbot_mvp.py --ingest --chat          # nạp xong rồi mở chatbot
"""

import os
import re
import sys
import time
import uuid
from collections import defaultdict
from datetime import datetime

import boto3
import gradio as gr
from dotenv import find_dotenv, load_dotenv
from google import genai
from google.genai import types as genai_types
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_experimental.text_splitter import SemanticChunker
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.http.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PayloadSchemaType,
    VectorParams,
)

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv(find_dotenv(usecwd=True))

# ==============================================================================
# CẤU HÌNH
# ==============================================================================
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
QDRANT_CLUSTER_ENDPOINT = os.getenv("QDRANT_CLUSTER_ENDPOINT")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "acdp_competitions")

BUCKET_NAME = os.getenv("BUCKET_NAME")
ENDPOINT_URL = os.getenv("AWS_ENDPOINT_URL")
ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "gemini-embedding-001")
# LLM sinh câu trả lời: mặc định dùng Google Gemma 4 (gemma-4-26b-a4b-it) hoặc fallback gemini-3.5-flash
CHAT_MODEL = os.getenv("CHAT_MODEL") or os.getenv("LLM_PROVIDER", "google/gemma-4-26b-a4b-it").split("/", 1)[-1]

RETRIEVER_K = 6               # số chunk đưa vào prompt
RETRIEVER_FETCH_K = 20        # số ứng viên trước khi MMR lọc đa dạng
MAX_HISTORY_TURNS = 6         # số lượt hỏi-đáp gần nhất đưa vào prompt

# ==============================================================================
# KHỞI TẠO CLIENT
# ==============================================================================
# google-genai tự đọc GOOGLE_API_KEY / GEMINI_API_KEY từ môi trường
llm_client = genai.Client()


class GeminiEmbeddings(Embeddings):
    """Embeddings sử dụng Gemini API với hỗ trợ batching và MRL output_dimensionality."""

    def __init__(self, client: genai.Client, model: str = "gemini-embedding-001", dimension: int = 2560, batch_size: int = 32):
        self.client = client
        self.model = model
        self.dimension = dimension
        self.batch_size = batch_size

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        vectors = []
        cfg = {"output_dimensionality": self.dimension} if self.dimension else None
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i : i + self.batch_size]
            res = self.client.models.embed_content(
                model=self.model,
                contents=batch,
                config=cfg,
            )
            for e in res.embeddings:
                vectors.append(e.values)
        return vectors

    def embed_query(self, text: str) -> list[float]:
        return self.embed_documents([text])[0]


embeddings = GeminiEmbeddings(
    client=llm_client,
    model=EMBEDDING_MODEL,
    dimension=2560,
    batch_size=int(os.getenv("EMBED_BATCH_SIZE", "32")),
)

qdrant_client = QdrantClient(url=QDRANT_CLUSTER_ENDPOINT, api_key=QDRANT_API_KEY)

s3_client = boto3.client(
    service_name="s3",
    endpoint_url=ENDPOINT_URL,
    aws_access_key_id=ACCESS_KEY_ID,
    aws_secret_access_key=SECRET_ACCESS_KEY,
    region_name="auto",
)


# ==============================================================================
# BƯỚC 1: ĐỌC SNAPSHOT MỚI NHẤT THEO NGÀY TRÊN R2
# ==============================================================================
BRONZE_KEY_PATTERN = re.compile(
    r"^bronze/([^/]+)/year=(\d{4})/month=(\d{2})/day=(\d{2})/(\d+)$"
)


def list_latest_bronze_snapshots(target_date: str | None = None) -> tuple[str, list[dict]]:
    """Trả về (ngày được chọn, danh sách snapshot mới nhất của mỗi domain trong ngày đó).

    Bỏ qua _delta_log, parquet và file rỗng. Nếu không truyền ngày: ưu tiên hôm nay,
    nếu hôm nay chưa cào thì lấy ngày cào mới nhất trên bucket.
    """
    items = []
    paginator = s3_client.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=BUCKET_NAME, Prefix="bronze/"):
        for obj in page.get("Contents", []):
            match = BRONZE_KEY_PATTERN.match(obj["Key"])
            if not match or obj.get("Size", 0) == 0:
                continue
            domain, year, month, day, ts = match.groups()
            items.append({
                "key": obj["Key"],
                "domain": domain,
                "date": f"{year}-{month}-{day}",
                "timestamp": int(ts),
            })

    if not items:
        raise RuntimeError("Không tìm thấy snapshot hợp lệ nào trong bronze/.")

    available_dates = sorted({it["date"] for it in items})
    if target_date:
        if target_date not in available_dates:
            raise ValueError(f"Ngày {target_date} không có dữ liệu. Khả dụng: {available_dates}")
        chosen_date = target_date
    else:
        today = datetime.now().strftime("%Y-%m-%d")
        chosen_date = today if today in available_dates else available_dates[-1]

    by_domain = defaultdict(list)
    for it in items:
        if it["date"] == chosen_date:
            by_domain[it["domain"]].append(it)

    latest = [max(group, key=lambda x: x["timestamp"]) for group in by_domain.values()]
    return chosen_date, sorted(latest, key=lambda x: x["domain"])


def clean_markdown(raw_md: str) -> str:
    """Loại bỏ ảnh, link rỗng, link neo điều hướng và dòng trùng lặp liên tiếp."""
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", raw_md)          # ảnh
    text = re.sub(r"\[\s*\]\([^)]*\)", "", text)                 # link rỗng
    text = re.sub(r"\[([^\]]+)\]\(#[^)]*\)", r"\1", text)        # link neo nội trang -> giữ chữ

    # Bỏ các dòng trùng lặp (crawler nối nhiều trang con nên header/footer lặp lại)
    seen, lines = set(), []
    for line in text.splitlines():
        key = line.strip()
        if key and len(key) > 30 and key in seen:
            continue
        seen.add(key)
        lines.append(line)
    text = "\n".join(lines)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def load_competition_documents(target_date: str | None = None) -> tuple[str, list[Document]]:
    """Mỗi domain (mỗi cuộc thi) -> 1 Document chứa nội dung Markdown đã làm sạch."""
    chosen_date, snapshots = list_latest_bronze_snapshots(target_date)
    docs = []
    for snap in snapshots:
        body = s3_client.get_object(Bucket=BUCKET_NAME, Key=snap["key"])["Body"]
        content = clean_markdown(body.read().decode("utf-8", errors="replace"))
        if not content:
            continue
        docs.append(Document(
            page_content=content,
            metadata={
                "domain": snap["domain"],
                "source_url": f"https://{snap['domain']}",
                "source_key": snap["key"],
                "crawl_date": snap["date"],
                "crawl_timestamp": snap["timestamp"],
            },
        ))
    return chosen_date, docs


# ==============================================================================
# BƯỚC 2: SEMANTIC CHUNKING
# ==============================================================================
def build_chunker() -> SemanticChunker:
    # Tách câu theo dấu câu HOẶC xuống dòng: Markdown cào về nhiều dòng không có dấu chấm
    # (menu, bullet, tiêu đề); nếu chỉ tách theo [.?!] sẽ tạo "câu" rất dài.
    return SemanticChunker(
        embeddings=embeddings,
        breakpoint_threshold_type="percentile",
        breakpoint_threshold_amount=90,
        sentence_split_regex=r"(?<=[.?!])\s+|\n+",
        min_chunk_size=200,
    )


def chunk_documents(docs: list[Document]) -> list[Document]:
    chunker = build_chunker()
    chunks = []
    for doc in docs:
        parts = chunker.split_documents([doc])
        for idx, part in enumerate(parts):
            # Gắn nguồn vào đầu chunk để embedding mang ngữ cảnh "cuộc thi nào"
            part.page_content = f"[Nguồn: {doc.metadata['domain']}]\n{part.page_content}"
            part.metadata["chunk_index"] = idx
        print(f"  - {doc.metadata['domain']}: {len(doc.page_content):,} ký tự -> {len(parts)} chunk")
        chunks.extend(parts)
    return chunks


# ==============================================================================
# BƯỚC 3: EMBEDDING + QDRANT
# ==============================================================================
def ensure_collection() -> None:
    if qdrant_client.collection_exists(QDRANT_COLLECTION):
        return
    dim = len(embeddings.embed_query("dimension probe"))
    qdrant_client.create_collection(
        collection_name=QDRANT_COLLECTION,
        vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
    )
    # Index để lọc / xóa theo domain (Qdrant Cloud yêu cầu index khi filter)
    qdrant_client.create_payload_index(
        collection_name=QDRANT_COLLECTION,
        field_name="metadata.domain",
        field_schema=PayloadSchemaType.KEYWORD,
    )
    print(f">> Đã tạo collection '{QDRANT_COLLECTION}' (dim={dim}).")


def get_vector_store() -> QdrantVectorStore:
    ensure_collection()
    return QdrantVectorStore(
        client=qdrant_client,
        collection_name=QDRANT_COLLECTION,
        embedding=embeddings,
    )


def ingest(target_date: str | None = None) -> None:
    """Nạp snapshot mới nhất của ngày mục tiêu vào Qdrant.

    Với mỗi domain: xóa các vector cũ của domain đó rồi upsert chunk mới, để Qdrant chỉ
    phục vụ dữ liệu mới nhất. Lịch sử đầy đủ vẫn được giữ nguyên trên R2.
    """
    chosen_date, docs = load_competition_documents(target_date)
    print(f">> Ngày cào: {chosen_date} | Số cuộc thi (domain): {len(docs)}")
    if not docs:
        return

    print(">> Semantic chunking ...")
    chunks = chunk_documents(docs)

    store = get_vector_store()
    for domain in {d.metadata["domain"] for d in docs}:
        qdrant_client.delete(
            collection_name=QDRANT_COLLECTION,
            points_selector=Filter(must=[
                FieldCondition(key="metadata.domain", match=MatchValue(value=domain))
            ]),
        )

    # ID xác định (uuid5) -> chạy lại cùng snapshot sẽ ghi đè thay vì nhân bản
    ids = [
        str(uuid.uuid5(uuid.NAMESPACE_URL,
                       f"{c.metadata['source_key']}#{c.metadata['chunk_index']}"))
        for c in chunks
    ]
    print(f">> Embedding & upsert {len(chunks)} chunk vào Qdrant ...")
    store.add_documents(chunks, ids=ids, batch_size=32)
    print(">> Hoàn tất ingest.")


# ==============================================================================
# BƯỚC 4: RETRIEVER + PROMPT
# ==============================================================================
SYSTEM_PROMPT = """Bạn là trợ lý tư vấn cuộc thi học thuật/công nghệ cho sinh viên của nền tảng ACDP.

Quy tắc bắt buộc:
1. Chỉ trả lời dựa trên phần NGỮ CẢNH được cung cấp. Không dùng kiến thức bên ngoài để bịa thông tin về cuộc thi.
2. Nếu ngữ cảnh không chứa thông tin cần thiết, nói rõ "Dữ liệu hiện có chưa có thông tin này" và gợi ý người dùng xem trang chính thức.
3. Mỗi thông tin về cuộc thi (thời hạn, giải thưởng, điều kiện, thể lệ) phải kèm nguồn dạng (Nguồn: <URL>).
4. Trả lời bằng ngôn ngữ của người dùng, ngắn gọn, ưu tiên gạch đầu dòng khi liệt kê.
5. Lưu ý ngày cào dữ liệu khi nói về trạng thái đăng ký; thông tin có thể đã thay đổi."""

_vector_store: QdrantVectorStore | None = None


def get_retriever():
    global _vector_store
    if _vector_store is None:
        _vector_store = get_vector_store()
    return _vector_store.as_retriever(
        search_type="mmr",
        search_kwargs={"k": RETRIEVER_K, "fetch_k": RETRIEVER_FETCH_K},
    )


def format_context(docs: list[Document]) -> str:
    blocks = []
    for i, d in enumerate(docs, 1):
        m = d.metadata
        blocks.append(
            f"--- Đoạn {i} | URL: {m.get('source_url')} | Ngày cào: {m.get('crawl_date')} ---\n"
            f"{d.page_content}"
        )
    return "\n\n".join(blocks)


# ==============================================================================
# BƯỚC 5: LƯU LỊCH SỬ HỘI THOẠI THEO SESSION
# ==============================================================================
# session_id -> danh sách message [{"role": "user"|"assistant", "content": str}, ...]
chat_sessions: dict[str, list[dict]] = defaultdict(list)


def build_retrieval_query(message: str, history: list[dict]) -> str:
    """Câu hỏi nối tiếp ngắn ("còn giải thưởng thì sao?") thiếu chủ thể -> ghép câu hỏi trước."""
    last_user = next((h["content"] for h in reversed(history) if h["role"] == "user"), None)
    if last_user and len(message.split()) < 8:
        return f"{last_user}\n{message}"
    return message


def generate_answer(message: str, session_id: str) -> tuple[str, list[Document]]:
    history = chat_sessions[session_id]
    docs = get_retriever().invoke(build_retrieval_query(message, history))

    contents = []
    for turn in history[-MAX_HISTORY_TURNS * 2:]:
        role = "model" if turn["role"] == "assistant" else "user"
        contents.append(genai_types.Content(role=role, parts=[genai_types.Part(text=turn["content"])]))
    contents.append(genai_types.Content(role="user", parts=[genai_types.Part(
        text=f"NGỮ CẢNH:\n{format_context(docs)}\n\nCÂU HỎI: {message}"
    )]))

    response = llm_client.models.generate_content(
        model=CHAT_MODEL,
        contents=contents,
        config=genai_types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT, temperature=0.2),
    )
    answer = (response.text or "").strip() or "Xin lỗi, tôi chưa tạo được câu trả lời."

    history.append({"role": "user", "content": message})
    history.append({"role": "assistant", "content": answer})
    return answer, docs


# ==============================================================================
# BƯỚC 6: GRADIO UI
# ==============================================================================
def chat_fn(message: str, history: list, request: gr.Request) -> str:
    session_id = request.session_hash if request else "default"
    try:
        answer, docs = generate_answer(message, session_id)
    except Exception as e:  # lỗi mạng / 503 từ API không làm sập UI
        return f"Lỗi khi xử lý: {e}"

    sources = sorted({d.metadata.get("source_url") for d in docs if d.metadata.get("source_url")})
    if sources:
        answer += "\n\n---\n**Tài liệu truy xuất:** " + ", ".join(sources)
    return answer


def launch_ui() -> None:
    demo = gr.ChatInterface(
        fn=chat_fn,
        title="ACDP – Trợ lý tra cứu cuộc thi (MVP)",
        description=f"RAG trên dữ liệu cào mới nhất | Embedding: {EMBEDDING_MODEL} | LLM: {CHAT_MODEL}",
        examples=[
            "Có những cuộc thi nào đang mở đăng ký?",
            "IT Consultant Challenge có giải thưởng gì?",
            "Cuộc thi nào dành cho sinh viên năm nhất?",
        ],
    )
    demo.launch()


if __name__ == "__main__":
    args = sys.argv[1:]
    date_arg = None
    if "--date" in args and args.index("--date") + 1 < len(args):
        date_arg = args[args.index("--date") + 1]

    if "--ingest" in args:
        ingest(date_arg)
    if "--ingest" not in args or "--chat" in args:
        launch_ui()
