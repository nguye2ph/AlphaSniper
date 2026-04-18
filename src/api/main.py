"""FastAPI application with lifespan management and health check."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes.admin_routes import router as admin_router
from src.api.routes.admin_scheduler_routes import router as admin_scheduler_router
from src.api.routes.articles_routes import router as articles_router
from src.api.routes.earnings_routes import router as earnings_router
from src.api.routes.insider_trades_routes import router as insider_trades_router
from src.api.routes.options_flow_routes import router as options_flow_router
from src.api.routes.sentiment_routes import router as sentiment_router
from src.api.routes.short_interest_routes import router as short_interest_router
from src.api.routes.sources_routes import router as sources_router
from src.api.routes.ticker_health_routes import router as ticker_health_router
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


# CORS: allow local dev + Vercel production frontend
_cors_origins = ["http://localhost:8210"]
if settings.frontend_url:
    _cors_origins.append(settings.frontend_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(articles_router)
app.include_router(tickers_router)
app.include_router(sources_router)
app.include_router(admin_router)
app.include_router(admin_scheduler_router)
app.include_router(insider_trades_router)
app.include_router(earnings_router)
app.include_router(sentiment_router)
app.include_router(short_interest_router)
app.include_router(options_flow_router)
app.include_router(ticker_health_router)


@app.get("/health")
async def health_check():
    """Basic health check — verifies the API is running."""
    return {
        "status": "ok",
        "service": "alpha-sniper",
        "env": settings.app_env,
    }
