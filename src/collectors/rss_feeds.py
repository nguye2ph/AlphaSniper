"""RSS feed collector — Yahoo Finance, CNBC, and other financial news feeds."""

import asyncio
import hashlib

import feedparser
import structlog

from src.collectors.base_collector import BaseCollector
from src.core.config import settings

logger = structlog.get_logger()


class RssFeeds(BaseCollector):
    """Polls multiple RSS feeds for financial news. Free, unlimited, no auth."""

    source_name = "rss_feeds"

    def __init__(self):
        self.feed_urls = settings.rss_feed_urls

    async def collect(self) -> None:
        loop = asyncio.get_running_loop()
        for url in self.feed_urls:
            try:
                # feedparser does network I/O — run in thread pool
                feed = await loop.run_in_executor(None, feedparser.parse, url)
                await self._save_entries(feed, url)
            except Exception as e:
                logger.error("rss_feed_error", url=url[:80], error=str(e)[:100])

    async def _save_entries(self, feed, url: str) -> int:
        """Save feed entries to MongoDB. Returns saved count."""
        if feed.bozo and not feed.entries:
            logger.warning("rss_parse_error", url=url[:80], error=str(feed.bozo_exception)[:80])
            return 0

        saved = 0
        for entry in feed.entries:
            link = entry.get("link", "")
            title = entry.get("title", "")
            if not link or not title:
                continue

            source_id = hashlib.sha256(link.encode()).hexdigest()[:32]

            payload = {
                "title": title,
                "url": link,
                "summary": entry.get("summary", "")[:1000],
                "published": entry.get("published", ""),
                "source_feed": url,
                "author": entry.get("author", ""),
            }

            result = await self.save_raw(source_id=source_id, payload=payload)
            if result:
                saved += 1

        logger.info("rss_feed_parsed", url=url[:60], entries=len(feed.entries), saved=saved)
        return saved
