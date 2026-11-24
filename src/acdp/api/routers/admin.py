"""Admin Control Center, RBAC User Management, Cache Kill-Switch & Protected Docs (/api/v1/admin/*)."""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from acdp.api.db.duckdb_client import refresh_duckdb_r2_connection
from acdp.api.db.models import User, UserSession
from acdp.api.db.postgres import get_db_session
from acdp.api.dependencies import require_admin
from acdp.api.middleware.security import get_rate_limit_stats, reset_rate_limiter
from acdp.api.schemas.admin import (
    AdminCacheRefreshDTO,
    AdminCacheRefreshRequest,
    AdminTelemetryDTO,
    AdminUserDTO,
    AdminUsersSummaryDTO,
    AdminUserUpdateRequest,
)
from acdp.api.services.gold_queries import get_gold_mart_cache_stats, invalidate_gold_mart_cache
from acdp.api.services.rag_service import get_rag_cache_stats, invalidate_rag_cache

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["Admin"])


def _to_admin_user_dto(user: User) -> AdminUserDTO:
    return AdminUserDTO(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,  # type: ignore[arg-type]
        is_active=user.is_active,
        student_or_staff_id=user.student_or_staff_id,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


@router.get("/telemetry", response_model=AdminTelemetryDTO)
async def get_admin_telemetry(
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db_session),
) -> AdminTelemetryDTO:
    """Return user counts, rate-limit telemetry, and DuckDB Gold / RAG TTL cache statistics."""
    rows = (await db.execute(select(User))).scalars().all()
    total_users = len(rows)
    active_users = sum(1 for u in rows if u.is_active)
    blocked_users = total_users - active_users
    admin_count = sum(1 for u in rows if u.role == "admin")
    lecturer_count = sum(1 for u in rows if u.role == "lecturer")
    student_count = sum(1 for u in rows if u.role == "student")

    return AdminTelemetryDTO(
        users_summary=AdminUsersSummaryDTO(
            total_users=total_users,
            active_users=active_users,
            blocked_users=blocked_users,
            admin_count=admin_count,
            lecturer_count=lecturer_count,
            student_count=student_count,
        ),
        rate_limit=get_rate_limit_stats(),
        gold_mart_cache=get_gold_mart_cache_stats(),
        rag_cache=get_rag_cache_stats(),
    )


@router.get("/users", response_model=list[AdminUserDTO])
async def list_admin_users(
    q: str | None = Query(default=None, max_length=120),
    role: str | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db_session),
) -> list[AdminUserDTO]:
    """List registered accounts with optional keyword, role, and active status filters."""
    stmt = select(User).order_by(User.created_at.desc())
    if role and role.strip() in {"student", "lecturer", "admin"}:
        stmt = stmt.where(User.role == role.strip())
    if is_active is not None:
        stmt = stmt.where(User.is_active.is_(is_active))

    users = (await db.execute(stmt)).scalars().all()
    if q and q.strip():
        needle = q.strip().lower()
        users = [
            u
            for u in users
            if needle in u.email.lower()
            or needle in u.full_name.lower()
            or (u.student_or_staff_id and needle in u.student_or_staff_id.lower())
        ]
    return [_to_admin_user_dto(u) for u in users]


@router.patch("/users/{user_id}", response_model=AdminUserDTO)
async def update_admin_user(
    user_id: UUID,
    payload: AdminUserUpdateRequest,
    current_admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db_session),
) -> AdminUserDTO:
    """Update a user's RBAC role or active status; revokes all sessions when deactivated."""
    target = (await db.execute(select(User).where(User.id == user_id))).scalars().first()
    if target is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    if target.id == current_admin.id and (
        payload.is_active is False or (payload.role is not None and payload.role != "admin")
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate or demote your own admin account.",
        )

    now = datetime.now(UTC)
    if payload.role is not None:
        target.role = payload.role
    if payload.is_active is not None:
        target.is_active = payload.is_active
    target.updated_at = now
    db.add(target)

    if payload.is_active is False:
        await db.execute(
            update(UserSession)
            .where(UserSession.user_id == target.id, UserSession.revoked_at.is_(None))
            .values(revoked_at=now)
        )

    await db.commit()
    await db.refresh(target)

    logger.warning(
        "Admin Audit [user_update]: admin=%s target_id=%s target_email=%s role=%s is_active=%s",
        current_admin.email,
        target.id,
        target.email,
        target.role,
        target.is_active,
    )
    return _to_admin_user_dto(target)


@router.post("/cache/refresh", response_model=AdminCacheRefreshDTO)
async def refresh_admin_caches(
    payload: AdminCacheRefreshRequest | None = None,
    current_admin: User = Depends(require_admin),
) -> AdminCacheRefreshDTO:
    """Refresh DuckDB R2 Gold Parquet entities, invalidate RAG cache, or reset rate limiter."""
    req = payload or AdminCacheRefreshRequest()
    duckdb_info: dict[str, object] | None = None
    rate_limit_reset = False

    if req.target in {"all", "duckdb_r2"}:
        try:
            duckdb_info = await asyncio.to_thread(refresh_duckdb_r2_connection)
        except Exception as exc:
            invalidate_gold_mart_cache()
            duckdb_info = {"status": "cache_invalidated", "detail": str(exc)}

    if req.target in {"all", "rag"}:
        invalidate_rag_cache()

    if req.target == "rate_limit":
        reset_rate_limiter()
        rate_limit_reset = True

    logger.warning(
        "Admin Audit [cache_refresh]: admin=%s target=%s rate_limit_reset=%s",
        current_admin.email,
        req.target,
        rate_limit_reset,
    )
    return AdminCacheRefreshDTO(
        target=req.target,
        duckdb_r2=duckdb_info,
        gold_mart_cache=get_gold_mart_cache_stats(),
        rag_cache=get_rag_cache_stats(),
        rate_limit_reset=rate_limit_reset,
        refreshed_at=datetime.now(UTC),
    )


@router.get("/openapi.json", include_in_schema=False)
async def get_admin_openapi(
    request: Request,
    _admin: User = Depends(require_admin),
) -> JSONResponse:
    """Serve OpenAPI 3.1 schema exclusively to authenticated administrators."""
    return JSONResponse(request.app.openapi())


@router.get("/docs", response_class=HTMLResponse, include_in_schema=False)
async def get_admin_swagger_docs(
    request: Request,
    _admin: User = Depends(require_admin),
) -> HTMLResponse:
    """Serve Swagger UI exclusively to authenticated administrators when public /docs is disabled."""
    return get_swagger_ui_html(
        openapi_url="/api/v1/admin/openapi.json",
        title=f"{request.app.title} - Admin Swagger UI",
    )
