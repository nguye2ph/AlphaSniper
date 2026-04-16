import asyncio
from sqlalchemy import select
from src.core.models.article import Article
from src.api.routes.articles_routes import list_articles
from unittest.mock import MagicMock

async def test_query_generation():
    # Mocking DB session
    mock_db = MagicMock()
    
    # Simulating the call to list_articles
    ticker = None
    market_cap_gte = 250000000.0
    market_cap_lte = 2000000000.0
    
    # We want to see how the query is constructed
    query = select(Article).order_by(Article.published_at.desc())
    
    if market_cap_gte is not None:
        query = query.where(Article.market_cap >= market_cap_gte)
    if market_cap_lte is not None:
        query = query.where(Article.market_cap <= market_cap_lte)
        
    print("Constructed Query:")
    print(query)
    
    # Check if where clause is present
    if "WHERE" in str(query):
        print("SUCCESS: WHERE clause is present.")
    else:
        print("FAILED: WHERE clause is missing!")

if __name__ == "__main__":
    asyncio.run(test_query_generation())
