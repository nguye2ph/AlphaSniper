"""Shared Pydantic schemas used across the application."""

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    service: str
    env: str


class TickerResponse(BaseModel):
    """Ticker data returned by API endpoints."""

    symbol: str
    name: str | None = None
    exchange: str | None = None
    market_cap: float | None = None
    sector: str | None = None
    is_active: bool = True

    model_config = {"from_attributes": True}


class SourceResponse(BaseModel):
    """Data source status response."""

    name: str
    source_type: str
    base_url: str
    is_active: bool
    article_count: int = 0

    model_config = {"from_attributes": True}
