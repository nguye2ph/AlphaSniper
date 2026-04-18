"""Auto-tuning engine: EMA threshold rules, circuit breaker, cooldown."""

from datetime import datetime, timezone

import redis.asyncio as aioredis
import structlog

from src.scheduler import config_manager, metrics_tracker
from src.scheduler.models import AdjustmentResult, SourceMetrics, SourceScheduleConfig

logger = structlog.get_logger()


def _clamp(value: int, lo: int, hi: int) -> int:
    return max(lo, min(hi, value))


def evaluate(config: SourceScheduleConfig, metrics: SourceMetrics) -> AdjustmentResult:
    """Evaluate a single source and decide adjustment action.

    Rules applied in order:
    1. Cooldown check — skip if adjusted too recently
    2. Circuit breaker — rate-limit errors >= threshold -> 2x interval
    3. EMA high — articles above threshold -> decrease interval (poll faster)
    4. EMA low — articles below threshold -> increase interval (poll slower)
    5. No change
    """
    old_interval = config.current_interval_seconds
    now = datetime.now(timezone.utc)

    # 1. Cooldown check
    if config.last_adjustment_at:
        elapsed = (now - config.last_adjustment_at).total_seconds()
        if elapsed < config.adjustment_cooldown_seconds:
            return AdjustmentResult(
                source_name=config.name,
                action="cooldown_skip",
                old_interval=old_interval,
                new_interval=old_interval,
                reason=f"Cooldown active ({int(elapsed)}s / {config.adjustment_cooldown_seconds}s)",
            )

    # 2. Circuit breaker — too many rate-limit errors
    if metrics.rate_limit_errors >= config.max_rate_errors:
        new_interval = _clamp(old_interval * 2, config.min_interval_seconds, config.max_interval_seconds)
        return AdjustmentResult(
            source_name=config.name,
            action="circuit_break",
            old_interval=old_interval,
            new_interval=new_interval,
            reason=f"Circuit breaker: {metrics.rate_limit_errors} rate-limit errors",
        )

    # 3. EMA above high threshold -> poll faster (decrease interval)
    if metrics.ema > config.articles_per_poll_high:
        # Reduce by 25%, clamped to min
        new_interval = _clamp(int(old_interval * 0.75), config.min_interval_seconds, config.max_interval_seconds)
        if new_interval < old_interval:
            return AdjustmentResult(
                source_name=config.name,
                action="decrease",
                old_interval=old_interval,
                new_interval=new_interval,
                reason=f"EMA {metrics.ema:.1f} > high threshold {config.articles_per_poll_high}",
            )

    # 4. EMA below low threshold -> poll slower (increase interval)
    if metrics.ema < config.articles_per_poll_low:
        # Increase by 50%, clamped to max
        new_interval = _clamp(int(old_interval * 1.5), config.min_interval_seconds, config.max_interval_seconds)
        if new_interval > old_interval:
            return AdjustmentResult(
                source_name=config.name,
                action="increase",
                old_interval=old_interval,
                new_interval=new_interval,
                reason=f"EMA {metrics.ema:.1f} < low threshold {config.articles_per_poll_low}",
            )

    # 5. No change needed
    return AdjustmentResult(
        source_name=config.name,
        action="no_change",
        old_interval=old_interval,
        new_interval=old_interval,
        reason="Within normal range",
    )


async def apply_adjustments(redis: aioredis.Redis) -> list[AdjustmentResult]:
    """Evaluate and apply adjustments for all enabled rate_based sources.

    Called by the hourly Taskiq task.
    """
    configs = await config_manager.list_configs(redis)
    results: list[AdjustmentResult] = []

    for cfg in configs:
        if not cfg.enabled or cfg.strategy != "rate_based":
            continue

        metrics = await metrics_tracker.get_metrics(redis, cfg.name)
        result = evaluate(cfg, metrics)
        results.append(result)

        if result.action in ("decrease", "increase", "circuit_break"):
            cfg.current_interval_seconds = result.new_interval
            cfg.last_adjustment_at = datetime.now(timezone.utc)
            await config_manager.set_config(redis, cfg)
            logger.info(
                "schedule_adjusted",
                source=cfg.name,
                action=result.action,
                old=result.old_interval,
                new=result.new_interval,
                reason=result.reason,
            )

    return results
