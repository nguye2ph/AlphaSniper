"""Seed Postgres `sources` table with registry of active data sources.

Idempotent: inserts new, updates metadata for existing.
Run: uv run python scripts/seed-sources.py
"""

import asyncio

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from src.core.database import async_session_factory, engine
from src.core.models.source import Source

SOURCES: list[dict] = [
    {"name": "finnhub_ws",         "source_type": "websocket", "base_url": "wss://ws.finnhub.io"},
    {"name": "finnhub_rest",       "source_type": "api",       "base_url": "https://finnhub.io/api/v1"},
    {"name": "marketaux",          "source_type": "api",       "base_url": "https://api.marketaux.com/v1"},
    {"name": "sec_edgar",          "source_type": "rss",       "base_url": "https://www.sec.gov/cgi-bin/browse-edgar"},
    {"name": "tickertick",         "source_type": "api",       "base_url": "https://api.tickertick.com"},
    {"name": "reddit",             "source_type": "api",       "base_url": "https://oauth.reddit.com"},
    {"name": "stocktwits",         "source_type": "api",       "base_url": "https://api.stocktwits.com/api/2"},
    {"name": "openinsider",        "source_type": "scraper",   "base_url": "http://openinsider.com"},
    {"name": "earnings_calendar",  "source_type": "api",       "base_url": "https://finnhub.io/api/v1/calendar/earnings"},
    {"name": "rss_feeds",          "source_type": "rss",       "base_url": "multi"},
    {"name": "ortex",              "source_type": "api",       "base_url": "https://api.ortex.com"},
    {"name": "unusual_whales",     "source_type": "api",       "base_url": "https://api.unusualwhales.com"},
    {"name": "discord_nuntio",     "source_type": "websocket", "base_url": "wss://gateway.discord.gg"},
]


async def seed() -> tuple[int, int]:
    inserted = updated = 0
    async with async_session_factory() as db:
        existing_names = {
            n for (n,) in (await db.execute(select(Source.name))).all()
        }
        for src in SOURCES:
            stmt = pg_insert(Source).values(**src, is_active=True)
            stmt = stmt.on_conflict_do_update(
                index_elements=["name"],
                set_={"source_type": src["source_type"], "base_url": src["base_url"]},
            )
            await db.execute(stmt)
            if src["name"] in existing_names:
                updated += 1
            else:
                inserted += 1
        await db.commit()
    return inserted, updated


async def main() -> None:
    ins, upd = await seed()
    print(f"seed-sources: inserted={ins} updated={upd} total={ins + upd}")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
