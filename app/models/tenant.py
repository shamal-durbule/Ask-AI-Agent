from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.lease import Lease
    from app.models.message import Message


class Tenant(TimestampMixin, Base):
    __tablename__ = "tenant"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    phone: Mapped[str] = mapped_column(String(30), nullable=False)

    leases: Mapped[list["Lease"]] = relationship("Lease", back_populates="tenant", lazy="selectin")
    messages: Mapped[list["Message"]] = relationship("Message", back_populates="tenant", lazy="noload")

    def __repr__(self) -> str:
        return f"<Tenant(id={self.id}, name={self.name!r})>"
