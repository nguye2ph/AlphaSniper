"""NYSE market hours and trading day detection using America/New_York timezone."""

from datetime import date, datetime, time
from typing import Literal
from zoneinfo import ZoneInfo

ET = ZoneInfo("America/New_York")

# NYSE session boundaries (Eastern Time)
_PRE_MARKET_START = time(4, 0)
_MARKET_OPEN = time(9, 30)
_MARKET_CLOSE = time(16, 0)
_AFTER_HOURS_END = time(20, 0)


def _now_et() -> datetime:
    """Current time in Eastern timezone."""
    return datetime.now(ET)


def is_trading_day(dt: date | None = None) -> bool:
    """Return True if the given date (default: today ET) is Mon-Fri.

    No holiday calendar — weekends only per KISS principle.
    """
    if dt is None:
        dt = _now_et().date()
    return dt.weekday() < 5  # 0=Mon, 4=Fri


def is_market_open() -> bool:
    """Return True if NYSE regular session is currently active (9:30-16:00 ET, Mon-Fri)."""
    now = _now_et()
    if not is_trading_day(now.date()):
        return False
    return _MARKET_OPEN <= now.time() < _MARKET_CLOSE


def get_market_phase() -> Literal["pre_market", "market_open", "after_hours", "closed"]:
    """Return current NYSE market phase based on Eastern Time.

    Phases:
        pre_market   — 04:00-09:30 ET, weekdays
        market_open  — 09:30-16:00 ET, weekdays
        after_hours  — 16:00-20:00 ET, weekdays
        closed       — all other times (weekends, overnight)
    """
    now = _now_et()

    if not is_trading_day(now.date()):
        return "closed"

    t = now.time()
    if _PRE_MARKET_START <= t < _MARKET_OPEN:
        return "pre_market"
    if _MARKET_OPEN <= t < _MARKET_CLOSE:
        return "market_open"
    if _MARKET_CLOSE <= t < _AFTER_HOURS_END:
        return "after_hours"
    return "closed"
