"""Bookmark DTOs."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class BookmarkCreateRequest(BaseModel):
    competition_key: str = Field(min_length=64, max_length=64, pattern=r"^[a-fA-F0-9]{64}$")
    personal_note: str | None = Field(default=None, max_length=1000)
    notify_before_deadline: bool = True


class BookmarkDTO(BaseModel):
    id: UUID
    competition_key: str
    competition_name: str
    personal_note: str | None = None
    notify_before_deadline: bool
    is_archived: bool = False
    mode_canonical: str | None = None
    total_prize_vnd: int | None = None
    created_at: datetime
