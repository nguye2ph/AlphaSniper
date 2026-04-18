"""SQLAlchemy model for parsed insider trades (PostgreSQL clean zone)."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, Index, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class InsiderTrade(Base):
    """Parsed insider trade from OpenInsider or SEC Form 4."""

    __tablename__ = "insider_trades"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticker: Mapped[str] = mapped_column(String(10), index=True)
    officer_name: Mapped[str] = mapped_column(String(255))
    officer_title: Mapped[str] = mapped_column(String(255), default="")
    transaction_type: Mapped[str] = mapped_column(String(20))  # "buy" | "sell" | "exercise"
    shares: Mapped[int] = mapped_column(Integer)
    price: Mapped[float] = mapped_column(Float)
    value: Mapped[float] = mapped_column(Float)
    filing_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    source: Mapped[str] = mapped_column(String(50), default="openinsider")
    source_id: Mapped[str] = mapped_column(String(255))
    raw_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    collected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        UniqueConstraint("source", "source_id", name="uq_insider_trade_source_id"),
        Index("ix_insider_trade_filing_date", "filing_date"),
        Index("ix_insider_trade_type", "transaction_type"),
    )
