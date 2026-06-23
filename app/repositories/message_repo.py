from datetime import datetime

from sqlalchemy import select

from app.models.message import Direction, Message, MessageStatus, ScheduledMessage, ScheduledMessageStatus
from app.repositories.base import BaseRepository


class MessageRepository(BaseRepository[Message]):
    model = Message

    async def create_outbound(self, tenant_id: int, body: str) -> Message:
        """Create an outbound message (delivery is mocked)."""
        msg = Message(
            tenant_id=tenant_id,
            body=body,
            direction=Direction.OUTBOUND,
            status=MessageStatus.SENT,
        )
        self._session.add(msg)
        await self._session.flush()
        return msg

    async def list_by_tenant(self, tenant_id: int, *, limit: int = 50) -> list[Message]:
        stmt = select(Message).where(Message.tenant_id == tenant_id).order_by(Message.sent_at.desc()).limit(limit)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def create_scheduled(
        self,
        tenant_id: int,
        body: str,
        send_at: datetime,
        tenant_name: str | None = None,
    ) -> ScheduledMessage:
        """Schedule a message for future delivery."""
        msg = ScheduledMessage(
            tenant_id=tenant_id,
            body=body,
            send_at=send_at,
            status=ScheduledMessageStatus.SCHEDULED,
            tenant_name=tenant_name,
        )
        self._session.add(msg)
        await self._session.flush()
        return msg
