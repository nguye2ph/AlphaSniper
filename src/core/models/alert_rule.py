"""SQLAlchemy model for user-defined alert rules (PostgreSQL clean zone)."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.dialects.postgresql import ARRAY, JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class AlertRule(Base):
    """Alert rule that triggers a Discord notification when conditions are met."""

    __tablename__ = "alert_rules"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)

    # List of condition dicts: {"source": "insider_trade", "field": "value", "op": ">", "value": 500000}
    conditions: Mapped[list] = mapped_column(JSON, nullable=False)

    # None = all tickers, or a list like ["AAPL", "TSLA"]
    ticker_filter: Mapped[list[str] | None] = mapped_column(ARRAY(String(10)), nullable=True)

    # Action type — currently only "discord_webhook" supported
    action: Mapped[str] = mapped_column(String(50), default="discord_webhook")

    # Skip re-triggering within this window
    cooldown_minutes: Mapped[int] = mapped_column(Integer, default=60)
    last_triggered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
