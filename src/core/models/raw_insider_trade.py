"""MongoDB Beanie document for raw insider trade data (OpenInsider)."""

from datetime import datetime, timezone

from beanie import Document, Indexed
from pydantic import Field


class RawInsiderTrade(Document):
    """Raw insider trade record before parsing."""

    source: Indexed(str)  # "openinsider"
    source_id: str  # "{ticker}_{filing_date}_{officer}"
    payload: dict  # Raw scraped data
    collected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_processed: bool = False

    class Settings:
        name = "raw_insider_trades"
        indexes = [
            [("source", 1), ("source_id", 1)],
            [("is_processed", 1), ("collected_at", -1)],
        ]
