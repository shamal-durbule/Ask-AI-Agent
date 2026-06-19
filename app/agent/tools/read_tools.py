"""Read-only tools that execute automatically without approval.

These tools let the agent look up domain data. They are thin wrappers
around repository methods, formatted for LLM consumption.
"""

import json
from decimal import Decimal

from strands import tool

from app.database import async_session_factory
from app.repositories.charge_repo import ChargeRepository
from app.repositories.lease_repo import LeaseRepository
from app.repositories.property_repo import PropertyRepository
from app.repositories.tenant_repo import TenantRepository


class _DecimalEncoder(json.JSONEncoder):
    def default(self, o: object) -> object:
        if isinstance(o, Decimal):
            return float(o)
        return super().default(o)


def _json(data: object) -> str:
    return json.dumps(data, cls=_DecimalEncoder, default=str)


@tool
async def get_properties() -> str:
    """List all properties with their units, occupancy counts, and monthly rent.

    Use this to answer questions about properties, available units, or occupancy rates.
    """
    async with async_session_factory() as session:
        repo = PropertyRepository(session)
        props = await repo.list_with_units()
        result = []
        for p in props:
            units = [
                {
                    "id": u.id,
                    "label": u.label,
                    "bedrooms": u.bedrooms,
                    "monthly_rent": float(u.monthly_rent),
                    "status": u.status.value,
                }
                for u in p.units
            ]
            total = len(units)
            occupied = sum(1 for u in units if u["status"] == "leased")
            result.append({
                "id": p.id,
                "name": p.name,
                "address": p.address,
                "total_units": total,
                "occupied_units": occupied,
                "available_units": total - occupied,
                "units": units,
            })
        return _json(result)


@tool
async def get_tenants() -> str:
    """List all tenants with their contact info and active lease details.

    Use this to find tenant information, look up who lives where, or check lease status.
    """
    async with async_session_factory() as session:
        repo = TenantRepository(session)
        tenants = await repo.list_with_active_leases()
        result = []
        for t in tenants:
            active = next((l for l in t.leases if l.status.value == "active"), None)
            tenant_data: dict[str, object] = {
                "id": t.id,
                "name": t.name,
                "email": t.email,
                "phone": t.phone,
            }
            if active:
                tenant_data["active_lease"] = {
                    "lease_id": active.id,
                    "unit": active.unit.label if active.unit else "N/A",
                    "rent_amount": float(active.rent_amount),
                    "start_date": str(active.start_date),
                    "end_date": str(active.end_date),
                }
            result.append(tenant_data)
        return _json(result)


@tool
async def get_leases(property_id: int | None = None) -> str:
    """List active leases, optionally filtered by property ID.

    Args:
        property_id: Optional property ID to filter by. Pass None for all properties.

    Use this to see current lease agreements, check rent amounts, or find lease dates.
    """
    async with async_session_factory() as session:
        repo = LeaseRepository(session)
        leases = await repo.list_active(property_id=property_id)
        result = [
            {
                "id": l.id,
                "tenant": l.tenant.name if l.tenant else "N/A",
                "unit": l.unit.label if l.unit else "N/A",
                "rent_amount": float(l.rent_amount),
                "start_date": str(l.start_date),
                "end_date": str(l.end_date),
                "status": l.status.value,
            }
            for l in leases
        ]
        return _json(result)


@tool
async def get_overdue_charges() -> str:
    """List all overdue charges with tenant and lease details.

    Use this to find who owes money, how much is overdue, and for which period.
    """
    async with async_session_factory() as session:
        repo = ChargeRepository(session)
        charges = await repo.get_overdue()
        result = [
            {
                "id": c.id,
                "tenant": c.lease.tenant.name if c.lease and c.lease.tenant else "N/A",
                "tenant_id": c.lease.tenant_id if c.lease else None,
                "period_month": c.period_month,
                "amount_due": float(c.amount_due),
                "amount_paid": float(c.amount_paid),
                "outstanding": float(c.amount_due - c.amount_paid),
                "due_date": str(c.due_date),
                "kind": c.kind.value,
            }
            for c in charges
        ]
        return _json(result)
