import enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, string_enum

if TYPE_CHECKING:
    from app.models.tenant import Tenant


class Direction(str, enum.Enum):
    OUTBOUND = "outbound"
    INBOUND = "inbound"


class MessageStatus(str, enum.Enum):
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"


class Message(Base):
    __tablename__ = "message"
    __table_args__ = (Index("ix_message_tenant_direction", "tenant_id", "direction"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenant.id"), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    direction: Mapped[Direction] = mapped_column(
        string_enum(Direction),
        nullable=False,
    )
    status: Mapped[MessageStatus] = mapped_column(
        string_enum(MessageStatus),
        default=MessageStatus.SENT,
        nullable=False,
    )
    sent_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="messages")

    def __repr__(self) -> str:
        return f"<Message(id={self.id}, direction={self.direction})>"


class ScheduledMessageStatus(str, enum.Enum):
    SCHEDULED = "scheduled"
    SENT = "sent"
    CANCELLED = "cancelled"


class ScheduledMessage(Base):
    __tablename__ = "scheduled_message"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenant.id"), nullable=False, index=True)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    send_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[ScheduledMessageStatus] = mapped_column(
        string_enum(ScheduledMessageStatus),
        default=ScheduledMessageStatus.SCHEDULED,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    tenant_name: Mapped[str] = mapped_column(String(255), nullable=True)

    def __repr__(self) -> str:
        return f"<ScheduledMessage(id={self.id}, status={self.status})>"
