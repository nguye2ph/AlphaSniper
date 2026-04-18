"""VADER-based sentiment analysis + ticker extraction for social media posts."""

import re

import structlog
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

logger = structlog.get_logger()

# Common English words that look like tickers but aren't
TICKER_BLACKLIST = {
    "I", "A", "AM", "PM", "AN", "AS", "AT", "BE", "BY", "DO", "GO", "IF",
    "IN", "IS", "IT", "ME", "MY", "NO", "OF", "OK", "ON", "OR", "SO", "TO",
    "UP", "US", "WE", "DD", "CEO", "CFO", "IPO", "ETF", "ATH", "IMO",
    "YOLO", "FOMO", "HODL", "NYSE", "NASDAQ", "SEC", "FDA", "WSB", "ALL",
    "FOR", "THE", "ARE", "NOT", "BUT", "CAN", "HAS", "HAD", "WAS", "HIS",
    "HER", "NEW", "OLD", "BIG", "LOW", "HIGH", "LONG", "SHORT", "CALL",
    "PUT", "BUY", "SELL", "HOLD", "MOON", "DIP", "RED", "GREEN", "PUMP",
    "DUMP", "GAIN", "LOSS", "BULL", "BEAR", "RIP", "LOL", "OMG", "WTF",
    "EDIT", "TLDR", "PSA", "FYI", "EPS", "PE", "PB", "ROE", "ROI",
}

# Regex: 1-5 uppercase letters as whole words, optionally prefixed by $
TICKER_PATTERN = re.compile(r"(?<!\w)\$?([A-Z]{1,5})(?!\w)")

_analyzer = SentimentIntensityAnalyzer()


def extract_tickers(text: str) -> list[str]:
    """Extract stock ticker symbols from text, filtering common words."""
    matches = TICKER_PATTERN.findall(text)
    tickers = []
    seen = set()
    for m in matches:
        if m not in TICKER_BLACKLIST and m not in seen and len(m) >= 2:
            tickers.append(m)
            seen.add(m)
    return tickers


def analyze_sentiment(text: str) -> tuple[float, str]:
    """Run VADER sentiment on text. Returns (score, label).

    Score: -1.0 (bearish) to 1.0 (bullish).
    Label: "bullish" | "bearish" | "neutral".
    """
    if not text:
        return 0.0, "neutral"
    scores = _analyzer.polarity_scores(text)
    compound = scores["compound"]
    if compound >= 0.05:
        label = "bullish"
    elif compound <= -0.05:
        label = "bearish"
    else:
        label = "neutral"
    return round(compound, 4), label
