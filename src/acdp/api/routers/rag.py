"""RAG Regulation Copilot router (/api/v1/rag/*)."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from acdp.api.db.models import ChatMessage, ChatSession, User
from acdp.api.db.postgres import get_db_session
from acdp.api.dependencies import get_current_user, get_optional_user
from acdp.api.schemas.rag import (
    ChatMessageDTO,
    ChatSessionDTO,
    RagChatRequest,
    RagChatResponse,
    RagCitationDTO,
)
from acdp.api.services.rag_service import RagUnavailableError, query_rag

router = APIRouter(prefix="/rag", tags=["RAG Copilot"])


async def _handle_rag_chat(
    payload: RagChatRequest,
    current_user: User | None,
    db: AsyncSession,
) -> RagChatResponse:
    history: list[dict[str, str]] = []
    chat_session: ChatSession | None = None

    if current_user is not None:
        if payload.session_id is not None:
            res = await db.execute(
                select(ChatSession).where(
                    ChatSession.id == payload.session_id,
                    ChatSession.user_id == current_user.id,
                )
            )
            chat_session = res.scalars().first()
            if chat_session is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat session not found.")

            msg_res = await db.execute(
                select(ChatMessage)
                .where(ChatMessage.session_id == chat_session.id)
                .order_by(ChatMessage.created_at.asc())
            )
            history = [{"role": m.role, "content": m.content} for m in msg_res.scalars().all()]
        else:
            title = payload.message.strip()[:80] or "Phiên hỏi đáp mới"
            chat_session = ChatSession(user_id=current_user.id, title=title)
            db.add(chat_session)
            await db.flush()

    try:
        rag_res = await query_rag(
            message=payload.message,
            domain_filter=payload.domain_filter,
            history=history,
        )
    except RagUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Dịch vụ RAG tạm thời gián đoạn: {exc}",
        ) from exc

    session_id = chat_session.id if chat_session is not None else (payload.session_id or uuid4())

    if chat_session is not None:
        user_msg = ChatMessage(session_id=chat_session.id, role="user", content=payload.message)
        assistant_msg = ChatMessage(
            session_id=chat_session.id,
            role="assistant",
            content=rag_res.answer,
            citations_json=[c.model_dump() for c in rag_res.citations],
            latency_ms=rag_res.latency_ms,
        )
        chat_session.updated_at = datetime.now(UTC)
        db.add(user_msg)
        db.add(assistant_msg)
        await db.commit()

    return RagChatResponse(
        session_id=session_id,
        answer=rag_res.answer,
        citations=rag_res.citations,
        grounded=rag_res.grounded,
        latency_ms=rag_res.latency_ms,
    )


@router.post("/chat", response_model=RagChatResponse)
async def rag_chat(
    payload: RagChatRequest,
    current_user: User | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db_session),
) -> RagChatResponse:
    """Query competition rules via Qdrant + LLM with grounded URL citations."""
    return await _handle_rag_chat(payload, current_user, db)


@router.post("/query", response_model=RagChatResponse, include_in_schema=False)
async def rag_query_alias(
    payload: RagChatRequest,
    current_user: User | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db_session),
) -> RagChatResponse:
    """Alias for /api/v1/rag/chat."""
    return await _handle_rag_chat(payload, current_user, db)


@router.get("/sessions", response_model=list[ChatSessionDTO])
async def list_chat_sessions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> list[ChatSessionDTO]:
    """List saved RAG chat sessions owned by the current user."""
    res = await db.execute(
        select(ChatSession)
        .where(ChatSession.user_id == current_user.id)
        .order_by(ChatSession.updated_at.desc())
    )
    return [
        ChatSessionDTO(id=s.id, title=s.title, created_at=s.created_at, updated_at=s.updated_at)
        for s in res.scalars().all()
    ]


@router.get("/sessions/{session_id}/messages", response_model=list[ChatMessageDTO])
async def list_session_messages(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> list[ChatMessageDTO]:
    """List messages and citations for a chat session owned by the current user."""
    sess_res = await db.execute(
        select(ChatSession).where(ChatSession.id == session_id, ChatSession.user_id == current_user.id)
    )
    if sess_res.scalars().first() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat session not found.")

    msg_res = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
    )
    return [
        ChatMessageDTO(
            id=m.id,
            role=m.role,  # type: ignore[arg-type]
            content=m.content,
            citations=[RagCitationDTO.model_validate(c) for c in (m.citations_json or [])],
            latency_ms=m.latency_ms,
            created_at=m.created_at,
        )
        for m in msg_res.scalars().all()
    ]


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chat_session(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> None:
    """Delete a chat session owned by the current user."""
    sess_res = await db.execute(
        select(ChatSession).where(ChatSession.id == session_id, ChatSession.user_id == current_user.id)
    )
    session_row = sess_res.scalars().first()
    if session_row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat session not found.")
    await db.delete(session_row)
    await db.commit()
