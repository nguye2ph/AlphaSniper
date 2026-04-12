"""SQLAlchemy model for parsed/clean articles (PostgreSQL clean zone)."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class Article(Base):
    """Parsed, structured news article ready for querying."""

    __tablename__ = "articles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source: Mapped[str] = mapped_column(String(50))  # "finnhub" | "marketaux" | "sec_edgar"
    source_id: Mapped[str] = mapped_column(String(255))  # Original ID for dedup

    # Content
    headline: Mapped[str] = mapped_column(Text)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    url: Mapped[str] = mapped_column(Text)

    # Timestamps
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    collected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Extracted data
    tickers: Mapped[list[str]] = mapped_column(ARRAY(String(10)), default=list)
    sentiment: Mapped[float | None] = mapped_column(Float, nullable=True)  # -1.0 to 1.0
    sentiment_label: Mapped[str | None] = mapped_column(String(20), nullable=True)  # bullish/bearish/neutral
    market_cap: Mapped[float | None] = mapped_column(Float, nullable=True)  # USD
    category: Mapped[str | None] = mapped_column(String(50), nullable=True)  # earnings/insider/merger/etc

    # Reference to MongoDB raw document
    raw_article_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Backup: store raw API response
    raw_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    __table_args__ = (
        UniqueConstraint("source", "source_id", name="uq_article_source_id"),
        Index("ix_article_published_at", "published_at"),
        Index("ix_article_tickers", "tickers", postgresql_using="gin"),
        Index("ix_article_sentiment", "sentiment"),
        Index("ix_article_source", "source"),
    )
