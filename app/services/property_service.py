from sqlalchemy.ext.asyncio import AsyncSession

from app.models.unit import UnitStatus
from app.repositories.property_repo import PropertyRepository
from app.schemas.domain import PropertyResponse, UnitResponse


class PropertyService:
    """Business logic for property operations."""

    def __init__(self, session: AsyncSession) -> None:
        self._repo = PropertyRepository(session)

    async def list_properties(self, *, limit: int = 100, offset: int = 0) -> list[PropertyResponse]:
        properties = await self._repo.list_with_units(limit=limit, offset=offset)
        return [
            PropertyResponse(
                id=p.id,
                name=p.name,
                address=p.address,
                units=[
                    UnitResponse(
                        id=u.id,
                        label=u.label,
                        bedrooms=u.bedrooms,
                        monthly_rent=u.monthly_rent,
                        status=u.status.value,
                    )
                    for u in p.units
                ],
                total_units=len(p.units),
                occupied_units=sum(1 for u in p.units if u.status == UnitStatus.LEASED),
            )
            for p in properties
        ]
