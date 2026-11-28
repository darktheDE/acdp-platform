"""Pydantic v2 DTOs and validators for Student Mini-CV Profiles (/api/v1/profile/*)."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Literal
from urllib.parse import urlparse
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

_STUDENT_ID_RE = re.compile(r"^[A-Za-z0-9_-]{4,32}$")
_PHONE_RE = re.compile(r"^[0-9+\-\s()]{8,20}$")


def _clean_optional_str(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def _validate_https_url(value: str | None, field_label: str) -> str | None:
    cleaned = _clean_optional_str(value)
    if cleaned is None:
        return None
    parsed = urlparse(cleaned)
    if parsed.scheme.lower() != "https" or not parsed.netloc:
        raise ValueError(f"{field_label} must be a valid https:// URL.")
    return cleaned


def _normalize_tag_list(items: list[str], *, max_items: int, max_len: int, label: str) -> list[str]:
    if len(items) > max_items:
        raise ValueError(f"{label} cannot exceed {max_items} items.")
    seen: set[str] = set()
    normalized: list[str] = []
    for raw in items:
        item = raw.strip()
        if not item:
            continue
        if len(item) > max_len:
            raise ValueError(f"Each entry in {label} must be at most {max_len} characters.")
        key = item.lower()
        if key not in seen:
            seen.add(key)
            normalized.append(item)
    return normalized


class ProfileUpdateRequest(BaseModel):
    """Payload for creating or updating the authenticated student's Mini-CV."""

    full_name: str | None = Field(default=None, min_length=2, max_length=120)
    student_or_staff_id: str | None = Field(default=None, max_length=32)
    faculty: str | None = Field(default=None, max_length=160)
    major: str | None = Field(default=None, max_length=160)
    academic_year: str | None = Field(default=None, max_length=32)
    phone: str | None = Field(default=None, max_length=24)
    bio: str | None = Field(default=None, max_length=600)
    skills: list[str] = Field(default_factory=list)
    preferred_roles: list[str] = Field(default_factory=list)
    achievements_summary: str | None = Field(default=None, max_length=1000)
    cv_url: str | None = Field(default=None, max_length=500)
    github_url: str | None = Field(default=None, max_length=300)
    linkedin_url: str | None = Field(default=None, max_length=300)
    is_open_to_team: bool = True

    @field_validator("full_name", "faculty", "major", "academic_year", "bio", "achievements_summary", mode="before")
    @classmethod
    def _strip_text_fields(cls, value: str | None) -> str | None:
        return _clean_optional_str(value)

    @field_validator("student_or_staff_id", mode="before")
    @classmethod
    def _validate_student_id(cls, value: str | None) -> str | None:
        cleaned = _clean_optional_str(value)
        if cleaned is None:
            return None
        if not _STUDENT_ID_RE.match(cleaned):
            raise ValueError("MSSV/Mã định danh chỉ gồm 4–32 ký tự chữ, số, '-' hoặc '_'.")
        return cleaned

    @field_validator("phone", mode="before")
    @classmethod
    def _validate_phone(cls, value: str | None) -> str | None:
        cleaned = _clean_optional_str(value)
        if cleaned is None:
            return None
        if not _PHONE_RE.match(cleaned):
            raise ValueError("Số điện thoại không hợp lệ (8–20 ký tự số, +, -, khoảng trắng).")
        return cleaned

    @field_validator("cv_url")
    @classmethod
    def _validate_cv_url(cls, value: str | None) -> str | None:
        return _validate_https_url(value, "cv_url")

    @field_validator("github_url")
    @classmethod
    def _validate_github_url(cls, value: str | None) -> str | None:
        return _validate_https_url(value, "github_url")

    @field_validator("linkedin_url")
    @classmethod
    def _validate_linkedin_url(cls, value: str | None) -> str | None:
        return _validate_https_url(value, "linkedin_url")

    @field_validator("skills")
    @classmethod
    def _validate_skills(cls, value: list[str]) -> list[str]:
        return _normalize_tag_list(value, max_items=20, max_len=40, label="skills")

    @field_validator("preferred_roles")
    @classmethod
    def _validate_roles(cls, value: list[str]) -> list[str]:
        return _normalize_tag_list(value, max_items=6, max_len=40, label="preferred_roles")


class StudentProfileDTO(BaseModel):
    """Full Mini-CV profile returned to the authenticated owner."""

    user_id: UUID
    email: str
    full_name: str
    role: Literal["student", "lecturer", "admin"]
    student_or_staff_id: str | None = None
    faculty: str | None = None
    major: str | None = None
    academic_year: str | None = None
    phone: str | None = None
    bio: str | None = None
    skills: list[str] = Field(default_factory=list)
    preferred_roles: list[str] = Field(default_factory=list)
    achievements_summary: str | None = None
    cv_url: str | None = None
    has_uploaded_cv: bool = False
    cv_filename: str | None = None
    cv_size_bytes: int | None = None
    cv_uploaded_at: datetime | None = None
    cv_download_path: str | None = None
    github_url: str | None = None
    linkedin_url: str | None = None
    is_open_to_team: bool = True
    completeness_pct: int = 0
    missing_fields: list[str] = Field(default_factory=list)
    updated_at: datetime


class PublicStudentProfileDTO(BaseModel):
    """Privacy-aware Mini-CV view for teammates and advisors."""

    user_id: UUID
    email: str
    full_name: str
    role: Literal["student", "lecturer", "admin"]
    student_or_staff_id: str | None = None
    faculty: str | None = None
    major: str | None = None
    academic_year: str | None = None
    phone: str | None = None
    bio: str | None = None
    skills: list[str] = Field(default_factory=list)
    preferred_roles: list[str] = Field(default_factory=list)
    achievements_summary: str | None = None
    cv_url: str | None = None
    has_uploaded_cv: bool = False
    cv_filename: str | None = None
    cv_download_path: str | None = None
    github_url: str | None = None
    linkedin_url: str | None = None
    is_open_to_team: bool = True
    completeness_pct: int = 0
