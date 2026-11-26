"""Student Mini-CV Profile & PDF CV Storage Router (/api/v1/profile/*)."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from acdp.api.db.models import User, UserProfile
from acdp.api.db.postgres import get_db_session
from acdp.api.dependencies import get_current_user
from acdp.api.schemas.profile import (
    ProfileUpdateRequest,
    PublicStudentProfileDTO,
    StudentProfileDTO,
)
from acdp.api.services.cv_storage import (
    MAX_CV_SIZE_BYTES,
    PDF_MAGIC_PREFIX,
    CvStorageService,
    get_cv_storage_service,
    sanitize_pdf_filename,
)

router = APIRouter(prefix="/profile", tags=["Profile"])


def _compute_completeness(user: User, profile: UserProfile | None) -> tuple[int, list[str]]:
    """Evaluate 8 Mini-CV checkpoints (100% total) and list missing human-readable fields."""
    checkpoints: list[tuple[str, bool]] = [
        ("MSSV / Mã định danh", bool(user.student_or_staff_id)),
        ("Khoa", bool(profile and profile.faculty)),
        ("Ngành học", bool(profile and profile.major)),
        ("Khóa / Năm học", bool(profile and profile.academic_year)),
        ("Kỹ năng (Skills)", bool(profile and profile.skills_json)),
        ("Vai trò thi đấu", bool(profile and profile.preferred_roles_json)),
        ("Giới thiệu hoặc Thành tích", bool(profile and (profile.bio or profile.achievements_summary))),
        ("Đính kèm CV (PDF hoặc Link)", bool(profile and (profile.cv_storage_key or profile.cv_url))),
    ]
    completed = sum(1 for _, ok in checkpoints if ok)
    missing = [label for label, ok in checkpoints if not ok]
    pct = round((completed / len(checkpoints)) * 100)
    return pct, missing


def _to_student_dto(user: User, profile: UserProfile | None) -> StudentProfileDTO:
    pct, missing = _compute_completeness(user, profile)
    has_uploaded_cv = bool(profile and profile.cv_storage_key)
    return StudentProfileDTO(
        user_id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,  # type: ignore[arg-type]
        student_or_staff_id=user.student_or_staff_id,
        faculty=profile.faculty if profile else None,
        major=profile.major if profile else None,
        academic_year=profile.academic_year if profile else None,
        phone=profile.phone if profile else None,
        bio=profile.bio if profile else None,
        skills=list(profile.skills_json) if profile else [],
        preferred_roles=list(profile.preferred_roles_json) if profile else [],
        achievements_summary=profile.achievements_summary if profile else None,
        cv_url=profile.cv_url if profile else None,
        has_uploaded_cv=has_uploaded_cv,
        cv_filename=profile.cv_filename if profile else None,
        cv_size_bytes=profile.cv_size_bytes if profile else None,
        cv_uploaded_at=profile.cv_uploaded_at if profile else None,
        cv_download_path=f"/api/v1/profile/{user.id}/cv" if has_uploaded_cv else None,
        github_url=profile.github_url if profile else None,
        linkedin_url=profile.linkedin_url if profile else None,
        is_open_to_team=profile.is_open_to_team if profile else True,
        completeness_pct=pct,
        missing_fields=missing,
        updated_at=profile.updated_at if profile else user.updated_at,
    )


def _to_public_dto(user: User, profile: UserProfile | None, *, include_phone: bool) -> PublicStudentProfileDTO:
    pct, _ = _compute_completeness(user, profile)
    has_uploaded_cv = bool(profile and profile.cv_storage_key)
    return PublicStudentProfileDTO(
        user_id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,  # type: ignore[arg-type]
        student_or_staff_id=user.student_or_staff_id,
        faculty=profile.faculty if profile else None,
        major=profile.major if profile else None,
        academic_year=profile.academic_year if profile else None,
        phone=(profile.phone if profile else None) if include_phone else None,
        bio=profile.bio if profile else None,
        skills=list(profile.skills_json) if profile else [],
        preferred_roles=list(profile.preferred_roles_json) if profile else [],
        achievements_summary=profile.achievements_summary if profile else None,
        cv_url=profile.cv_url if profile else None,
        has_uploaded_cv=has_uploaded_cv,
        cv_filename=profile.cv_filename if profile else None,
        cv_download_path=f"/api/v1/profile/{user.id}/cv" if has_uploaded_cv else None,
        github_url=profile.github_url if profile else None,
        linkedin_url=profile.linkedin_url if profile else None,
        is_open_to_team=profile.is_open_to_team if profile else True,
        completeness_pct=pct,
    )


async def _get_or_create_profile(user_id: UUID, db: AsyncSession) -> UserProfile:
    result = await db.execute(select(UserProfile).where(UserProfile.user_id == user_id))
    profile = result.scalars().first()
    if profile is None:
        profile = UserProfile(user_id=user_id)
        db.add(profile)
    return profile


@router.get("/me", response_model=StudentProfileDTO)
async def get_my_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> StudentProfileDTO:
    """Return the authenticated student's Mini-CV profile (defaulting from users if not yet saved)."""
    result = await db.execute(select(UserProfile).where(UserProfile.user_id == current_user.id))
    profile = result.scalars().first()
    return _to_student_dto(current_user, profile)


@router.put("/me", response_model=StudentProfileDTO)
async def upsert_my_profile(
    payload: ProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> StudentProfileDTO:
    """Create or update the authenticated student's Mini-CV and sync identity fields atomically."""
    now = datetime.now(UTC)
    if payload.full_name is not None:
        current_user.full_name = payload.full_name
    current_user.student_or_staff_id = payload.student_or_staff_id
    current_user.updated_at = now
    db.add(current_user)

    profile = await _get_or_create_profile(current_user.id, db)
    profile.faculty = payload.faculty
    profile.major = payload.major
    profile.academic_year = payload.academic_year
    profile.phone = payload.phone
    profile.bio = payload.bio
    profile.skills_json = payload.skills
    profile.preferred_roles_json = payload.preferred_roles
    profile.achievements_summary = payload.achievements_summary
    profile.cv_url = payload.cv_url
    profile.github_url = payload.github_url
    profile.linkedin_url = payload.linkedin_url
    profile.is_open_to_team = payload.is_open_to_team
    profile.updated_at = now
    db.add(profile)

    await db.commit()
    await db.refresh(current_user)
    await db.refresh(profile)
    return _to_student_dto(current_user, profile)


@router.post("/me/cv", response_model=StudentProfileDTO)
async def upload_my_cv_pdf(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    storage: CvStorageService = Depends(get_cv_storage_service),
) -> StudentProfileDTO:
    """Upload a PDF CV (<= 2 MB, %PDF- magic bytes) to Cloudflare R2 (Option B)."""
    content = await file.read(MAX_CV_SIZE_BYTES + 1)
    if not content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tệp CV trống.")
    if len(content) > MAX_CV_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail="Dung lượng tệp CV vượt quá giới hạn 2 MB.",
        )
    if not content.startswith(PDF_MAGIC_PREFIX):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Chỉ chấp nhận tệp định dạng PDF hợp lệ (%PDF-).",
        )
    if not storage.is_configured():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Dịch vụ lưu trữ tệp CV trên Cloudflare R2 chưa được cấu hình.",
        )

    safe_name = sanitize_pdf_filename(file.filename)
    storage_key = await storage.upload_pdf(current_user.id, content, safe_name)

    now = datetime.now(UTC)
    profile = await _get_or_create_profile(current_user.id, db)
    profile.cv_storage_key = storage_key
    profile.cv_filename = safe_name
    profile.cv_size_bytes = len(content)
    profile.cv_uploaded_at = now
    profile.updated_at = now
    db.add(profile)
    await db.commit()
    await db.refresh(profile)
    return _to_student_dto(current_user, profile)


@router.delete("/me/cv", response_model=StudentProfileDTO)
async def delete_my_cv_pdf(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    storage: CvStorageService = Depends(get_cv_storage_service),
) -> StudentProfileDTO:
    """Remove the uploaded PDF CV from Cloudflare R2 and clear stored metadata."""
    result = await db.execute(select(UserProfile).where(UserProfile.user_id == current_user.id))
    profile = result.scalars().first()
    if profile and profile.cv_storage_key:
        await storage.delete_pdf(profile.cv_storage_key)
        profile.cv_storage_key = None
        profile.cv_filename = None
        profile.cv_size_bytes = None
        profile.cv_uploaded_at = None
        profile.updated_at = datetime.now(UTC)
        db.add(profile)
        await db.commit()
        await db.refresh(profile)
    return _to_student_dto(current_user, profile)


@router.get("/{user_id}", response_model=PublicStudentProfileDTO)
async def get_public_profile(
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> PublicStudentProfileDTO:
    """Return privacy-aware Mini-CV for teammates and advisors."""
    user_res = await db.execute(select(User).where(User.id == user_id, User.is_active.is_(True)))
    target_user = user_res.scalars().first()
    if target_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student profile not found.")

    prof_res = await db.execute(select(UserProfile).where(UserProfile.user_id == user_id))
    target_profile = prof_res.scalars().first()
    include_phone = current_user.id == user_id or current_user.role in {"lecturer", "admin"}
    return _to_public_dto(target_user, target_profile, include_phone=include_phone)


@router.get("/{user_id}/cv")
async def download_student_cv_pdf(
    user_id: UUID,
    _: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    storage: CvStorageService = Depends(get_cv_storage_service),
) -> Response:
    """Stream an uploaded student PDF CV from Cloudflare R2 with safe response headers."""
    user_res = await db.execute(select(User).where(User.id == user_id, User.is_active.is_(True)))
    if user_res.scalars().first() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student profile not found.")

    prof_res = await db.execute(select(UserProfile).where(UserProfile.user_id == user_id))
    profile = prof_res.scalars().first()
    if profile is None or not profile.cv_storage_key:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Uploaded PDF CV not found.")

    if not storage.is_configured():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Dịch vụ lưu trữ tệp CV trên Cloudflare R2 chưa được cấu hình.",
        )

    pdf_bytes = await storage.download_pdf(profile.cv_storage_key)
    if pdf_bytes is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Uploaded PDF CV not found in storage.")

    safe_name = sanitize_pdf_filename(profile.cv_filename)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'inline; filename="{safe_name}"',
            "X-Content-Type-Options": "nosniff",
        },
    )
