"""API endpoints for social sentiment data."""

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Query
from sqlalchemy import func, select

from src.core.database import async_session_factory
from src.core.models.social_sentiment import SocialSentiment

router = APIRouter(prefix="/api/sentiment", tags=["sentiment"])


@router.get("/social")
async def list_social_sentiment(
    ticker: str | None = None,
    platform: str | None = None,
    days: int = Query(default=7, le=30),
    limit: int = Query(default=50, le=200),
):
    """Get recent social sentiment posts."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    query = select(SocialSentiment).where(SocialSentiment.posted_at >= cutoff)

    if ticker:
        query = query.where(SocialSentiment.ticker == ticker.upper())
    if platform:
        query = query.where(SocialSentiment.platform == platform)

    query = query.order_by(SocialSentiment.posted_at.desc()).limit(limit)

    async with async_session_factory() as session:
        result = await session.execute(query)
        posts = result.scalars().all()

    return [
        {
            "id": str(p.id),
            "ticker": p.ticker,
            "platform": p.platform,
            "post_title": p.post_title,
            "post_score": p.post_score,
            "subreddit": p.subreddit,
            "sentiment_score": p.sentiment_score,
            "sentiment_label": p.sentiment_label,
            "tickers": p.tickers,
            "posted_at": p.posted_at.isoformat(),
        }
        for p in posts
    ]


@router.get("/social/summary")
async def sentiment_summary(
    ticker: str,
    days: int = Query(default=7, le=30),
):
    """Aggregated sentiment summary for a ticker."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    ticker = ticker.upper()

    async with async_session_factory() as session:
        result = await session.execute(
            select(
                func.count(SocialSentiment.id),
                func.avg(SocialSentiment.sentiment_score),
                func.sum(SocialSentiment.post_score),
            ).where(
                SocialSentiment.ticker == ticker,
                SocialSentiment.posted_at >= cutoff,
            )
        )
        row = result.one()

    return {
        "ticker": ticker,
        "days": days,
        "post_count": row[0] or 0,
        "avg_sentiment": round(row[1], 4) if row[1] is not None else 0.0,
        "total_score": row[2] or 0,
    }
