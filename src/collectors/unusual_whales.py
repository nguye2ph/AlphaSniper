"""Unusual Whales API collector — options flow data (experimental, free tier)."""

import asyncio

import httpx
import structlog

from src.collectors.base_collector import BaseCollector
from src.core.config import settings

logger = structlog.get_logger()

UW_BASE = "https://api.unusualwhales.com/api/stock"


class UnusualWhales(BaseCollector):
    """Polls Unusual Whales for options flow. Experimental: 100-500 req/day free."""

    source_name = "unusual_whales"

    def __init__(self):
        self.api_key = settings.unusual_whales_api_key
        self.symbols = settings.finnhub_symbols

    async def collect(self) -> None:
        if not self.api_key:
            logger.debug("unusual_whales_disabled", reason="no API key")
            return

        headers = {"Authorization": f"Bearer {self.api_key}"}
        async with httpx.AsyncClient(timeout=30.0, headers=headers) as client:
            for symbol in self.symbols:
                try:
                    await self._fetch_options_flow(client, symbol)
                except Exception as e:
                    logger.error("uw_error", symbol=symbol, error=str(e)[:100])
                await asyncio.sleep(3.0)  # Conservative: limited quota

    async def _fetch_options_flow(self, client: httpx.AsyncClient, symbol: str) -> int:
        """Fetch options flow for a symbol. Returns saved count."""
        try:
            resp = await client.get(f"{UW_BASE}/{symbol}/options-flow")
            if resp.status_code == 429:
                logger.warning("uw_rate_limited", symbol=symbol)
                return 0
            if resp.status_code == 401:
                logger.error("uw_auth_failed", symbol=symbol)
                return 0
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            logger.error("uw_http_error", symbol=symbol, status=e.response.status_code)
            return 0
        except httpx.RequestError as e:
            logger.error("uw_request_error", symbol=symbol, error=str(e)[:100])
            return 0

        data = resp.json()
        flows = data.get("data", [])
        if not isinstance(flows, list):
            return 0

        saved = 0
        for flow in flows[:20]:  # Cap per symbol to conserve quota
            contract_id = flow.get("id", "")
            if not contract_id:
                continue

            source_id = f"{contract_id}"
            payload = {
                "ticker": symbol,
                "contract": flow.get("option_symbol", ""),
                "strike": flow.get("strike_price"),
                "expiry": flow.get("expires_at", ""),
                "call_put": flow.get("put_call", ""),
                "volume": flow.get("volume", 0),
                "open_interest": flow.get("open_interest", 0),
                "premium": flow.get("premium", 0),
                "sentiment": flow.get("sentiment", "neutral"),
                "timestamp": flow.get("created_at", ""),
            }

            result = await self.save_raw(source_id=source_id, payload=payload)
            if result:
                saved += 1

        logger.info("uw_fetched", symbol=symbol, flows=len(flows), saved=saved)
        return saved
