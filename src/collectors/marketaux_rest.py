"""MarketAux REST poller — global news aggregation with sentiment scoring."""

import asyncio
from datetime import datetime, timezone

import httpx
import structlog

from src.collectors.base_collector import BaseCollector
from src.core.config import settings

logger = structlog.get_logger()

MARKETAUX_BASE = "https://api.marketaux.com/v1"


class MarketAuxRest(BaseCollector):
    """REST poller for MarketAux news API. Free tier: 100 req/day."""

    source_name = "marketaux"

    def __init__(self):
        self.api_key = settings.marketaux_api_key

    async def collect(self) -> None:
        """Single poll cycle: fetch latest news with entity/sentiment data."""
        if not self.api_key:
            logger.error("marketaux_api_key_missing", msg="Set MARKETAUX_API_KEY in .env")
            return

        async with httpx.AsyncClient(timeout=30.0) as client:
            await self._fetch_news(client)

    async def _fetch_news(self, client: httpx.AsyncClient, page: int = 1) -> int:
        """Fetch news articles from MarketAux. Returns count saved."""
        params = {
            "api_token": self.api_key,
            "language": "en",
            "filter_entities": "true",  # Include entity extraction
            "page": page,
        }

        try:
            resp = await client.get(f"{MARKETAUX_BASE}/news/all", params=params)
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            logger.error("marketaux_http_error", status=e.response.status_code)
            return 0
        except httpx.RequestError as e:
            logger.error("marketaux_request_error", error=str(e))
            return 0

        data = resp.json()
        articles = data.get("data", [])
        saved = 0

        for article in articles:
            article_uuid = article.get("uuid", "")
            if not article_uuid:
                continue
            result = await self.save_raw(source_id=article_uuid, payload=article)
            if result:
                saved += 1

        meta = data.get("meta", {})
        logger.info(
            "marketaux_fetched",
            found=meta.get("found", 0),
            returned=meta.get("returned", 0),
            saved=saved,
            page=page,
        )
        return saved


async def main():
    """Standalone: run one collection cycle."""
    collector = MarketAuxRest()
    await collector.setup()
    try:
        await collector.collect()
    finally:
        await collector.teardown()


if __name__ == "__main__":
    asyncio.run(main())
