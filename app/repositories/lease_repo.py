from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.lease import Lease, LeaseStatus
from app.repositories.base import BaseRepository


class LeaseRepository(BaseRepository[Lease]):
    model = Lease

    async def list_active(self, *, property_id: int | None = None) -> list[Lease]:
        """List active leases, optionally filtered by property."""
        stmt = (
            select(Lease)
            .options(selectinload(Lease.tenant), selectinload(Lease.unit))
            .where(Lease.status == LeaseStatus.ACTIVE)
            .order_by(Lease.id)
        )
        if property_id is not None:
            from app.models.unit import Unit

            stmt = stmt.join(Unit, Unit.id == Lease.unit_id).where(Unit.property_id == property_id)
        result = await self._session.execute(stmt)
        return list(result.scalars().unique().all())

    async def get_by_tenant(self, tenant_id: int) -> list[Lease]:
        stmt = (
            select(Lease)
            .options(selectinload(Lease.unit))
            .where(Lease.tenant_id == tenant_id)
            .order_by(Lease.start_date.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
