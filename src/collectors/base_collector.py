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

    async def setup(self) -> None:
        """Initialize DB connections before collecting."""
        await init_mongo()

    async def teardown(self) -> None:
        """Cleanup DB connections."""
        await close_mongo()
