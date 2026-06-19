import enum
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Date, Enum, ForeignKey, Index, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.charge import Charge
    from app.models.tenant import Tenant
    from app.models.unit import Unit


class LeaseStatus(str, enum.Enum):
    ACTIVE = "active"
    ENDED = "ended"


class Lease(TimestampMixin, Base):
    __tablename__ = "lease"
    __table_args__ = (
        Index("ix_lease_unit_status", "unit_id", "status"),
        Index("ix_lease_tenant", "tenant_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    unit_id: Mapped[int] = mapped_column(ForeignKey("unit.id"), nullable=False)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenant.id"), nullable=False)
    rent_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[LeaseStatus] = mapped_column(
        Enum(LeaseStatus, native_enum=False, length=20),
        default=LeaseStatus.ACTIVE,
        nullable=False,
    )

    unit: Mapped["Unit"] = relationship("Unit", back_populates="leases")
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="leases")
    charges: Mapped[list["Charge"]] = relationship("Charge", back_populates="lease", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Lease(id={self.id}, tenant_id={self.tenant_id}, status={self.status})>"
