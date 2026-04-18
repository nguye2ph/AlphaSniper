"""API Ninjas earnings calendar collector — upcoming/recent earnings events."""

import asyncio
from datetime import date

import httpx
import structlog

from src.collectors.base_collector import BaseCollector
from src.core.config import settings

logger = structlog.get_logger()

API_NINJAS_URL = "https://api.api-ninjas.com/v1/earningscalendar"


class EarningsCalendar(BaseCollector):
    """REST poller for API Ninjas earnings calendar. Free: 1,700 req/day."""

    source_name = "earnings_calendar"

    def __init__(self):
        self.api_key = settings.api_ninjas_key
        self.symbols = settings.finnhub_symbols

    async def collect(self) -> None:
        if not self.api_key:
            logger.warning("api_ninjas_key_missing")
            return

        headers = {"X-Api-Key": self.api_key}
        async with httpx.AsyncClient(timeout=30.0, headers=headers) as client:
            # Fetch by date range (next 7 days)
            await self._fetch_by_date(client)
            # Fetch by watchlist tickers
            for symbol in self.symbols:
                await self._fetch_by_ticker(client, symbol)
                await asyncio.sleep(0.5)  # rate limit

    async def _fetch_by_date(self, client: httpx.AsyncClient) -> int:
        """Fetch earnings for upcoming week."""
        today = date.today()
        params = {
            "date": today.isoformat(),
        }
        try:
            resp = await client.get(API_NINJAS_URL, params=params)
            if resp.status_code == 429:
                logger.warning("api_ninjas_rate_limited")
                return 0
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            logger.error("api_ninjas_http_error", status=e.response.status_code)
            return 0
        except httpx.RequestError as e:
            logger.error("api_ninjas_request_error", error=str(e)[:100])
            return 0

        events = resp.json()
        if not isinstance(events, list):
            return 0

        saved = 0
        for event in events:
            ticker = event.get("ticker", "")
            report_date = event.get("pricedate", today.isoformat())
            if not ticker:
                continue

            source_id = f"{ticker}_{report_date}"
            result = await self.save_raw(source_id=source_id, payload=event)
            if result:
                saved += 1

        logger.info("earnings_date_fetched", date=today.isoformat(), saved=saved)
        return saved

    async def _fetch_by_ticker(self, client: httpx.AsyncClient, ticker: str) -> int:
        """Fetch earnings for a specific ticker."""
        try:
            resp = await client.get(API_NINJAS_URL, params={"ticker": ticker})
            if resp.status_code == 429:
                logger.warning("api_ninjas_rate_limited", ticker=ticker)
                return 0
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            logger.error("api_ninjas_ticker_error", ticker=ticker, status=e.response.status_code)
            return 0
        except httpx.RequestError as e:
            logger.error("api_ninjas_request_error", ticker=ticker, error=str(e)[:100])
            return 0

        events = resp.json()
        if not isinstance(events, list):
            return 0

        saved = 0
        for event in events:
            report_date = event.get("pricedate", "")
            source_id = f"{ticker}_{report_date}"
            result = await self.save_raw(source_id=source_id, payload=event)
            if result:
                saved += 1

        logger.info("earnings_ticker_fetched", ticker=ticker, saved=saved)
        return saved
