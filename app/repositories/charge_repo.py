from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.charge import Charge, ChargeKind, ChargeStatus
from app.models.lease import Lease
from app.repositories.base import BaseRepository


class ChargeRepository(BaseRepository[Charge]):
    model = Charge

    async def get_overdue(self) -> list[Charge]:
        """All overdue charges with lease and tenant info eagerly loaded."""
        stmt = (
            select(Charge)
            .options(selectinload(Charge.lease).selectinload(Lease.tenant))
            .where(Charge.status == ChargeStatus.OVERDUE)
            .order_by(Charge.due_date)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_outstanding_by_month(self, period_month: str) -> list[Charge]:
        """Charges that are open or overdue for a given month."""
        stmt = (
            select(Charge)
            .options(selectinload(Charge.lease).selectinload(Lease.tenant))
            .where(Charge.period_month == period_month)
            .where(Charge.status.in_([ChargeStatus.OPEN, ChargeStatus.OVERDUE]))
            .order_by(Charge.due_date)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def create_credit(
        self,
        lease_id: int,
        amount: Decimal,
        reason: str,
    ) -> Charge:
        """Apply a credit charge (negative amount) to a lease."""
        today = date.today()
        credit = Charge(
            lease_id=lease_id,
            period_month=today.strftime("%Y-%m"),
            amount_due=-abs(amount),
            amount_paid=Decimal("0.00"),
            due_date=today,
            status=ChargeStatus.PAID,
            kind=ChargeKind.CREDIT,
        )
        self._session.add(credit)
        await self._session.flush()
        return credit

    async def waive_late_fee(self, charge_id: int) -> Charge | None:
        """Mark a late fee charge as paid (waived) with zero payment."""
        charge = await self.get_by_id(charge_id)
        if charge is None or charge.kind != ChargeKind.LATE_FEE:
            return None
        charge.status = ChargeStatus.PAID
        charge.amount_paid = charge.amount_due
        await self._session.flush()
        return charge
