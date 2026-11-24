"""Student Bookmarks router (/api/v1/bookmarks) with EC-A2 & EC-A3 handling."""

from __future__ import annotations

import duckdb
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from acdp.api.db.models import SavedCompetition, User
from acdp.api.db.postgres import get_db_session
from acdp.api.dependencies import get_current_user, get_duckdb
from acdp.api.schemas.bookmarks import BookmarkCreateRequest, BookmarkDTO
from acdp.api.services.gold_queries import (
    check_competition_name,
    fetch_gold_metadata_map,
)

router = APIRouter(prefix="/bookmarks", tags=["Bookmarks"])


@router.get("", response_model=list[BookmarkDTO])
async def list_bookmarks(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    con: duckdb.DuckDBPyConnection = Depends(get_duckdb),
) -> list[BookmarkDTO]:
    """List current user's saved competitions enriched with Gold status (EC-A2 archived safe)."""
    res = await db.execute(
        select(SavedCompetition)
        .where(SavedCompetition.user_id == current_user.id)
        .order_by(SavedCompetition.created_at.desc())
    )
    saved_rows = list(res.scalars().all())
    gold_map = fetch_gold_metadata_map(con, [row.competition_key for row in saved_rows])

    items: list[BookmarkDTO] = []
    for row in saved_rows:
        gold_info = gold_map.get(row.competition_key)
        items.append(
            BookmarkDTO(
                id=row.id,
                competition_key=row.competition_key,
                competition_name=row.competition_name_snapshot,
                personal_note=row.personal_note,
                notify_before_deadline=row.notify_before_deadline,
                is_archived=gold_info is None,
                mode_canonical=gold_info[0] if gold_info else None,
                total_prize_vnd=gold_info[1] if gold_info else None,
                created_at=row.created_at,
            )
        )
    return items


@router.post("", response_model=BookmarkDTO, status_code=status.HTTP_201_CREATED)
async def save_bookmark(
    payload: BookmarkCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    con: duckdb.DuckDBPyConnection = Depends(get_duckdb),
) -> BookmarkDTO:
    """Save or idempotently update a competition bookmark (SPEC-0004 EC-A3)."""
    comp_name = check_competition_name(con, payload.competition_key)
    if comp_name is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Competition '{payload.competition_key}' not found in Gold layer.",
        )

    stmt = (
        pg_insert(SavedCompetition)
        .values(
            user_id=current_user.id,
            competition_key=payload.competition_key,
            competition_name_snapshot=comp_name,
            personal_note=payload.personal_note,
            notify_before_deadline=payload.notify_before_deadline,
        )
        .on_conflict_do_update(
            constraint="uq_user_saved_competition",
            set_={
                "competition_name_snapshot": comp_name,
                "personal_note": payload.personal_note,
                "notify_before_deadline": payload.notify_before_deadline,
            },
        )
        .returning(SavedCompetition.id, SavedCompetition.created_at)
    )
    row = (await db.execute(stmt)).one()
    await db.commit()

    gold_map = fetch_gold_metadata_map(con, [payload.competition_key])
    gold_info = gold_map.get(payload.competition_key)
    return BookmarkDTO(
        id=row[0],
        competition_key=payload.competition_key,
        competition_name=comp_name,
        personal_note=payload.personal_note,
        notify_before_deadline=payload.notify_before_deadline,
        is_archived=gold_info is None,
        mode_canonical=gold_info[0] if gold_info else None,
        total_prize_vnd=gold_info[1] if gold_info else None,
        created_at=row[1],
    )


@router.delete("/{competition_key}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bookmark(
    competition_key: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> None:
    """Delete a saved competition belonging to the authenticated user."""
    res = await db.execute(
        select(SavedCompetition).where(
            SavedCompetition.user_id == current_user.id,
            SavedCompetition.competition_key == competition_key,
        )
    )
    row = res.scalars().first()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bookmark not found.")
    await db.delete(row)
    await db.commit()
