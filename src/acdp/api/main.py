"""FastAPI Unified Serving Gateway entrypoint (SPEC-0004)."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from acdp.api.db.postgres import engine, init_oltp_schema
from acdp.api.middleware.security import (
    SecurityHardeningMiddleware,
    register_security_exception_handlers,
)
from acdp.api.routers import admin, analytics, auth, bookmarks, competitions, health, profile, rag
from acdp.config import settings


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Validate production security settings, initialize OLTP schema, and dispose pool on shutdown."""
    settings.validate_production_security()
    await init_oltp_schema()
    yield
    await engine.dispose()


_is_prod = settings.environment == "production"

app = FastAPI(
    title="ACDP Serving Gateway",
    description="Unified FastAPI Gateway over DuckDB Gold Star Schema, PostgreSQL 18 OLTP, and Qdrant RAG.",
    version="1.0.0",
    openapi_url=None if _is_prod else "/openapi.json",
    docs_url=None if _is_prod else "/docs",
    redoc_url=None,
    lifespan=lifespan,
)

register_security_exception_handlers(app)
app.add_middleware(SecurityHardeningMiddleware)

origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
origin_regex = settings.cors_origin_regex.strip() or None
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

API_PREFIX = "/api/v1"
app.include_router(health.router, prefix=API_PREFIX)
app.include_router(analytics.router, prefix=API_PREFIX)
app.include_router(competitions.router, prefix=API_PREFIX)
app.include_router(auth.router, prefix=API_PREFIX)
app.include_router(profile.router, prefix=API_PREFIX)
app.include_router(bookmarks.router, prefix=API_PREFIX)
app.include_router(rag.router, prefix=API_PREFIX)
app.include_router(admin.router, prefix=API_PREFIX)
