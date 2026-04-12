# System Architecture

## Overview

AlphaSniper uses a **two-zone database design** with a scalable task queue. Raw data lands in MongoDB, gets parsed by workers, then flows into PostgreSQL for clean queryable storage.

## Database Architecture

### Zone 1: Raw Zone (MongoDB)

**Purpose:** Store unmodified API responses for audit trail and reprocessing.

**Collection:** `raw_articles`

```python
RawArticle (Beanie Document):
  - _id: ObjectId (auto)
  - source: str          # "finnhub" | "marketaux" | "sec_edgar"
  - source_id: str       # Unique ID from original API (dedup key)
  - payload: dict        # Raw API response (as-is)
  - collected_at: datetime
  - is_processed: bool   # Flag for parser status
```

### Zone 2: Clean Zone (PostgreSQL)

**Purpose:** Structured, queryable data for API serving and analytics.

**Tables:** `articles`, `tickers`, `sources`

```python
Article:
  - id: UUID (primary key)
  - source: str
  - source_id: str         # Reference to raw article
  - headline: str
  - summary: str | None
  - url: str
  - published_at: datetime
  - collected_at: datetime
  - tickers: list[str]     # ["AAPL", "TSLA"]
  - sentiment: float       # -1.0 to 1.0
  - sentiment_label: str   # "bullish" | "bearish" | "neutral"
  - market_cap: float | None
  - category: str          # "earnings", "insider", "merger", etc.
  - raw_article_id: str    # Dedup reference
  - created_at: datetime
  - updated_at: datetime

Ticker:
  - id: UUID
  - symbol: str            # "AAPL"
  - name: str              # "Apple Inc"
  - market_cap: float | None
  - is_small_cap: bool

Source:
  - id: UUID
  - name: str              # "finnhub", "marketaux", "sec_edgar"
  - last_collection_at: datetime
  - status: str            # "active" | "inactive"
```

### Zone 3: Cache (Redis)

**Purpose:** Dedup tracking and task queue broker.

- Dedup SET: `dedup:{source}:{source_id}` with TTL=7 days
- Taskiq broker: Tasks queued and distributed to workers
- Session cache: API request caching (future)

## Service Architecture

### Docker Compose Stack (7 containers)

```
┌─────────────────────────────────────────────────┐
│ PostgreSQL 16 (port 5432)                       │
│ - Articles, tickers, sources                    │
│ - Alembic migrations                            │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│ MongoDB 7 (port 27017)                          │
│ - Raw articles (unprocessed)                    │
│ - Beanie ODM models                             │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│ Redis 7 (port 6379)                             │
│ - Dedup sets, TTL=7d                            │
│ - Taskiq broker + queue                         │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│ FastAPI (port 8200)                             │
│ - GET /articles, /articles/latest, /articles/stats
│ - GET /tickers, /tickers/{symbol}/news          │
│ - GET /sources                                  │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│ Collector (background process)                  │
│ - finnhub_ws.py (WebSocket, persistent)        │
│ - marketaux_rest.py (scheduled task)            │
│ - sec_edgar_rss.py (scheduled task)             │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│ Taskiq Worker Pool                              │
│ - Consumes parse tasks from Redis               │
│ - Calls Gemini API for parsing                  │
│ - Writes to PostgreSQL                          │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│ Taskiq Scheduler (Beat)                         │
│ - Triggers MarketAux collector every 15min      │
│ - Triggers SEC EDGAR collector every 10min      │
│ - Cleanup job (dedup expiry)                    │
└─────────────────────────────────────────────────┘
```

## Data Flow Pipeline

```
Step 1: COLLECT
  Finnhub WS ──────────────────────┐
  MarketAux REST (scheduled) ─────┼──> Dedup Check (Redis)
  SEC EDGAR RSS (scheduled) ──────┘         │
                                           v
                              If new: INSERT MongoDB
                                      Enqueue to Taskiq
                                      
Step 2: QUEUE
  Redis Taskiq Queue ──> Task = { mongo_id, source }
                        
Step 3: PARSE
  Taskiq Worker  ──> GET raw from MongoDB
                  ──> CALL Gemini API for extraction
                      - tickers: ["AAPL", "TSLA"]
                      - sentiment: 0.85
                      - category: "earnings"
                      
Step 4: STORE CLEAN
  Parser ──> INSERT Article in PostgreSQL
          ──> UPDATE RawArticle.is_processed = True
          
Step 5: SERVE
  FastAPI ──> Query PostgreSQL
           ──> Return articles by:
               - ticker (symbol filter)
               - date range
               - sentiment range
               - source
```

## API Endpoints

| Method | Route | Purpose | Response |
|--------|-------|---------|----------|
| GET | `/articles` | List articles with filters | `ArticleResponse[]` |
| GET | `/articles/latest` | Last N articles (default 10) | `ArticleResponse[]` |
| GET | `/articles/stats` | Article counts by sentiment, source | `ArticleStats` |
| GET | `/tickers` | List tracked tickers | `TickerResponse[]` |
| GET | `/tickers/{symbol}/news` | All articles for a ticker | `ArticleResponse[]` |
| GET | `/sources` | Data source status | `SourceResponse[]` |

**Query Parameters (articles endpoints):**
- `limit: int` (default 10, max 100)
- `offset: int` (default 0)
- `ticker: str` (optional, filter by symbol)
- `sentiment_min: float` (optional, -1.0 to 1.0)
- `sentiment_max: float` (optional)
- `source: str` (optional, "finnhub" | "marketaux" | "sec_edgar")
- `from_date: datetime` (optional, ISO 8601)
- `to_date: datetime` (optional, ISO 8601)

## Deployment Details

**API Server:**
- Port: 8200 (configurable via `API_PORT` env var)
- Uvicorn (async ASGI)
- CORS enabled for localhost (configurable)

**Database Connections:**
- PostgreSQL: Connection pooling via SQLAlchemy
- MongoDB: Beanie ODM connection manager
- Redis: Taskiq manages connection pool

**Process Management:**
- API: `docker compose up api`
- Collector: `docker compose up collector`
- Workers: `docker compose up worker` (scales with `--scale`)
- Scheduler: `docker compose up beat`

## Error Handling & Resilience

- **Dedup**: Redis SET prevents duplicate processing
- **Retries**: Tenacity library for API failures (exponential backoff)
- **Dead Letter Queue**: Failed parse tasks logged for review
- **Graceful Shutdown**: SIGTERM handlers flush pending tasks
