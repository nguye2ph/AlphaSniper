"""Auto-tuning engine: EMA threshold rules, circuit breaker, cooldown."""

from datetime import datetime, timezone

import redis.asyncio as aioredis
import structlog

from src.scheduler import config_manager, market_calendar, metrics_tracker
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

    # 0. Market calendar check — park at max_interval when market is closed
    if config.trading_hours_only and not market_calendar.is_market_open():
        phase = market_calendar.get_market_phase()
        return AdjustmentResult(
            source_name=config.name,
            action="market_closed",
            old_interval=old_interval,
            new_interval=config.max_interval_seconds,
            reason=f"Market closed (phase={phase}), trading_hours_only=True",
        )

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
    from src.core.config import settings

    configs = await config_manager.list_configs(redis)
    results: list[AdjustmentResult] = []
    # Track per-source metrics for optional LLM pass
    source_metrics_map: dict[str, SourceMetrics] = {}

    for cfg in configs:
        if not cfg.enabled or cfg.strategy != "rate_based":
            continue

        metrics = await metrics_tracker.get_metrics(redis, cfg.name)
        source_metrics_map[cfg.name] = metrics
        result = evaluate(cfg, metrics)
        results.append(result)

        if result.action in ("decrease", "increase", "circuit_break", "market_closed"):
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

    # Optional LLM advisor pass — only if enabled and not all sources are in cooldown/closed
    if settings.llm_advisor_enabled:
        try:
            from src.scheduler import llm_advisor

            # Build metrics payload for LLM
            cfg_map = {cfg.name: cfg for cfg in configs if cfg.enabled and cfg.strategy == "rate_based"}
            llm_sources = [
                {
                    "name": name,
                    "ema": source_metrics_map[name].ema,
                    "articles_per_poll_high": cfg_map[name].articles_per_poll_high,
                    "articles_per_poll_low": cfg_map[name].articles_per_poll_low,
                    "current_interval": cfg_map[name].current_interval_seconds,
                    "min_interval": cfg_map[name].min_interval_seconds,
                    "max_interval": cfg_map[name].max_interval_seconds,
                    "rate_limit_errors": source_metrics_map[name].rate_limit_errors,
                    "empty_responses_count": source_metrics_map[name].empty_responses_count,
                }
                for name in source_metrics_map
                if name in cfg_map
            ]

            recommendations = await llm_advisor.get_recommendations(llm_sources)

            for rec in recommendations:
                if rec.source not in cfg_map:
                    continue
                cfg = cfg_map[rec.source]
                # Find the rule-based result for this source
                rule_result = next((r for r in results if r.source_name == rec.source), None)
                rule_action = rule_result.action if rule_result else "no_change"

                # Only apply if LLM suggests a different action and interval is within bounds
                new_iv = _clamp(rec.new_interval, cfg.min_interval_seconds, cfg.max_interval_seconds)
                if rec.action != rule_action and new_iv != cfg.current_interval_seconds:
                    logger.info(
                        "llm_advisor_override",
                        source=rec.source,
                        rule_action=rule_action,
                        llm_action=rec.action,
                        new_interval=new_iv,
                        confidence=rec.confidence,
                        reason=rec.reason,
                    )
                    cfg.current_interval_seconds = new_iv
                    cfg.last_adjustment_at = datetime.now(timezone.utc)
                    await config_manager.set_config(redis, cfg)
                else:
                    logger.debug(
                        "llm_advisor_skipped",
                        source=rec.source,
                        llm_action=rec.action,
                        rule_action=rule_action,
                        confidence=rec.confidence,
                    )
        except Exception as e:
            logger.warning("llm_advisor_apply_error", error=str(e))

    return results
