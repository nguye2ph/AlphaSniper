"""API endpoints for earnings calendar events."""

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Query
from sqlalchemy import select

from src.core.database import async_session_factory
from src.core.models.earnings_event import EarningsEvent

router = APIRouter(prefix="/api/earnings", tags=["earnings"])


@router.get("")
async def list_earnings(
    ticker: str | None = None,
    days: int = Query(default=14, le=90),
    limit: int = Query(default=50, le=200),
):
    """Get upcoming/recent earnings events."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    query = select(EarningsEvent).where(EarningsEvent.report_date >= cutoff)

    if ticker:
        query = query.where(EarningsEvent.ticker == ticker.upper())

    query = query.order_by(EarningsEvent.report_date.asc()).limit(limit)

    async with async_session_factory() as session:
        result = await session.execute(query)
        events = result.scalars().all()

    return [
        {
            "id": str(e.id),
            "ticker": e.ticker,
            "report_date": e.report_date.isoformat(),
            "estimated_eps": e.estimated_eps,
            "actual_eps": e.actual_eps,
            "estimated_revenue": e.estimated_revenue,
            "actual_revenue": e.actual_revenue,
            "surprise_pct": e.surprise_pct,
        }
        for e in events
    ]
