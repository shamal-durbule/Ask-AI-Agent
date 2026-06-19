from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.unit import Unit


class Property(TimestampMixin, Base):
    __tablename__ = "property"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    address: Mapped[str] = mapped_column(String(500), nullable=False)

    units: Mapped[list["Unit"]] = relationship("Unit", back_populates="property", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Property(id={self.id}, name={self.name!r})>"
