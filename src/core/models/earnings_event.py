"""SQLAlchemy model for earnings calendar events (PostgreSQL clean zone)."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, Index, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class EarningsEvent(Base):
    """Upcoming or reported earnings event for a ticker."""

    __tablename__ = "earnings_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticker: Mapped[str] = mapped_column(String(10), index=True)
    report_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    estimated_eps: Mapped[float | None] = mapped_column(Float, nullable=True)
    actual_eps: Mapped[float | None] = mapped_column(Float, nullable=True)
    estimated_revenue: Mapped[float | None] = mapped_column(Float, nullable=True)
    actual_revenue: Mapped[float | None] = mapped_column(Float, nullable=True)
    surprise_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    source: Mapped[str] = mapped_column(String(50), default="earnings_calendar")
    source_id: Mapped[str] = mapped_column(String(255))
    collected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        UniqueConstraint("source", "source_id", name="uq_earnings_source_id"),
        Index("ix_earnings_report_date", "report_date"),
    )
