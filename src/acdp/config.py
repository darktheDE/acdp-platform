"""Configuration management module for ACDP Platform.

Conforms to SPEC-0001 (Pydantic v2 Settings) and supports Dual-Storage backends:
Local POSIX and Cloudflare R2 (Cloud S3).
"""

from typing import Any, Literal
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_DEV_JWT_SECRET = "acdp-local-dev-secret-change-in-prod-32bytes"


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

    # Relational Database (PostgreSQL 18 / Supabase OLTP - SPEC-0004, SPEC-0006, ADR-0002)
    postgres_mode: Literal["auto", "cloud", "local"] = Field(
        default="auto",
        description="PostgreSQL routing mode: 'auto'/'cloud' prioritizes SUPABASE_DATABASE_URL/DATABASE_URL; 'local' forces local Docker Postgres backup",
    )
    database_url: str = Field(
        default="",
        description="Optional full PostgreSQL/Supabase connection URI override",
    )
    supabase_database_url: str = Field(
        default="",
        description="Supabase Supavisor connection pooler URI (:6543 transaction or :5432 session)",
    )
    supabase_direct_url: str = Field(
        default="",
        description="Optional Supabase direct/session connection URI (:5432) for migrations and pg_dump",
    )
    postgres_pool_mode: Literal["auto", "transaction", "session"] = Field(
        default="auto",
        description="Connection pool mode: 'auto' detects port 6543 or pgbouncer=true as transaction mode",
    )
    postgres_ssl_mode: Literal["auto", "require", "disable"] = Field(
        default="auto",
        description="SSL mode for asyncpg connections ('auto' enables TLS for cloud hosts)",
    )
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
    duckdb_r2_table_cache: bool = Field(
        default=True,
        description="Materialize R2 Gold Parquets into DuckDB :memory: tables on init to avoid per-query HTTP round-trips",
    )
    gold_mart_cache_enabled: bool = Field(
        default=True,
        description="Enable in-memory TTL cache for the 6 Gold mart_* tables (TASK-CLD-05)",
    )
    gold_mart_cache_ttl_seconds: int = Field(
        default=600,
        ge=0,
        le=3600,
        description="TTL in seconds for Gold mart_* cache (300-900s recommended, default 600s = 10 min)",
    )
    gold_mart_cache_max_entries: int = Field(
        default=256,
        ge=16,
        le=4096,
        description="Maximum cached query keys retained in GoldMartsTTLCache",
    )
    usd_to_vnd_rate: int = Field(
        default=25400,
        description="Reference USD to VND exchange rate for Gold prize normalization",
    )
    motherduck_token: str = Field(
        default="",
        description="Optional MotherDuck Lite service token for Cloud BI SQL Workbench",
    )
    motherduck_database: str = Field(
        default="acdp_gold",
        description="Target MotherDuck database name for Gold Star Schema views",
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

    # Vector Search (Qdrant: Cloud-first default with local Docker backup mode - TASK-CLD-01)
    qdrant_mode: Literal["auto", "cloud", "local"] = Field(
        default="auto",
        description="Qdrant routing mode: 'auto'/'cloud' prioritizes Qdrant Cloud; 'local' forces local Docker Qdrant backup",
    )
    qdrant_host: str = Field(default="localhost")
    qdrant_port: int = Field(default=6333)
    qdrant_url: str = Field(default="")
    qdrant_cluster_endpoint: str = Field(default="")
    qdrant_api_key: str = Field(default="")
    qdrant_collection: str = Field(default="acdp_competitions_bge_m3")
    qdrant_bge_collection: str = Field(default="")

    # LLM & Embedding Providers (Cloudflare Workers AI + Google AI Studio + Fallback Chain)
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
    groq_api_key: str = Field(
        default="",
        description="Groq Cloud API key for Tier-2 LLM fallback (TASK-CLD-06)",
    )
    groq_chat_model: str = Field(
        default="qwen/qwen3.8-27b",
        description="Groq LPU fallback model ID",
    )
    openrouter_api_key: str = Field(
        default="",
        description="OpenRouter API key for Tier-3 :free LLM fallback (TASK-CLD-06)",
    )
    openrouter_chat_model: str = Field(
        default="google/gemma-4-31b-it:free",
        description="OpenRouter :free fallback model ID",
    )
    llm_fallback_enabled: bool = Field(
        default=True,
        description="Enable multi-provider LLM fallback chain (Gemini -> Groq -> OpenRouter :free)",
    )
    use_litellm_router: bool = Field(
        default=False,
        description="Use litellm.completion with fallbacks=[] when litellm is installed; otherwise use built-in httpx OpenAI-compatible fallback client",
    )
    rag_cache_enabled: bool = Field(
        default=True,
        description="Enable in-memory TTL cache for repeated grounded RAG queries (TASK-CLD-06)",
    )
    rag_cache_ttl_seconds: int = Field(
        default=300,
        ge=0,
        le=3600,
        description="TTL in seconds for RAG response cache (default 300s = 5 min)",
    )
    rag_cache_max_entries: int = Field(
        default=128,
        ge=16,
        le=2048,
        description="Maximum cached RAG query entries",
    )
    oltp_backup_r2_prefix: str = Field(
        default="backups/oltp",
        description="Private prefix on Cloudflare R2 bucket for weekly pg_dump backups",
    )
    oltp_backup_retention_days: int = Field(
        default=30,
        ge=1,
        le=365,
        description="Retention days for OLTP pg_dump backups on R2",
    )

    # Discovery 3-Tier Search APIs (TASK-ING-03 - Free Tier)
    tavily_api_key: str = Field(default="")
    exa_api_key: str = Field(default="")
    serper_api_key: str = Field(default="")
    discovery_max_queries_per_run: int = Field(default=12)

    # Serving API & Auth (SPEC-0004, TASK-SEC-01)
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=8000)
    jwt_secret_key: str = Field(default=DEFAULT_DEV_JWT_SECRET)
    jwt_algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=15)
    refresh_token_expire_days: int = Field(default=7)
    cors_origins: str = Field(default="http://localhost:3000")
    cors_origin_regex: str = Field(
        default=r"^https://.*\.vercel\.app$",
        description="Regex matching allowed Vercel Hobby preview/production origins",
    )
    internal_api_url: str = Field(default="http://localhost:8000")
    admin_emails: str = Field(
        default="",
        description="Comma-separated emails automatically granted admin role (TASK-SEC-02)",
    )

    # OWASP & LLM10:2025 Security Hardening (TASK-SEC-01)
    rag_max_output_tokens: int = Field(
        default=600,
        ge=64,
        le=2048,
        description="Hard ceiling on LLM output tokens to mitigate OWASP LLM10:2025 Unbounded Consumption",
    )
    rate_limit_enabled: bool = Field(
        default=True,
        description="Enable Multi-Tier Sliding-Window Rate Limiting (AI / Auth / Public)",
    )
    rate_limit_ai_per_minute: int = Field(default=5, ge=1)
    rate_limit_ai_per_day: int = Field(default=30, ge=1)
    rate_limit_ai_global_rpm: int = Field(default=10, ge=1)
    rate_limit_auth_per_minute: int = Field(default=10, ge=1)
    rate_limit_public_per_minute: int = Field(default=60, ge=1)

    @property
    def is_production(self) -> bool:
        """Return True when running in production environment."""
        return (self.environment or "").strip().lower() == "production"

    def get_admin_emails(self) -> set[str]:
        """Return normalized set of administrator emails configured via ADMIN_EMAILS."""
        return {
            e.strip().lower()
            for e in (self.admin_emails or "").split(",")
            if e.strip()
        }

    def validate_production_security(self) -> None:
        """Fail-fast check (OWASP A04:2025 / Gate G2): reject weak or default JWT_SECRET_KEY in production."""
        if not self.is_production:
            return
        secret = (self.jwt_secret_key or "").strip()
        insecure_defaults = {
            DEFAULT_DEV_JWT_SECRET,
            "changeme",
            "secret",
            "your-secret-key",
        }
        if (
            len(secret) < 32
            or secret in insecure_defaults
            or "local-dev-secret" in secret
            or "change-in-prod" in secret
        ):
            raise RuntimeError(
                "SECURITY FAIL-FAST (OWASP A04:2025 / Gate G2): ENVIRONMENT=production requires "
                "a strong custom JWT_SECRET_KEY with at least 32 characters."
            )

    def get_qdrant_url(self) -> str:
        """Resolve Qdrant endpoint: Cloud endpoint first in 'auto'/'cloud' mode, or local URL in 'local' backup mode."""
        mode = (self.qdrant_mode or "auto").strip().lower()
        if mode == "local":
            if self.qdrant_url.strip():
                return self.qdrant_url.strip()
            return f"http://{self.qdrant_host}:{self.qdrant_port}"
        if self.qdrant_cluster_endpoint.strip():
            return self.qdrant_cluster_endpoint.strip()
        if self.qdrant_url.strip():
            return self.qdrant_url.strip()
        return f"http://{self.qdrant_host}:{self.qdrant_port}"

    def get_qdrant_api_key(self) -> str | None:
        """Return Qdrant API key for HTTPS/Cloud endpoints; omit on local HTTP backup to avoid insecure key warnings."""
        mode = (self.qdrant_mode or "auto").strip().lower()
        if mode == "local":
            return None
        target_url = self.get_qdrant_url()
        if target_url.startswith("http://"):
            return None
        return self.qdrant_api_key.strip() or None

    def is_qdrant_cloud_active(self) -> bool:
        """Return True when resolved Qdrant endpoint targets an external HTTPS Qdrant Cloud cluster."""
        return self.get_qdrant_url().startswith("https://")

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

    def get_llm_fallback_chain(self) -> list[dict[str, str]]:
        """Return ordered multi-provider LLM fallback chain (Gemini -> Groq -> OpenRouter :free)."""
        gemini_model = self.get_chat_model()
        gemini_key = (self.gemini_api_key or self.google_api_key).strip()
        chain: list[dict[str, str]] = [
            {
                "provider": "gemini",
                "model": gemini_model,
                "litellm_model": f"gemini/{gemini_model}",
                "api_key": gemini_key,
            }
        ]
        if not self.llm_fallback_enabled:
            return chain

        if self.groq_api_key.strip():
            groq_model = self.groq_chat_model.strip() or "qwen/qwen3.8-27b"
            if groq_model == "llama-3.3-70b-versatile":
                groq_model = "qwen/qwen3.8-27b"
            chain.append(
                {
                    "provider": "groq",
                    "model": groq_model,
                    "litellm_model": f"groq/{groq_model}",
                    "api_key": self.groq_api_key.strip(),
                    "base_url": "https://api.groq.com/openai/v1/chat/completions",
                }
            )

        if self.openrouter_api_key.strip():
            or_model = self.openrouter_chat_model.strip() or "google/gemma-4-31b-it:free"
            if or_model == "meta-llama/llama-3.3-70b-instruct:free":
                or_model = "google/gemma-4-31b-it:free"
            chain.append(
                {
                    "provider": "openrouter",
                    "model": or_model,
                    "litellm_model": f"openrouter/{or_model}",
                    "api_key": self.openrouter_api_key.strip(),
                    "base_url": "https://openrouter.ai/api/v1/chat/completions",
                }
            )
        return chain

    def get_pg_dump_database_url(self) -> str:
        """Resolve a standard postgresql:// URI safe for pg_dump over IPv4 Session Pooler (:5432)."""
        mode = (self.postgres_mode or "auto").strip().lower()
        if mode == "local":
            raw_url = (
                f"postgresql://{self.postgres_user}:{self.postgres_password}"
                f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
            )
        elif self.supabase_direct_url.strip():
            raw_url = self.supabase_direct_url.strip()
        else:
            raw_url = self._resolve_raw_postgres_url()

        if raw_url.startswith("postgresql+asyncpg://"):
            raw_url = "postgresql://" + raw_url[len("postgresql+asyncpg://") :]
        elif raw_url.startswith("postgres://"):
            raw_url = "postgresql://" + raw_url[len("postgres://") :]

        parsed = urlparse(raw_url)
        host = (parsed.hostname or "").strip().lower()
        netloc = parsed.netloc
        # Supabase Transaction Pooler (:6543) breaks pg_dump session locks; rewrite to Session Pooler (:5432)
        if host.endswith(".pooler.supabase.com") and parsed.port == 6543:
            userinfo = ""
            if parsed.username:
                userinfo = parsed.username
                if parsed.password is not None:
                    userinfo = f"{userinfo}:{parsed.password}"
                userinfo = f"{userinfo}@"
            netloc = f"{userinfo}{parsed.hostname}:5432"

        filtered_params = [
            (k, v)
            for k, v in parse_qsl(parsed.query, keep_blank_values=True)
            if k.lower() not in {"pgbouncer", "prepared_statement_cache_size", "statement_cache_size"}
        ]
        is_cloud_host = host not in {"", "localhost", "127.0.0.1", "postgres", "::1"}
        ssl_mode = (self.postgres_ssl_mode or "auto").strip().lower()
        has_sslmode = any(k.lower() == "sslmode" for k, _ in filtered_params)
        if not has_sslmode and (ssl_mode == "require" or (ssl_mode == "auto" and is_cloud_host)):
            filtered_params.append(("sslmode", "require"))

        rebuilt_query = urlencode(filtered_params)
        return urlunparse(parsed._replace(netloc=netloc, query=rebuilt_query))

    def get_motherduck_dsn(self) -> str:
        """Return MotherDuck connection URI (`md:<db>`) with token if configured."""
        db = (self.motherduck_database or "acdp_gold").strip() or "acdp_gold"
        token = self.motherduck_token.strip()
        if token:
            return f"md:{db}?motherduck_token={token}"
        return f"md:{db}"

    def _resolve_raw_postgres_url(self) -> str:
        """Select active PostgreSQL/Supabase connection string based on postgres_mode."""
        mode = (self.postgres_mode or "auto").strip().lower()
        if mode != "local":
            if self.supabase_database_url.strip():
                return self.supabase_database_url.strip()
            if self.database_url.strip():
                return self.database_url.strip()
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @staticmethod
    def _normalize_asyncpg_scheme(raw_url: str) -> str:
        """Normalize postgres:// and postgresql:// URIs to postgresql+asyncpg://."""
        if raw_url.startswith("postgres://"):
            return "postgresql+asyncpg://" + raw_url[len("postgres://") :]
        if raw_url.startswith("postgresql://"):
            return "postgresql+asyncpg://" + raw_url[len("postgresql://") :]
        return raw_url

    def is_postgres_cloud_active(self) -> bool:
        """Return True when resolved PostgreSQL host targets an external cloud database (Supabase/Neon)."""
        parsed = urlparse(self._normalize_asyncpg_scheme(self._resolve_raw_postgres_url()))
        host = (parsed.hostname or "").strip().lower()
        return host not in {"", "localhost", "127.0.0.1", "postgres", "::1"}

    def is_transaction_pooler_active(self) -> bool:
        """Return True when targeting a Supavisor/PgBouncer transaction pooler (e.g., port 6543)."""
        pool_mode = (self.postgres_pool_mode or "auto").strip().lower()
        if pool_mode == "transaction":
            return True
        if pool_mode == "session":
            return False
        parsed = urlparse(self._normalize_asyncpg_scheme(self._resolve_raw_postgres_url()))
        if parsed.port == 6543:
            return True
        query_map = dict(parse_qsl(parsed.query, keep_blank_values=True))
        return (
            query_map.get("prepared_statement_cache_size") == "0"
            or query_map.get("pgbouncer", "").lower() == "true"
        )

    def get_database_url(self) -> str:
        """Build asyncpg SQLAlchemy connection URI for Supabase Cloud or local PostgreSQL 18 OLTP."""
        normalized = self._normalize_asyncpg_scheme(self._resolve_raw_postgres_url())
        parsed = urlparse(normalized)
        filtered_params = [
            (k, v)
            for k, v in parse_qsl(parsed.query, keep_blank_values=True)
            if k.lower() not in {"sslmode", "pgbouncer"}
        ]
        if self.is_transaction_pooler_active():
            filtered_params = [
                (k, v) for k, v in filtered_params if k != "prepared_statement_cache_size"
            ]
            filtered_params.append(("prepared_statement_cache_size", "0"))
        rebuilt_query = urlencode(filtered_params)
        return urlunparse(parsed._replace(query=rebuilt_query))

    def get_asyncpg_connect_args(self) -> dict[str, Any]:
        """Return asyncpg connect_args disabling statement caching for transaction poolers and enabling Cloud TLS."""
        connect_args: dict[str, Any] = {}
        if self.is_transaction_pooler_active():
            connect_args["statement_cache_size"] = 0

        ssl_mode = (self.postgres_ssl_mode or "auto").strip().lower()
        if ssl_mode == "require" or (ssl_mode == "auto" and self.is_postgres_cloud_active()):
            connect_args["ssl"] = "require"
        return connect_args

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
