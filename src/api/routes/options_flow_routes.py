"""API endpoints for options flow data (from Unusual Whales)."""

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Query
from sqlalchemy import select

from src.core.database import async_session_factory
from src.core.models.article import Article

router = APIRouter(prefix="/api/options-flow", tags=["options-flow"])


@router.get("")
async def list_options_flow(
    ticker: str | None = None,
    days: int = Query(default=7, le=30),
    limit: int = Query(default=50, le=200),
):
    """Get recent options flow articles from Unusual Whales."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    query = select(Article).where(
        Article.source == "unusual_whales",
        Article.published_at >= cutoff,
    )

    if ticker:
        query = query.where(Article.tickers.contains([ticker.upper()]))

    query = query.order_by(Article.published_at.desc()).limit(limit)

    async with async_session_factory() as session:
        result = await session.execute(query)
        articles = result.scalars().all()

    return [
        {
            "id": str(a.id),
            "headline": a.headline,
            "tickers": a.tickers,
            "published_at": a.published_at.isoformat(),
            "raw_data": a.raw_data,
        }
        for a in articles
    ]
