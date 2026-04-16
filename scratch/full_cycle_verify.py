import asyncio
import os
import sys

# Ensure src is in sys.path
sys.path.append(os.getcwd())

from src.jobs.taskiq_app import process_raw_articles, collect_finnhub_rest
from src.core.database import async_session_factory, init_mongo, close_mongo
from src.core.models.article import Article
from sqlalchemy import select, func

async def run_and_verify():
    print("Step 1: Collecting new articles from Finnhub...")
    await collect_finnhub_rest()
    
    print("\nStep 2: Processing raw articles with new enrichment logic...")
    await process_raw_articles(batch_size=20)
    
    print("\nStep 3: Verifying database results...")
    async with async_session_factory() as session:
        total = await session.scalar(select(func.count(Article.id)))
        with_mcap = await session.scalar(select(func.count(Article.id)).where(Article.market_cap != None))
        print(f"Total articles: {total}")
        print(f"Articles with Market Cap: {with_mcap}")
        
        if with_mcap > 0:
            latest_with_mc = await session.execute(
                select(Article).where(Article.market_cap != None).order_by(Article.published_at.desc()).limit(5)
            )
            print("\nRecent articles with Market Cap:")
            for a in latest_with_mc.scalars().all():
                print(f"- {a.headline[:60]}... | MC: {a.market_cap/1e6:.1f}M | Tickers: {a.tickers}")
        else:
            print("\nWARNING: No articles captured market cap. This might be because:")
            print("1. No new articles were found.")
            print("2. Tickers found are not in Finnhub profile2 (uncommon).")
            print("3. API limits reached.")

if __name__ == "__main__":
    asyncio.run(run_and_verify())
