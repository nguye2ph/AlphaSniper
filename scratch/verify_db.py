import asyncio
import os
import sys

# Ensure src is in sys.path
sys.path.append(os.getcwd())

from src.core.database import async_session_factory
from src.core.models.article import Article
from sqlalchemy import select, func

async def check_db():
    async with async_session_factory() as session:
        total = await session.scalar(select(func.count(Article.id)))
        with_mcap = await session.scalar(select(func.count(Article.id)).where(Article.market_cap != None))
        print(f"Total articles: {total}")
        print(f"Articles with Market Cap: {with_mcap}")
        
        # Check latest 5 with MC
        latest_with_mc = await session.execute(
            select(Article).where(Article.market_cap != None).order_by(Article.published_at.desc()).limit(5)
        )
        for a in latest_with_mc.scalars().all():
            print(f"- {a.headline} | MC: {a.market_cap/1e6:.1f}M | Tickers: {a.tickers}")

if __name__ == "__main__":
    asyncio.run(check_db())
