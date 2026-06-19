import enum
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, Numeric, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, string_enum

if TYPE_CHECKING:
    from app.models.lease import Lease
    from app.models.property import Property


class UnitStatus(str, enum.Enum):
    AVAILABLE = "available"
    LEASED = "leased"


class Unit(TimestampMixin, Base):
    __tablename__ = "unit"
    __table_args__ = (Index("ix_unit_property_status", "property_id", "status"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    property_id: Mapped[int] = mapped_column(ForeignKey("property.id"), nullable=False, index=True)
    label: Mapped[str] = mapped_column(String(50), nullable=False)
    bedrooms: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    monthly_rent: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    status: Mapped[UnitStatus] = mapped_column(
        string_enum(UnitStatus),
        default=UnitStatus.AVAILABLE,
        nullable=False,
    )

    property: Mapped["Property"] = relationship("Property", back_populates="units")
    leases: Mapped[list["Lease"]] = relationship("Lease", back_populates="unit", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Unit(id={self.id}, label={self.label!r}, status={self.status})>"
