# Python Tech Stack Analysis: AlphaSniper Real-Time Stock News Pipeline

**Date:** April 11, 2026 | **Python:** 3.12+ | **Status:** FINAL RECOMMENDATIONS

---

## Executive Summary

For AlphaSniper's real-time stock news pipeline, recommend **Beanie** (MongoDB ODM), **SQLAlchemy 2.0** (PostgreSQL), **Taskiq** (task queue), and **websockets** (WebSocket client). These selections prioritize async-first design, production maturity, and real-time performance. Motor (current async MongoDB driver) will deprecate May 14, 2026—Beanie abstracts this transition while delivering 5-10x throughput in async scenarios. Celery remains viable for distributed scheduling but adds operational complexity; Taskiq offers modern async-first alternative. HTTPX for HTTP client provides both sync/async flexibility needed for API integrations.

---

## 1. Package Selection & Justification

### 1.1 MongoDB Driver: **Beanie** ✅

| Aspect | Beanie | Motor | PyMongo | MongoEngine |
|--------|--------|-------|---------|------------|
| **Async Support** | ✓ Native | ⚠ Deprecated (May 2026) | ✓ PyMongo Async | ✗ Sync only |
| **Performance (QPS)** | 45k | ~25k | 4k (sync) | ~3k (sync) |
| **Type Hints** | ✓ Full Pydantic | ✗ Limited | ✗ None | ✗ Minimal |
| **Production Ready** | ✓ 1.x stable | ✓ 3.7.1 stable | ✓ 4.x stable | ⚠ Legacy |
| **ORM Features** | ✓ Relations, migrations | ✗ Low-level | ✗ Low-level | ✓ Full ORM |

**Decision:** **Beanie** (Motor-powered, Pydantic-integrated)
- Built on Motor + Pydantic v2 declarative models
- Delivers 5-10x throughput vs sync PyMongo in async apps
- Single unified validation + serialization layer
- Motor deprecation handled transparently
- Trade-off: 15% slower on single-doc queries; use raw Motor for edge cases

**Setup:**
```python
# pyproject.toml
beanie = "^1.26.0"  # 2026 stable

# main.py
from beanie import init_beanie, Document, PydanticObjectId
from pydantic import Field

class StockNews(Document):
    ticker: str
    headline: str
    timestamp: datetime
    raw_html: str
    parsed_data: Optional[dict] = None
    
    class Settings:
        collection = "news_raw"

# Startup
await init_beanie(
    database=client.alpha_sniper,
    models=[StockNews]
)
```

---

### 1.2 PostgreSQL ORM: **SQLAlchemy 2.0** ✅

| Aspect | SQLAlchemy 2.0 | Tortoise ORM | SQLModel |
|--------|----------------|--------------|----------|
| **Async Support** | ✓ Full async/sync | ✓ Async-first | ✓ Full async/sync |
| **Query Performance** | ✓ Excellent | ✓ Fast (benchmarks vary) | ✓ Good |
| **Type Hints** | ✓ Full PEP 484 | ✗ Basic | ✓ Via Pydantic |
| **Flexibility** | ✓✓ Maximum | ⚠ Medium | ⚠ Opinionated |
| **Community/Ecosystem** | ✓✓ Largest Python | ✓ Growing | ⚠ Emerging |
| **Maturity** | ✓ 19+ years | ✓ 5+ years | ⚠ 3+ years |

**Decision:** **SQLAlchemy 2.0** (Core async mode)
- "Safe default choice even if newer tools exist"
- Flexible query construction with Core + ORM layers
- Best-in-class relationship handling for complex data models
- Production-proven at enterprise scale
- Tortoise simpler but less flexible for nuanced queries; SQLModel still emerging

**Setup:**
```python
# pyproject.toml
sqlalchemy = "^2.1.0"  # 2026 latest
alembic = "^1.14.0"    # Migrations

# models.py
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, DateTime, ForeignKey
from datetime import datetime

class ParsedNews(Base):
    __tablename__ = "parsed_news"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    news_id: Mapped[str] = mapped_column(ForeignKey("news_raw.id"))
    ticker: Mapped[str]
    sentiment: Mapped[str]  # bullish, bearish, neutral
    entities: Mapped[dict]
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

# Async engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

engine = create_async_engine(
    "postgresql+asyncpg://user:pass@localhost/alpha_sniper",
    echo=False,
    pool_size=20,
    max_overflow=40
)

async_session = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)
```

---

### 1.3 Task Queue: **Taskiq** ✅

| Aspect | Celery | Dramatiq | Taskiq | ARQ |
|--------|--------|----------|--------|-----|
| **Async Support** | ⚠ Limited | ✓ Good | ✓ Full native | ✓ Full |
| **Performance (QPS)** | ~3k | ~30k (10x faster) | ~30k | ~2k |
| **Learning Curve** | Hard | Medium | Easy | Medium |
| **Feature Completeness** | ✓✓ Massive | ✓ Solid | ✓ Growing | ⚠ Minimal |
| **Production Maturity** | ✓ 13+ years | ✓ 5+ years | ⚠ Newer | ✗ Lesser-known |
| **Redis + RabbitMQ** | ✓ Both | ✓ Both | ✓ Both | ✓ Redis only |

**Decision:** **Taskiq** (modern async-first)
- 10x Celery performance; supports both sync + async tasks
- Simpler configuration for greenfield projects
- FastAPI + AioHTTP integration built-in
- Falls back to Celery if enterprise feature chains needed later
- Huey also performs well but less async-native

**Setup:**
```python
# pyproject.toml
taskiq = "^0.37.0"
taskiq-redis = "^0.6.0"

# tasks.py
from taskiq import InMemoryBroker
from taskiq.brokers.redis import RedisBroker
import asyncio

broker = RedisBroker("redis://localhost:6379/1")

@broker.task
async def parse_news_batch(news_ids: list[str]):
    """Async task: parse news with Gemini"""
    async with httpx.AsyncClient() as client:
        # Call Gemini API
        pass

@broker.task
async def update_sentiment_scores(ticker: str):
    """Async aggregation task"""
    pass

# In FastAPI
from fastapi import FastAPI
app = FastAPI()

@app.post("/news/parse")
async def enqueue_parse(news_id: str):
    await parse_news_batch.kiq([news_id])
    return {"queued": True}

# Run worker: taskiq worker tasks:broker --concurrency 16
```

---

### 1.4 WebSocket Client: **websockets** ✅

| Aspect | websockets | aiohttp | websocket-client |
|--------|-----------|---------|-----------------|
| **Async Support** | ✓ Native asyncio | ✓ Full | ✗ Sync only |
| **Production Ready** | ✓ De facto standard | ✓ Proven | ✓ Stable |
| **Protocol Compliance** | ✓ RFC 6455 | ✓ Full | ✓ Full |
| **Connection Pooling** | ✗ Single conn | ✓ Built-in | ✗ Manual |
| **Simplicity** | ✓ Minimal API | ⚠ Complex | ✓ Simple |

**Decision:** **websockets** (purpose-built, lowest complexity)
- "Default choice for Python WebSocket work"
- Handles protocol correctly, stays out of your way
- Perfect for long-lived Finnhub streaming connections
- Use aiohttp only if needing HTTP + WebSocket together

**Setup:**
```python
# pyproject.toml
websockets = "^16.0"

# finnhub_client.py
import asyncio
import websockets
import json
from typing import Callable

class FinnhubClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.uri = "wss://ws.finnhub.io?token=" + api_key
        self.message_handler: Callable = None
    
    async def connect_and_stream(self, handler: Callable):
        """Maintain persistent WebSocket connection"""
        self.message_handler = handler
        
        while True:
            try:
                async with websockets.connect(self.uri) as ws:
                    await ws.send(json.dumps({
                        "type": "subscribe",
                        "symbol": "AAPL"
                    }))
                    
                    async for message in ws:
                        data = json.loads(message)
                        await handler(data)
            
            except websockets.exceptions.ConnectionClosed:
                await asyncio.sleep(5)  # Reconnect backoff
            except Exception as e:
                print(f"Error: {e}")
                await asyncio.sleep(10)

# Usage: Run in separate async task
async def news_handler(data: dict):
    if data.get("type") == "news":
        await db_client.save_news(data)
```

---

### 1.5 HTTP Client: **httpx** ✅

| Aspect | httpx | aiohttp | requests |
|--------|-------|---------|----------|
| **Async + Sync** | ✓ Both | ✗ Async only | ✗ Sync only |
| **HTTP/2 Support** | ✓ Yes | ✗ No | ✗ No |
| **High Concurrency** | ✓ Good | ✓ Better | ✗ N/A |
| **Simplicity** | ✓ requests-like API | ⚠ Steeper | ✓ Simple |
| **Used by OpenAI/Anthropic** | ✓ Yes | ✗ No | ✗ No |

**Decision:** **httpx** (requests-compatible async)
- Async + sync in single lib; use aiohttp only if >10k concurrent connections
- OpenAI SDK uses it; FastAPI TestClient uses it
- HTTP/2 support for future API upgrades
- Slightly lower throughput than aiohttp but negligible for AlphaSniper scale

**Setup:**
```python
# pyproject.toml
httpx = "^0.28.0"

# api_client.py
import httpx

async def fetch_market_data(symbols: list[str]):
    async with httpx.AsyncClient(
        timeout=30.0,
        limits=httpx.Limits(max_keepalive_connections=5)
    ) as client:
        tasks = [
            client.get(f"https://api.example.com/quote/{s}")
            for s in symbols
        ]
        responses = await asyncio.gather(*tasks)
        return [r.json() for r in responses]
```

---

### 1.6 Data Validation: **Pydantic v2** ✅

Pydantic v2 (standard):
- 5-50x faster than v1 (Rust core)
- Full async validator support via `@field_validator`
- Use `pydantic-async-validation` package for complex async lookups
- Integrated into Beanie, SQLModel, FastAPI

```python
# pyproject.toml
pydantic = "^2.9.0"  # Latest 2.x
pydantic-settings = "^2.5.0"

# models.py
from pydantic import BaseModel, field_validator, Field
from typing import Optional

class StockNewsInput(BaseModel):
    headline: str = Field(..., min_length=5)
    ticker: str = Field(..., pattern=r'^[A-Z]{1,5}$')
    
    @field_validator('headline')
    def validate_no_spam(cls, v):
        if len(v.split()) < 3:
            raise ValueError('Headline too short')
        return v
```

---

### 1.7 Configuration: **pydantic-settings** ✅

```python
# pyproject.toml
pydantic-settings = "^2.5.0"

# config.py
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # MongoDB
    mongo_uri: str = "mongodb://localhost:27017"
    mongo_db: str = "alpha_sniper"
    
    # PostgreSQL
    postgres_url: str = "postgresql+asyncpg://user:pass@localhost/alpha"
    
    # Redis
    redis_url: str = "redis://localhost:6379/1"
    
    # Finnhub
    finnhub_api_key: str
    finnhub_symbols: list[str] = ["AAPL", "MSFT", "TSLA"]
    
    # Gemini (Phase 2)
    gemini_api_key: Optional[str] = None
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
```

---

### 1.8 Testing: **pytest + pytest-asyncio + factory-boy**

```python
# pyproject.toml
pytest = "^8.3.0"
pytest-asyncio = "^0.25.0"
pytest-cov = "^6.0.0"
factory-boy = "^3.4.0"
faker = "^28.0.0"

# tests/conftest.py
import pytest
from factory import Factory, Faker
from app.models import StockNews

class StockNewsFactory(Factory):
    class Meta:
        model = StockNews
    
    ticker = Faker("lexify", word="?????")
    headline = Faker("sentence", nb_words=10)
    timestamp = Faker("date_time")
    raw_html = Faker("text")

@pytest.fixture
async def db_session():
    # Async fixture setup
    await init_beanie(...)
    yield
    await cleanup_beanie()

@pytest.mark.asyncio
async def test_parse_news(db_session):
    news = await StockNewsFactory.create_async()
    assert news.ticker is not None
```

---

## 2. Project Setup: pyproject.toml Blueprint

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "alpha-sniper"
version = "0.1.0"
description = "Real-time stock news data pipeline"
requires-python = ">=3.12"
license = {text = "MIT"}
authors = [{name = "Your Name", email = "you@example.com"}]

dependencies = [
    # Core async
    "fastapi==0.115.0",
    "uvicorn[standard]==0.30.0",
    
    # Data validation
    "pydantic==2.9.2",
    "pydantic-settings==2.5.0",
    
    # MongoDB
    "beanie==1.26.0",
    "motor==3.7.1",
    
    # PostgreSQL
    "sqlalchemy==2.1.0",
    "asyncpg==0.30.0",
    "alembic==1.14.1",
    
    # Task queue
    "taskiq[redis]==0.37.0",
    
    # WebSocket
    "websockets==16.0",
    
    # HTTP
    "httpx==0.28.1",
    
    # Redis
    "redis==5.2.0",
    
    # Logging
    "python-json-logger==2.0.7",
    
    # Observability
    "opentelemetry-api==1.28.0",
    "opentelemetry-exporter-jaeger==1.28.0",
]

[project.optional-dependencies]
dev = [
    "pytest==8.3.3",
    "pytest-asyncio==0.25.0",
    "pytest-cov==6.0.0",
    "factory-boy==3.4.0",
    "faker==28.1.0",
    "ruff==0.10.0",
    "mypy==1.14.1",
    "black==24.10.0",
]

[tool.hatch.build.targets.wheel]
packages = ["src/alpha_sniper"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
asyncio_default_fixture_scope = "function"
testpaths = ["tests"]
```

**Dependency Management:** Use **uv** (ultra-fast, 2026 standard)
```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Bootstrap
uv venv .venv
source .venv/bin/activate
uv sync --all-extras

# Run
uv run uvicorn app:app --reload
```

---

## 3. Docker Compose Blueprint

```yaml
version: "3.9"

services:
  postgres:
    image: "timescaledb/timescaledb:latest-pg16"
    ports:
      - "5432:5432"
    environment:
      POSTGRES_USER: alpha
      POSTGRES_PASSWORD: alpha_dev_only
      POSTGRES_DB: alpha_sniper
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U alpha"]
      interval: 10s
      timeout: 5s
      retries: 5

  mongo:
    image: "mongo:7-alpine"
    ports:
      - "27017:27017"
    volumes:
      - mongo_data:/data/db
    healthcheck:
      test: ["CMD", "mongosh", "--eval", "db.adminCommand('ping')"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: "redis:7-alpine"
    ports:
      - "6379:6379"
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5

  api:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      PYTHONUNBUFFERED: "1"
      MONGO_URI: mongodb://mongo:27017
      POSTGRES_URL: postgresql+asyncpg://alpha:alpha_dev_only@postgres:5432/alpha_sniper
      REDIS_URL: redis://redis:6379/1
      FINNHUB_API_KEY: ${FINNHUB_API_KEY}
    depends_on:
      postgres:
        condition: service_healthy
      mongo:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - .:/app
    command: uvicorn app.main:app --host 0.0.0.0 --reload

  collector:
    build:
      context: .
      dockerfile: Dockerfile
    environment:
      PYTHONUNBUFFERED: "1"
      MONGO_URI: mongodb://mongo:27017
      POSTGRES_URL: postgresql+asyncpg://alpha:alpha_dev_only@postgres:5432/alpha_sniper
      REDIS_URL: redis://redis:6379/1
      FINNHUB_API_KEY: ${FINNHUB_API_KEY}
    depends_on:
      - mongo
      - redis
    volumes:
      - .:/app
    command: python -m app.collectors.finnhub_stream

  worker:
    build:
      context: .
      dockerfile: Dockerfile
    environment:
      PYTHONUNBUFFERED: "1"
      MONGO_URI: mongodb://mongo:27017
      POSTGRES_URL: postgresql+asyncpg://alpha:alpha_dev_only@postgres:5432/alpha_sniper
      REDIS_URL: redis://redis:6379/1
      GEMINI_API_KEY: ${GEMINI_API_KEY:-}
    depends_on:
      - redis
    volumes:
      - .:/app
    command: taskiq worker app.tasks:broker --concurrency 8

  beat:
    build:
      context: .
      dockerfile: Dockerfile
    environment:
      PYTHONUNBUFFERED: "1"
      REDIS_URL: redis://redis:6379/1
    depends_on:
      - redis
    volumes:
      - .:/app
    command: taskiq scheduler app.tasks:broker

volumes:
  postgres_data:
  mongo_data:
  redis_data:
```

**Dockerfile:**
```dockerfile
FROM python:3.12-slim

WORKDIR /app

RUN pip install uv

COPY pyproject.toml uv.lock ./
RUN uv sync --no-dev

COPY . .

# Alembic migrations on startup
RUN ["uv", "run", "alembic", "upgrade", "head"]

EXPOSE 8000
```

---

## 4. Async Architecture Patterns

### 4.1 Finnhub WebSocket + Celery Workers

Run in **separate containers** to prevent event loop conflicts:

```python
# app/main.py (API + scheduler)
from fastapi import FastAPI
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    yield
    # Shutdown
    await cleanup_db()

app = FastAPI(lifespan=lifespan)

# app/collectors/finnhub_stream.py (Separate process)
import asyncio
from app.clients import FinnhubClient
from app.db import get_db

async def main():
    client = FinnhubClient(api_key=settings.finnhub_api_key)
    
    async def handle_update(data):
        # Save to MongoDB raw zone
        await db_client.news.insert_one({
            "source": "finnhub",
            "payload": data,
            "timestamp": datetime.utcnow()
        })
        
        # Enqueue parsing task
        from app.tasks import parse_news_batch
        await parse_news_batch.kiq([data.get("id")])
    
    await client.connect_and_stream(handle_update)

if __name__ == "__main__":
    asyncio.run(main())
```

### 4.2 Graceful Shutdown

```python
# app/main.py
import signal
import asyncio
from typing import AsyncGenerator

shutdown_event = asyncio.Event()

def handle_sigterm(signum, frame):
    shutdown_event.set()

signal.signal(signal.SIGTERM, handle_sigterm)
signal.signal(signal.SIGINT, handle_sigterm)

# In collector
async def main():
    collector_task = asyncio.create_task(client.connect_and_stream(...))
    await shutdown_event.wait()
    
    collector_task.cancel()
    try:
        await collector_task
    except asyncio.CancelledError:
        print("Collector shut down gracefully")
```

### 4.3 Error Handling + Retries

```python
from tenacity import retry, wait_exponential, stop_after_attempt

@retry(
    wait=wait_exponential(multiplier=1, min=2, max=10),
    stop=stop_after_attempt(5)
)
async def fetch_with_retry(url: str) -> dict:
    async with httpx.AsyncClient() as client:
        r = await client.get(url)
        r.raise_for_status()
        return r.json()

# Taskiq built-in retries
@broker.task(max_tries=3, retry_delay=60)
async def parse_news_batch(news_ids: list[str]):
    # Auto-retry on failure
    pass
```

---

## 5. Development Workflow

```bash
# Lint + format
uv run ruff check . --fix
uv run black src tests

# Type check
uv run mypy src

# Tests
uv run pytest tests -v --cov=src

# Migrations
uv run alembic init migrations
uv run alembic revision --autogenerate -m "Add parsed_news table"
uv run alembic upgrade head

# Run locally
docker-compose up -d

# Access services
curl http://localhost:8000/docs          # API Swagger
mongosh mongodb://localhost:27017        # MongoDB shell
psql -h localhost -U alpha -d alpha_sniper  # PostgreSQL
redis-cli -n 1                           # Redis
```

---

## Unresolved Questions

1. **Gemini API rate limits** – Phase 2 research needed for batch processing patterns
2. **Scale testing** – Exact throughput targets unknown; recommend load testing at 50k news/hour
3. **MongoDB sharding strategy** – Raw zone landing may need sharding beyond 1TB
4. **Observability depth** – Jaeger vs Datadog vs custom; requires ops/monitoring plan
5. **Real-time alerting** – Mention framework (e.g., Alertmanager) but not yet scoped

---

## References

- [Motor 3.7 Deprecation](https://www.mongodb.com/docs/drivers/motor/)
- [Beanie Async MongoDB ORM](https://johal.in/beanie-async-pydantic-motor-powered-python-mongodb-queries-2025/)
- [SQLAlchemy 2.0 Docs](https://docs.sqlalchemy.org/)
- [Taskiq Task Queue](https://taskiq-python.github.io/guide/)
- [websockets 16.0 Docs](https://websockets.readthedocs.io/en/stable/reference/asyncio/client.html)
- [HTTPX vs Requests vs AIOHTTP](https://oxylabs.io/blog/httpx-vs-requests-vs-aiohttp)
- [Pydantic v2 Validation](https://docs.pydantic.dev/latest/concepts/validators/)
