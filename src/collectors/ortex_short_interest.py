"""ORTEX public API collector — daily short interest data per ticker."""

import asyncio
from datetime import date

import httpx
import structlog

from src.collectors.base_collector import BaseCollector
from src.core.config import settings

logger = structlog.get_logger()

ORTEX_URL = "https://public.ortex.com/api/v1/short_interest"


class OrtexShortInterest(BaseCollector):
    """Polls ORTEX public API for short interest. Free ~100 req/day."""

    source_name = "ortex"

    def __init__(self):
        self.symbols = settings.finnhub_symbols

    async def collect(self) -> None:
        async with httpx.AsyncClient(
            timeout=30.0,
            headers={"User-Agent": "AlphaSniper/1.0"},
        ) as client:
            for symbol in self.symbols:
                try:
                    await self._fetch_short_interest(client, symbol)
                except Exception as e:
                    logger.error("ortex_error", symbol=symbol, error=str(e)[:100])
                await asyncio.sleep(2.0)  # Conservative: ~100 req/day budget

    async def _fetch_short_interest(self, client: httpx.AsyncClient, symbol: str) -> int:
        """Fetch short interest for a symbol. Returns saved count."""
        try:
            resp = await client.get(ORTEX_URL, params={"ticker": symbol})
            if resp.status_code == 429:
                logger.warning("ortex_rate_limited", symbol=symbol)
                return 0
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            logger.error("ortex_http_error", symbol=symbol, status=e.response.status_code)
            return 0
        except httpx.RequestError as e:
            logger.error("ortex_request_error", symbol=symbol, error=str(e)[:100])
            return 0

        data = resp.json()
        if not data or not isinstance(data, dict):
            logger.debug("ortex_empty_response", symbol=symbol)
            return 0

        today = date.today().isoformat()
        source_id = f"{symbol}_{today}"

        payload = {
            "ticker": symbol,
            "short_pct_float": data.get("short_interest_pct_float", 0),
            "days_to_cover": data.get("days_to_cover", 0),
            "borrow_fee_pct": data.get("borrow_fee", None),
            "squeeze_score": data.get("squeeze_score", None),
            "report_date": today,
        }

        result = await self.save_raw(source_id=source_id, payload=payload)
        if result:
            logger.info("ortex_fetched", symbol=symbol, short_pct=payload["short_pct_float"])
            return 1
        return 0
