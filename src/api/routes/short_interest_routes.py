"""API endpoints for short interest data."""

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Query
from sqlalchemy import select

from src.core.database import async_session_factory
from src.core.models.short_interest import ShortInterest

router = APIRouter(prefix="/api/short-interest", tags=["short-interest"])


@router.get("")
async def list_short_interest(
    ticker: str | None = None,
    days: int = Query(default=30, le=90),
    limit: int = Query(default=50, le=200),
):
    """Get recent short interest snapshots."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    query = select(ShortInterest).where(ShortInterest.report_date >= cutoff)

    if ticker:
        query = query.where(ShortInterest.ticker == ticker.upper())

    query = query.order_by(ShortInterest.report_date.desc()).limit(limit)

    async with async_session_factory() as session:
        result = await session.execute(query)
        rows = result.scalars().all()

    return [
        {
            "id": str(r.id),
            "ticker": r.ticker,
            "short_pct_float": r.short_pct_float,
            "days_to_cover": r.days_to_cover,
            "borrow_fee_pct": r.borrow_fee_pct,
            "squeeze_score": r.squeeze_score,
            "report_date": r.report_date.isoformat(),
        }
        for r in rows
    ]
