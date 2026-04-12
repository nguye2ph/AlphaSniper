"""Database connections: MongoDB (Beanie), PostgreSQL (SQLAlchemy async), Redis."""

import redis.asyncio as aioredis
from motor.motor_asyncio import AsyncIOMotorClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from src.core.config import settings


# --- PostgreSQL (clean zone) ---

engine = create_async_engine(
    settings.postgres_url,
    echo=(settings.app_env == "development"),
    pool_size=10,
    max_overflow=20,
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """SQLAlchemy declarative base for all PostgreSQL models."""

    pass


async def get_pg_session() -> AsyncSession:
    """FastAPI dependency: yields an async PostgreSQL session."""
    async with async_session_factory() as session:
        yield session


# --- MongoDB (raw zone) ---

mongo_client: AsyncIOMotorClient | None = None
mongo_db = None


async def init_mongo():
    """Initialize MongoDB connection and Beanie ODM."""
    global mongo_client, mongo_db

    from beanie import init_beanie

    from src.core.models.raw_article import RawArticle

    mongo_client = AsyncIOMotorClient(settings.mongo_uri)
    mongo_db = mongo_client[settings.mongo_db]
    await init_beanie(database=mongo_db, document_models=[RawArticle])


async def close_mongo():
    """Close MongoDB connection."""
    global mongo_client
    if mongo_client:
        mongo_client.close()


# --- Redis (queue + cache + dedup) ---

redis_client: aioredis.Redis | None = None


async def init_redis() -> aioredis.Redis:
    """Initialize Redis connection."""
    global redis_client
    redis_client = aioredis.from_url(settings.redis_url, decode_responses=True)
    return redis_client


async def close_redis():
    """Close Redis connection."""
    global redis_client
    if redis_client:
        await redis_client.close()


async def get_redis() -> aioredis.Redis:
    """FastAPI dependency: returns Redis client."""
    if redis_client is None:
        await init_redis()
    return redis_client
