"""Send filtered article alerts to Discord via webhook."""

import httpx
import structlog

from src.core.config import settings

logger = structlog.get_logger()

SENTIMENT_COLORS = {
    "bullish": 0x22C55E,
    "bearish": 0xEF4444,
    "neutral": 0x6B7280,
}

SENTIMENT_EMOJI = {
    "bullish": "🟢",
    "bearish": "🔴",
    "neutral": "⚪",
}


def should_notify(article) -> bool:
    """Check if article should trigger a Discord alert."""
    if not settings.discord_webhook_url:
        return False
    if article.sentiment is None:
        return False
    return abs(article.sentiment) >= settings.discord_sentiment_threshold


async def send_discord_alert(article) -> bool:
    """Send rich embed to Discord webhook. Returns True on success."""
    url = settings.discord_webhook_url
    if not url:
        return False

    label = article.sentiment_label or "neutral"
    emoji = SENTIMENT_EMOJI.get(label, "⚪")
    color = SENTIMENT_COLORS.get(label, 0x6B7280)
    tickers_str = ", ".join(f"${t}" for t in article.tickers) if article.tickers else "N/A"
    sentiment_str = f"{'+' if article.sentiment > 0 else ''}{article.sentiment:.2f}" if article.sentiment else "N/A"

    embed = {
        "title": f"{emoji} {tickers_str} — {label.capitalize()} {sentiment_str}",
        "description": article.headline[:256],
        "color": color,
        "fields": [
            {"name": "Source", "value": article.source, "inline": True},
            {"name": "Category", "value": article.category or "general", "inline": True},
            {"name": "Sentiment", "value": sentiment_str, "inline": True},
        ],
        "url": article.url if article.url else None,
        "timestamp": article.published_at.isoformat() if article.published_at else None,
    }

    payload = {
        "username": "AlphaSniper",
        "embeds": [embed],
    }

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code in (200, 204):
                logger.info("discord_alert_sent", ticker=tickers_str, sentiment=sentiment_str)
                return True
            logger.warning("discord_alert_failed", status=resp.status_code)
            return False
    except Exception as e:
        logger.warning("discord_alert_error", error=str(e)[:80])
        return False
