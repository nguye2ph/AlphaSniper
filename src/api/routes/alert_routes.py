"""Alert rule CRUD endpoints — create, list, update, delete alert rules."""

import uuid
from datetime import datetime

import structlog
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_db
from src.core.models.alert_rule import AlertRule

logger = structlog.get_logger()
router = APIRouter(prefix="/api/alerts", tags=["alerts"])


# --- Schemas ---


class AlertRuleCreate(BaseModel):
    name: str
    conditions: list[dict]
    ticker_filter: list[str] | None = None
    action: str = "discord_webhook"
    cooldown_minutes: int = 60


class AlertRuleUpdate(BaseModel):
    name: str | None = None
    enabled: bool | None = None
    conditions: list[dict] | None = None
    ticker_filter: list[str] | None = None
    action: str | None = None
    cooldown_minutes: int | None = None


class AlertRuleResponse(BaseModel):
    id: uuid.UUID
    name: str
    enabled: bool
    conditions: list[dict]
    ticker_filter: list[str] | None
    action: str
    cooldown_minutes: int
    last_triggered_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Routes ---


@router.get("/rules", response_model=list[AlertRuleResponse])
async def list_rules(db: AsyncSession = Depends(get_db)):
    """List all alert rules ordered by creation date."""
    result = await db.execute(select(AlertRule).order_by(AlertRule.created_at.desc()))
    return result.scalars().all()


@router.post("/rules", response_model=AlertRuleResponse, status_code=201)
async def create_rule(body: AlertRuleCreate, db: AsyncSession = Depends(get_db)):
    """Create a new alert rule."""
    rule = AlertRule(
        id=uuid.uuid4(),
        name=body.name,
        conditions=body.conditions,
        ticker_filter=body.ticker_filter,
        action=body.action,
        cooldown_minutes=body.cooldown_minutes,
    )
    db.add(rule)
    await db.commit()
    await db.refresh(rule)
    logger.info("alert_rule_created", rule_id=str(rule.id), name=rule.name)
    return rule


@router.put("/rules/{rule_id}", response_model=AlertRuleResponse)
async def update_rule(rule_id: uuid.UUID, body: AlertRuleUpdate, db: AsyncSession = Depends(get_db)):
    """Update an existing alert rule (partial update)."""
    result = await db.execute(select(AlertRule).where(AlertRule.id == rule_id))
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="Alert rule not found")

    for field, value in body.model_dump(exclude_none=True).items():
        setattr(rule, field, value)

    await db.commit()
    await db.refresh(rule)
    logger.info("alert_rule_updated", rule_id=str(rule_id))
    return rule


@router.delete("/rules/{rule_id}", status_code=204)
async def delete_rule(rule_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Delete an alert rule."""
    result = await db.execute(select(AlertRule).where(AlertRule.id == rule_id))
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="Alert rule not found")

    await db.delete(rule)
    await db.commit()
    logger.info("alert_rule_deleted", rule_id=str(rule_id))
