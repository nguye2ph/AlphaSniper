"""StockTwits public API collector — sentiment-labeled messages per ticker."""

import asyncio
from datetime import datetime, timezone

import httpx
import structlog

from src.collectors.base_collector import BaseCollector
from src.core.config import settings
from src.core.models.raw_social_post import RawSocialPost

logger = structlog.get_logger()

STOCKTWITS_URL = "https://api.stocktwits.com/api/2/streams/symbol"


class StockTwitsRest(BaseCollector):
    """Polls StockTwits public symbol streams. Free, no auth, 100 req/min."""

    source_name = "stocktwits"

    def __init__(self):
        self.symbols = settings.finnhub_symbols  # Reuse watchlist

    async def collect(self) -> None:
        async with httpx.AsyncClient(timeout=30.0) as client:
            for symbol in self.symbols:
                try:
                    await self._fetch_symbol(client, symbol)
                except Exception as e:
                    logger.error("stocktwits_error", symbol=symbol, error=str(e)[:100])
                await asyncio.sleep(1.0)  # Rate limit: stay under 100/min

    async def _fetch_symbol(self, client: httpx.AsyncClient, symbol: str) -> int:
        """Fetch recent messages for a symbol. Returns saved count."""
        try:
            resp = await client.get(f"{STOCKTWITS_URL}/{symbol}.json")
            if resp.status_code == 429:
                logger.warning("stocktwits_rate_limited", symbol=symbol)
                return 0
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            logger.error("stocktwits_http_error", symbol=symbol, status=e.response.status_code)
            return 0
        except httpx.RequestError as e:
            logger.error("stocktwits_request_error", symbol=symbol, error=str(e)[:100])
            return 0

        data = resp.json()
        messages = data.get("messages", [])
        saved = 0

        for msg in messages:
            msg_id = str(msg.get("id", ""))
            if not msg_id:
                continue

            sentiment = msg.get("entities", {}).get("sentiment", {})
            payload = {
                "title": msg.get("body", "")[:500],
                "body": msg.get("body", ""),
                "score": 0,  # StockTwits doesn't have upvotes
                "sentiment_label": sentiment.get("basic", "neutral") if sentiment else "neutral",
                "author": msg.get("user", {}).get("username", ""),
                "platform": "stocktwits",
                "symbol": symbol,
                "created_at": msg.get("created_at", ""),
            }

            existing = await RawSocialPost.find_one(
                RawSocialPost.source == self.source_name,
                RawSocialPost.source_id == msg_id,
            )
            if existing:
                continue

            doc = RawSocialPost(
                source=self.source_name,
                source_id=msg_id,
                payload=payload,
                collected_at=datetime.now(timezone.utc),
            )
            await doc.insert()
            saved += 1

        logger.info("stocktwits_fetched", symbol=symbol, messages=len(messages), saved=saved)
        return saved
