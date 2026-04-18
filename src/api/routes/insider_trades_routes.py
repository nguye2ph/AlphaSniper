"""API endpoints for insider trade data."""

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Query
from sqlalchemy import select

from src.core.database import async_session_factory
from src.core.models.insider_trade import InsiderTrade

router = APIRouter(prefix="/api/insider-trades", tags=["insider-trades"])


@router.get("")
async def list_insider_trades(
    ticker: str | None = None,
    transaction_type: str | None = None,
    days: int = Query(default=7, le=90),
    limit: int = Query(default=50, le=200),
):
    """Get recent insider trades, optionally filtered by ticker or type."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    query = select(InsiderTrade).where(InsiderTrade.filing_date >= cutoff)

    if ticker:
        query = query.where(InsiderTrade.ticker == ticker.upper())
    if transaction_type:
        query = query.where(InsiderTrade.transaction_type == transaction_type)

    query = query.order_by(InsiderTrade.filing_date.desc()).limit(limit)

    async with async_session_factory() as session:
        result = await session.execute(query)
        trades = result.scalars().all()

    return [
        {
            "id": str(t.id),
            "ticker": t.ticker,
            "officer_name": t.officer_name,
            "officer_title": t.officer_title,
            "transaction_type": t.transaction_type,
            "shares": t.shares,
            "price": t.price,
            "value": t.value,
            "filing_date": t.filing_date.isoformat(),
        }
        for t in trades
    ]
