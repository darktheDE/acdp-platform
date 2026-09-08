# SPEC-0001: System Foundation, Coding Standards, and Configuration

- **Status**: Approved
- **Author(s)**: Do Kien Hung, Nguyen Van Quang Duy
- **Related ADR**: [ADR-0001: Core Architecture, Medallion Lakehouse, and Hybrid RAG Stack](../adr/0001-medallion-lakehouse-and-rag-stack.md)
- **Target Phase**: Phase 1: TLCN MVP

---

## 1. Objective & Scope

This specification establishes the cross-cutting engineering conventions, strict typing practices, configuration management, and directory inception rules for the ACDP repository.

---

## 2. Configuration Management

All runtime configurations must be managed via `pydantic-settings`, reading environment variables from `.env` with fallback to `.env.example`.

```python
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class AppConfig(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")
    
    # Environment
    environment: str = Field(default="development", description="Current environment (development, staging, production)")
    
    # Databases
    postgres_user: str = Field(default="postgres")
    postgres_password: str = Field(default="postgres")
    postgres_db: str = Field(default="acdp_db")
    postgres_host: str = Field(default="localhost")
    postgres_port: int = Field(default=5432)
    duckdb_database_path: str = Field(default="./lakehouse/acdp.duckdb")
    
    # Vector Search
    qdrant_host: str = Field(default="localhost")
    qdrant_port: int = Field(default=6333)
    
    # LLM
    openai_api_key: str = Field(default="")
    gemini_api_key: str = Field(default="")
```

---

## 3. Python & Code Quality Standards

- **Language Version**: Python `3.13+`
- **Typing**: Strict type annotations are mandatory for all function signatures and public APIs.
- **Linter & Formatter**: Use `ruff` for linting and formatting (`line-length = 100`).
- **Data Models**: Use Pydantic v2 for all serialization, deserialization, and validation.
- **Logging**: Use structured logging (e.g. `loguru` or standard `logging` with JSON formatter). Never use bare `print()` statements in production code.

---

## 4. Directory Inception Rule (Just-In-Time)

To prevent clutter:
1. No folder shall be created unless an active specification requires files within it.
2. When implementing the Ingestion engine (SPEC-0002), only then will `pipelines/ingestion/` be created.
3. When implementing Lakehouse dbt models (SPEC-0003), only then will `pipelines/lakehouse/` be created.
4. When implementing FastAPI services (SPEC-0004), only then will `apps/api/` be created.
5. When implementing Next.js frontend (SPEC-0005), only then will `apps/web/` be created.

---

## 5. Verification & Acceptance Criteria

- [ ] Configuration model validates sample `.env.example` without exceptions.
- [ ] Ruff configuration checks pass with zero warnings.
- [ ] No empty mock directories committed to version control.
