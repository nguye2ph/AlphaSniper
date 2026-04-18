"""Pydantic schemas for adaptive scheduler configuration and metrics."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class SourceScheduleConfig(BaseModel):
    """Per-source scheduling configuration stored in Redis JSON."""

    name: str
    enabled: bool = True
    min_interval_seconds: int = Field(default=60, ge=10)
    max_interval_seconds: int = Field(default=3600, le=86400)
    current_interval_seconds: int = 300
    strategy: Literal["rate_based", "manual"] = "rate_based"
    # EMA tuning parameters
    ema_alpha: float = Field(default=0.3, ge=0.0, le=1.0)
    articles_per_poll_high: int = 50
    articles_per_poll_low: int = 5
    # Circuit breaker
    max_rate_errors: int = 5
    adjustment_cooldown_seconds: int = 300
    last_adjustment_at: datetime | None = None
    trading_hours_only: bool = False  # If True, use max_interval when market closed


class SourceMetrics(BaseModel):
    """Runtime metrics for a data source, stored in Redis hash."""

    articles_last_hour: int = 0
    ema: float = 0.0
    empty_responses_count: int = 0
    api_errors_last_hour: int = 0
    rate_limit_errors: int = 0
    last_poll_at: datetime | None = None
    total_polls: int = 0


class AdjustmentResult(BaseModel):
    """Result of an adjustment evaluation for a source."""

    source_name: str
    action: Literal["decrease", "increase", "circuit_break", "cooldown_skip", "no_change", "market_closed"]
    old_interval: int
    new_interval: int
    reason: str
