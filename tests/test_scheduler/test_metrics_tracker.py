"""Tests for metrics tracker — record_poll, get_metrics, EMA updates."""

import pytest
import redis.asyncio as aioredis

from src.scheduler.metrics_tracker import get_metrics, record_poll, reset_metrics


@pytest.fixture
async def redis():
    """Provide a clean Redis connection for each test."""
    client = aioredis.from_url("redis://localhost:6379/1", decode_responses=True)
    async for key in client.scan_iter("scheduler:metrics:*"):
        await client.delete(key)
    yield client
    async for key in client.scan_iter("scheduler:metrics:*"):
        await client.delete(key)
    await client.aclose()


@pytest.mark.asyncio
async def test_record_poll_basic(redis):
    metrics = await record_poll(redis, "test_src", articles_count=10)
    assert metrics.articles_last_hour == 10
    assert metrics.ema > 0
    assert metrics.total_polls == 1
    assert metrics.last_poll_at is not None


@pytest.mark.asyncio
async def test_ema_accumulates(redis):
    # First poll
    m1 = await record_poll(redis, "test_src", articles_count=10, ema_alpha=0.3)
    assert m1.ema == pytest.approx(3.0)  # 0.3*10 + 0.7*0

    # Second poll
    m2 = await record_poll(redis, "test_src", articles_count=10, ema_alpha=0.3)
    assert m2.ema == pytest.approx(5.1)  # 0.3*10 + 0.7*3.0


@pytest.mark.asyncio
async def test_empty_response_counter(redis):
    m1 = await record_poll(redis, "test_src", articles_count=0)
    assert m1.empty_responses_count == 1

    m2 = await record_poll(redis, "test_src", articles_count=0)
    assert m2.empty_responses_count == 2

    # Non-empty resets counter
    m3 = await record_poll(redis, "test_src", articles_count=5)
    assert m3.empty_responses_count == 0


@pytest.mark.asyncio
async def test_error_tracking(redis):
    m1 = await record_poll(redis, "test_src", articles_count=0, had_error=True)
    assert m1.api_errors_last_hour == 1
    assert m1.rate_limit_errors == 0

    m2 = await record_poll(redis, "test_src", articles_count=0, had_error=True, is_rate_limit=True)
    assert m2.api_errors_last_hour == 2
    assert m2.rate_limit_errors == 1


@pytest.mark.asyncio
async def test_error_counters_reset_on_success(redis):
    await record_poll(redis, "test_src", articles_count=0, had_error=True, is_rate_limit=True)
    m = await record_poll(redis, "test_src", articles_count=5)
    assert m.api_errors_last_hour == 0
    assert m.rate_limit_errors == 0


@pytest.mark.asyncio
async def test_get_metrics_empty(redis):
    metrics = await get_metrics(redis, "nonexistent")
    assert metrics.total_polls == 0
    assert metrics.ema == 0.0
    assert metrics.last_poll_at is None


@pytest.mark.asyncio
async def test_get_metrics_after_polls(redis):
    await record_poll(redis, "test_src", articles_count=10)
    await record_poll(redis, "test_src", articles_count=20)

    metrics = await get_metrics(redis, "test_src")
    assert metrics.total_polls == 2
    assert metrics.articles_last_hour == 20
    assert metrics.last_poll_at is not None


@pytest.mark.asyncio
async def test_reset_metrics(redis):
    await record_poll(redis, "test_src", articles_count=10)
    await reset_metrics(redis, "test_src")
    metrics = await get_metrics(redis, "test_src")
    assert metrics.total_polls == 0
