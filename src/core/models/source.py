"""SQLAlchemy model for data source tracking."""

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class Source(Base):
    """Tracks data source status and collection metadata."""

    __tablename__ = "sources"

    name: Mapped[str] = mapped_column(String(50), primary_key=True)  # "finnhub"
    source_type: Mapped[str] = mapped_column(String(20))  # "api" | "rss" | "websocket"
    base_url: Mapped[str] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_collected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    article_count: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
