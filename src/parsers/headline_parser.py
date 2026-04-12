"""Rule-based headline parser — extract tickers and sentiment from news headlines."""

import re

from pydantic import BaseModel

# Regex: match $TICKER or standalone uppercase 1-5 letter words that look like tickers
TICKER_PATTERN = re.compile(r"\$([A-Z]{1,5})\b")
# Fallback: match known ticker patterns in context like "shares of AAPL"
CONTEXTUAL_PATTERN = re.compile(r"\b([A-Z]{2,5})\b")

# Common false positives to exclude
FALSE_POSITIVES = {
    "CEO", "CFO", "CTO", "COO", "IPO", "SEC", "FDA", "NYSE", "NASDAQ",
    "ETF", "GDP", "CPI", "API", "EPS", "PE", "AI", "US", "UK", "EU",
    "Q1", "Q2", "Q3", "Q4", "YOY", "MOM", "THE", "FOR", "AND", "BUT",
    "INC", "LLC", "LTD", "CORP", "NEW", "TOP", "USD", "EST", "PST",
    "AM", "PM", "CEO", "NFT", "ESG", "SPY", "DOW", "JUST", "NOW",
    "ALL", "BIG", "LOW", "HIGH", "UP", "DOWN", "NOT", "HAS", "WAS",
}

BULLISH_WORDS = {
    "surges", "soars", "jumps", "rallies", "beats", "exceeds", "upgrade",
    "bullish", "positive", "growth", "profit", "gains", "rises", "climbs",
    "breakthrough", "record", "strong", "outperform", "buy", "upside",
    "raises", "dividend", "acquisition", "approved", "launches",
}

BEARISH_WORDS = {
    "plunges", "drops", "falls", "crashes", "misses", "downgrades",
    "bearish", "negative", "loss", "decline", "sinks", "tumbles",
    "warning", "fraud", "lawsuit", "recall", "bankruptcy", "resign",
    "investigation", "probe", "cuts", "layoffs", "sell", "downside",
    "delays", "fails", "weak", "underperform", "debt",
}


class ParsedHeadline(BaseModel):
    """Result of parsing a news headline."""

    tickers: list[str] = []
    sentiment: float = 0.0  # -1.0 to 1.0
    sentiment_label: str = "neutral"  # bullish/bearish/neutral
    category: str = "general"


def parse_headline(headline: str) -> ParsedHeadline:
    """Extract tickers and sentiment from a headline string."""
    tickers = _extract_tickers(headline)
    sentiment, label = _score_sentiment(headline)
    category = _detect_category(headline)

    return ParsedHeadline(
        tickers=tickers,
        sentiment=sentiment,
        sentiment_label=label,
        category=category,
    )


def _extract_tickers(text: str) -> list[str]:
    """Extract stock ticker symbols from text."""
    # First: explicit $TICKER patterns
    explicit = TICKER_PATTERN.findall(text)
    if explicit:
        return list(dict.fromkeys(t for t in explicit if t not in FALSE_POSITIVES))

    # Fallback: contextual uppercase words (less reliable)
    candidates = CONTEXTUAL_PATTERN.findall(text)
    tickers = [t for t in candidates if t not in FALSE_POSITIVES and len(t) >= 2]
    # Only return if few candidates (high confidence)
    return list(dict.fromkeys(tickers))[:3] if len(tickers) <= 5 else []


def _score_sentiment(text: str) -> tuple[float, str]:
    """Score headline sentiment based on keyword matching."""
    words = set(text.lower().split())
    bull_count = len(words & BULLISH_WORDS)
    bear_count = len(words & BEARISH_WORDS)
    total = bull_count + bear_count

    if total == 0:
        return 0.0, "neutral"

    score = (bull_count - bear_count) / total
    if score > 0.2:
        return round(score, 2), "bullish"
    elif score < -0.2:
        return round(score, 2), "bearish"
    return round(score, 2), "neutral"


def _detect_category(text: str) -> str:
    """Detect article category from headline keywords."""
    lower = text.lower()
    if any(w in lower for w in ("earnings", "revenue", "profit", "quarterly", "q1", "q2", "q3", "q4")):
        return "earnings"
    if any(w in lower for w in ("merger", "acquisition", "acquire", "buyout", "takeover")):
        return "merger"
    if any(w in lower for w in ("ceo", "cfo", "resign", "appoint", "hire", "fired")):
        return "insider"
    if any(w in lower for w in ("fda", "approved", "clinical", "trial")):
        return "regulatory"
    if any(w in lower for w in ("analyst", "upgrade", "downgrade", "price target", "rating")):
        return "analyst"
    if any(w in lower for w in ("lawsuit", "sec", "investigation", "fraud", "probe")):
        return "legal"
    return "general"
