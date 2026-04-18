"""Redis JSON CRUD for per-source scheduling configuration."""


import redis.asyncio as aioredis
import structlog

from src.scheduler.models import SourceScheduleConfig

logger = structlog.get_logger()

# Redis key prefix for source configs
CONFIG_PREFIX = "scheduler:sources"


# Default configs for existing sources + adjustment task
DEFAULT_SOURCES: list[dict] = [
    {"name": "finnhub_rest", "current_interval_seconds": 300,
     "min_interval_seconds": 120, "max_interval_seconds": 1800},
    {"name": "marketaux", "current_interval_seconds": 900,
     "min_interval_seconds": 600, "max_interval_seconds": 3600},
    {"name": "sec_edgar", "current_interval_seconds": 1800,
     "min_interval_seconds": 900, "max_interval_seconds": 7200},
    {"name": "tickertick", "current_interval_seconds": 60,
     "min_interval_seconds": 60, "max_interval_seconds": 600},
    {"name": "scrape_content", "current_interval_seconds": 300,
     "min_interval_seconds": 120, "max_interval_seconds": 1800,
     "strategy": "manual"},
    {"name": "process_raw", "current_interval_seconds": 120,
     "min_interval_seconds": 60, "max_interval_seconds": 600,
     "strategy": "manual"},
    {"name": "adjust_schedules", "current_interval_seconds": 3600,
     "min_interval_seconds": 1800, "max_interval_seconds": 7200,
     "strategy": "manual"},
]


def _key(source_name: str) -> str:
    return f"{CONFIG_PREFIX}:{source_name}"


async def get_config(redis: aioredis.Redis, source_name: str) -> SourceScheduleConfig | None:
    """Get scheduling config for a source. Returns None if not found."""
    data = await redis.get(_key(source_name))
    if data is None:
        return None
    return SourceScheduleConfig.model_validate_json(data)


async def set_config(redis: aioredis.Redis, config: SourceScheduleConfig) -> None:
    """Save/update scheduling config for a source (atomic)."""
    await redis.set(_key(config.name), config.model_dump_json())
    logger.info("config_updated", source=config.name, interval=config.current_interval_seconds)


async def list_configs(redis: aioredis.Redis) -> list[SourceScheduleConfig]:
    """List all source configs from Redis."""
    keys = []
    async for key in redis.scan_iter(f"{CONFIG_PREFIX}:*"):
        keys.append(key)
    if not keys:
        return []
    values = await redis.mget(keys)
    configs = []
    for val in values:
        if val:
            try:
                configs.append(SourceScheduleConfig.model_validate_json(val))
            except Exception:
                logger.warning("invalid_config_json", value=str(val)[:100])
    return sorted(configs, key=lambda c: c.name)


async def delete_config(redis: aioredis.Redis, source_name: str) -> bool:
    """Delete a source config. Returns True if existed."""
    deleted = await redis.delete(_key(source_name))
    return deleted > 0


async def seed_defaults(redis: aioredis.Redis, overwrite: bool = False) -> int:
    """Populate Redis with default configs for existing sources.

    Returns count of configs seeded.
    """
    seeded = 0
    for defaults in DEFAULT_SOURCES:
        name = defaults["name"]
        if not overwrite:
            existing = await redis.get(_key(name))
            if existing:
                continue
        config = SourceScheduleConfig(**defaults)
        await set_config(redis, config)
        seeded += 1
    logger.info("configs_seeded", count=seeded, overwrite=overwrite)
    return seeded
