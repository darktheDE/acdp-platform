"""Authentication & Refresh Token Rotation router (/api/v1/auth/*)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from acdp.api.db.models import User, UserSession
from acdp.api.db.postgres import get_db_session
from acdp.api.dependencies import get_current_user
from acdp.api.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserProfileDTO,
)
from acdp.api.security import (
    create_access_token,
    generate_refresh_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)
from acdp.config import settings

router = APIRouter(prefix="/auth", tags=["Authentication"])

_REFRESH_COOKIE_NAME = "acdp_refresh_token"
_REFRESH_COOKIE_PATH = "/api/v1/auth"


def _to_profile(user: User) -> UserProfileDTO:
    return UserProfileDTO(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,  # type: ignore[arg-type]
        student_or_staff_id=user.student_or_staff_id,
        created_at=user.created_at,
    )


def _set_refresh_cookie(response: Response, raw_token: str) -> None:
    response.set_cookie(
        key=_REFRESH_COOKIE_NAME,
        value=raw_token,
        httponly=True,
        samesite="lax",
        secure=settings.environment == "production",
        path=_REFRESH_COOKIE_PATH,
        max_age=settings.refresh_token_expire_days * 86400,
    )


@router.post("/register", response_model=UserProfileDTO, status_code=status.HTTP_201_CREATED)
async def register(
    payload: RegisterRequest,
    db: AsyncSession = Depends(get_db_session),
) -> UserProfileDTO:
    """Register a new student account in PostgreSQL 18."""
    normalized_email = payload.email.strip().lower()
    existing = await db.execute(select(User).where(User.email == normalized_email))
    if existing.scalars().first() is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email is already registered.")

    user = User(
        email=normalized_email,
        full_name=payload.full_name.strip(),
        role="student",
        student_or_staff_id=payload.student_or_staff_id.strip() if payload.student_or_staff_id else None,
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return _to_profile(user)


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db_session),
) -> TokenResponse:
    """Authenticate credentials and issue Access JWT + HttpOnly Refresh Token cookie."""
    normalized_email = payload.email.strip().lower()
    result = await db.execute(select(User).where(User.email == normalized_email, User.is_active.is_(True)))
    user = result.scalars().first()
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
        )

    raw_refresh = generate_refresh_token()
    session_row = UserSession(
        user_id=user.id,
        refresh_token_hash=hash_refresh_token(raw_refresh),
        user_agent=request.headers.get("user-agent", "")[:255] or None,
        expires_at=datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_days),
    )
    db.add(session_row)
    await db.commit()

    _set_refresh_cookie(response, raw_refresh)
    access_token = create_access_token(user.id, user.role)
    return TokenResponse(
        access_token=access_token,
        expires_in=settings.access_token_expire_minutes * 60,
        user=_to_profile(user),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_tokens(
    request: Request,
    response: Response,
    acdp_refresh_token: str | None = Cookie(default=None, alias=_REFRESH_COOKIE_NAME),
    db: AsyncSession = Depends(get_db_session),
) -> TokenResponse:
    """Rotate Refresh Token and issue a fresh Access JWT; revoke all sessions on reuse."""
    if not acdp_refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing refresh token.")

    token_hash = hash_refresh_token(acdp_refresh_token)
    result = await db.execute(select(UserSession).where(UserSession.refresh_token_hash == token_hash))
    session_row = result.scalars().first()
    if session_row is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token.")

    now = datetime.now(UTC)
    if session_row.revoked_at is not None:
        # Reuse detection: revoke all active sessions for this user immediately
        await db.execute(
            update(UserSession)
            .where(UserSession.user_id == session_row.user_id, UserSession.revoked_at.is_(None))
            .values(revoked_at=now)
        )
        await db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token reuse detected.")

    if session_row.expires_at <= now:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expired.")

    user_res = await db.execute(select(User).where(User.id == session_row.user_id, User.is_active.is_(True)))
    user = user_res.scalars().first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User account unavailable.")

    session_row.revoked_at = now
    new_raw = generate_refresh_token()
    new_session = UserSession(
        user_id=user.id,
        refresh_token_hash=hash_refresh_token(new_raw),
        user_agent=request.headers.get("user-agent", "")[:255] or None,
        expires_at=now + timedelta(days=settings.refresh_token_expire_days),
    )
    db.add(new_session)
    await db.commit()

    _set_refresh_cookie(response, new_raw)
    access_token = create_access_token(user.id, user.role)
    return TokenResponse(
        access_token=access_token,
        expires_in=settings.access_token_expire_minutes * 60,
        user=_to_profile(user),
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    response: Response,
    acdp_refresh_token: str | None = Cookie(default=None, alias=_REFRESH_COOKIE_NAME),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> None:
    """Revoke the current refresh session and clear the refresh cookie."""
    now = datetime.now(UTC)
    if acdp_refresh_token:
        token_hash = hash_refresh_token(acdp_refresh_token)
        await db.execute(
            update(UserSession)
            .where(
                UserSession.user_id == current_user.id,
                UserSession.refresh_token_hash == token_hash,
                UserSession.revoked_at.is_(None),
            )
            .values(revoked_at=now)
        )
        await db.commit()
    response.delete_cookie(key=_REFRESH_COOKIE_NAME, path=_REFRESH_COOKIE_PATH)


@router.get("/me", response_model=UserProfileDTO)
async def get_me(current_user: User = Depends(get_current_user)) -> UserProfileDTO:
    """Return the authenticated user's profile."""
    return _to_profile(current_user)
