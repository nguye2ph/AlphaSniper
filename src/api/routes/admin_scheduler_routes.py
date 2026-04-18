"""Admin endpoints for adaptive scheduler — config CRUD + metrics."""

from typing import Literal

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from src.core.database import get_redis
from src.scheduler import config_manager, metrics_tracker

router = APIRouter(prefix="/api/admin/scheduler", tags=["admin-scheduler"])


class ConfigUpdate(BaseModel):
    """Partial config update — only provided fields are applied."""

    enabled: bool | None = None
    min_interval_seconds: int | None = None
    max_interval_seconds: int | None = None
    current_interval_seconds: int | None = None
    strategy: Literal["rate_based", "manual"] | None = None
    ema_alpha: float | None = None
    articles_per_poll_high: int | None = None
    articles_per_poll_low: int | None = None
    max_rate_errors: int | None = None
    adjustment_cooldown_seconds: int | None = None


@router.get("/sources")
async def list_sources(redis: aioredis.Redis = Depends(get_redis)):
    """List all source configs with their current metrics."""
    configs = await config_manager.list_configs(redis)
    result = []
    for cfg in configs:
        metrics = await metrics_tracker.get_metrics(redis, cfg.name)
        result.append({"config": cfg.model_dump(), "metrics": metrics.model_dump()})
    return result


@router.get("/sources/{name}/config")
async def get_source_config(name: str, redis: aioredis.Redis = Depends(get_redis)):
    """Get config for a specific source."""
    config = await config_manager.get_config(redis, name)
    if not config:
        raise HTTPException(404, f"Source '{name}' not found")
    return config.model_dump()


@router.post("/sources/{name}/config")
async def update_source_config(
    name: str,
    body: ConfigUpdate,
    redis: aioredis.Redis = Depends(get_redis),
):
    """Update config for a source. Only provided fields are changed."""
    config = await config_manager.get_config(redis, name)
    if not config:
        raise HTTPException(404, f"Source '{name}' not found")

    updates = body.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(400, "No fields to update")

    updated = config.model_copy(update=updates)
    # Validate interval bounds
    if updated.current_interval_seconds < updated.min_interval_seconds:
        raise HTTPException(400, "current_interval cannot be below min_interval")
    if updated.current_interval_seconds > updated.max_interval_seconds:
        raise HTTPException(400, "current_interval cannot exceed max_interval")

    await config_manager.set_config(redis, updated)

    # Re-sync schedules to pick up change
    from src.jobs.taskiq_app import schedule_source
    from src.scheduler.scheduler_integration import sync_schedules

    await sync_schedules(schedule_source)

    return updated.model_dump()


@router.get("/metrics")
async def all_metrics(redis: aioredis.Redis = Depends(get_redis)):
    """Get metrics for all configured sources."""
    configs = await config_manager.list_configs(redis)
    result = {}
    for cfg in configs:
        metrics = await metrics_tracker.get_metrics(redis, cfg.name)
        result[cfg.name] = metrics.model_dump()
    return result


@router.post("/seed")
async def seed_configs(overwrite: bool = False, redis: aioredis.Redis = Depends(get_redis)):
    """Seed default configs for existing sources."""
    count = await config_manager.seed_defaults(redis, overwrite=overwrite)
    return {"seeded": count}


@router.post("/sync")
async def sync_all(redis: aioredis.Redis = Depends(get_redis)):
    """Force re-sync all schedules to Taskiq."""
    from src.jobs.taskiq_app import schedule_source
    from src.scheduler.scheduler_integration import sync_schedules

    synced = await sync_schedules(schedule_source)
    return {"synced": synced}
