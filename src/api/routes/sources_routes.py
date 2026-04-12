"""Data source status endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_db
from src.core.models.source import Source
from src.core.schemas.common_schema import SourceResponse

router = APIRouter(prefix="/api/sources", tags=["sources"])


@router.get("", response_model=list[SourceResponse])
async def list_sources(db: AsyncSession = Depends(get_db)):
    """List all data sources with their status."""
    result = await db.execute(select(Source).order_by(Source.name))
    return result.scalars().all()
