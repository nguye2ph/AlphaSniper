"""Taskiq broker configuration and scheduled task definitions."""

import uuid
from datetime import datetime, timezone

import structlog
from taskiq_redis import ListQueueBroker

from src.core.config import settings

logger = structlog.get_logger()

# Redis-backed broker for task queue
broker = ListQueueBroker(url=settings.redis_url)


@broker.task()
async def collect_finnhub_rest():
    """Scheduled: poll Finnhub REST API for market + company news."""
    from src.collectors.finnhub_rest import FinnhubRest

    collector = FinnhubRest()
    await collector.setup()
    try:
        await collector.collect()
    finally:
        await collector.teardown()


@broker.task()
async def collect_marketaux():
    """Scheduled: poll MarketAux API for global news."""
    from src.collectors.marketaux_rest import MarketAuxRest

    collector = MarketAuxRest()
    await collector.setup()
    try:
        await collector.collect()
    finally:
        await collector.teardown()


@broker.task()
async def collect_sec_edgar():
    """Scheduled: poll SEC EDGAR for 8-K filings."""
    from src.collectors.sec_edgar_rss import SecEdgarCollector

    collector = SecEdgarCollector()
    await collector.setup()
    try:
        await collector.collect()
    finally:
        await collector.teardown()


@broker.task()
async def process_raw_articles(batch_size: int = 50):
    """Process unprocessed raw articles: dedup → parse → insert to PostgreSQL."""
    import redis.asyncio as aioredis
    from sqlalchemy import select

    from src.core.database import async_session_factory, init_mongo, close_mongo
    from src.core.models.article import Article
    from src.core.models.raw_article import RawArticle
    from src.parsers.dedup import DedupChecker
    from src.parsers.headline_parser import parse_headline

    await init_mongo()
    redis_client = aioredis.from_url(settings.redis_url, decode_responses=True)
    dedup = DedupChecker(redis_client)

    try:
        # Fetch unprocessed raw articles
        raw_docs = await RawArticle.find(
            RawArticle.is_processed == False  # noqa: E712
        ).sort("-collected_at").limit(batch_size).to_list()

        if not raw_docs:
            logger.info("no_unprocessed_articles")
            return

        logger.info("processing_batch", count=len(raw_docs))
        processed = 0

        async with async_session_factory() as session:
            for raw in raw_docs:
                # Dedup check
                is_new = await dedup.check_and_mark(raw.source, raw.source_id)
                if not is_new:
                    raw.is_processed = True
                    await raw.save()
                    continue

                # Extract headline from payload (varies by source)
                headline = _extract_headline(raw.source, raw.payload)
                url = raw.payload.get("url", "")
                published_at = _extract_timestamp(raw.source, raw.payload)

                # Parse headline
                parsed = parse_headline(headline)

                # Also use tickers from payload if available
                payload_tickers = _extract_payload_tickers(raw.source, raw.payload)
                all_tickers = list(dict.fromkeys(payload_tickers + parsed.tickers))

                # Create clean article and commit individually
                article = Article(
                    id=uuid.uuid4(),
                    source=raw.source,
                    source_id=raw.source_id,
                    headline=headline,
                    summary=raw.payload.get("summary", ""),
                    url=url,
                    published_at=published_at,
                    tickers=all_tickers,
                    sentiment=parsed.sentiment,
                    sentiment_label=parsed.sentiment_label,
                    category=parsed.category,
                    raw_article_id=str(raw.id),
                    raw_data=raw.payload,
                )
                try:
                    session.add(article)
                    await session.commit()
                    processed += 1
                except Exception as e:
                    await session.rollback()
                    logger.warning("article_insert_error", source_id=raw.source_id, error=str(e)[:100])

                # Mark raw as processed regardless
                raw.is_processed = True
                await raw.save()

        logger.info("batch_processed", processed=processed, total=len(raw_docs))

    finally:
        await redis_client.close()
        await close_mongo()


def _extract_headline(source: str, payload: dict) -> str:
    """Extract headline from raw payload based on source format."""
    if source == "finnhub":
        return payload.get("headline", "")
    elif source == "marketaux":
        return payload.get("title", "")
    elif source == "sec_edgar":
        return payload.get("entity_name", "") + " - " + payload.get("form_type", "8-K")
    return payload.get("headline", payload.get("title", ""))


def _extract_timestamp(source: str, payload: dict) -> datetime:
    """Extract publish timestamp from raw payload."""
    if source == "finnhub":
        ts = payload.get("datetime", 0)
        if ts:
            return datetime.fromtimestamp(ts, tz=timezone.utc)
    elif source == "marketaux":
        dt_str = payload.get("published_at", "")
        if dt_str:
            try:
                return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
            except ValueError:
                pass
    elif source == "sec_edgar":
        date_str = payload.get("filed_at", "")
        if date_str:
            try:
                return datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            except ValueError:
                pass
    return datetime.now(timezone.utc)


def _extract_payload_tickers(source: str, payload: dict) -> list[str]:
    """Extract ticker symbols directly from payload data."""
    if source == "finnhub":
        related = payload.get("related", "")
        return [t.strip() for t in related.split(",") if t.strip()] if related else []
    elif source == "marketaux":
        entities = payload.get("entities", [])
        return [e.get("symbol", "") for e in entities if e.get("symbol")]
    elif source == "sec_edgar":
        ticker = payload.get("ticker")
        return [ticker] if ticker else []
    return []
