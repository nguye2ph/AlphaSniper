"""Finnhub WebSocket consumer — real-time news streaming with auto-reconnect."""

import asyncio
import json
import signal

import structlog
import websockets

from src.collectors.base_collector import BaseCollector
from src.core.config import settings

logger = structlog.get_logger()


class FinnhubWebSocket(BaseCollector):
    """Persistent WebSocket connection to Finnhub for real-time news."""

    source_name = "finnhub"

    def __init__(self):
        self.api_key = settings.finnhub_api_key
        self.symbols = settings.finnhub_symbols
        self.ws_url = f"wss://ws.finnhub.io?token={self.api_key}"
        self._shutdown = asyncio.Event()
        self._backoff = 2  # Initial reconnect delay in seconds
        self._max_backoff = 60

    async def collect(self) -> None:
        """Main loop: connect, subscribe, stream, reconnect on failure."""
        if not self.api_key:
            logger.error("finnhub_api_key_missing", msg="Set FINNHUB_API_KEY in .env")
            return

        while not self._shutdown.is_set():
            try:
                await self._stream()
                self._backoff = 2  # Reset on clean disconnect
            except websockets.exceptions.ConnectionClosed as e:
                logger.warning("ws_disconnected", code=e.code, reason=e.reason)
            except Exception as e:
                logger.error("ws_error", error=str(e))

            if not self._shutdown.is_set():
                logger.info("ws_reconnecting", delay=self._backoff)
                await asyncio.sleep(self._backoff)
                self._backoff = min(self._backoff * 2, self._max_backoff)

    async def _stream(self) -> None:
        """Connect, subscribe to symbols, and process incoming messages."""
        async with websockets.connect(self.ws_url) as ws:
            logger.info("ws_connected", url="wss://ws.finnhub.io")
            self._backoff = 2  # Reset backoff on successful connect

            # Subscribe to news for each symbol (max 50 on free tier)
            for symbol in self.symbols[:50]:
                await ws.send(json.dumps({"type": "subscribe", "symbol": symbol}))
            logger.info("ws_subscribed", symbols=len(self.symbols[:50]))

            async for message in ws:
                if self._shutdown.is_set():
                    break
                await self._handle_message(message)

    async def _handle_message(self, raw_message: str) -> None:
        """Parse incoming WS message and save news articles to MongoDB."""
        try:
            data = json.loads(raw_message)
        except json.JSONDecodeError:
            logger.warning("ws_invalid_json", raw=raw_message[:100])
            return

        msg_type = data.get("type", "")

        if msg_type == "ping":
            return  # websockets library handles ping/pong automatically

        if msg_type == "news":
            articles = data.get("data", [])
            for article in articles:
                article_id = str(article.get("id", ""))
                if article_id:
                    await self.save_raw(source_id=article_id, payload=article)

        elif msg_type == "trade":
            pass  # Ignore trade data for now

    def shutdown(self) -> None:
        """Signal graceful shutdown."""
        logger.info("ws_shutdown_requested")
        self._shutdown.set()


async def main():
    """Entrypoint for running the Finnhub WebSocket collector as standalone process."""
    collector = FinnhubWebSocket()
    await collector.setup()

    # Handle SIGTERM/SIGINT for graceful shutdown
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, collector.shutdown)

    try:
        await collector.collect()
    finally:
        await collector.teardown()
        logger.info("ws_collector_stopped")


if __name__ == "__main__":
    asyncio.run(main())
