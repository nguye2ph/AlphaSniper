"""Ticker health score endpoints — composite score from all data sources."""

import json

import redis.asyncio as aioredis
import structlog
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_db
from src.core.config import settings
from src.parsers.ticker_health_score import TickerHealth, compute_health_score

logger = structlog.get_logger()

router = APIRouter(prefix="/api/ticker", tags=["ticker-health"])

_CACHE_TTL = 3600  # 1 hour


@router.get("/{symbol}/health", response_model=TickerHealth)
async def get_ticker_health(
    symbol: str,
    session: AsyncSession = Depends(get_db),
):
    """Get composite health score for a ticker (cached 1h in Redis)."""
    symbol = symbol.upper()
    cache_key = f"ticker:health:{symbol}"

    redis = aioredis.from_url(settings.redis_url, decode_responses=True)
    try:
        cached = await redis.get(cache_key)
        if cached:
            logger.info("ticker_health_cache_hit", ticker=symbol)
            return TickerHealth(**json.loads(cached))

        health = await compute_health_score(symbol, session)
        await redis.set(cache_key, health.model_dump_json(), ex=_CACHE_TTL)
        logger.info("ticker_health_computed", ticker=symbol, score=health.score)
        return health
    finally:
        await redis.aclose()
