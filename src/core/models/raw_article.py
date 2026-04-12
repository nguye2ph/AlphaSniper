"""MongoDB Beanie document for raw API responses (landing zone)."""

from datetime import datetime, timezone

from beanie import Document, Indexed
from pydantic import Field


class RawArticle(Document):
    """Stores raw API responses from any data source before parsing."""

    source: Indexed(str)  # "finnhub" | "marketaux" | "sec_edgar"
    source_id: str  # Original article/filing ID for dedup
    payload: dict  # Raw API response stored as-is
    collected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_processed: bool = False

    class Settings:
        name = "raw_articles"
        indexes = [
            # Compound index for dedup lookups
            [("source", 1), ("source_id", 1)],
            # Filter unprocessed articles for worker queue
            [("is_processed", 1), ("collected_at", -1)],
        ]
