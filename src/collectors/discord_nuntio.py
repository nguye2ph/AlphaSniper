"""Discord NuntioBot passive listener — selfbot using discord.py-self."""

import asyncio
import signal

import structlog

from src.collectors.base_collector import BaseCollector
from src.core.config import settings
from src.parsers.nuntio_message_parser import parse_nuntio_message

logger = structlog.get_logger()


class DiscordNuntioCollector(BaseCollector):
    """Passive Discord listener for NuntioBot stock alerts."""

    source_name = "discord_nuntio"

    def __init__(self):
        self.token = settings.discord_token
        self.channel_ids = set(settings.discord_channel_ids)
        self.bot_name = settings.nuntio_bot_name.lower()
        self.limit = settings.market_cap_limit
        self._shutdown = asyncio.Event()

    async def collect(self) -> None:
        """Connect to Discord and listen for NuntioBot messages."""
        if not self.token:
            logger.error("discord_token_missing", msg="Set DISCORD_TOKEN in .env")
            return

        if not self.channel_ids:
            logger.error("discord_channels_missing", msg="Set DISCORD_CHANNEL_IDS in .env")
            return

        try:
            import discord
        except ImportError:
            logger.error("discord_py_self_not_installed", msg="pip install discord.py-self")
            return

        client = discord.Client()

        @client.event
        async def on_ready():
            logger.info("discord_connected", user=str(client.user), channels=len(self.channel_ids))

        @client.event
        async def on_message(message):
            # Filter: only watched channels
            if str(message.channel.id) not in self.channel_ids:
                return

            # Filter: only NuntioBot messages
            if not message.author.bot:
                return
            if self.bot_name not in message.author.name.lower():
                return

            # Get message content (text or embed)
            content = message.content
            if not content and message.embeds:
                embed = message.embeds[0]
                content = embed.description or ""
                if embed.fields:
                    content = " ".join(f.value for f in embed.fields)

            if not content:
                return

            # Parse NuntioBot message format
            alert = parse_nuntio_message(content)
            if not alert:
                logger.debug("nuntio_parse_failed", content=content[:100])
                return

            # Market cap filter
            if alert.market_cap > self.limit:
                logger.debug("nuntio_mcap_filtered", ticker=alert.ticker, mc=alert.market_cap)
                return

            # Save to MongoDB raw zone
            await self.save_raw(
                source_id=str(message.id),
                payload=alert.model_dump() | {"channel_id": str(message.channel.id)},
            )

        # Run client — blocks until shutdown
        try:
            await client.start(self.token)
        except Exception as e:
            if not self._shutdown.is_set():
                logger.error("discord_error", error=str(e))

    def shutdown(self) -> None:
        """Signal graceful shutdown."""
        logger.info("discord_shutdown_requested")
        self._shutdown.set()


async def main():
    """Entrypoint for running Discord collector as standalone process."""
    collector = DiscordNuntioCollector()
    await collector.setup()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, collector.shutdown)

    try:
        await collector.collect()
    finally:
        await collector.teardown()
        logger.info("discord_collector_stopped")


if __name__ == "__main__":
    asyncio.run(main())
