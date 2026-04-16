"""Article query endpoints — filter by ticker, date, sentiment, source."""

from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_db
from src.core.models.article import Article
from src.core.schemas.article_schema import (
    ArticleResponse,
    ArticleStats,
    HourlyBucket,
    SentimentTrendPoint,
    TopTicker,
)

router = APIRouter(prefix="/api/articles", tags=["articles"])


@router.get("", response_model=list[ArticleResponse])
async def list_articles(
    ticker: str | None = None,
    source: str | None = None,
    sentiment_gte: float | None = Query(None, ge=-1.0, le=1.0),
    sentiment_lte: float | None = Query(None, ge=-1.0, le=1.0),
    market_cap_gte: float | None = Query(None, ge=0),
    market_cap_lte: float | None = Query(None, ge=0),
    category: str | None = None,
    from_date: datetime | None = None,
    to_date: datetime | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """List articles with optional filters."""
    query = select(Article).order_by(Article.published_at.desc(), Article.id.desc())

    if ticker:
        query = query.where(Article.tickers.any(ticker.upper()))
    if source:
        query = query.where(Article.source == source)
    if sentiment_gte is not None:
        query = query.where(Article.sentiment >= sentiment_gte)
    if sentiment_lte is not None:
        query = query.where(Article.sentiment <= sentiment_lte)
    if market_cap_gte is not None:
        query = query.where(Article.market_cap >= market_cap_gte)
    if market_cap_lte is not None:
        query = query.where(Article.market_cap <= market_cap_lte)
    if category:
        query = query.where(Article.category == category)
    if from_date:
        query = query.where(Article.published_at >= from_date)
    if to_date:
        query = query.where(Article.published_at <= to_date)

    query = query.offset(offset).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/latest", response_model=list[ArticleResponse])
async def latest_articles(
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    """Get the most recent articles."""
    result = await db.execute(
        select(Article).order_by(Article.published_at.desc()).limit(limit)
    )
    return result.scalars().all()


@router.get("/stats", response_model=ArticleStats)
async def article_stats(db: AsyncSession = Depends(get_db)):
    """Get aggregated article statistics."""
    total = await db.scalar(select(func.count(Article.id)))
    avg_sent = await db.scalar(select(func.avg(Article.sentiment)))

    # Count by source
    source_counts = await db.execute(
        select(Article.source, func.count(Article.id)).group_by(Article.source)
    )
    by_source = {row[0]: row[1] for row in source_counts.all()}

    # Today's count
    from datetime import date, timezone
    today_start = datetime.combine(date.today(), datetime.min.time()).replace(tzinfo=timezone.utc)
    today_count = await db.scalar(
        select(func.count(Article.id)).where(Article.published_at >= today_start)
    )

    return ArticleStats(
        total_count=total or 0,
        by_source=by_source,
        avg_sentiment=round(avg_sent, 3) if avg_sent else None,
        articles_today=today_count or 0,
    )


@router.get("/sentiment-trend", response_model=list[SentimentTrendPoint])
async def sentiment_trend(
    days: int = Query(7, ge=1, le=30),
    db: AsyncSession = Depends(get_db),
):
    """Hourly average sentiment over the last N days."""
    rows = await db.execute(
        text(
            "SELECT date_trunc('hour', published_at) AS ts, "
            "avg(sentiment) AS avg_s, count(*) AS cnt "
            "FROM articles "
            "WHERE published_at >= now() - make_interval(days => :days) "
            "GROUP BY ts ORDER BY ts"
        ).bindparams(days=days)
    )
    return [
        SentimentTrendPoint(timestamp=r.ts, avg_sentiment=round(r.avg_s, 4), count=r.cnt)
        for r in rows.all()
        if r.avg_s is not None
    ]


@router.get("/top-tickers", response_model=list[TopTicker])
async def top_tickers(
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    """Most-mentioned tickers with average sentiment."""
    rows = await db.execute(
        text(
            "SELECT unnest(tickers) AS symbol, count(*) AS cnt, avg(sentiment) AS avg_s "
            "FROM articles "
            "GROUP BY symbol ORDER BY cnt DESC LIMIT :limit"
        ).bindparams(limit=limit)
    )
    return [
        TopTicker(
            symbol=r.symbol,
            count=r.cnt,
            avg_sentiment=round(r.avg_s, 4) if r.avg_s is not None else None,
        )
        for r in rows.all()
    ]


@router.get("/by-hour", response_model=list[HourlyBucket])
async def articles_by_hour(
    hours: int = Query(24, ge=1, le=168),
    db: AsyncSession = Depends(get_db),
):
    """Article counts bucketed by hour for the last N hours."""
    rows = await db.execute(
        text(
            "SELECT date_trunc('hour', published_at) AS hour, count(*) AS cnt "
            "FROM articles "
            "WHERE published_at >= now() - make_interval(hours => :hours) "
            "GROUP BY hour ORDER BY hour"
        ).bindparams(hours=hours)
    )
    return [HourlyBucket(hour=r.hour, count=r.cnt) for r in rows.all()]
