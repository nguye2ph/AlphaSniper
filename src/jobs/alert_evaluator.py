"""Alert evaluation engine — evaluate active rules and trigger Discord notifications."""

import operator
from datetime import datetime, timedelta, timezone

import structlog
from sqlalchemy import select, text

from src.core.database import async_session_factory

logger = structlog.get_logger()

# Supported comparison operators for conditions
_OPS = {
    ">": operator.gt,
    ">=": operator.ge,
    "<": operator.lt,
    "<=": operator.le,
    "==": operator.eq,
    "!=": operator.ne,
}

# Table + field mapping for supported condition sources
_SOURCE_QUERY = {
    "insider_trade": (
        "SELECT {field} FROM insider_trades "
        "WHERE collected_at >= now() - interval '1 hour'"
    ),
    "article": (
        "SELECT {field} FROM articles "
        "WHERE collected_at >= now() - interval '1 hour'"
    ),
    "short_interest": (
        "SELECT {field} FROM short_interests "
        "WHERE collected_at >= now() - interval '1 hour'"
    ),
    "earnings_event": (
        "SELECT {field} FROM earnings_events "
        "WHERE collected_at >= now() - interval '1 hour'"
    ),
}

# Whitelist of allowed field names to prevent SQL injection
_ALLOWED_FIELDS = {
    "insider_trade": {"value", "shares", "short_pct_float"},
    "article": {"sentiment", "market_cap"},
    "short_interest": {"short_pct_float", "days_to_cover", "squeeze_score"},
    "earnings_event": {"surprise_pct", "actual_eps", "estimated_eps"},
}


async def _condition_matches(condition: dict, session) -> bool:
    """Return True if any recent row satisfies the condition."""
    source = condition.get("source", "")
    field = condition.get("field", "")
    op_str = condition.get("op", ">")
    threshold = condition.get("value")

    if source not in _SOURCE_QUERY:
        logger.warning("alert_unknown_source", source=source)
        return False

    # Guard against SQL injection via field name
    allowed = _ALLOWED_FIELDS.get(source, set())
    if field not in allowed:
        logger.warning("alert_field_not_allowed", source=source, field=field)
        return False

    op_fn = _OPS.get(op_str)
    if op_fn is None:
        logger.warning("alert_unknown_op", op=op_str)
        return False

    sql = _SOURCE_QUERY[source].format(field=field)
    result = await session.execute(text(sql))
    rows = result.fetchall()

    return any(op_fn(row[0], threshold) for row in rows if row[0] is not None)


async def _trigger_action(rule, session) -> None:
    """Execute rule action (currently discord_webhook only)."""
    if rule.action == "discord_webhook":
        from src.jobs.discord_notify import send_discord_alert

        # Build a minimal mock object that send_discord_alert can consume
        class _AlertMsg:
            source = "alert_rule"
            sentiment = None
            sentiment_label = "neutral"
            tickers = rule.ticker_filter or []
            headline = f"Alert triggered: {rule.name}"
            url = ""
            published_at = datetime.now(timezone.utc)
            category = "alert"

        await send_discord_alert(_AlertMsg())
        logger.info("alert_action_triggered", rule=rule.name, action=rule.action)
    else:
        logger.warning("alert_unknown_action", action=rule.action)


async def evaluate_all_rules() -> None:
    """Fetch all enabled alert rules, evaluate conditions, trigger actions."""
    from src.core.models.alert_rule import AlertRule

    async with async_session_factory() as session:
        result = await session.execute(
            select(AlertRule).where(AlertRule.enabled.is_(True))
        )
        rules = result.scalars().all()

    if not rules:
        logger.debug("alert_no_active_rules")
        return

    logger.info("alert_evaluating_rules", count=len(rules))

    for rule in rules:
        try:
            now = datetime.now(timezone.utc)

            # Cooldown check
            if rule.last_triggered_at:
                cooldown_end = rule.last_triggered_at + timedelta(minutes=rule.cooldown_minutes)
                if now < cooldown_end:
                    logger.debug("alert_cooldown_skip", rule=rule.name)
                    continue

            # Evaluate all conditions (AND logic)
            async with async_session_factory() as session:
                all_match = True
                for condition in rule.conditions:
                    if not await _condition_matches(condition, session):
                        all_match = False
                        break

                if all_match:
                    await _trigger_action(rule, session)
                    # Update last_triggered_at
                    rule.last_triggered_at = now
                    session.add(rule)
                    await session.commit()
                    logger.info("alert_rule_fired", rule=rule.name)

        except Exception as e:
            logger.error("alert_rule_error", rule=rule.name, error=str(e)[:120])
