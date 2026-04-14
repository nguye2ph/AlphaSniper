"""Ticker endpoints — watchlist management and per-ticker news."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_db
from src.core.models.article import Article
from src.core.models.ticker import Ticker
from src.core.schemas.article_schema import ArticleResponse, TickerSentimentPoint
from src.core.schemas.common_schema import TickerResponse

router = APIRouter(prefix="/api/tickers", tags=["tickers"])


@router.get("", response_model=list[TickerResponse])
async def list_tickers(db: AsyncSession = Depends(get_db)):
    """List all tracked ticker symbols."""
    result = await db.execute(select(Ticker).order_by(Ticker.symbol))
    return result.scalars().all()


@router.get("/{symbol}/sentiment-history", response_model=list[TickerSentimentPoint])
async def ticker_sentiment_history(
    symbol: str,
    days: int = Query(7, ge=1, le=90),
    db: AsyncSession = Depends(get_db),
):
    """Per-article sentiment history for a ticker over the last N days."""
    rows = await db.execute(
        text(
            "SELECT published_at, sentiment, headline FROM articles "
            "WHERE tickers @> ARRAY[:symbol]::varchar[] "
            "AND published_at >= now() - make_interval(days => :days) "
            "ORDER BY published_at"
        ).bindparams(symbol=symbol.upper(), days=days)
    )
    return [
        TickerSentimentPoint(timestamp=r.published_at, sentiment=r.sentiment, headline=r.headline)
        for r in rows.all()
    ]


@router.get("/{symbol}/news", response_model=list[ArticleResponse])
async def ticker_news(symbol: str, limit: int = 20, db: AsyncSession = Depends(get_db)):
    """Get latest news articles for a specific ticker."""
    result = await db.execute(
        select(Article)
        .where(Article.tickers.any(symbol.upper()))
        .order_by(Article.published_at.desc())
        .limit(limit)
    )
    return result.scalars().all()
