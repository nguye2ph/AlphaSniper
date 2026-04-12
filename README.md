# AlphaSniper

**Slogan:** *Identify the Alpha, Snipe the News.*

Real-time stock news data pipeline for personal trading, focused on small-cap stocks.

## What It Does

Automated "radar station" that scans, extracts, and delivers high-quality stock news for trading decisions in seconds.

**Pipeline:** Collect (APIs) -> Store (MongoDB raw) -> Parse (AI) -> Clean (PostgreSQL) -> Query (FastAPI) -> Notify (Discord/Algo)

## Architecture

```
Finnhub WebSocket (1-5s) ──┐
MarketAux REST (15min)  ───┼──> Redis Queue ──> Taskiq Workers
SEC EDGAR RSS (10min)   ───┘        |               |
                              Dedup Check      Parse + Enrich
                                                    |
                                    ┌───────────────┤
                                    v               v
                               MongoDB          PostgreSQL
                              (raw zone)       (clean zone)
                                    |               |
                              Raw responses    Structured data
                                              (ticker, sentiment,
                                               market_cap, headline)
                                                    |
                                    ┌───────────────┼───────────────┐
                                    v               v               v
                                FastAPI        Discord Bot      Algo Feed
                               (query)         (notify)        (trading)
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.12+ |
| API | FastAPI |
| Task Queue | Taskiq + Redis |
| Raw DB | MongoDB (Beanie ODM) |
| Clean DB | PostgreSQL (SQLAlchemy 2.0) |
| WebSocket | websockets 16.0 |
| HTTP | httpx |
| AI Parser | Google Gemini API |
| Validation | Pydantic v2 |
| Config | pydantic-settings |
| Deps | uv |
| Deploy | Docker Compose |

## Quick Start

```bash
# Prerequisites: Docker, uv
cp .env.example .env
# Edit .env with your API keys (FINNHUB_API_KEY, etc.)

# Start infrastructure
docker compose up -d

# Install Python deps
uv sync --all-extras

# Run collector (fetch news into MongoDB)
uv run python -m src.collectors.finnhub_rest

# Process raw -> clean (MongoDB -> PostgreSQL)
uv run python -c "
import asyncio
from src.jobs.taskiq_app import process_raw_articles
asyncio.run(process_raw_articles.original_func(batch_size=200))
"

# Start API server
uv run uvicorn src.api.main:app --reload --port 8200
```

## Collecting Data

### One-time collection (manual)
```bash
# Fetch from Finnhub (market news + company news for watchlist)
uv run python -m src.collectors.finnhub_rest

# Fetch from MarketAux (global news with sentiment)
uv run python -m src.collectors.marketaux_rest

# Fetch from SEC EDGAR (8-K filings)
uv run python -m src.collectors.sec_edgar_rss

# Process all raw articles into clean PostgreSQL
uv run python -c "
import asyncio
from src.jobs.taskiq_app import process_raw_articles
asyncio.run(process_raw_articles.original_func(batch_size=200))
"
```

### Real-time streaming (Finnhub WebSocket)
```bash
# Persistent WebSocket connection, auto-reconnect
uv run python -m src.collectors.finnhub_ws
```

## Viewing Data

### Via API (recommended)

```bash
# All articles (latest first)
curl http://localhost:8200/api/articles/latest?limit=10 | python3 -m json.tool

# Filter by ticker
curl "http://localhost:8200/api/articles?ticker=AAPL" | python3 -m json.tool

# Filter by sentiment (bullish only)
curl "http://localhost:8200/api/articles?sentiment_gte=0.5" | python3 -m json.tool

# Filter by category
curl "http://localhost:8200/api/articles?category=earnings" | python3 -m json.tool

# Filter by date range
curl "http://localhost:8200/api/articles?from_date=2026-04-12&to_date=2026-04-13" | python3 -m json.tool

# Combined filters
curl "http://localhost:8200/api/articles?ticker=AAPL&sentiment_gte=0.3&category=earnings&limit=5" | python3 -m json.tool

# Stats overview
curl http://localhost:8200/api/articles/stats | python3 -m json.tool

# News for specific ticker
curl http://localhost:8200/api/tickers/NVDA/news | python3 -m json.tool

# Swagger UI (interactive docs)
open http://localhost:8200/docs
```

### Via Database (direct query)

```bash
# PostgreSQL (clean/structured data)
docker compose exec postgres psql -U alpha -d alpha_sniper

# Useful queries:
# Total articles
SELECT count(*) FROM articles;

# Articles by source
SELECT source, count(*) FROM articles GROUP BY source;

# Sentiment distribution
SELECT sentiment_label, count(*) FROM articles GROUP BY sentiment_label;

# Category breakdown
SELECT category, count(*) FROM articles GROUP BY category;

# Latest articles with tickers
SELECT headline, tickers, sentiment_label, category, published_at
FROM articles
WHERE array_length(tickers, 1) > 0
ORDER BY published_at DESC
LIMIT 20;

# Search by ticker
SELECT headline, sentiment, sentiment_label, published_at
FROM articles
WHERE 'AAPL' = ANY(tickers)
ORDER BY published_at DESC;

# Bullish articles today
SELECT headline, tickers, sentiment
FROM articles
WHERE sentiment_label = 'bullish'
  AND published_at >= CURRENT_DATE
ORDER BY sentiment DESC;
```

```bash
# MongoDB (raw API responses)
docker compose exec mongo mongosh alpha_sniper

# Useful queries:
# Total raw articles
db.raw_articles.countDocuments()

# By source
db.raw_articles.aggregate([{$group: {_id: "$source", count: {$sum: 1}}}])

# Latest raw article (full payload)
db.raw_articles.find().sort({collected_at: -1}).limit(1).pretty()

# Unprocessed articles
db.raw_articles.countDocuments({is_processed: false})
```

```bash
# Redis (dedup cache)
docker compose exec redis redis-cli

# Check dedup keys
KEYS dedup:*
DBSIZE
```

### Via Python (programmatic)

```python
import asyncio
from src.core.database import init_mongo, async_session_factory
from src.core.models.raw_article import RawArticle
from src.core.models.article import Article
from sqlalchemy import select

async def query_data():
    # MongoDB: raw articles
    await init_mongo()
    raw_count = await RawArticle.find().count()
    latest_raw = await RawArticle.find().sort("-collected_at").limit(5).to_list()
    for r in latest_raw:
        print(f"[RAW] {r.source}: {r.payload.get('headline', r.payload.get('title', 'N/A'))[:60]}")

    # PostgreSQL: clean articles
    async with async_session_factory() as session:
        result = await session.execute(
            select(Article)
            .where(Article.tickers.any("AAPL"))
            .order_by(Article.published_at.desc())
            .limit(5)
        )
        for a in result.scalars():
            print(f"[CLEAN] {a.headline[:60]} | {a.sentiment_label} | {a.tickers}")

asyncio.run(query_data())
```

## Data Schema

### PostgreSQL — Clean Zone (`articles` table)

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `source` | VARCHAR | "finnhub", "marketaux", "sec_edgar" |
| `source_id` | VARCHAR | Original ID (unique per source) |
| `headline` | TEXT | News headline |
| `summary` | TEXT | Article summary |
| `url` | TEXT | Original article URL |
| `published_at` | TIMESTAMP | When article was published |
| `tickers` | VARCHAR[] | Extracted ticker symbols, e.g. `{AAPL,TSLA}` |
| `sentiment` | FLOAT | -1.0 (bearish) to 1.0 (bullish) |
| `sentiment_label` | VARCHAR | "bullish", "bearish", "neutral" |
| `market_cap` | FLOAT | Company market cap (USD, nullable) |
| `category` | VARCHAR | "earnings", "merger", "insider", "regulatory", "analyst", "legal", "general" |
| `raw_data` | JSONB | Full raw API response (backup) |

### MongoDB — Raw Zone (`raw_articles` collection)

| Field | Type | Description |
|-------|------|-------------|
| `source` | string | Data source name |
| `source_id` | string | Original article ID |
| `payload` | object | Raw API response stored as-is |
| `collected_at` | datetime | When we fetched it |
| `is_processed` | boolean | Whether parsed into PostgreSQL |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Service health check |
| GET | `/api/articles` | List articles (filter: ticker, source, sentiment, category, date) |
| GET | `/api/articles/latest` | Most recent N articles |
| GET | `/api/articles/stats` | Aggregated statistics |
| GET | `/api/tickers` | List tracked tickers |
| GET | `/api/tickers/{symbol}/news` | Articles for specific ticker |
| GET | `/api/sources` | Data source status |

## Project Structure

```
alpha-sniper/
├── src/
│   ├── core/           # Config, DB connections, shared models
│   ├── collectors/     # Data source workers (Finnhub, MarketAux, SEC)
│   ├── parsers/        # AI parsing + ticker extraction
│   ├── api/            # FastAPI endpoints
│   ├── jobs/           # Taskiq tasks + scheduling
│   └── webapp/         # (Future) TypeScript web UI
├── research/           # API samples, source evaluations
├── plans/              # Implementation plans + reports
├── docs/               # Project documentation
├── migrations/         # Alembic DB migrations
└── tests/              # pytest test suites
```

## Data Sources

| Source | Role | Latency | Cost |
|--------|------|---------|------|
| Finnhub | Primary (WebSocket + REST) | 1-5s | Free (60 calls/min) |
| MarketAux | Secondary (REST) | 5-10s | Free (100 req/day) |
| SEC EDGAR | Background (RSS + API) | 10min | Free (unlimited) |

## Development

```bash
uv run ruff check . --fix    # Lint
uv run mypy src              # Type check
uv run pytest tests -v       # Tests (requires Docker services running)
uv run alembic upgrade head  # Run migrations
```
