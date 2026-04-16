import asyncio
import os
import sys

# Ensure src is in sys.path
sys.path.append(os.getcwd())

from src.core.database import init_mongo, close_mongo
from src.core.models.raw_article import RawArticle

async def reset_raw():
    await init_mongo()
    # Find the most recent 50 processed articles
    docs = await RawArticle.find(RawArticle.is_processed == True).sort("-collected_at").limit(50).to_list()
    if not docs:
        print("No articles to reset.")
        return
    
    ids = [d.id for d in docs]
    # Beanie update_many
    await RawArticle.find({"_id": {"$in": ids}}).update({"$set": {RawArticle.is_processed: False}})
    print(f"Reset {len(docs)} RawArticles to unprocessed status.")
    await close_mongo()

if __name__ == "__main__":
    asyncio.run(reset_raw())
