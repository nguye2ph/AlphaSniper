"""Abstract base class for all data source collectors."""

import abc
from datetime import datetime, timezone

import structlog

from src.core.database import close_mongo, init_mongo
from src.core.models.raw_article import RawArticle

logger = structlog.get_logger()


class BaseCollector(abc.ABC):
    """Interface all collectors must implement."""

    source_name: str = "unknown"

    @abc.abstractmethod
    async def collect(self) -> None:
        """Main collection loop — run continuously or poll once."""
        ...

    async def save_raw(self, source_id: str, payload: dict) -> RawArticle | None:
        """Save raw API response to MongoDB. Returns None if duplicate."""
        existing = await RawArticle.find_one(
            RawArticle.source == self.source_name,
            RawArticle.source_id == source_id,
        )
        if existing:
            logger.debug("duplicate_skipped", source=self.source_name, source_id=source_id)
            return None

        doc = RawArticle(
            source=self.source_name,
            source_id=source_id,
            payload=payload,
            collected_at=datetime.now(timezone.utc),
        )
        await doc.insert()
        logger.info("article_saved", source=self.source_name, source_id=source_id)
        return doc

    async def report_metrics(
        self,
        articles_count: int,
        had_error: bool = False,
        is_rate_limit: bool = False,
    ) -> None:
        """Report poll metrics to the adaptive scheduler.

        Call after each collect() cycle with the number of articles found.
        """
        try:
            from src.core.database import get_redis
            from src.scheduler.config_manager import get_config
            from src.scheduler.metrics_tracker import record_poll

            redis = await get_redis()
            # Get source-specific EMA alpha, fallback to default
            config = await get_config(redis, self.source_name)
            ema_alpha = config.ema_alpha if config else 0.3
            await record_poll(redis, self.source_name, articles_count, had_error, is_rate_limit, ema_alpha)
        except Exception as e:
            # Never let metrics reporting break collection
            logger.warning("metrics_report_failed", source=self.source_name, error=str(e)[:100])

    async def setup(self) -> None:
        """Initialize DB connections before collecting."""
        await init_mongo()

    async def teardown(self) -> None:
        """Cleanup DB connections."""
        await close_mongo()
