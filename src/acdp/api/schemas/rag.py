"""RAG Copilot DTOs."""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class RagChatRequest(BaseModel):
    session_id: UUID | None = None
    message: str = Field(min_length=2, max_length=2000)
    domain_filter: str | None = None


class RagCitationDTO(BaseModel):
    title: str
    url: str
    domain: str
    snippet: str


class RagChatResponse(BaseModel):
    session_id: UUID
    answer: str
    citations: list[RagCitationDTO]
    grounded: bool
    latency_ms: int


class ChatSessionDTO(BaseModel):
    id: UUID
    title: str
    created_at: datetime
    updated_at: datetime


class ChatMessageDTO(BaseModel):
    id: UUID
    role: Literal["user", "assistant"]
    content: str
    citations: list[RagCitationDTO]
    latency_ms: int | None = None
    created_at: datetime
