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
