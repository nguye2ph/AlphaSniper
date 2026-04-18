"""Bridge between Redis configs and Taskiq ListRedisScheduleSource.

Reads all SourceScheduleConfigs, converts intervals to ScheduledTask entries,
and pushes them to the ListRedisScheduleSource so Taskiq picks them up dynamically.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

if TYPE_CHECKING:
    import redis.asyncio as aioredis
from taskiq import ScheduledTask
from taskiq_redis import ListRedisScheduleSource

from src.core.config import settings
from src.scheduler import config_manager
from src.scheduler.models import SourceScheduleConfig

logger = structlog.get_logger()

# Maps source config name -> taskiq task name (fully qualified)
TASK_NAME_MAP: dict[str, str] = {
    "finnhub_rest": "src.jobs.taskiq_app:collect_finnhub_rest",
    "marketaux": "src.jobs.taskiq_app:collect_marketaux",
    "sec_edgar": "src.jobs.taskiq_app:collect_sec_edgar",
    "tickertick": "src.jobs.taskiq_app:collect_tickertick",
    "scrape_content": "src.jobs.taskiq_app:scrape_unscraped_articles",
    "process_raw": "src.jobs.taskiq_app:process_raw_articles",
    "adjust_schedules": "src.jobs.taskiq_app:adjust_schedules",
    # Phase 2: Tier 1 sources
    "reddit": "src.jobs.taskiq_app:collect_reddit",
    "openinsider": "src.jobs.taskiq_app:collect_openinsider",
    "earnings_calendar": "src.jobs.taskiq_app:collect_earnings",
    "rss_feeds": "src.jobs.taskiq_app:collect_rss_feeds",
    # Phase 3: Tier 2 sources
    "stocktwits": "src.jobs.taskiq_app:collect_stocktwits",
    "ortex": "src.jobs.taskiq_app:collect_ortex",
    "unusual_whales": "src.jobs.taskiq_app:collect_unusual_whales",
}


def _interval_to_cron(seconds: int) -> str:
    """Convert interval in seconds to closest cron expression.

    Supports: every N minutes (60-3540s) and every N hours (3600+s).
    Falls back to minute-based for non-round values.
    """
    if seconds < 60:
        return "* * * * *"  # every minute minimum
    minutes = seconds // 60
    if minutes <= 59:
        return f"*/{minutes} * * * *"
    hours = minutes // 60
    return f"0 */{hours} * * *"


def config_to_scheduled_task(config: SourceScheduleConfig) -> ScheduledTask | None:
    """Convert a SourceScheduleConfig to a Taskiq ScheduledTask.

    Returns None if config is disabled or has no mapped task.
    """
    if not config.enabled:
        return None
    task_name = TASK_NAME_MAP.get(config.name)
    if not task_name:
        logger.warning("no_task_mapping", source=config.name)
        return None

    cron_expr = _interval_to_cron(config.current_interval_seconds)
    return ScheduledTask(
        task_name=task_name,
        labels={},
        args=[],
        kwargs={},
        schedule_id=f"adaptive:{config.name}",
        cron=cron_expr,
    )


def create_schedule_source() -> ListRedisScheduleSource:
    """Create a ListRedisScheduleSource connected to Redis."""
    return ListRedisScheduleSource(url=settings.redis_url)


async def sync_schedules(
    schedule_source: ListRedisScheduleSource,
    redis: aioredis.Redis | None = None,
) -> int:
    """Read all configs from Redis and sync to ListRedisScheduleSource.

    Clears existing adaptive schedules, then pushes current configs.
    Returns count of schedules synced.
    """
    import redis.asyncio as aioredis

    close_after = False
    if redis is None:
        redis = aioredis.from_url(settings.redis_url, decode_responses=True)
        close_after = True
    try:
        configs = await config_manager.list_configs(redis)
    finally:
        if close_after:
            await redis.close()

    # Remove existing adaptive schedules
    existing = await schedule_source.get_schedules()
    for task in existing:
        if task.schedule_id.startswith("adaptive:"):
            await schedule_source.delete_schedule(task.schedule_id)

    # Add current configs
    synced = 0
    for cfg in configs:
        scheduled = config_to_scheduled_task(cfg)
        if scheduled:
            await schedule_source.add_schedule(scheduled)
            synced += 1
            logger.debug("schedule_synced", source=cfg.name, interval=cfg.current_interval_seconds)

    logger.info("schedules_synced", count=synced, total_configs=len(configs))
    return synced
