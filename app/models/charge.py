import enum
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Date, ForeignKey, Index, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, string_enum

if TYPE_CHECKING:
    from app.models.lease import Lease
    from app.models.payment import Payment


class ChargeStatus(str, enum.Enum):
    OPEN = "open"
    PAID = "paid"
    OVERDUE = "overdue"


class ChargeKind(str, enum.Enum):
    RENT = "rent"
    LATE_FEE = "late_fee"
    CREDIT = "credit"


class Charge(TimestampMixin, Base):
    __tablename__ = "charge"
    __table_args__ = (
        Index("ix_charge_lease_status", "lease_id", "status"),
        Index("ix_charge_due_status", "due_date", "status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    lease_id: Mapped[int] = mapped_column(ForeignKey("lease.id"), nullable=False)
    period_month: Mapped[str] = mapped_column(String(7), nullable=False)  # YYYY-MM
    amount_due: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    amount_paid: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"), nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[ChargeStatus] = mapped_column(
        string_enum(ChargeStatus),
        default=ChargeStatus.OPEN,
        nullable=False,
    )
    kind: Mapped[ChargeKind] = mapped_column(
        string_enum(ChargeKind),
        default=ChargeKind.RENT,
        nullable=False,
    )

    lease: Mapped["Lease"] = relationship("Lease", back_populates="charges")
    payments: Mapped[list["Payment"]] = relationship("Payment", back_populates="charge", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Charge(id={self.id}, kind={self.kind}, status={self.status})>"
