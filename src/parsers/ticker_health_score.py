"""Compute composite health score (0-100) per ticker from all data sources."""

from datetime import datetime, timedelta, timezone

import structlog
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.models.article import Article
from src.core.models.earnings_event import EarningsEvent
from src.core.models.insider_trade import InsiderTrade
from src.core.models.short_interest import ShortInterest
from src.core.models.social_sentiment import SocialSentiment

logger = structlog.get_logger()


class TickerHealth(BaseModel):
    ticker: str
    score: float  # 0-100
    breakdown: dict  # {"sentiment": 72, "insider": 85, "squeeze_risk": 60, "earnings": 50}
    signals: list[str]  # ["Strong insider buying", "High short interest", ...]
    computed_at: str  # ISO timestamp


def _normalize_sentiment(avg: float) -> float:
    """Normalize sentiment from -1..1 to 0..100."""
    return round((avg + 1.0) / 2.0 * 100, 1)


async def _get_sentiment_score(ticker: str, since: datetime, session: AsyncSession) -> float | None:
    """Avg sentiment from news articles + social posts in last 7d."""
    # News articles
    news_avg = await session.scalar(
        select(func.avg(Article.sentiment))
        .where(Article.tickers.any(ticker))
        .where(Article.published_at >= since)
    )
    # Social sentiment
    social_avg = await session.scalar(
        select(func.avg(SocialSentiment.sentiment_score))
        .where(SocialSentiment.ticker == ticker)
        .where(SocialSentiment.posted_at >= since)
    )

    values = [v for v in (news_avg, social_avg) if v is not None]
    if not values:
        return None
    return _normalize_sentiment(sum(values) / len(values))


async def _get_insider_score(
    ticker: str, since: datetime, session: AsyncSession
) -> tuple[float | None, list[str]]:
    """Score insider activity: buys vs sells in last 7d."""
    result = await session.execute(
        select(InsiderTrade.transaction_type, func.sum(InsiderTrade.value).label("total_value"))
        .where(InsiderTrade.ticker == ticker)
        .where(InsiderTrade.filing_date >= since)
        .group_by(InsiderTrade.transaction_type)
    )
    rows = result.all()
    if not rows:
        return None, []

    buy_value = sum(r.total_value for r in rows if r.transaction_type == "buy")
    sell_value = sum(r.total_value for r in rows if r.transaction_type == "sell")
    total = buy_value + sell_value
    if total == 0:
        return None, []

    buy_ratio = buy_value / total
    score = round(buy_ratio * 100, 1)
    signals = []
    if buy_ratio > 0.7:
        signals.append(f"Strong insider buying last 7d (${buy_value:,.0f})")
    elif buy_ratio < 0.3:
        signals.append(f"Heavy insider selling last 7d (${sell_value:,.0f})")
    return score, signals


async def _get_squeeze_score(
    ticker: str, since: datetime, session: AsyncSession
) -> tuple[float | None, list[str]]:
    """Latest squeeze risk — invert so low squeeze = good health."""
    row = await session.scalar(
        select(ShortInterest.squeeze_score)
        .where(ShortInterest.ticker == ticker)
        .where(ShortInterest.report_date >= since)
        .order_by(ShortInterest.report_date.desc())
        .limit(1)
    )
    if row is None:
        return None, []
    # High squeeze_score = high risk = lower health
    score = round(100 - float(row), 1)
    signals = []
    if row >= 75:
        signals.append(f"High squeeze risk (score {row})")
    elif row <= 25:
        signals.append(f"Low short interest pressure (score {row})")
    return score, signals


async def _get_earnings_score(
    ticker: str, session: AsyncSession
) -> tuple[float | None, list[str]]:
    """Check for upcoming earnings within 7 days."""
    now = datetime.now(timezone.utc)
    upcoming = await session.scalar(
        select(func.count(EarningsEvent.id))
        .where(EarningsEvent.ticker == ticker)
        .where(EarningsEvent.report_date >= now)
        .where(EarningsEvent.report_date <= now + timedelta(days=7))
    )
    signals = []
    if upcoming:
        signals.append("Earnings report within 7 days")
        return 70.0, signals
    return 50.0, signals


async def compute_health_score(ticker: str, session: AsyncSession) -> TickerHealth:
    """Query last 7d data, compute weighted health score (0-100)."""
    since = datetime.now(timezone.utc) - timedelta(days=7)
    ticker = ticker.upper()

    components: list[tuple[str, float, float]] = []  # (name, score, weight)
    signals: list[str] = []
    breakdown: dict = {}

    # Sentiment (weight=0.3)
    sent = await _get_sentiment_score(ticker, since, session)
    if sent is not None:
        components.append(("sentiment", sent, 0.3))
        breakdown["sentiment"] = sent

    # Insider (weight=0.3)
    insider, insider_signals = await _get_insider_score(ticker, since, session)
    if insider is not None:
        components.append(("insider", insider, 0.3))
        breakdown["insider"] = insider
        signals.extend(insider_signals)

    # Squeeze risk (weight=0.2)
    squeeze, squeeze_signals = await _get_squeeze_score(ticker, since, session)
    if squeeze is not None:
        components.append(("squeeze_risk", squeeze, 0.2))
        breakdown["squeeze_risk"] = squeeze
        signals.extend(squeeze_signals)

    # Earnings (weight=0.2)
    earnings, earnings_signals = await _get_earnings_score(ticker, session)
    components.append(("earnings", earnings, 0.2))
    breakdown["earnings"] = earnings
    signals.extend(earnings_signals)

    if not components or all(c[0] == "earnings" for c in components):
        logger.info("no_health_data", ticker=ticker)
        return TickerHealth(
            ticker=ticker,
            score=50.0,
            breakdown=breakdown,
            signals=["No recent data"],
            computed_at=datetime.now(timezone.utc).isoformat(),
        )

    total_weight = sum(w for _, _, w in components)
    health = sum(score * weight for _, score, weight in components) / total_weight

    logger.info("health_computed", ticker=ticker, score=round(health, 1))
    return TickerHealth(
        ticker=ticker,
        score=round(health, 1),
        breakdown=breakdown,
        signals=signals or ["Normal market conditions"],
        computed_at=datetime.now(timezone.utc).isoformat(),
    )
