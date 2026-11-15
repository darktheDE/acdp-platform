"""Configuration management module for ACDP Platform.

Conforms to SPEC-0001 (Pydantic v2 Settings) and supports Dual-Storage backends:
Local POSIX and Cloudflare R2 (Cloud S3).
"""

from typing import Literal

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
    usd_to_vnd_rate: int = Field(
        default=25400,
        description="Reference USD to VND exchange rate for Gold prize normalization",
    )

    # Lakehouse Storage Configuration
    bronze_storage_backend: Literal["local", "cloudflare_r2"] = Field(
        default="cloudflare_r2",
        description="Storage backend: 'local' (POSIX SSD) or 'cloudflare_r2' (Cloud S3)",
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
    qdrant_api_key: str = Field(default="")

    # LLM Providers
    openai_api_key: str = Field(default="")
    gemini_api_key: str = Field(default="")

    # Serving API & Auth (SPEC-0004)
    jwt_secret_key: str = Field(default="acdp-local-dev-secret-change-in-prod-32bytes")
    jwt_algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=15)
    refresh_token_expire_days: int = Field(default=7)
    cors_origins: str = Field(default="http://localhost:3000")
    internal_api_url: str = Field(default="http://localhost:8000")

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

    def get_storage_options(self) -> dict[str, str]:
        """Generate S3/R2 storage options dictionary for PyArrow and boto3."""
        if self.bronze_storage_backend == "local" and not self.bronze_storage_uri.startswith(("s3://", "r2://")):
            return {}

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
