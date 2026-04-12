"""Ticker endpoints — watchlist management and per-ticker news."""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_db
from src.core.models.article import Article
from src.core.models.ticker import Ticker
from src.core.schemas.article_schema import ArticleResponse
from src.core.schemas.common_schema import TickerResponse

router = APIRouter(prefix="/api/tickers", tags=["tickers"])


@router.get("", response_model=list[TickerResponse])
async def list_tickers(db: AsyncSession = Depends(get_db)):
    """List all tracked ticker symbols."""
    result = await db.execute(select(Ticker).order_by(Ticker.symbol))
    return result.scalars().all()


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
