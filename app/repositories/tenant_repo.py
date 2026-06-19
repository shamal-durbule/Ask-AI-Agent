from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.lease import Lease, LeaseStatus
from app.models.tenant import Tenant
from app.models.unit import Unit
from app.repositories.base import BaseRepository


class TenantRepository(BaseRepository[Tenant]):
    model = Tenant

    async def list_with_active_leases(self, *, limit: int = 100, offset: int = 0) -> list[Tenant]:
        """List tenants with eagerly loaded active leases (avoids N+1)."""
        stmt = (
            select(Tenant)
            .options(
                selectinload(Tenant.leases)
                .selectinload(Lease.unit)
                .selectinload(Unit.property),
            )
            .limit(limit)
            .offset(offset)
            .order_by(Tenant.id)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().unique().all())

    async def get_by_email(self, email: str) -> Tenant | None:
        stmt = select(Tenant).where(Tenant.email == email)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_with_overdue_charges(self) -> list[Tenant]:
        """Tenants who have at least one overdue charge on an active lease."""
        from app.models.charge import Charge, ChargeStatus

        stmt = (
            select(Tenant)
            .join(Lease, Lease.tenant_id == Tenant.id)
            .join(Charge, Charge.lease_id == Lease.id)
            .where(Lease.status == LeaseStatus.ACTIVE)
            .where(Charge.status == ChargeStatus.OVERDUE)
            .distinct()
            .order_by(Tenant.id)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
