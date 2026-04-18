"""Taskiq broker configuration and scheduled task definitions.

Scheduling is dynamic via ListRedisScheduleSource — intervals are managed
in Redis by the adaptive scheduler (src/scheduler/). No hardcoded cron here.
"""

import uuid
from datetime import datetime, timezone

import httpx
import structlog
from taskiq import TaskiqScheduler
from taskiq_redis import ListQueueBroker

from src.core.config import settings
from src.scheduler.scheduler_integration import create_schedule_source

logger = structlog.get_logger()

# Redis-backed broker for task queue
broker = ListQueueBroker(url=settings.redis_url)

# Dynamic schedule source — reads cron entries from Redis list
schedule_source = create_schedule_source()
scheduler = TaskiqScheduler(broker=broker, sources=[schedule_source])


async def _count_unprocessed(source_name: str) -> int:
    """Count unprocessed raw docs for a source across all MongoDB collections."""
    from src.core.models.raw_article import RawArticle
    from src.core.models.raw_insider_trade import RawInsiderTrade
    from src.core.models.raw_social_post import RawSocialPost

    count = 0
    for model in (RawArticle, RawSocialPost, RawInsiderTrade):
        count += await model.find(
            model.source == source_name,
            model.is_processed == False,  # noqa: E712
        ).count()
    return count


async def _run_collector(collector_cls: type) -> None:
    """Run a collector with metrics reporting and error tracking."""
    collector = collector_cls()
    await collector.setup()
    try:
        await collector.collect()
        count = await _count_unprocessed(collector.source_name)
        await collector.report_metrics(count)
    except httpx.HTTPStatusError as e:
        is_rate = e.response.status_code == 429
        await collector.report_metrics(0, had_error=True, is_rate_limit=is_rate)
        raise
    except Exception:
        await collector.report_metrics(0, had_error=True)
        raise
    finally:
        await collector.teardown()


@broker.task()
async def collect_finnhub_rest():
    """Poll Finnhub REST API for market + company news."""
    from src.collectors.finnhub_rest import FinnhubRest

    await _run_collector(FinnhubRest)


@broker.task()
async def collect_marketaux():
    """Poll MarketAux API."""
    from src.collectors.marketaux_rest import MarketAuxRest

    await _run_collector(MarketAuxRest)


@broker.task()
async def collect_sec_edgar():
    """Poll SEC EDGAR RSS feed."""
    from src.collectors.sec_edgar_rss import SecEdgarCollector

    await _run_collector(SecEdgarCollector)


@broker.task()
async def collect_tickertick():
    """Poll TickerTick API."""
    from src.collectors.tickertick_rest import TickerTickRest

    await _run_collector(TickerTickRest)


# --- Phase 2: Tier 1 Data Sources ---


@broker.task()
async def collect_reddit():
    """Poll Reddit (WSB, stocks, pennystocks) for stock mentions."""
    from src.collectors.reddit_praw import RedditPraw

    await _run_collector(RedditPraw)


@broker.task()
async def collect_openinsider():
    """Scrape OpenInsider for insider buy/sell transactions."""
    from src.collectors.openinsider_scraper import OpenInsiderScraper

    await _run_collector(OpenInsiderScraper)


@broker.task()
async def collect_earnings():
    """Poll API Ninjas for earnings calendar events."""
    from src.collectors.earnings_calendar import EarningsCalendar

    await _run_collector(EarningsCalendar)


@broker.task()
async def collect_rss_feeds():
    """Poll Yahoo/CNBC RSS feeds for financial news."""
    from src.collectors.rss_feeds import RssFeeds

    await _run_collector(RssFeeds)


# --- Phase 3: Tier 2 Data Sources ---


@broker.task()
async def collect_stocktwits():
    """Poll StockTwits public symbol streams for sentiment."""
    from src.collectors.stocktwits_rest import StockTwitsRest

    await _run_collector(StockTwitsRest)


@broker.task()
async def collect_ortex():
    """Poll ORTEX for daily short interest data."""
    from src.collectors.ortex_short_interest import OrtexShortInterest

    await _run_collector(OrtexShortInterest)


@broker.task()
async def collect_unusual_whales():
    """Poll Unusual Whales for options flow (experimental)."""
    from src.collectors.unusual_whales import UnusualWhales

    await _run_collector(UnusualWhales)


@broker.task()
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


@broker.task()
async def process_raw_articles(batch_size: int = 50):
    """Process unprocessed raw articles: dedup → parse → insert to PostgreSQL."""
    import redis.asyncio as aioredis

    from src.collectors.market_cap_cache import MarketCapCache
    from src.core.database import async_session_factory, close_mongo, init_mongo
    from src.core.models.article import Article
    from src.core.models.raw_article import RawArticle
    from src.parsers.cross_source_dedup import CrossSourceDedup
    from src.parsers.dedup import DedupChecker
    from src.parsers.gemini_parser import GeminiParser

    await init_mongo()
    redis_client = aioredis.from_url(settings.redis_url, decode_responses=True)
    dedup = DedupChecker(redis_client)
    cross_dedup = CrossSourceDedup(redis_client)
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
                # Dedup check (source-level)
                is_new = await dedup.check_and_mark(raw.source, raw.source_id)
                if not is_new:
                    raw.is_processed = True
                    await raw.save()
                    continue

                # Extract headline from payload (varies by source)
                headline = _extract_headline(raw.source, raw.payload)
                url = raw.payload.get("url", "")

                # Cross-source dedup: URL layer
                if url and await cross_dedup.is_url_duplicate(url, raw.source):
                    raw.is_processed = True
                    await raw.save()
                    continue

                # Queue headline for batch LLM dedup (runs every 5 min via separate task)
                if headline:
                    await cross_dedup.queue_for_headline_dedup(headline, str(raw.id))
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
    elif source == "rss_feeds":
        return payload.get("title", "")
    elif source == "earnings_calendar":
        ticker = payload.get("ticker", "")
        return f"{ticker} Earnings Report"
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
    elif source == "rss_feeds":
        published = payload.get("published", "")
        if published:
            try:
                from email.utils import parsedate_to_datetime

                return parsedate_to_datetime(published)
            except Exception:
                pass
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
    elif source == "rss_feeds":
        return []  # RSS headlines parsed by Gemini
    elif source == "earnings_calendar":
        ticker = payload.get("ticker")
        return [ticker] if ticker else []
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


# --- Phase 2: Process Social Posts + Insider Trades ---


@broker.task()
async def process_social_posts(batch_size: int = 50):
    """Process raw Reddit/StockTwits posts -> SocialSentiment in PostgreSQL."""
    from src.core.database import async_session_factory, close_mongo, init_mongo
    from src.core.models.raw_social_post import RawSocialPost
    from src.core.models.social_sentiment import SocialSentiment
    from src.parsers.social_sentiment_parser import analyze_sentiment, extract_tickers

    await init_mongo()
    try:
        raw_posts = await RawSocialPost.find(
            RawSocialPost.is_processed == False  # noqa: E712
        ).sort("-collected_at").limit(batch_size).to_list()

        if not raw_posts:
            return

        logger.info("processing_social_posts", count=len(raw_posts))
        processed = 0

        async with async_session_factory() as session:
            for raw in raw_posts:
                payload = raw.payload
                title = payload.get("title", "")
                body = payload.get("body", "")
                text = f"{title} {body}".strip()

                tickers = extract_tickers(text)
                if not tickers:
                    raw.is_processed = True
                    await raw.save()
                    continue

                score, label = analyze_sentiment(text)
                posted_at = datetime.fromtimestamp(
                    payload.get("created_utc", 0), tz=timezone.utc
                ) if payload.get("created_utc") else datetime.now(timezone.utc)

                sentiment = SocialSentiment(
                    id=uuid.uuid4(),
                    ticker=tickers[0],
                    platform=raw.source,
                    post_title=title[:500],
                    post_body=body[:2000] if body else None,
                    post_score=payload.get("score", 0),
                    subreddit=payload.get("subreddit"),
                    sentiment_score=score,
                    sentiment_label=label,
                    tickers=tickers,
                    source_id=raw.source_id,
                    posted_at=posted_at,
                    raw_data=payload,
                )
                try:
                    session.add(sentiment)
                    await session.commit()
                    processed += 1
                except Exception as e:
                    await session.rollback()
                    logger.warning("social_insert_error", source_id=raw.source_id, error=str(e)[:100])

                raw.is_processed = True
                await raw.save()

        logger.info("social_posts_processed", processed=processed, total=len(raw_posts))
    finally:
        await close_mongo()


@broker.task()
async def process_insider_trades(batch_size: int = 50):
    """Process raw OpenInsider trades -> InsiderTrade in PostgreSQL."""
    from src.core.database import async_session_factory, close_mongo, init_mongo
    from src.core.models.insider_trade import InsiderTrade
    from src.core.models.raw_insider_trade import RawInsiderTrade
    from src.parsers.insider_trade_parser import parse_trade

    await init_mongo()
    try:
        raw_trades = await RawInsiderTrade.find(
            RawInsiderTrade.is_processed == False  # noqa: E712
        ).sort("-collected_at").limit(batch_size).to_list()

        if not raw_trades:
            return

        logger.info("processing_insider_trades", count=len(raw_trades))
        processed = 0

        async with async_session_factory() as session:
            for raw in raw_trades:
                parsed = parse_trade(raw.payload)
                if not parsed:
                    raw.is_processed = True
                    await raw.save()
                    continue

                trade = InsiderTrade(
                    id=uuid.uuid4(),
                    source=raw.source,
                    source_id=raw.source_id,
                    raw_data=raw.payload,
                    **parsed,
                )
                try:
                    session.add(trade)
                    await session.commit()
                    processed += 1
                except Exception as e:
                    await session.rollback()
                    logger.warning("insider_insert_error", source_id=raw.source_id, error=str(e)[:100])

                raw.is_processed = True
                await raw.save()

        logger.info("insider_trades_processed", processed=processed, total=len(raw_trades))
    finally:
        await close_mongo()


@broker.task()
async def process_earnings_events(batch_size: int = 50):
    """Process raw earnings data -> EarningsEvent in PostgreSQL."""
    from src.core.database import async_session_factory, close_mongo, init_mongo
    from src.core.models.earnings_event import EarningsEvent
    from src.core.models.raw_article import RawArticle

    await init_mongo()
    try:
        raw_docs = await RawArticle.find(
            RawArticle.source == "earnings_calendar",
            RawArticle.is_processed == False,  # noqa: E712
        ).sort("-collected_at").limit(batch_size).to_list()

        if not raw_docs:
            return

        logger.info("processing_earnings", count=len(raw_docs))
        processed = 0

        async with async_session_factory() as session:
            for raw in raw_docs:
                p = raw.payload
                ticker = p.get("ticker", "")
                if not ticker:
                    raw.is_processed = True
                    await raw.save()
                    continue

                report_date_str = p.get("pricedate", "")
                try:
                    report_date = datetime.strptime(report_date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                except (ValueError, TypeError):
                    report_date = datetime.now(timezone.utc)

                event = EarningsEvent(
                    id=uuid.uuid4(),
                    ticker=ticker,
                    report_date=report_date,
                    estimated_eps=p.get("estimated_eps"),
                    actual_eps=p.get("actual_eps"),
                    estimated_revenue=p.get("estimated_revenue"),
                    actual_revenue=p.get("actual_revenue"),
                    surprise_pct=p.get("eps_surprise_pct"),
                    source="earnings_calendar",
                    source_id=raw.source_id,
                )
                try:
                    session.add(event)
                    await session.commit()
                    processed += 1
                except Exception as e:
                    await session.rollback()
                    logger.warning("earnings_insert_error", source_id=raw.source_id, error=str(e)[:100])

                raw.is_processed = True
                await raw.save()

        logger.info("earnings_processed", processed=processed, total=len(raw_docs))
    finally:
        await close_mongo()


@broker.task()
async def process_short_interest(batch_size: int = 50):
    """Process raw ORTEX data -> ShortInterest in PostgreSQL."""
    from src.core.database import async_session_factory, close_mongo, init_mongo
    from src.core.models.raw_article import RawArticle
    from src.core.models.short_interest import ShortInterest

    await init_mongo()
    try:
        raw_docs = await RawArticle.find(
            RawArticle.source == "ortex",
            RawArticle.is_processed == False,  # noqa: E712
        ).sort("-collected_at").limit(batch_size).to_list()

        if not raw_docs:
            return

        logger.info("processing_short_interest", count=len(raw_docs))
        processed = 0

        async with async_session_factory() as session:
            for raw in raw_docs:
                p = raw.payload
                ticker = p.get("ticker", "")
                if not ticker:
                    raw.is_processed = True
                    await raw.save()
                    continue

                report_date_str = p.get("report_date", "")
                try:
                    report_date = datetime.strptime(report_date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                except (ValueError, TypeError):
                    report_date = datetime.now(timezone.utc)

                si = ShortInterest(
                    id=uuid.uuid4(),
                    ticker=ticker,
                    short_pct_float=float(p.get("short_pct_float", 0)),
                    days_to_cover=float(p.get("days_to_cover", 0)),
                    borrow_fee_pct=p.get("borrow_fee_pct"),
                    squeeze_score=p.get("squeeze_score"),
                    report_date=report_date,
                    source="ortex",
                    source_id=raw.source_id,
                    raw_data=raw.payload,
                )
                try:
                    session.add(si)
                    await session.commit()
                    processed += 1
                except Exception as e:
                    await session.rollback()
                    logger.warning("short_interest_insert_error", source_id=raw.source_id, error=str(e)[:100])

                raw.is_processed = True
                await raw.save()

        logger.info("short_interest_processed", processed=processed, total=len(raw_docs))
    finally:
        await close_mongo()


@broker.task()
async def process_stocktwits_posts(batch_size: int = 50):
    """Process raw StockTwits posts -> SocialSentiment in PostgreSQL.

    StockTwits provides sentiment labels directly, no VADER needed.
    """
    from src.core.database import async_session_factory, close_mongo, init_mongo
    from src.core.models.raw_social_post import RawSocialPost
    from src.core.models.social_sentiment import SocialSentiment
    from src.parsers.social_sentiment_parser import extract_tickers

    await init_mongo()
    try:
        raw_posts = await RawSocialPost.find(
            RawSocialPost.source == "stocktwits",
            RawSocialPost.is_processed == False,  # noqa: E712
        ).sort("-collected_at").limit(batch_size).to_list()

        if not raw_posts:
            return

        logger.info("processing_stocktwits", count=len(raw_posts))
        processed = 0

        async with async_session_factory() as session:
            for raw in raw_posts:
                payload = raw.payload
                body = payload.get("body", "")
                symbol = payload.get("symbol", "")
                tickers = [symbol] if symbol else extract_tickers(body)

                if not tickers:
                    raw.is_processed = True
                    await raw.save()
                    continue

                # StockTwits gives sentiment directly
                st_label = payload.get("sentiment_label", "neutral").lower()
                score_map = {"bullish": 0.6, "bearish": -0.6, "neutral": 0.0}
                score = score_map.get(st_label, 0.0)

                created_str = payload.get("created_at", "")
                try:
                    posted_at = datetime.fromisoformat(created_str.replace("Z", "+00:00"))
                except (ValueError, AttributeError):
                    posted_at = datetime.now(timezone.utc)

                sentiment = SocialSentiment(
                    id=uuid.uuid4(),
                    ticker=tickers[0],
                    platform="stocktwits",
                    post_title=body[:500],
                    post_body=body if body else None,
                    post_score=0,
                    sentiment_score=score,
                    sentiment_label=st_label if st_label in ("bullish", "bearish") else "neutral",
                    tickers=tickers,
                    source_id=raw.source_id,
                    posted_at=posted_at,
                    raw_data=payload,
                )
                try:
                    session.add(sentiment)
                    await session.commit()
                    processed += 1
                except Exception as e:
                    await session.rollback()
                    logger.warning("stocktwits_insert_error", source_id=raw.source_id, error=str(e)[:100])

                raw.is_processed = True
                await raw.save()

        logger.info("stocktwits_processed", processed=processed, total=len(raw_posts))
    finally:
        await close_mongo()


# --- Adaptive Scheduler Tasks ---


@broker.task()
async def adjust_schedules():
    """Hourly: evaluate all sources and adjust polling intervals via EMA rules."""
    import redis.asyncio as aioredis

    from src.scheduler.adjustment_engine import apply_adjustments
    from src.scheduler.scheduler_integration import sync_schedules

    if not settings.scheduler_adjustment_enabled:
        logger.info("scheduler_adjustment_disabled")
        return

    redis = aioredis.from_url(settings.redis_url, decode_responses=True)
    try:
        results = await apply_adjustments(redis)
        changed = [r for r in results if r.action not in ("no_change", "cooldown_skip")]
        if changed:
            # Re-sync schedules to pick up new intervals
            await sync_schedules(schedule_source)
            logger.info("schedules_resynced", changed=[r.source_name for r in changed])
        logger.info("adjustment_complete", total=len(results), changed=len(changed))
    finally:
        await redis.close()


@broker.task()
async def refresh_ticker_health_scores():
    """Hourly: recompute health scores for active tickers and cache in Redis."""
    import redis.asyncio as aioredis
    from sqlalchemy import func, select, text

    from src.core.database import async_session_factory
    from src.core.models.article import Article
    from src.parsers.ticker_health_score import compute_health_score

    # Get top 50 active tickers (most articles in last 24h)
    async with async_session_factory() as session:
        result = await session.execute(
            select(func.unnest(Article.tickers).label("ticker"))
            .where(Article.published_at >= func.now() - text("interval '24 hours'"))
            .group_by("ticker")
            .order_by(func.count().desc())
            .limit(50)
        )
        tickers = [r[0] for r in result.all()]

    if not tickers:
        logger.info("no_active_tickers_for_health")
        return

    redis = aioredis.from_url(settings.redis_url, decode_responses=True)
    try:
        async with async_session_factory() as session:
            for ticker in tickers:
                health = await compute_health_score(ticker, session)
                await redis.set(f"ticker:health:{ticker}", health.model_dump_json(), ex=3600)
        logger.info("health_scores_refreshed", count=len(tickers))
    finally:
        await redis.aclose()


@broker.task()
async def run_headline_dedup_batch():
    """Every 5 min: batch-evaluate queued headlines for cross-source duplicates."""
    import redis.asyncio as aioredis

    from src.parsers.cross_source_dedup import CrossSourceDedup

    redis_client = aioredis.from_url(settings.redis_url, decode_responses=True)
    try:
        cross_dedup = CrossSourceDedup(redis_client)
        groups = await cross_dedup.run_batch_headline_dedup()
        if groups:
            logger.info("headline_dedup_complete", duplicate_groups=len(groups), groups=groups)
        else:
            logger.debug("headline_dedup_no_duplicates")
    finally:
        await redis_client.close()


@broker.task()
async def evaluate_alert_rules():
    """Every 5 min: evaluate alert rules and trigger actions."""
    from src.jobs.alert_evaluator import evaluate_all_rules

    await evaluate_all_rules()


@broker.task()
async def seed_and_sync_schedules():
    """Startup task: seed default configs and sync schedules to Redis list."""
    import redis.asyncio as aioredis

    from src.scheduler.config_manager import seed_defaults
    from src.scheduler.scheduler_integration import sync_schedules

    redis = aioredis.from_url(settings.redis_url, decode_responses=True)
    try:
        seeded = await seed_defaults(redis)
        logger.info("startup_seed_complete", seeded=seeded)
    finally:
        await redis.close()

    synced = await sync_schedules(schedule_source)
    logger.info("startup_sync_complete", synced=synced)
