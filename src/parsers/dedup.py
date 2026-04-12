"""Redis-based article deduplication. Uses SET with TTL to track seen articles."""

import redis.asyncio as aioredis
import structlog

logger = structlog.get_logger()

DEDUP_PREFIX = "dedup"
DEDUP_TTL = 7 * 24 * 3600  # 7 days


class DedupChecker:
    """Check if an article has already been processed using Redis SET."""

    def __init__(self, redis: aioredis.Redis):
        self.redis = redis

    def _key(self, source: str, source_id: str) -> str:
        return f"{DEDUP_PREFIX}:{source}:{source_id}"

    async def is_duplicate(self, source: str, source_id: str) -> bool:
        """Check if article was already seen. Returns True if duplicate."""
        key = self._key(source, source_id)
        exists = await self.redis.exists(key)
        return bool(exists)

    async def mark_seen(self, source: str, source_id: str) -> None:
        """Mark article as seen with TTL."""
        key = self._key(source, source_id)
        await self.redis.set(key, "1", ex=DEDUP_TTL)

    async def check_and_mark(self, source: str, source_id: str) -> bool:
        """Atomic check-and-mark. Returns True if NEW (not duplicate)."""
        key = self._key(source, source_id)
        # SET NX returns True if key was set (new), None if exists (dup)
        result = await self.redis.set(key, "1", ex=DEDUP_TTL, nx=True)
        is_new = result is not None
        if not is_new:
            logger.debug("dedup_skip", source=source, source_id=source_id)
        return is_new
