"""Taskiq broker configuration and scheduled task definitions."""

import uuid
from datetime import datetime, timezone

import structlog
from taskiq import TaskiqScheduler
from taskiq.schedule_sources import LabelScheduleSource
from taskiq_redis import ListQueueBroker

from src.core.config import settings

logger = structlog.get_logger()

# Redis-backed broker for task queue
broker = ListQueueBroker(url=settings.redis_url)

# Schedule source for taskiq scheduler
schedule_source = LabelScheduleSource(broker)
scheduler = TaskiqScheduler(broker=broker, sources=[schedule_source])


@broker.task(schedule=[{"cron": "*/5 * * * *"}])
async def collect_finnhub_rest():
    """Scheduled: poll Finnhub REST API for market + company news."""
    from src.collectors.finnhub_rest import FinnhubRest

    collector = FinnhubRest()
    await collector.setup()
    try:
        await collector.collect()
    finally:
        await collector.teardown()


@broker.task(schedule=[{"cron": "*/15 * * * *"}])
async def collect_marketaux():
    """Scheduled: poll MarketAux API every 15 min."""
    from src.collectors.marketaux_rest import MarketAuxRest

    collector = MarketAuxRest()
    await collector.setup()
    try:
        await collector.collect()
    finally:
        await collector.teardown()


@broker.task(schedule=[{"cron": "*/30 * * * *"}])
async def collect_sec_edgar():
    """Scheduled: poll SEC EDGAR every 30 min."""
    from src.collectors.sec_edgar_rss import SecEdgarCollector

    collector = SecEdgarCollector()
    await collector.setup()
    try:
        await collector.collect()
    finally:
        await collector.teardown()


@broker.task(schedule=[{"cron": "* * * * *"}])
async def collect_tickertick():
    """Scheduled: poll TickerTick API every 1 min (2 req/cycle, within 10 req/min limit)."""
    from src.collectors.tickertick_rest import TickerTickRest

    collector = TickerTickRest()
    await collector.setup()
    try:
        await collector.collect()
    finally:
        await collector.teardown()


@broker.task(schedule=[{"cron": "*/5 * * * *"}])
async def scrape_unscraped_articles(batch_size: int = 20):
    """Scrape unscraped article URLs for content extraction."""
    import asyncio

    from sqlalchemy import select, update

    from src.core.database import async_session_factory
    from src.core.models.article import Article
    from src.parsers.content_scraper import fetch_article_content

    async with async_session_factory() as session:
        result = await session.execute(
            select(Article)
            .where(Article.content_scraped == False)  # noqa: E712
            .order_by(Article.published_at.desc())
            .limit(batch_size)
        )
        articles = result.scalars().all()
        if not articles:
            return

        logger.info("scraping_batch", count=len(articles))
        scraped = 0
        for article in articles:
            await asyncio.sleep(1.0)
            content_result = await fetch_article_content(article.url)
            values: dict = {"content_scraped": True}
            if content_result and content_result.body:
                values.update(
                    content=content_result.body,
                    image_url=content_result.image_url,
                    author=content_result.author,
                )
                scraped += 1
            await session.execute(update(Article).where(Article.id == article.id).values(**values))
            await session.commit()

        logger.info("scrape_batch_done", scraped=scraped, total=len(articles))


@broker.task(schedule=[{"cron": "*/2 * * * *"}])
async def process_raw_articles(batch_size: int = 50):
    """Process unprocessed raw articles: dedup → parse → insert to PostgreSQL."""
    import redis.asyncio as aioredis

    from src.core.database import async_session_factory, close_mongo, init_mongo
    from src.core.models.article import Article
    from src.core.models.raw_article import RawArticle
    from src.parsers.dedup import DedupChecker
    from src.parsers.gemini_parser import GeminiParser
    from src.collectors.market_cap_cache import MarketCapCache

    await init_mongo()
    redis_client = aioredis.from_url(settings.redis_url, decode_responses=True)
    dedup = DedupChecker(redis_client)
    mcap_cache = MarketCapCache(redis_client, settings.finnhub_api_key)
    gemini = GeminiParser()

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

                # Parse headline with Gemini AI
                parsed = await gemini.parse_headline(headline)

                # Also use tickers from payload if available
                payload_tickers = _extract_payload_tickers(raw.source, raw.payload)
                all_tickers = list(dict.fromkeys(payload_tickers + parsed.tickers))

                # Enrich with market cap from payload or cache
                market_cap = _extract_market_cap(raw.source, raw.payload)
                if market_cap is None and all_tickers:
                    # Lookup many tickers but take the first valid MC (usually lead ticker)
                    for ticker in all_tickers:
                        mc = await mcap_cache.get_market_cap(ticker)
                        if mc:
                            market_cap = mc
                            break

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
                    market_cap=market_cap,
                    category=parsed.category,
                    raw_article_id=str(raw.id),
                    raw_data=raw.payload,
                )
                try:
                    session.add(article)
                    await session.commit()
                    processed += 1
                    # Discord alert for high-sentiment articles
                    from src.jobs.discord_notify import send_discord_alert, should_notify
                    if should_notify(article):
                        await send_discord_alert(article)
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
    elif source == "discord_nuntio":
        return payload.get("headline", "")
    elif source == "tickertick":
        return payload.get("title", "")
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
    elif source == "tickertick":
        ts = payload.get("time", 0)
        if ts:
            return datetime.fromtimestamp(ts / 1000, tz=timezone.utc)  # ms epoch
    # discord_nuntio + fallback: use collected_at
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
    elif source == "discord_nuntio":
        ticker = payload.get("ticker")
        return [ticker] if ticker else []
    elif source == "tickertick":
        return payload.get("tags", [])
    return []


def _extract_market_cap(source: str, payload: dict) -> float | None:
    """Extract market cap from payload if available."""
    if source == "discord_nuntio":
        return payload.get("market_cap")
    elif source == "marketaux":
        entities = payload.get("entities", [])
        mcs = [e.get("market_cap") for e in entities if e.get("market_cap")]
        return min(mcs) if mcs else None
    return None
