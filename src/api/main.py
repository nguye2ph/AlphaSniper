"""FastAPI application with lifespan management and health check."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.api.routes.articles_routes import router as articles_router
from src.api.routes.sources_routes import router as sources_router
from src.api.routes.tickers_routes import router as tickers_router
from src.core.config import settings
from src.core.database import close_mongo, close_redis, init_mongo, init_redis


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: connect to databases. Shutdown: close connections."""
    await init_mongo()
    await init_redis()
    yield
    await close_mongo()
    await close_redis()


app = FastAPI(
    title="AlphaSniper",
    description="Real-time stock news data pipeline API",
    version="0.1.0",
    lifespan=lifespan,
)


app.include_router(articles_router)
app.include_router(tickers_router)
app.include_router(sources_router)


@app.get("/health")
async def health_check():
    """Basic health check — verifies the API is running."""
    return {
        "status": "ok",
        "service": "alpha-sniper",
        "env": settings.app_env,
    }
