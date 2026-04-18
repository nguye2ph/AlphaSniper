"""Parse raw OpenInsider HTML table data into structured InsiderTrade fields."""

from datetime import datetime, timezone

import structlog

logger = structlog.get_logger()

# OpenInsider transaction type normalization
TRANSACTION_TYPE_MAP = {
    "P - Purchase": "buy",
    "S - Sale": "sell",
    "S - Sale+OE": "sell",
    "M - Exempt": "exercise",
    "A - Award": "award",
    "F - Tax": "tax",
    "G - Gift": "gift",
    "D - Disposition": "sell",
    "C - Conversion": "exercise",
}


def parse_trade(payload: dict) -> dict | None:
    """Convert raw OpenInsider payload to clean trade fields.

    Returns dict ready for InsiderTrade model, or None if unparseable.
    """
    try:
        ticker = payload.get("ticker", "").strip().upper()
        if not ticker:
            return None

        raw_type = payload.get("transaction_type", "")
        transaction_type = TRANSACTION_TYPE_MAP.get(raw_type, raw_type.lower())

        # Parse numeric fields (OpenInsider uses comma-separated numbers)
        shares = _parse_int(payload.get("shares", "0"))
        price = _parse_float(payload.get("price", "0"))
        value = _parse_float(payload.get("value", "0"))

        # Parse filing date
        filing_date_str = payload.get("filing_date", "")
        filing_date = _parse_date(filing_date_str)
        if not filing_date:
            return None

        return {
            "ticker": ticker,
            "officer_name": payload.get("officer_name", "Unknown"),
            "officer_title": payload.get("officer_title", ""),
            "transaction_type": transaction_type,
            "shares": abs(shares),
            "price": price,
            "value": abs(value),
            "filing_date": filing_date,
        }
    except Exception as e:
        logger.warning("insider_parse_error", error=str(e)[:100])
        return None


def _parse_int(value: str | int) -> int:
    if isinstance(value, int):
        return value
    return int(value.replace(",", "").replace("+", "").strip() or "0")


def _parse_float(value: str | float) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    return float(value.replace(",", "").replace("$", "").strip() or "0")


def _parse_date(date_str: str) -> datetime | None:
    if not date_str:
        return None
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(date_str.strip(), fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None
