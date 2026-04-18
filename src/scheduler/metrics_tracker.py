"""Per-poll metrics tracking with EMA calculation, stored in Redis hashes."""

from datetime import datetime, timezone

import redis.asyncio as aioredis
import structlog

from src.scheduler.models import SourceMetrics

logger = structlog.get_logger()

METRICS_PREFIX = "scheduler:metrics"


def _key(source_name: str) -> str:
    return f"{METRICS_PREFIX}:{source_name}"


def compute_ema(current_value: float, previous_ema: float, alpha: float) -> float:
    """Exponential Moving Average: EMA = alpha * current + (1-alpha) * previous."""
    return alpha * current_value + (1.0 - alpha) * previous_ema


async def record_poll(
    redis: aioredis.Redis,
    source_name: str,
    articles_count: int,
    had_error: bool = False,
    is_rate_limit: bool = False,
    ema_alpha: float = 0.3,
) -> SourceMetrics:
    """Record a poll result and update metrics atomically.

    Args:
        redis: Redis client
        source_name: Collector source name
        articles_count: Number of articles found in this poll
        had_error: Whether the poll had an API error
        is_rate_limit: Whether the error was a rate-limit (429)
        ema_alpha: EMA smoothing factor from source config
    """
    key = _key(source_name)
    now = datetime.now(timezone.utc)

    # Get current metrics
    raw = await redis.hgetall(key)
    prev_ema = float(raw.get("ema", "0.0"))
    total_polls = int(raw.get("total_polls", "0"))
    empty_count = int(raw.get("empty_responses_count", "0"))
    api_errors = int(raw.get("api_errors_last_hour", "0"))
    rate_errors = int(raw.get("rate_limit_errors", "0"))

    # Update EMA
    new_ema = compute_ema(float(articles_count), prev_ema, ema_alpha)

    # Build update
    updates = {
        "ema": str(round(new_ema, 4)),
        "articles_last_hour": str(articles_count),
        "total_polls": str(total_polls + 1),
        "last_poll_at": now.isoformat(),
    }

    if articles_count == 0:
        updates["empty_responses_count"] = str(empty_count + 1)
    else:
        # Reset empty count on success
        updates["empty_responses_count"] = "0"

    if had_error:
        updates["api_errors_last_hour"] = str(api_errors + 1)
        if is_rate_limit:
            updates["rate_limit_errors"] = str(rate_errors + 1)
    else:
        # Reset error counters on clean poll
        updates["api_errors_last_hour"] = "0"
        updates["rate_limit_errors"] = "0"

    await redis.hset(key, mapping=updates)
    # Expire metrics after 24h to auto-cleanup stale sources
    await redis.expire(key, 86400)

    metrics = SourceMetrics(
        articles_last_hour=articles_count,
        ema=new_ema,
        empty_responses_count=int(updates["empty_responses_count"]),
        api_errors_last_hour=int(updates["api_errors_last_hour"]),
        rate_limit_errors=int(updates.get("rate_limit_errors", "0")),
        last_poll_at=now,
        total_polls=total_polls + 1,
    )
    logger.debug("metrics_recorded", source=source_name, ema=round(new_ema, 2), articles=articles_count)
    return metrics


async def get_metrics(redis: aioredis.Redis, source_name: str) -> SourceMetrics:
    """Get current metrics for a source."""
    raw = await redis.hgetall(_key(source_name))
    if not raw:
        return SourceMetrics()
    last_poll = raw.get("last_poll_at")
    return SourceMetrics(
        articles_last_hour=int(raw.get("articles_last_hour", "0")),
        ema=float(raw.get("ema", "0.0")),
        empty_responses_count=int(raw.get("empty_responses_count", "0")),
        api_errors_last_hour=int(raw.get("api_errors_last_hour", "0")),
        rate_limit_errors=int(raw.get("rate_limit_errors", "0")),
        last_poll_at=datetime.fromisoformat(last_poll) if last_poll else None,
        total_polls=int(raw.get("total_polls", "0")),
    )


async def reset_metrics(redis: aioredis.Redis, source_name: str) -> None:
    """Reset all metrics for a source."""
    await redis.delete(_key(source_name))
