"""SQLAlchemy model for social media sentiment (PostgreSQL clean zone)."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class SocialSentiment(Base):
    """Aggregated social sentiment from Reddit/StockTwits posts."""

    __tablename__ = "social_sentiments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticker: Mapped[str] = mapped_column(String(10), index=True)
    platform: Mapped[str] = mapped_column(String(20))  # "reddit" | "stocktwits"
    post_title: Mapped[str] = mapped_column(Text)
    post_body: Mapped[str | None] = mapped_column(Text, nullable=True)
    post_score: Mapped[int] = mapped_column(Integer, default=0)
    subreddit: Mapped[str | None] = mapped_column(String(50), nullable=True)
    sentiment_score: Mapped[float] = mapped_column(Float)  # -1.0 to 1.0
    sentiment_label: Mapped[str] = mapped_column(String(20))  # bullish/bearish/neutral
    tickers: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    source_id: Mapped[str] = mapped_column(String(255))
    posted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    collected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    raw_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    __table_args__ = (
        UniqueConstraint("platform", "source_id", name="uq_social_platform_source_id"),
        Index("ix_social_posted_at", "posted_at"),
        Index("ix_social_platform", "platform"),
        Index("ix_social_sentiment", "sentiment_score"),
    )
