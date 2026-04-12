"""Full pipeline integration test: collect -> dedup -> parse -> query API."""

import uuid
from datetime import datetime, timezone

import httpx
import pytest
import redis.asyncio as aioredis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from src.core.config import settings
from src.core.database import init_mongo, close_mongo
from src.core.models.raw_article import RawArticle
from src.parsers.dedup import DedupChecker
from src.parsers.headline_parser import parse_headline

BASE_URL = "http://localhost:8200"


@pytest.mark.asyncio
async def test_full_pipeline_end_to_end():
    """Test: raw MongoDB -> dedup -> parse -> PostgreSQL -> API query."""
    await init_mongo()
    redis_client = aioredis.from_url("redis://localhost:6379/0", decode_responses=True)
    dedup = DedupChecker(redis_client)
    test_id = f"integ-{uuid.uuid4().hex[:8]}"
    test_engine = create_async_engine(settings.postgres_url, pool_size=1)

    try:
        # 1. Collector: save raw to MongoDB
        raw = RawArticle(
            source="finnhub",
            source_id=test_id,
            payload={
                "id": 999999,
                "headline": "$NVDA jumps 15% on AI chip demand surge",
                "summary": "NVIDIA reports record revenue",
                "url": "https://test.com/nvda",
                "datetime": int(datetime.now(timezone.utc).timestamp()),
                "related": "NVDA",
            },
        )
        await raw.insert()

        # 2. Dedup: should be new
        assert await dedup.check_and_mark(raw.source, raw.source_id) is True

        # 3. Parse headline
        parsed = parse_headline(raw.payload["headline"])
        assert "NVDA" in parsed.tickers
        assert parsed.sentiment_label == "bullish"

        # 4. Insert clean article to PostgreSQL
        article_id = uuid.uuid4()
        async with test_engine.begin() as conn:
            await conn.execute(text("""
                INSERT INTO articles (id, source, source_id, headline, summary, url,
                    published_at, collected_at, tickers, sentiment, sentiment_label,
                    category, raw_article_id)
                VALUES (:id, :src, :sid, :hl, :sum, :url,
                    :pub, :col, ARRAY['NVDA'], :sent, :label, :cat, :raw_id)
            """), {
                "id": str(article_id), "src": raw.source, "sid": test_id,
                "hl": raw.payload["headline"], "sum": raw.payload["summary"],
                "url": raw.payload["url"],
                "pub": datetime.now(timezone.utc), "col": datetime.now(timezone.utc),
                "sent": parsed.sentiment, "label": parsed.sentiment_label,
                "cat": parsed.category, "raw_id": str(raw.id),
            })

        # 5. Query via running API
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{BASE_URL}/api/articles?ticker=NVDA")
            assert resp.status_code == 200
            found = [a for a in resp.json() if a["source_id"] == test_id]
            assert len(found) == 1
            assert found[0]["sentiment_label"] == "bullish"
            assert "NVDA" in found[0]["tickers"]

        # 6. Dedup: should be duplicate now
        assert await dedup.check_and_mark(raw.source, raw.source_id) is False

        # Cleanup
        async with test_engine.begin() as conn:
            await conn.execute(text("DELETE FROM articles WHERE source_id = :sid"), {"sid": test_id})
        await raw.delete()

    finally:
        await redis_client.delete(f"dedup:finnhub:{test_id}")
        await redis_client.aclose()
        await test_engine.dispose()
        await close_mongo()
