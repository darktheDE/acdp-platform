"""Configuration management module for ACDP Platform.

Conforms to SPEC-0001 (Pydantic v2 Settings) and supports Dual-Storage backends:
Local POSIX and Cloudflare R2 (Cloud S3).
"""

from typing import Literal
from urllib.parse import urlparse

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppConfig(BaseSettings):
    """Global application configuration loaded from environment and .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Environment
    environment: str = Field(
        default="development",
        description="Runtime environment (development, staging, production)",
    )

    # Relational Database (PostgreSQL 18 OLTP - SPEC-0004 & SPEC-0006)
    postgres_user: str = Field(default="acdp")
    postgres_password: str = Field(default="acdp_local_dev_only")
    postgres_db: str = Field(default="acdp_app")
    postgres_host: str = Field(default="localhost")
    postgres_port: int = Field(default=5432)

    # Lakehouse DuckDB Analytics Engine
    duckdb_database_path: str = Field(
        default="./data/lakehouse/acdp.duckdb",
        description="Path to local DuckDB lakehouse database file",
    )
    duckdb_memory_limit: str = Field(
        default="256MB",
        description="Per-connection DuckDB memory cap for read-only API queries",
    )
    duckdb_threads: int = Field(
        default=2,
        description="Per-connection DuckDB thread cap for read-only API queries",
    )
    usd_to_vnd_rate: int = Field(
        default=25400,
        description="Reference USD to VND exchange rate for Gold prize normalization",
    )

    # Lakehouse Storage Configuration (Cloudflare R2 Exclusive - DIR-021)
    bronze_storage_backend: Literal["cloudflare_r2"] = Field(
        default="cloudflare_r2",
        description="Storage backend locked exclusively to Cloudflare R2 ('cloudflare_r2')",
    )
    bronze_storage_uri: str = Field(
        default="s3://acdp-lakehouse/bronze",
        description="Bronze storage directory path or s3:// URI",
    )
    silver_storage_uri: str = Field(
        default="s3://acdp-lakehouse/silver",
        description="Silver layer Parquet storage directory path or s3:// URI",
    )
    gold_storage_uri: str = Field(
        default="s3://acdp-lakehouse/gold",
        description="Gold layer storage directory path or s3:// URI",
    )
    bucket_name: str = Field(
        default="acdp-lakehouse",
        description="S3/R2 Bucket name for lakehouse storage layers",
    )

    # S3 Object Storage Credentials (for Cloudflare R2 / S3)
    aws_endpoint_url: str = Field(
        default="",
        description="Custom endpoint URL for S3 API (e.g. https://<account_id>.r2.cloudflarestorage.com)",
    )
    aws_access_key_id: str = Field(
        default="",
        description="Access key ID for S3 object storage",
    )
    aws_secret_access_key: str = Field(
        default="",
        description="Secret access key for S3 object storage",
    )
    aws_region: str = Field(
        default="auto",
        description="AWS/S3 region (use 'auto' for Cloudflare R2)",
    )
    aws_allow_http: bool = Field(
        default=False,
        description="Allow unencrypted HTTP communication if using a custom S3 endpoint",
    )
    aws_s3_allow_unsafe_rename: bool = Field(
        default=True,
        description="Enable unsafe rename flag for non-AWS S3 providers",
    )

    # Vector Search (Qdrant)
    qdrant_host: str = Field(default="localhost")
    qdrant_port: int = Field(default=6333)
    qdrant_url: str = Field(default="")
    qdrant_cluster_endpoint: str = Field(default="")
    qdrant_api_key: str = Field(default="")
    qdrant_collection: str = Field(default="acdp_competitions_bge_m3")
    qdrant_bge_collection: str = Field(default="")

    # LLM & Embedding Providers (Cloudflare Workers AI + Google AI Studio)
    cloudflare_api_token: str = Field(default="")
    cloudflare_account_id: str = Field(default="")
    cloudflare_embedding_model: str = Field(default="")
    ollama_base_url: str = Field(default="http://localhost:11434")
    embedding_model: str = Field(default="@cf/baai/bge-m3")
    chat_model: str = Field(default="gemini-3.5-flash-lite")
    llm_provider: str = Field(default="")
    openai_api_key: str = Field(default="")
    gemini_api_key: str = Field(default="")
    google_api_key: str = Field(default="")

    # Serving API & Auth (SPEC-0004)
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=8000)
    jwt_secret_key: str = Field(default="acdp-local-dev-secret-change-in-prod-32bytes")
    jwt_algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=15)
    refresh_token_expire_days: int = Field(default=7)
    cors_origins: str = Field(default="http://localhost:3000")
    internal_api_url: str = Field(default="http://localhost:8000")

    def get_qdrant_url(self) -> str:
        """Resolve Qdrant endpoint: Cloud endpoint first, then explicit URL, then host:port."""
        if self.qdrant_cluster_endpoint:
            return self.qdrant_cluster_endpoint
        if self.qdrant_url:
            return self.qdrant_url
        return f"http://{self.qdrant_host}:{self.qdrant_port}"

    def get_qdrant_collection(self) -> str:
        """Resolve target Qdrant collection, redirecting legacy collections to BGE-M3."""
        target = (self.qdrant_bge_collection or self.qdrant_collection or "acdp_competitions_bge_m3").strip()
        if target in {"acdp_competitions", "acdp_competitions_gemini"}:
            return "acdp_competitions_bge_m3"
        return target

    def get_cloudflare_account_id(self) -> str:
        """Return Cloudflare Account ID directly or parse it from R2 AWS_ENDPOINT_URL."""
        if self.cloudflare_account_id.strip():
            return self.cloudflare_account_id.strip()
        if self.aws_endpoint_url.strip():
            host = urlparse(self.aws_endpoint_url.strip()).netloc
            if host:
                return host.split(".", 1)[0]
        return ""

    def get_embedding_model(self) -> str:
        """Return active embedding model, redirecting deprecated Ollama/Gemini IDs to @cf/baai/bge-m3."""
        raw = (self.cloudflare_embedding_model or self.embedding_model or "@cf/baai/bge-m3").strip()
        if any(legacy in raw.lower() for legacy in ("qwen", "ollama", "gemini")):
            return "@cf/baai/bge-m3"
        return raw

    def get_chat_model(self) -> str:
        """Resolve active Gemini chat model for RAG generation, guarding against incompatible defaults."""
        raw = self.chat_model.strip() or "gemini-3.5-flash-lite"
        if self.llm_provider.strip():
            candidate = self.llm_provider.strip().split("/", 1)[-1]
            if "ollama" not in self.llm_provider.lower() and "gemma" not in candidate.lower():
                raw = candidate
        if any(legacy in raw.lower() for legacy in ("gemma", "ollama", "gemini-1.5", "gemini-2.5")):
            return "gemini-3.5-flash-lite"
        return raw

    def get_database_url(self) -> str:
        """Build asyncpg SQLAlchemy connection URI for PostgreSQL 18 OLTP."""
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    def create_r2_client(self):
        """Create a configured boto3 S3/R2 client from unified settings."""
        import boto3

        return boto3.client(
            service_name="s3",
            endpoint_url=self.aws_endpoint_url or None,
            aws_access_key_id=self.aws_access_key_id or None,
            aws_secret_access_key=self.aws_secret_access_key or None,
            region_name=self.aws_region or "auto",
        )

    def get_r2_endpoint_host(self) -> str:
        """Return Cloudflare R2 endpoint host without scheme (e.g. <account_id>.r2.cloudflarestorage.com)."""
        raw = self.aws_endpoint_url.strip()
        if not raw:
            return ""
        parsed = urlparse(raw)
        return (parsed.netloc or raw.split("://")[-1]).rstrip("/")

    def configure_duckdb_r2(self, con) -> None:
        """Configure DuckDB httpfs extension and S3 secret for direct Cloudflare R2 Parquet I/O."""
        import os

        ext_dir = os.getenv("DUCKDB_EXTENSION_DIRECTORY", "").strip()
        if ext_dir:
            escaped_dir = ext_dir.replace("'", "''")
            con.execute(f"SET extension_directory='{escaped_dir}'")

        try:
            con.execute("LOAD httpfs")
        except Exception:
            con.execute("INSTALL httpfs")
            con.execute("LOAD httpfs")

        endpoint_host = self.get_r2_endpoint_host()
        if not endpoint_host or not self.aws_access_key_id or not self.aws_secret_access_key:
            raise RuntimeError(
                "Cloudflare R2 credentials (AWS_ENDPOINT_URL, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY) "
                "are required for DuckDB httpfs queries."
            )

        key_id = self.aws_access_key_id.replace("'", "''")
        secret = self.aws_secret_access_key.replace("'", "''")
        endpoint = endpoint_host.replace("'", "''")
        region = (self.aws_region or "auto").replace("'", "''")
        use_ssl = "false" if self.aws_allow_http else "true"

        con.execute(
            f"""
            CREATE OR REPLACE SECRET r2_secret (
                TYPE s3,
                PROVIDER config,
                KEY_ID '{key_id}',
                SECRET '{secret}',
                ENDPOINT '{endpoint}',
                REGION '{region}',
                URL_STYLE 'path',
                USE_SSL {use_ssl}
            )
            """
        )

    def get_storage_options(self) -> dict[str, str]:
        """Generate S3/R2 storage options dictionary for PyArrow and boto3."""
        options: dict[str, str] = {
            "AWS_S3_ALLOW_UNSAFE_RENAME": "true" if self.aws_s3_allow_unsafe_rename else "false",
        }

        if self.aws_endpoint_url:
            options["AWS_ENDPOINT_URL"] = self.aws_endpoint_url
        if self.aws_access_key_id:
            options["AWS_ACCESS_KEY_ID"] = self.aws_access_key_id
        if self.aws_secret_access_key:
            options["AWS_SECRET_ACCESS_KEY"] = self.aws_secret_access_key
        if self.aws_region:
            options["AWS_REGION"] = self.aws_region
        if self.aws_allow_http:
            options["AWS_ALLOW_HTTP"] = "true"

        return options


# Singleton configuration instance
settings = AppConfig()
