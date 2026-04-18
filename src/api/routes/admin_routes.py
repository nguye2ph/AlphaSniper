"""Admin endpoints — job management, watchlist, system stats."""

from datetime import date, datetime, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import func, select

from src.core.database import async_session_factory
from src.core.models.app_settings import load_settings, save_settings
from src.core.models.article import Article

router = APIRouter(prefix="/api/admin", tags=["admin"])


class WatchlistUpdate(BaseModel):
    symbols: list[str]


class FiltersUpdate(BaseModel):
    alert_sentiment_threshold: float = 0.5
    alert_enabled: bool = True


@router.get("/settings")
async def get_settings():
    """Get current app settings."""
    return load_settings().model_dump()


@router.put("/settings/watchlist")
async def update_watchlist(body: WatchlistUpdate):
    """Update tracked ticker watchlist."""
    symbols = [s.upper().strip() for s in body.symbols if 1 <= len(s.strip()) <= 5]
    if not symbols:
        raise HTTPException(400, "At least one valid symbol required")
    settings = load_settings()
    settings.watchlist = symbols
    save_settings(settings)
    return {"watchlist": symbols}


@router.put("/settings/filters")
async def update_filters(body: FiltersUpdate):
    """Update alert filter config."""
    settings = load_settings()
    settings.alert_sentiment_threshold = body.alert_sentiment_threshold
    settings.alert_enabled = body.alert_enabled
    save_settings(settings)
    return settings.model_dump()


@router.get("/system/stats")
async def system_stats():
    """Get system statistics."""
    async with async_session_factory() as session:
        total = await session.scalar(select(func.count(Article.id)))
        today_start = datetime.combine(date.today(), datetime.min.time()).replace(tzinfo=timezone.utc)
        today_count = await session.scalar(
            select(func.count(Article.id)).where(Article.published_at >= today_start)
        )
        source_counts = await session.execute(
            select(Article.source, func.count(Article.id)).group_by(Article.source)
        )
        scraped_count = await session.scalar(
            select(func.count(Article.id)).where(Article.content_scraped == True)  # noqa: E712
        )
    return {
        "total_articles": total or 0,
        "articles_today": today_count or 0,
        "articles_scraped": scraped_count or 0,
        "by_source": {row[0]: row[1] for row in source_counts.all()},
    }


@router.post("/jobs/trigger/{job_name}")
async def trigger_job(job_name: str):
    """Manually trigger a collector job."""
    valid_jobs = [
        "finnhub_rest", "marketaux", "sec_edgar", "tickertick",
        "process_raw", "scrape_content",
        "reddit", "openinsider", "earnings", "rss_feeds",
        "process_social", "process_insider", "process_earnings",
    ]
    if job_name not in valid_jobs:
        raise HTTPException(400, f"Invalid job. Valid: {valid_jobs}")
    from src.jobs.taskiq_app import (
        collect_earnings,
        collect_finnhub_rest,
        collect_marketaux,
        collect_openinsider,
        collect_reddit,
        collect_rss_feeds,
        collect_sec_edgar,
        collect_tickertick,
        process_earnings_events,
        process_insider_trades,
        process_raw_articles,
        process_social_posts,
        scrape_unscraped_articles,
    )
    task_map = {
        "finnhub_rest": collect_finnhub_rest,
        "marketaux": collect_marketaux,
        "sec_edgar": collect_sec_edgar,
        "tickertick": collect_tickertick,
        "process_raw": process_raw_articles,
        "scrape_content": scrape_unscraped_articles,
        "reddit": collect_reddit,
        "openinsider": collect_openinsider,
        "earnings": collect_earnings,
        "rss_feeds": collect_rss_feeds,
        "process_social": process_social_posts,
        "process_insider": process_insider_trades,
        "process_earnings": process_earnings_events,
    }
    await task_map[job_name].kiq()
    return {"status": "triggered", "job": job_name}
