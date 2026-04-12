"""Tests for Redis-based deduplication."""

import pytest
import redis.asyncio as aioredis

from src.parsers.dedup import DedupChecker


@pytest.fixture
async def dedup():
    """Create DedupChecker with real Redis connection."""
    r = aioredis.from_url("redis://localhost:6379/0", decode_responses=True)
    checker = DedupChecker(r)
    yield checker
    # Cleanup test keys
    keys = [k async for k in r.scan_iter("dedup:test_*")]
    if keys:
        await r.delete(*keys)
    await r.aclose()


@pytest.mark.asyncio
async def test_new_article_is_not_duplicate(dedup):
    is_new = await dedup.check_and_mark("test_src", "new-001")
    assert is_new is True


@pytest.mark.asyncio
async def test_same_article_is_duplicate(dedup):
    await dedup.check_and_mark("test_src", "dup-001")
    is_new = await dedup.check_and_mark("test_src", "dup-001")
    assert is_new is False


@pytest.mark.asyncio
async def test_different_source_same_id_is_new(dedup):
    await dedup.check_and_mark("test_src_a", "cross-001")
    is_new = await dedup.check_and_mark("test_src_b", "cross-001")
    assert is_new is True


@pytest.mark.asyncio
async def test_is_duplicate_check_only(dedup):
    assert await dedup.is_duplicate("test_src", "check-001") is False
    await dedup.mark_seen("test_src", "check-001")
    assert await dedup.is_duplicate("test_src", "check-001") is True
