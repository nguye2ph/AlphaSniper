"""SQLAlchemy model for short interest data (PostgreSQL clean zone)."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, Index, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class ShortInterest(Base):
    """Daily short interest snapshot for a ticker from ORTEX."""

    __tablename__ = "short_interests"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticker: Mapped[str] = mapped_column(String(10), index=True)
    short_pct_float: Mapped[float] = mapped_column(Float)  # % of float shorted
    days_to_cover: Mapped[float] = mapped_column(Float, default=0.0)
    borrow_fee_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    squeeze_score: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 0-100
    report_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    source: Mapped[str] = mapped_column(String(50), default="ortex")
    source_id: Mapped[str] = mapped_column(String(255))
    raw_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    collected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        UniqueConstraint("source", "source_id", name="uq_short_interest_source_id"),
        Index("ix_short_interest_report_date", "report_date"),
        Index("ix_short_interest_squeeze", "squeeze_score"),
    )
