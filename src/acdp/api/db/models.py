"""SQLModel ORM tables for PostgreSQL 18 OLTP App DB (SPEC-0004 §2.2)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    """Return timezone-aware UTC timestamp."""
    return datetime.now(UTC)


class User(SQLModel, table=True):
    """Student, lecturer, or admin account."""

    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("role IN ('student', 'lecturer', 'admin')", name="ck_users_role"),
    )

    id: UUID = Field(
        default_factory=uuid4,
        sa_column=Column(PG_UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")),
    )
    email: str = Field(sa_column=Column(String(255), nullable=False, unique=True))
    full_name: str = Field(sa_column=Column(String(120), nullable=False))
    role: str = Field(default="student", sa_column=Column(String(20), nullable=False, server_default="student"))
    student_or_staff_id: str | None = Field(default=None, sa_column=Column(String(32), nullable=True))
    password_hash: str = Field(sa_column=Column(String(255), nullable=False))
    is_active: bool = Field(default=True, nullable=False)
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False, server_default=text("NOW()")),
    )
    updated_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False, server_default=text("NOW()")),
    )


class UserSession(SQLModel, table=True):
    """Refresh token rotation session ledger."""

    __tablename__ = "user_sessions"
    __table_args__ = (
        Index("idx_user_sessions_user_id", "user_id"),
    )

    id: UUID = Field(
        default_factory=uuid4,
        sa_column=Column(PG_UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")),
    )
    user_id: UUID = Field(
        sa_column=Column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
    )
    refresh_token_hash: str = Field(sa_column=Column(String(128), nullable=False, unique=True))
    user_agent: str | None = Field(default=None, sa_column=Column(String(255), nullable=True))
    expires_at: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False))
    revoked_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), nullable=True))
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False, server_default=text("NOW()")),
    )


class SavedCompetition(SQLModel, table=True):
    """Student bookmarked competition loosely coupled to DuckDB via competition_key."""

    __tablename__ = "saved_competitions"
    __table_args__ = (
        UniqueConstraint("user_id", "competition_key", name="uq_user_saved_competition"),
        Index("idx_saved_competitions_user_id", "user_id"),
    )

    id: UUID = Field(
        default_factory=uuid4,
        sa_column=Column(PG_UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")),
    )
    user_id: UUID = Field(
        sa_column=Column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
    )
    competition_key: str = Field(sa_column=Column(String(64), nullable=False))
    competition_name_snapshot: str = Field(sa_column=Column(String(255), nullable=False))
    personal_note: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    notify_before_deadline: bool = Field(default=True, nullable=False)
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False, server_default=text("NOW()")),
    )


class ChatSession(SQLModel, table=True):
    """RAG Copilot conversation thread."""

    __tablename__ = "chat_sessions"
    __table_args__ = (
        Index("idx_chat_sessions_user_updated", "user_id", "updated_at"),
    )

    id: UUID = Field(
        default_factory=uuid4,
        sa_column=Column(PG_UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")),
    )
    user_id: UUID = Field(
        sa_column=Column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
    )
    title: str = Field(
        default="Phiên hỏi đáp mới",
        sa_column=Column(String(200), nullable=False, server_default="Phiên hỏi đáp mới"),
    )
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False, server_default=text("NOW()")),
    )
    updated_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False, server_default=text("NOW()")),
    )


class ChatMessage(SQLModel, table=True):
    """Individual RAG turn with persisted citations_json."""

    __tablename__ = "chat_messages"
    __table_args__ = (
        CheckConstraint("role IN ('user', 'assistant')", name="ck_chat_messages_role"),
        Index("idx_chat_messages_session_created", "session_id", "created_at"),
    )

    id: UUID = Field(
        default_factory=uuid4,
        sa_column=Column(PG_UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")),
    )
    session_id: UUID = Field(
        sa_column=Column(PG_UUID(as_uuid=True), ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False),
    )
    role: str = Field(sa_column=Column(String(16), nullable=False))
    content: str = Field(sa_column=Column(Text, nullable=False))
    citations_json: list[dict[str, Any]] = Field(
        default_factory=list,
        sa_column=Column(JSONB, nullable=False, server_default=text("'[]'::jsonb")),
    )
    latency_ms: int | None = Field(default=None, nullable=True)
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False, server_default=text("NOW()")),
    )
