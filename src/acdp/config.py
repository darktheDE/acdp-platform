"""Configuration management module for ACDP Platform.

Conforms to SPEC-0001 (Pydantic v2 Settings) and supports Tri-Storage backends:
Local POSIX, SeaweedFS (Local S3), and Cloudflare R2 (Cloud S3).
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

    # Lakehouse Bronze Storage Configuration
    bronze_storage_backend: Literal["local", "seaweedfs", "cloudflare_r2"] = Field(
        default="local",
        description="Storage backend: 'local' (POSIX SSD), 'seaweedfs' (Docker S3), or 'cloudflare_r2' (Cloud S3)",
    )
    bronze_storage_uri: str = Field(
        default="./data/lakehouse/bronze",
        description="Delta Lake storage directory path or s3:// URI",
    )

    # S3 Object Storage Credentials (for SeaweedFS & Cloudflare R2)
    aws_endpoint_url: str = Field(
        default="",
        description="Custom endpoint URL for S3 API (e.g. http://localhost:8333 or https://<account_id>.r2.cloudflarestorage.com)",
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
        default="us-east-1",
        description="AWS/S3 region (use 'auto' for Cloudflare R2)",
    )
    aws_allow_http: bool = Field(
        default=True,
        description="Allow unencrypted HTTP communication (required for localhost SeaweedFS)",
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
