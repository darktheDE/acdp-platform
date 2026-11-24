"""Admin Control Center & RBAC DTO schemas (TASK-SEC-02)."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel


class AdminUserDTO(BaseModel):
    id: UUID
    email: str
    full_name: str
    role: Literal["student", "lecturer", "admin"]
    is_active: bool
    student_or_staff_id: str | None = None
    created_at: datetime
    updated_at: datetime


class AdminUserUpdateRequest(BaseModel):
    role: Literal["student", "lecturer", "admin"] | None = None
    is_active: bool | None = None


class AdminUsersSummaryDTO(BaseModel):
    total_users: int
    active_users: int
    blocked_users: int
    admin_count: int
    lecturer_count: int
    student_count: int


class AdminTelemetryDTO(BaseModel):
    users_summary: AdminUsersSummaryDTO
    rate_limit: dict[str, Any]
    gold_mart_cache: dict[str, Any]
    rag_cache: dict[str, Any]


class AdminCacheRefreshRequest(BaseModel):
    target: Literal["all", "duckdb_r2", "rag", "rate_limit"] = "all"


class AdminCacheRefreshDTO(BaseModel):
    target: Literal["all", "duckdb_r2", "rag", "rate_limit"]
    duckdb_r2: dict[str, Any] | None = None
    gold_mart_cache: dict[str, Any]
    rag_cache: dict[str, Any]
    rate_limit_reset: bool = False
    refreshed_at: datetime
