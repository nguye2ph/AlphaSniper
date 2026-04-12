"""SQLAlchemy model for tracked ticker symbols."""

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, String
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class Ticker(Base):
    """Stock ticker symbol with metadata for watchlist management."""

    __tablename__ = "tickers"

    symbol: Mapped[str] = mapped_column(String(10), primary_key=True)  # e.g. "AAPL"
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)  # "Apple Inc."
    exchange: Mapped[str | None] = mapped_column(String(50), nullable=True)  # "NASDAQ"
    market_cap: Mapped[float | None] = mapped_column(Float, nullable=True)  # USD
    sector: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)  # On watchlist?
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
