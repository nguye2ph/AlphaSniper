"""MongoDB Beanie document for raw social media posts (Reddit, StockTwits)."""

from datetime import datetime, timezone

from beanie import Document, Indexed
from pydantic import Field


class RawSocialPost(Document):
    """Raw social media post before sentiment parsing."""

    source: Indexed(str)  # "reddit" | "stocktwits"
    source_id: str  # Reddit post ID or StockTwits message ID
    payload: dict  # Raw post data as-is
    collected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_processed: bool = False

    class Settings:
        name = "raw_social_posts"
        indexes = [
            [("source", 1), ("source_id", 1)],
            [("is_processed", 1), ("collected_at", -1)],
        ]
