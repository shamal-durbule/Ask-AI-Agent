from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import get_workspace_id
from app.schemas.domain import PropertyResponse
from app.services.property_service import PropertyService

router = APIRouter(prefix="/api/properties", tags=["properties"])


@router.get("", response_model=list[PropertyResponse])
async def list_properties(
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    workspace_id: str = Depends(get_workspace_id),
) -> list[PropertyResponse]:
    """List all properties with their units and occupancy info."""
    service = PropertyService(db)
    return await service.list_properties(limit=limit, offset=offset)
