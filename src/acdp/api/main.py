"""FastAPI Unified Serving Gateway entrypoint (SPEC-0004)."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from acdp.api.db.postgres import engine, init_oltp_schema
from acdp.api.routers import analytics, auth, bookmarks, competitions, health, rag
from acdp.config import settings


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Initialize PostgreSQL 18 OLTP schema on startup and dispose pool on shutdown."""
    await init_oltp_schema()
    yield
    await engine.dispose()


app = FastAPI(
    title="ACDP Serving Gateway",
    description="Unified FastAPI Gateway over DuckDB Gold Star Schema, PostgreSQL 18 OLTP, and Qdrant RAG.",
    version="1.0.0",
    openapi_url="/openapi.json",
    docs_url="/docs",
    lifespan=lifespan,
)

origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

API_PREFIX = "/api/v1"
app.include_router(health.router, prefix=API_PREFIX)
app.include_router(analytics.router, prefix=API_PREFIX)
app.include_router(competitions.router, prefix=API_PREFIX)
app.include_router(auth.router, prefix=API_PREFIX)
app.include_router(bookmarks.router, prefix=API_PREFIX)
app.include_router(rag.router, prefix=API_PREFIX)
