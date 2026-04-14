"""Finnhub REST poller — market news + company news with rate limiting."""

import asyncio
from datetime import date

import httpx
import structlog

from src.collectors.base_collector import BaseCollector
from src.core.config import settings

logger = structlog.get_logger()

FINNHUB_BASE = "https://finnhub.io/api/v1"


class FinnhubRest(BaseCollector):
    """REST poller for Finnhub market news and company news endpoints."""

    source_name = "finnhub"

    def __init__(self):
        self.api_key = settings.finnhub_api_key
        self.symbols = settings.finnhub_symbols
        self.headers = {"X-Finnhub-Token": self.api_key}
        self._min_id: int = 0  # Track last seen news ID for pagination

    async def collect(self) -> None:
        """Single poll cycle: fetch market news + company news for watchlist."""
        if not self.api_key:
            logger.error("finnhub_api_key_missing")
            return

        async with httpx.AsyncClient(headers=self.headers, timeout=30.0) as client:
            await self._fetch_market_news(client)
            await self._fetch_company_news(client)

    async def _fetch_market_news(self, client: httpx.AsyncClient) -> int:
        """Fetch general market news. Returns count of new articles saved."""
        params = {"category": "general"}
        if self._min_id > 0:
            params["minId"] = self._min_id

        try:
            resp = await client.get(f"{FINNHUB_BASE}/news", params=params)
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            logger.error("finnhub_market_news_error", status=e.response.status_code)
            return 0
        except httpx.RequestError as e:
            logger.error("finnhub_request_error", error=str(e))
            return 0

        articles = resp.json()
        saved = 0
        for article in articles:
            article_id = str(article.get("id", ""))
            if not article_id:
                continue
            # Update min_id for next poll
            self._min_id = max(self._min_id, int(article_id))
            result = await self.save_raw(source_id=article_id, payload=article)
            if result:
                saved += 1

        logger.info("finnhub_market_news", fetched=len(articles), saved=saved)
        return saved

    async def _fetch_company_news(self, client: httpx.AsyncClient) -> int:
        """Fetch news for each watchlist ticker. Returns total new articles."""
        today = date.today().isoformat()
        total_saved = 0

        for symbol in self.symbols:
            params = {"symbol": symbol, "from": today, "to": today}
            try:
                resp = await client.get(f"{FINNHUB_BASE}/company-news", params=params)
                resp.raise_for_status()
            except httpx.HTTPStatusError as e:
                logger.warning("finnhub_company_error", symbol=symbol, status=e.response.status_code)
                continue
            except httpx.RequestError as e:
                logger.warning("finnhub_request_error", symbol=symbol, error=str(e))
                continue

            articles = resp.json()
            for article in articles:
                article_id = str(article.get("id", ""))
                if not article_id:
                    continue
                result = await self.save_raw(source_id=article_id, payload=article)
                if result:
                    total_saved += 1

            # Rate limiting: ~2 requests/sec to stay well under 30/sec limit
            await asyncio.sleep(0.5)

        logger.info("finnhub_company_news", symbols=len(self.symbols), saved=total_saved)
        return total_saved


async def main():
    """Standalone poller: run one collection cycle."""
    collector = FinnhubRest()
    await collector.setup()
    try:
        await collector.collect()
    finally:
        await collector.teardown()


if __name__ == "__main__":
    asyncio.run(main())
