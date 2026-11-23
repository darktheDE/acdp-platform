"""Verification tests for SPEC-0006 Docker infrastructure, pinning, and AppConfig."""

from pathlib import Path

import yaml

from acdp.config import AppConfig

ROOT = Path(__file__).resolve().parents[1]


def _parse_mem_mb(limit: str) -> int:
    text = limit.strip().upper()
    if text.endswith("G"):
        return int(float(text[:-1]) * 1024)
    if text.endswith("M"):
        return int(float(text[:-1]))
    raise ValueError(f"Unsupported memory unit: {limit}")


def test_docker_compose_version_pinning_and_profiles() -> None:
    """Ensure zero :latest tags, proper Compose profiles, and <= 2.0 GB core RAM cap."""
    compose = yaml.safe_load((ROOT / "docker-compose.yml").read_text(encoding="utf-8"))
    services = compose["services"]

    expected_services = {"postgres", "qdrant", "api", "web", "metabase", "prefect-server"}
    assert expected_services.issubset(services.keys())

    core_mem_mb = 0
    for name, svc in services.items():
        image = svc.get("image")
        if image:
            assert not image.endswith(":latest"), f"Service '{name}' must not use :latest tag"
        profiles = svc.get("profiles", [])
        assert len(profiles) >= 1, f"Service '{name}' must define a Compose profile"
        if "core" in profiles:
            mem_limit = svc["deploy"]["resources"]["limits"]["memory"]
            core_mem_mb += _parse_mem_mb(mem_limit)

    assert core_mem_mb == 1408, f"Expected core profile memory budget 1408 MB (Cloud-First Qdrant), got {core_mem_mb} MB"
    assert core_mem_mb <= 2048, f"Core profile memory budget exceeded: {core_mem_mb} MB > 2048 MB"
    assert services["postgres"]["image"] == "postgres:18.7-alpine3.23"
    assert "postgres_data:/var/lib/postgresql" in services["postgres"]["volumes"]
    assert services["qdrant"]["image"] == "qdrant/qdrant:v1.13.4"
    assert services["qdrant"]["profiles"] == ["local-backup"]
    assert "qdrant" not in services["api"].get("depends_on", {})
    assert "3001:3000" in services["metabase"]["ports"]
    # DIR-021: API & Metabase query Gold Parquet directly from Cloudflare R2 via DuckDB httpfs (no local lakehouse mount)
    assert "volumes" not in services["api"]
    assert "metabase_data:/metabase-data" in services["metabase"]["volumes"]
    assert "./data/lakehouse:/data/lakehouse:ro" not in services["metabase"]["volumes"]
    for svc_name in ("api", "metabase"):
        env = services[svc_name]["environment"]
        for key in ("BUCKET_NAME", "AWS_ENDPOINT_URL", "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"):
            assert key in env, f"Missing R2 env var '{key}' in service '{svc_name}'"


def test_dockerignore_and_dockerfile_api_hardening() -> None:
    """Verify .dockerignore excludes runtime lakehouse/secrets and Dockerfile.api runs non-root with httpfs."""
    dockerignore = (ROOT / ".dockerignore").read_text(encoding="utf-8").splitlines()
    for required in (".git", ".venv", "data/lakehouse", "node_modules", ".env", "*.duckdb", "*.parquet"):
        assert required in dockerignore, f"Missing '{required}' in .dockerignore"

    dockerfile_api = (ROOT / "Dockerfile.api").read_text(encoding="utf-8")
    assert "FROM python:3.13-slim-bookworm" in dockerfile_api
    assert "USER appuser" in dockerfile_api
    assert "acdp.api.main:app" in dockerfile_api
    assert "DUCKDB_EXTENSION_DIRECTORY" in dockerfile_api
    assert "INSTALL httpfs" in dockerfile_api


def test_app_config_qdrant_resolution_and_env_example(monkeypatch) -> None:
    """Verify AppConfig Qdrant/R2 resolution and .env.example compatibility."""
    monkeypatch.delenv("POSTGRES_DB", raising=False)
    monkeypatch.delenv("DUCKDB_MEMORY_LIMIT", raising=False)
    monkeypatch.delenv("BRONZE_STORAGE_BACKEND", raising=False)

    cloud_cfg = AppConfig(
        _env_file=None,
        qdrant_mode="auto",
        qdrant_cluster_endpoint="https://cloud.qdrant.example:6333",
        qdrant_url="http://qdrant:6333",
        qdrant_api_key="secret-cloud-key",
    )
    assert cloud_cfg.get_qdrant_url() == "https://cloud.qdrant.example:6333"
    assert cloud_cfg.get_qdrant_api_key() == "secret-cloud-key"
    assert cloud_cfg.is_qdrant_cloud_active() is True

    local_backup_cfg = AppConfig(
        _env_file=None,
        qdrant_mode="local",
        qdrant_cluster_endpoint="https://cloud.qdrant.example:6333",
        qdrant_url="http://qdrant:6333",
        qdrant_api_key="secret-cloud-key",
    )
    assert local_backup_cfg.get_qdrant_url() == "http://qdrant:6333"
    assert local_backup_cfg.get_qdrant_api_key() is None
    assert local_backup_cfg.is_qdrant_cloud_active() is False

    docker_cfg = AppConfig(
        _env_file=None,
        qdrant_cluster_endpoint="",
        qdrant_url="http://qdrant:6333",
        qdrant_api_key="secret-cloud-key",
    )
    assert docker_cfg.get_qdrant_url() == "http://qdrant:6333"
    assert docker_cfg.get_qdrant_api_key() is None

    local_cfg = AppConfig(_env_file=None, qdrant_cluster_endpoint="", qdrant_url="")
    assert local_cfg.get_qdrant_url() == "http://localhost:6333"
    assert local_cfg.get_qdrant_api_key() is None

    example_cfg = AppConfig(_env_file=str(ROOT / ".env.example"))
    assert example_cfg.qdrant_mode == "auto"
    assert example_cfg.bronze_storage_backend == "cloudflare_r2"
    assert example_cfg.postgres_db == "acdp_app"
    assert example_cfg.duckdb_memory_limit == "256MB"
    assert example_cfg.get_qdrant_collection() == "acdp_competitions_bge_m3"
    assert example_cfg.get_embedding_model() == "@cf/baai/bge-m3"
    assert example_cfg.get_chat_model() == "gemini-3.5-flash-lite"


def test_supabase_oltp_pooler_and_duckdb_r2_config(monkeypatch) -> None:
    """Verify Supabase Transaction/Session Pooler resolution, NullPool selection, and local fallback (TASK-CLD-04)."""
    from sqlalchemy.pool import AsyncAdaptedQueuePool, NullPool

    from acdp.api.db.postgres import build_async_engine

    for key in (
        "POSTGRES_MODE",
        "SUPABASE_DATABASE_URL",
        "DATABASE_URL",
        "POSTGRES_POOL_MODE",
        "POSTGRES_SSL_MODE",
    ):
        monkeypatch.delenv(key, raising=False)

    # 1. Supabase Supavisor Transaction Pooler (:6543) with postgres:// scheme & pgbouncer=true
    tx_cfg = AppConfig(
        _env_file=None,
        postgres_mode="auto",
        supabase_database_url="postgres://postgres.projref:secret@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres?pgbouncer=true",
    )
    assert tx_cfg.is_postgres_cloud_active() is True
    assert tx_cfg.is_transaction_pooler_active() is True
    tx_url = tx_cfg.get_database_url()
    assert tx_url.startswith("postgresql+asyncpg://")
    assert "prepared_statement_cache_size=0" in tx_url
    assert "pgbouncer=" not in tx_url
    assert tx_cfg.get_asyncpg_connect_args() == {"statement_cache_size": 0, "ssl": "require"}
    tx_engine = build_async_engine(tx_cfg)
    assert isinstance(tx_engine.pool, NullPool)

    # 2. Supabase Session Pooler (:5432) -> keeps QueuePool with Cloud TLS
    sess_cfg = AppConfig(
        _env_file=None,
        postgres_mode="auto",
        supabase_database_url="postgresql://postgres.projref:secret@aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres?sslmode=require",
    )
    assert sess_cfg.is_postgres_cloud_active() is True
    assert sess_cfg.is_transaction_pooler_active() is False
    sess_url = sess_cfg.get_database_url()
    assert "sslmode=" not in sess_url
    assert sess_cfg.get_asyncpg_connect_args() == {"ssl": "require"}
    sess_engine = build_async_engine(sess_cfg)
    assert isinstance(sess_engine.pool, AsyncAdaptedQueuePool)

    # 3. Local backup mode overrides Supabase URL and disables Cloud TLS
    local_cfg = AppConfig(
        _env_file=None,
        postgres_mode="local",
        supabase_database_url="postgres://postgres.projref:secret@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres",
    )
    assert local_cfg.is_postgres_cloud_active() is False
    assert local_cfg.is_transaction_pooler_active() is False
    assert local_cfg.get_database_url() == "postgresql+asyncpg://acdp:acdp_local_dev_only@localhost:5432/acdp_app"
    assert local_cfg.get_asyncpg_connect_args() == {}
    local_engine = build_async_engine(local_cfg)
    assert isinstance(local_engine.pool, AsyncAdaptedQueuePool)
