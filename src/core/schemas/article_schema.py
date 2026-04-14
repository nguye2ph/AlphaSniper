"""Pydantic schemas for Article API input/output."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ArticleResponse(BaseModel):
    """Article data returned by API endpoints."""

    id: UUID
    source: str
    source_id: str
    headline: str
    summary: str | None = None
    url: str
    published_at: datetime
    tickers: list[str] = []
    sentiment: float | None = None
    sentiment_label: str | None = None
    market_cap: float | None = None
    category: str | None = None
    content: str | None = None
    key_points: list[str] | None = None
    image_url: str | None = None
    author: str | None = None

    model_config = {"from_attributes": True}


class ArticleListParams(BaseModel):
    """Query parameters for listing articles."""

    ticker: str | None = None
    source: str | None = None
    sentiment_gte: float | None = Field(None, ge=-1.0, le=1.0)
    sentiment_lte: float | None = Field(None, ge=-1.0, le=1.0)
    category: str | None = None
    from_date: datetime | None = None
    to_date: datetime | None = None
    limit: int = Field(50, ge=1, le=200)
    offset: int = Field(0, ge=0)


class ArticleStats(BaseModel):
    """Aggregated article statistics."""

    total_count: int
    by_source: dict[str, int] = {}
    avg_sentiment: float | None = None
    articles_today: int = 0


class SentimentTrendPoint(BaseModel):
    """Single time-bucketed sentiment data point."""

    timestamp: datetime
    avg_sentiment: float
    count: int


class TopTicker(BaseModel):
    """Ticker ranked by article volume."""

    symbol: str
    count: int
    avg_sentiment: float | None = None


class HourlyBucket(BaseModel):
    """Article count for a single hour bucket."""

    hour: datetime
    count: int


class TickerSentimentPoint(BaseModel):
    """Single article sentiment data point for a ticker."""

    timestamp: datetime
    sentiment: float | None
    headline: str
