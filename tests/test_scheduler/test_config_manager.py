"""Tests for scheduler config manager — Redis CRUD operations."""

import pytest
import redis.asyncio as aioredis

from src.scheduler.config_manager import (
    delete_config,
    get_config,
    list_configs,
    seed_defaults,
    set_config,
)
from src.scheduler.models import SourceScheduleConfig


@pytest.fixture
async def redis():
    """Provide a clean Redis connection for each test."""
    client = aioredis.from_url("redis://localhost:6379/1", decode_responses=True)
    # Clean scheduler keys before test
    async for key in client.scan_iter("scheduler:*"):
        await client.delete(key)
    yield client
    # Cleanup after test
    async for key in client.scan_iter("scheduler:*"):
        await client.delete(key)
    await client.aclose()


@pytest.mark.asyncio
async def test_set_and_get_config(redis):
    config = SourceScheduleConfig(name="test_source", current_interval_seconds=120)
    await set_config(redis, config)

    result = await get_config(redis, "test_source")
    assert result is not None
    assert result.name == "test_source"
    assert result.current_interval_seconds == 120
    assert result.enabled is True


@pytest.mark.asyncio
async def test_get_nonexistent_config(redis):
    result = await get_config(redis, "nonexistent")
    assert result is None


@pytest.mark.asyncio
async def test_list_configs(redis):
    await set_config(redis, SourceScheduleConfig(name="source_a"))
    await set_config(redis, SourceScheduleConfig(name="source_b"))

    configs = await list_configs(redis)
    assert len(configs) == 2
    names = [c.name for c in configs]
    assert "source_a" in names
    assert "source_b" in names


@pytest.mark.asyncio
async def test_delete_config(redis):
    await set_config(redis, SourceScheduleConfig(name="to_delete"))
    assert await delete_config(redis, "to_delete") is True
    assert await get_config(redis, "to_delete") is None
    # Delete nonexistent returns False
    assert await delete_config(redis, "to_delete") is False


@pytest.mark.asyncio
async def test_seed_defaults_no_overwrite(redis):
    count = await seed_defaults(redis)
    assert count == 7

    configs = await list_configs(redis)
    assert len(configs) == 7

    # Second seed should skip existing
    count2 = await seed_defaults(redis)
    assert count2 == 0


@pytest.mark.asyncio
async def test_seed_defaults_with_overwrite(redis):
    await seed_defaults(redis)
    # Modify one
    cfg = await get_config(redis, "finnhub_rest")
    cfg.current_interval_seconds = 999
    await set_config(redis, cfg)

    # Overwrite resets it
    await seed_defaults(redis, overwrite=True)
    cfg2 = await get_config(redis, "finnhub_rest")
    assert cfg2.current_interval_seconds == 300


@pytest.mark.asyncio
async def test_config_validation_bounds():
    """Pydantic validation rejects out-of-bounds values."""
    with pytest.raises(Exception):
        SourceScheduleConfig(name="bad", min_interval_seconds=5)  # ge=10


@pytest.mark.asyncio
async def test_update_config_preserves_fields(redis):
    config = SourceScheduleConfig(
        name="test_update",
        current_interval_seconds=200,
        ema_alpha=0.5,
    )
    await set_config(redis, config)

    # Update one field
    loaded = await get_config(redis, "test_update")
    loaded.current_interval_seconds = 400
    await set_config(redis, loaded)

    reloaded = await get_config(redis, "test_update")
    assert reloaded.current_interval_seconds == 400
    assert reloaded.ema_alpha == 0.5  # preserved
