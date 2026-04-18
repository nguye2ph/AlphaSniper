"""Sentiment heatmap endpoint — per-ticker sentiment aggregation for last 7 days."""

import json

import structlog
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_db
from src.core.database import get_redis

logger = structlog.get_logger()
router = APIRouter(prefix="/api/sentiment", tags=["sentiment"])


class HeatmapCell(BaseModel):
    ticker: str
    sentiment_avg: float
    mention_count: int
    health_score: int | None = None


@router.get("/heatmap", response_model=list[HeatmapCell])
async def sentiment_heatmap(
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    """Aggregate article sentiment by ticker over last 7 days, sorted by mention count."""
    rows = await db.execute(
        text(
            "SELECT unnest(tickers) AS ticker, "
            "avg(sentiment) AS sentiment_avg, "
            "count(*) AS mention_count "
            "FROM articles "
            "WHERE published_at >= now() - interval '7 days' "
            "AND sentiment IS NOT NULL "
            "GROUP BY ticker "
            "ORDER BY mention_count DESC "
            "LIMIT :limit"
        ).bindparams(limit=limit)
    )
    records = rows.all()

    if not records:
        return []

    # Fetch health scores from Redis cache in bulk
    redis = await get_redis()
    cells = []
    for r in records:
        health_score = None
        try:
            cached = await redis.get(f"ticker:health:{r.ticker}")
            if cached:
                data = json.loads(cached)
                # health score stored as int field in the JSON blob
                health_score = data.get("health_score") or data.get("score")
                if health_score is not None:
                    health_score = int(health_score)
        except Exception as e:
            logger.debug("health_score_cache_miss", ticker=r.ticker, error=str(e)[:60])

        cells.append(
            HeatmapCell(
                ticker=r.ticker,
                sentiment_avg=round(float(r.sentiment_avg), 4),
                mention_count=int(r.mention_count),
                health_score=health_score,
            )
        )

    return cells
