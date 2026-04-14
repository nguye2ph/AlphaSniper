"""TickerTick API collector — free stock news with query language."""

import asyncio

import httpx
import structlog

from src.collectors.base_collector import BaseCollector
from src.core.config import settings

logger = structlog.get_logger()

TICKERTICK_FEED_URL = "https://api.tickertick.com/feed"


class TickerTickRest(BaseCollector):
    """REST poller for TickerTick API. Free, 10 req/min, no API key."""

    source_name = "tickertick"

    def __init__(self):
        self.symbols = settings.finnhub_symbols  # Reuse watchlist
        self.limit = settings.market_cap_limit

    async def collect(self) -> None:
        """Dual query: watchlist tickers + broad small-cap sources."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Query 1: watchlist tickers
            if self.symbols:
                ticker_query = "(or " + " ".join(f"tt:{s}" for s in self.symbols) + ")"
                await self._fetch_feed(client, ticker_query, "watchlist")

            # Query 2: broad small-cap from SEC + press releases
            broad_query = "(or (and tt:* s:sec.gov) (and tt:* s:globenewswire.com) (and tt:* s:prnewswire.com))"
            await self._fetch_feed(client, broad_query, "broad")

    async def _fetch_feed(self, client: httpx.AsyncClient, query: str, label: str) -> int:
        """Fetch articles from TickerTick /feed endpoint."""
        try:
            resp = await client.get(TICKERTICK_FEED_URL, params={"q": query, "n": 50})
            if resp.status_code == 429:
                logger.warning("tickertick_rate_limited", label=label)
                return 0
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            logger.error("tickertick_http_error", status=e.response.status_code, label=label)
            return 0
        except httpx.RequestError as e:
            logger.error("tickertick_request_error", error=str(e), label=label)
            return 0

        data = resp.json()
        stories = data.get("stories", [])
        saved = 0

        for story in stories:
            story_id = str(story.get("id", ""))
            if not story_id:
                continue

            # Extract tickers from tags
            tickers = [t for t in story.get("tags", []) if t and t.isalpha() and t.isupper()]

            # Market cap filter via cache (import here to avoid circular)
            # For now, save all — mc filter applied during process_raw_articles
            result = await self.save_raw(source_id=story_id, payload={
                "title": story.get("title", ""),
                "url": story.get("url", ""),
                "site": story.get("site", ""),
                "time": story.get("time", 0),
                "tags": tickers,
                "description": story.get("description", ""),
            })
            if result:
                saved += 1

        logger.info("tickertick_fetched", label=label, stories=len(stories), saved=saved)
        return saved


async def main():
    """Standalone: run one collection cycle."""
    collector = TickerTickRest()
    await collector.setup()
    try:
        await collector.collect()
    finally:
        await collector.teardown()


if __name__ == "__main__":
    asyncio.run(main())
