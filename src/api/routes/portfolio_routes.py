"""Portfolio stats endpoint — 24h article summary, top movers, earnings, short interest."""

from datetime import datetime, timedelta, timezone

import structlog
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_db
from src.core.models.article import Article
from src.core.models.earnings_event import EarningsEvent

logger = structlog.get_logger()
router = APIRouter(prefix="/api/portfolio", tags=["portfolio"])

_HIGH_SHORT_INTEREST_THRESHOLD = 20.0  # percent


class PortfolioStats(BaseModel):
    total_articles_24h: int
    avg_sentiment: float | None
    top_movers: list[dict]  # top 5 tickers by mention count with avg sentiment
    upcoming_earnings: int
    high_short_interest_count: int


@router.get("/stats", response_model=PortfolioStats)
async def portfolio_stats(db: AsyncSession = Depends(get_db)):
    """Aggregate portfolio-level stats: articles 24h, sentiment, movers, earnings, SI."""
    now = datetime.now(timezone.utc)
    cutoff_24h = now - timedelta(hours=24)
    cutoff_7d = now - timedelta(days=7)

    # Total articles in last 24h
    total_24h = await db.scalar(
        select(func.count(Article.id)).where(Article.published_at >= cutoff_24h)
    )

    # Avg sentiment last 24h
    avg_sent = await db.scalar(
        select(func.avg(Article.sentiment)).where(Article.published_at >= cutoff_24h)
    )

    # Top 5 tickers by mention count (last 24h) with avg sentiment
    movers_result = await db.execute(
        text(
            "SELECT unnest(tickers) AS ticker, "
            "count(*) AS cnt, avg(sentiment) AS avg_s "
            "FROM articles "
            "WHERE published_at >= :cutoff "
            "GROUP BY ticker "
            "ORDER BY cnt DESC "
            "LIMIT 5"
        ).bindparams(cutoff=cutoff_24h)
    )
    top_movers = [
        {
            "ticker": r.ticker,
            "mention_count": int(r.cnt),
            "avg_sentiment": round(float(r.avg_s), 4) if r.avg_s is not None else None,
        }
        for r in movers_result.all()
    ]

    # Upcoming earnings in next 7 days
    upcoming_earnings = await db.scalar(
        select(func.count(EarningsEvent.id)).where(
            EarningsEvent.report_date >= now,
            EarningsEvent.report_date <= cutoff_7d + timedelta(days=14),
        )
    )

    # Tickers with short interest > threshold (latest record per ticker)
    high_si_result = await db.execute(
        text(
            "SELECT COUNT(DISTINCT ticker) FROM short_interests "
            "WHERE short_pct_float > :threshold"
        ).bindparams(threshold=_HIGH_SHORT_INTEREST_THRESHOLD)
    )
    high_si_count = high_si_result.scalar() or 0

    return PortfolioStats(
        total_articles_24h=total_24h or 0,
        avg_sentiment=round(float(avg_sent), 4) if avg_sent is not None else None,
        top_movers=top_movers,
        upcoming_earnings=upcoming_earnings or 0,
        high_short_interest_count=int(high_si_count),
    )
