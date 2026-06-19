from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lease import LeaseStatus
from app.repositories.tenant_repo import TenantRepository
from app.schemas.domain import LeaseResponse, TenantResponse


class TenantService:
    """Business logic for tenant operations."""

    def __init__(self, session: AsyncSession) -> None:
        self._repo = TenantRepository(session)

    async def list_tenants(self, *, limit: int = 100, offset: int = 0) -> list[TenantResponse]:
        tenants = await self._repo.list_with_active_leases(limit=limit, offset=offset)
        result: list[TenantResponse] = []
        for t in tenants:
            active_lease = next(
                (lease for lease in t.leases if lease.status == LeaseStatus.ACTIVE),
                None,
            )
            lease_resp = None
            if active_lease is not None:
                unit = active_lease.unit
                lease_resp = LeaseResponse(
                    id=active_lease.id,
                    unit_label=unit.label if unit else "N/A",
                    property_name=unit.property.name if unit and unit.property else "N/A",
                    tenant_name=t.name,
                    rent_amount=active_lease.rent_amount,
                    start_date=active_lease.start_date,
                    end_date=active_lease.end_date,
                    status=active_lease.status.value,
                )
            result.append(
                TenantResponse(
                    id=t.id,
                    name=t.name,
                    email=t.email,
                    phone=t.phone,
                    active_lease=lease_resp,
                )
            )
        return result
