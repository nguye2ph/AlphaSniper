"""Parser for NuntioBot Discord message format."""

import re

import structlog
from pydantic import BaseModel

logger = structlog.get_logger()

# Market cap: "4.6 M", "1.2 B", "850 K"
MC_PATTERN = re.compile(r'^\s*([\d,]+\.?\d*)\s+([KMBkmb])\b')
# Country flag emoji (Unicode regional indicators)
FLAG_PATTERN = re.compile(r'([\U0001F1E0-\U0001F1FF]{2})')
# Ticker: 1-5 uppercase letters followed by colon or space-colon
TICKER_PATTERN = re.compile(r'\b([A-Z]{1,5})\s*:')
# Link at end
LINK_PATTERN = re.compile(r'(https?://\S+)')

MC_MULTIPLIERS = {"K": 1_000, "k": 1_000, "M": 1_000_000, "m": 1_000_000, "B": 1_000_000_000, "b": 1_000_000_000}


class NuntioAlert(BaseModel):
    """Parsed NuntioBot alert data."""

    market_cap: float
    market_cap_raw: str
    ticker: str
    country_flag: str
    headline: str
    link: str | None = None


def parse_nuntio_message(content: str) -> NuntioAlert | None:
    """Parse NuntioBot message text into structured alert.
    Returns None if message doesn't match expected format."""
    if not content or len(content) < 10:
        return None

    # Extract market cap
    mc_match = MC_PATTERN.search(content)
    if not mc_match:
        logger.debug("nuntio_no_mc", content=content[:80])
        return None

    mc_value = float(mc_match.group(1).replace(",", ""))
    mc_unit = mc_match.group(2).upper()
    market_cap = mc_value * MC_MULTIPLIERS.get(mc_unit, 1)
    mc_raw = f"{mc_match.group(1)} {mc_match.group(2)}"

    # Extract country flag
    flag_match = FLAG_PATTERN.search(content)
    country_flag = flag_match.group(1) if flag_match else ""

    # Extract ticker (first uppercase word before colon)
    ticker_match = TICKER_PATTERN.search(content)
    if not ticker_match:
        logger.debug("nuntio_no_ticker", content=content[:80])
        return None
    ticker = ticker_match.group(1)

    # Extract headline: everything after "TICKER :" until link or end
    ticker_pos = content.find(f"{ticker} :") or content.find(f"{ticker}:")
    if ticker_pos == -1:
        ticker_pos = ticker_match.end()
    headline_start = content.index(":", ticker_pos) + 1
    headline_text = content[headline_start:].strip()

    # Extract link
    link_match = LINK_PATTERN.search(headline_text)
    link = None
    if link_match:
        link = link_match.group(1)
        headline_text = headline_text[: link_match.start()].strip()
        # Remove trailing " - " before link
        headline_text = headline_text.rstrip(" -").strip()

    if not headline_text:
        return None

    return NuntioAlert(
        market_cap=market_cap,
        market_cap_raw=mc_raw,
        ticker=ticker,
        country_flag=country_flag,
        headline=headline_text,
        link=link,
    )
