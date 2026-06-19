from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.models.property import Property
from app.models.unit import Unit, UnitStatus
from app.repositories.base import BaseRepository


class PropertyRepository(BaseRepository[Property]):
    model = Property

    async def list_with_units(self, *, limit: int = 100, offset: int = 0) -> list[Property]:
        """List properties with eagerly loaded units to avoid N+1."""
        stmt = (
            select(Property)
            .options(selectinload(Property.units))
            .limit(limit)
            .offset(offset)
            .order_by(Property.id)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().unique().all())

    async def get_occupancy_summary(self) -> list[dict[str, object]]:
        """Per-property occupancy stats using a single aggregated query."""
        stmt = (
            select(
                Property.id,
                Property.name,
                func.count(Unit.id).label("total_units"),
                func.count(Unit.id).filter(Unit.status == UnitStatus.LEASED).label("occupied_units"),
            )
            .outerjoin(Unit, Unit.property_id == Property.id)
            .group_by(Property.id, Property.name)
            .order_by(Property.id)
        )
        result = await self._session.execute(stmt)
        return [dict(row._mapping) for row in result.all()]
