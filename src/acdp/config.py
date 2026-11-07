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

    # Relational Database (PostgreSQL)
    postgres_user: str = Field(default="postgres")
    postgres_password: str = Field(default="postgres")
    postgres_db: str = Field(default="acdp_db")
    postgres_host: str = Field(default="localhost")
    postgres_port: int = Field(default=5432)

    # Lakehouse DuckDB Analytics Engine
    duckdb_database_path: str = Field(
        default="./data/lakehouse/acdp.duckdb",
        description="Path to local DuckDB lakehouse database file",
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

    def get_storage_options(self) -> dict[str, str]:
        """Generate storage options dictionary for deltalake and pyarrow."""
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
