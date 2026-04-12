"""API endpoint tests against running Docker container.

Requires: `docker compose up -d` with api service running on port 8200.
"""

import uuid
from datetime import datetime, timezone

import httpx
import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from src.core.config import settings

BASE_URL = "http://localhost:8200"


@pytest.fixture
async def db_with_sample():
    """Insert sample article via separate engine, cleanup after test."""
    engine = create_async_engine(settings.postgres_url, pool_size=1)
    source_id = f"test-api-{uuid.uuid4().hex[:8]}"
    article_id = uuid.uuid4()

    async with engine.begin() as conn:
        await conn.execute(text("""
            INSERT INTO articles (id, source, source_id, headline, summary, url,
                published_at, collected_at, tickers, sentiment, sentiment_label, category)
            VALUES (:id, 'finnhub', :sid, '$AAPL surges on earnings beat',
                'Apple Q3 exceeded', 'https://test.com/aapl',
                :ts, :ts, ARRAY['AAPL'], 0.85, 'bullish', 'earnings')
        """), {"id": str(article_id), "sid": source_id, "ts": datetime.now(timezone.utc)})

    yield source_id

    async with engine.begin() as conn:
        await conn.execute(text("DELETE FROM articles WHERE source_id = :sid"), {"sid": source_id})
    await engine.dispose()


@pytest.mark.asyncio
async def test_health():
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{BASE_URL}/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_list_articles():
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{BASE_URL}/api/articles")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_latest_articles():
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{BASE_URL}/api/articles/latest?limit=5")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_article_stats():
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{BASE_URL}/api/articles/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert "total_count" in data
    assert "by_source" in data


@pytest.mark.asyncio
async def test_list_tickers():
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{BASE_URL}/api/tickers")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_list_sources():
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{BASE_URL}/api/sources")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_filter_by_ticker(db_with_sample):
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{BASE_URL}/api/articles?ticker=AAPL")
    assert resp.status_code == 200
    articles = resp.json()
    assert len(articles) >= 1
    assert any(a["source_id"] == db_with_sample for a in articles)


@pytest.mark.asyncio
async def test_filter_by_sentiment(db_with_sample):
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{BASE_URL}/api/articles?sentiment_gte=0.5")
    assert resp.status_code == 200
    assert all(a["sentiment"] >= 0.5 for a in resp.json())


@pytest.mark.asyncio
async def test_ticker_news(db_with_sample):
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{BASE_URL}/api/tickers/AAPL/news")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1
