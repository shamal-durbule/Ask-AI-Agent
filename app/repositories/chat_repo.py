import json
from datetime import datetime, timezone

from sqlalchemy import select, update

from app.models.chat import ActionLog, ActionStatus, ChatMessage, ChatSession, MessageRole
from app.repositories.base import BaseRepository


class ChatRepository(BaseRepository[ChatSession]):
    model = ChatSession

    async def create_session(self, session_id: str, title: str = "New Chat") -> ChatSession:
        chat_session = ChatSession(id=session_id, title=title)
        self._session.add(chat_session)
        await self._session.flush()
        return chat_session

    async def list_sessions(self, *, limit: int = 50, offset: int = 0) -> list[ChatSession]:
        stmt = (
            select(ChatSession)
            .order_by(ChatSession.updated_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def add_message(
        self,
        session_id: str,
        role: MessageRole,
        content: str,
        metadata: dict[str, object] | None = None,
    ) -> ChatMessage:
        msg = ChatMessage(
            session_id=session_id,
            role=role,
            content=content,
            metadata_json=json.dumps(metadata) if metadata else None,
        )
        self._session.add(msg)
        await self._session.flush()
        return msg

    async def get_messages(self, session_id: str) -> list[ChatMessage]:
        stmt = (
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update_session_title(self, session_id: str, title: str) -> None:
        stmt = (
            update(ChatSession)
            .where(ChatSession.id == session_id)
            .values(title=title)
        )
        await self._session.execute(stmt)

    # -- Action Log --

    async def create_action_log(
        self,
        action_id: str,
        session_id: str,
        tool_name: str,
        params: dict[str, object],
        preview: str,
    ) -> ActionLog:
        log = ActionLog(
            id=action_id,
            session_id=session_id,
            tool_name=tool_name,
            params_json=json.dumps(params, default=str),
            preview=preview,
            status=ActionStatus.PENDING,
        )
        self._session.add(log)
        await self._session.flush()
        return log

    async def get_action_log(self, action_id: str) -> ActionLog | None:
        return await self._session.get(ActionLog, action_id)

    async def approve_action(self, action_id: str) -> ActionLog | None:
        """CAS: only transitions PENDING -> APPROVED."""
        stmt = (
            update(ActionLog)
            .where(ActionLog.id == action_id, ActionLog.status == ActionStatus.PENDING)
            .values(status=ActionStatus.APPROVED)
            .returning(ActionLog)
        )
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        return row

    async def reject_action(self, action_id: str) -> ActionLog | None:
        stmt = (
            update(ActionLog)
            .where(ActionLog.id == action_id, ActionLog.status == ActionStatus.PENDING)
            .values(status=ActionStatus.REJECTED)
            .returning(ActionLog)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def mark_executed(self, action_id: str) -> ActionLog | None:
        """CAS: only transitions APPROVED -> EXECUTED (exactly-once)."""
        stmt = (
            update(ActionLog)
            .where(ActionLog.id == action_id, ActionLog.status == ActionStatus.APPROVED)
            .values(status=ActionStatus.EXECUTED, executed_at=datetime.now(timezone.utc))
            .returning(ActionLog)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()
