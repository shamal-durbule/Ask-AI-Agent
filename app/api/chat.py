import json
import uuid
from collections.abc import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.chat import ApprovalRequest, ChatMessageResponse, ChatRequest, ChatSessionResponse
from app.services.chat_service import ChatService

router = APIRouter(prefix="/api/chat", tags=["chat"])


def _sse_event(event_type: str, data: dict[str, object]) -> str:
    """Format a Server-Sent Event string."""
    return f"event: {event_type}\ndata: {json.dumps(data, default=str)}\n\n"


@router.post("")
async def chat(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """Stream a chat response via Server-Sent Events."""
    session_id = request.session_id or str(uuid.uuid4())
    service = ChatService(db)

    async def event_stream() -> AsyncGenerator[str, None]:
        try:
            async for event in service.stream_chat(session_id, request.message):
                event_type = event.get("type", "text")
                yield _sse_event(event_type, event)
        except Exception as e:
            yield _sse_event("error", {"message": str(e)})

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-store, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/sessions/{session_id}/approve")
async def approve_action(
    session_id: str,
    request: ApprovalRequest,
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """Handle approval/rejection of an agent action.

    Returns an SSE stream with the agent's continuation after approval,
    or a simple confirmation for rejections.
    """
    service = ChatService(db)

    async def event_stream() -> AsyncGenerator[str, None]:
        try:
            async for event in service.handle_approval(
                session_id=session_id,
                interrupt_id=request.interrupt_id,
                decision=request.decision,
                edited_params=request.edited_params,
            ):
                event_type = event.get("type", "text")
                yield _sse_event(event_type, event)
        except ValueError as e:
            yield _sse_event("error", {"message": str(e)})
        except Exception as e:
            yield _sse_event("error", {"message": f"Internal error: {e}"})

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-store, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/sessions", response_model=list[ChatSessionResponse])
async def list_sessions(
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
) -> list[ChatSessionResponse]:
    """List chat sessions ordered by most recent."""
    service = ChatService(db)
    sessions = await service.list_sessions(limit=limit, offset=offset)
    return [ChatSessionResponse.model_validate(s) for s in sessions]


@router.get("/sessions/{session_id}/messages", response_model=list[ChatMessageResponse])
async def get_session_messages(
    session_id: str,
    db: AsyncSession = Depends(get_db),
) -> list[ChatMessageResponse]:
    """Get all messages for a chat session."""
    service = ChatService(db)
    if not await service.session_exists(session_id):
        raise HTTPException(status_code=404, detail="Session not found")
    messages = await service.get_messages(session_id)
    return [ChatMessageResponse.model_validate(m) for m in messages]
