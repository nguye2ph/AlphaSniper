# Codebase Summary

## Overview

AlphaSniper is a real-time stock news data pipeline with a modular, async-first architecture. All code follows strict type hints, Pydantic validation, and structured logging.

## Directory Structure

```
src/
├── api/                    # FastAPI application
│   ├── main.py            # App instantiation, middleware setup
│   ├── deps.py            # Dependency injection (DB sessions, etc)
│   └── routes/
│       ├── articles_routes.py    # GET /articles, /articles/latest, /articles/stats
│       ├── tickers_routes.py     # GET /tickers, /tickers/{symbol}/news
│       └── sources_routes.py     # GET /sources
│
├── collectors/            # Data collection from external APIs
│   ├── base_collector.py  # Abstract BaseCollector interface
│   ├── finnhub_ws.py      # WebSocket stream (real-time, 1-5s latency)
│   ├── finnhub_rest.py    # REST fallback (scheduled)
│   ├── marketaux_rest.py  # Secondary news source (scheduled every 15min)
│   └── sec_edgar_rss.py   # SEC filings (scheduled every 10min)
│
├── parsers/               # Data extraction and enrichment
│   ├── base_parser.py     # Abstract BaseParser interface
│   ├── gemini_parser.py   # Google Gemini API calls (ticker + sentiment extraction)
│   ├── headline_parser.py # Headline parsing and cleaning
│   ├── dedup.py           # Redis-based duplicate detection
│   └── utils/
│       ├── sentiment.py   # Sentiment score calculation (-1.0 to 1.0)
│       └── ticker_extract.py # Ticker symbol extraction helpers
│
├── jobs/                  # Taskiq tasks and scheduler
│   ├── celery_app.py      # Taskiq broker and worker setup
│   ├── parse_task.py      # Main parse task (MongoDB -> PostgreSQL)
│   ├── collect_task.py    # Collection task wrappers
│   ├── cleanup_task.py    # Dedup TTL cleanup
│   └── scheduler.py       # Periodic task scheduling (beat)
│
├── core/                  # Configuration and shared models
│   ├── config.py          # Pydantic Settings (env vars)
│   ├── database.py        # DB connection managers (async)
│   │   ├── get_pg_session() - PostgreSQL async context
│   │   ├── get_mongo_db() - MongoDB Beanie connection
│   │   └── get_redis_client() - Redis connection
│   │
│   ├── models/            # Pydantic + SQLAlchemy models
│   │   ├── article.py     # SQLAlchemy Article (PostgreSQL clean zone)
│   │   ├── raw_article.py # Beanie RawArticle (MongoDB raw zone)
│   │   ├── ticker.py      # Ticker reference table
│   │   └── source.py      # Source status tracking
│   │
│   └── schemas/           # Pydantic request/response models
│       ├── article_schema.py     # ArticleResponse, ArticleRequest
│       ├── common_schema.py      # Shared enums (SentimentLabel, Source)
│       └── pagination_schema.py  # PaginationParams, ListResponse

migrations/               # Alembic database migrations (PostgreSQL only)
├── versions/
│   └── 6e8e48a17a0f_initial_schema.py  # Initial schema
└── env.py               # Alembic environment configuration

tests/                   # pytest test suites
├── test_collectors/
│   ├── test_finnhub_ws.py
│   ├── test_marketaux_rest.py
│   └── test_sec_edgar_rss.py
├── test_parsers/
│   ├── test_gemini_parser.py
│   ├── test_headline_parser.py
│   └── test_dedup.py
├── test_api/
│   ├── test_articles_routes.py
│   ├── test_tickers_routes.py
│   └── test_sources_routes.py
├── test_jobs/
│   └── test_parse_task.py
└── conftest.py          # Shared pytest fixtures (db_session, redis_client, etc)

research/               # API exploration and data samples
├── api-samples/
│   ├── INDEX.md                          # API research summary
│   ├── finnhub-api-analysis.md          # Finnhub deep dive
│   ├── marketaux-sec-edgar-analysis.md  # MarketAux + SEC EDGAR
│   ├── api-usage-quick-reference.md     # API cheat sheet
│   ├── live-test-results.md             # Real API test runs
│   ├── finnhub-request-examples.json    # Sample requests
│   ├── marketaux-request-examples.json
│   └── sec-edgar-apple-sample.json      # Sample responses
└── README.md

plans/                  # Implementation plans and reports
├── 260412-0010-alphasniper-mvp/
│   ├── plan.md          # Overview of all 8 phases
│   ├── phase-01-project-scaffold.md     # Docker, pyproject.toml setup
│   ├── phase-02-database-models.md      # MongoDB + PostgreSQL models
│   ├── phase-03-finnhub-collector.md    # WebSocket implementation
│   ├── phase-04-secondary-collectors.md # MarketAux + SEC EDGAR
│   ├── phase-05-dedup-taskiq-pipeline.md # Queue + dedup logic
│   ├── phase-06-fastapi-endpoints.md    # API routes
│   ├── phase-07-ai-parser-gemini.md     # Gemini integration
│   └── phase-08-integration-tests.md    # Testing + polish
│
└── reports/            # Research findings
    ├── brainstorm-260411-2304-alphasniper-architecture.md
    ├── researcher-260411-2315-stock-news-api-research.md
    └── researcher-260411-2353-python-stack-analysis.md

docs/                   # Project documentation (you are here)
├── codebase-summary.md          # This file
├── project-overview-pdr.md      # Project mission, scope, PDR
├── system-architecture.md       # DB design, service architecture, data flow
├── code-standards.md            # Coding rules, style guide
└── deployment-guide.md          # Setup, running, troubleshooting
```

## Key Files by Responsibility

### Data Collection

| File | Purpose | Trigger |
|------|---------|---------|
| `src/collectors/finnhub_ws.py` | Persistent WebSocket stream | Service startup |
| `src/collectors/finnhub_rest.py` | REST fallback polling | Scheduled task (Taskiq) |
| `src/collectors/marketaux_rest.py` | Secondary news source | Every 15 min (Taskiq) |
| `src/collectors/sec_edgar_rss.py` | SEC filing RSS feed | Every 10 min (Taskiq) |

### Data Processing Pipeline

| File | Purpose | Input | Output |
|------|---------|-------|--------|
| `src/parsers/dedup.py` | Check Redis for duplicates | `source:source_id` | `bool (seen or new)` |
| `src/parsers/gemini_parser.py` | Extract tickers + sentiment | Raw article text | Parsed JSON |
| `src/parsers/headline_parser.py` | Clean and normalize text | Raw headline | Cleaned headline |
| `src/jobs/parse_task.py` | Main pipeline orchestrator | MongoDB RawArticle | PostgreSQL Article |

### API Service

| File | Purpose | Routes |
|------|---------|--------|
| `src/api/main.py` | FastAPI app setup | / |
| `src/api/routes/articles_routes.py` | Article queries | /articles, /articles/latest, /articles/stats |
| `src/api/routes/tickers_routes.py` | Ticker queries | /tickers, /tickers/{symbol}/news |
| `src/api/routes/sources_routes.py` | Source status | /sources |

### Database Models

| File | DB Zone | Purpose |
|------|---------|---------|
| `src/core/models/raw_article.py` | MongoDB | Unmodified API responses |
| `src/core/models/article.py` | PostgreSQL | Clean, queryable articles |
| `src/core/models/ticker.py` | PostgreSQL | Stock symbols and metadata |
| `src/core/models/source.py` | PostgreSQL | Data source tracking |

## Code Patterns

### Async Database Access

```python
# PostgreSQL (SQLAlchemy 2.0 + asyncio)
from src.core.database import get_session

async def get_articles_by_ticker(ticker: str):
    async with get_session() as session:
        result = await session.execute(
            select(Article).where(Article.tickers.contains([ticker]))
        )
        return result.scalars().all()
```

### MongoDB (Beanie ODM)

```python
# Read from raw zone
from src.core.models.raw_article import RawArticle

raw = await RawArticle.get(article_id)
payload = raw.payload  # Dictionary of raw API response
```

### Taskiq Task Definition

```python
# src/jobs/parse_task.py
@broker.task
async def parse_article_task(raw_article_id: str) -> str:
    """Parse raw article and store cleaned version in PostgreSQL."""
    # Task code here
    return article_id
```

### Pydantic Validation

```python
# Schema with validation
class ArticleRequest(BaseModel):
    ticker: str = Field(..., min_length=1, max_length=5)
    limit: int = Field(default=10, ge=1, le=100)
    
# Auto-validated in API route
@router.get("")
async def list_articles(params: ArticleRequest) -> list[ArticleResponse]:
    pass  # params are guaranteed valid
```

## Testing Strategy

### Fixtures (conftest.py)

- `async_client` - Async HTTP client for API testing
- `db_session` - PostgreSQL session for integration tests
- `mongo_db` - MongoDB connection for integration tests
- `redis_client` - Redis for dedup testing

### Test Organization

- **Unit tests** (with mocks): Fast, no external dependencies
- **Integration tests** (with Docker services): Slow but comprehensive
- **API tests** (with test client): Exercise FastAPI routes

### Running Tests

```bash
# All tests
pytest tests -v

# Unit tests only (mocked)
pytest tests -k "not integration" -v

# Integration tests (requires Docker services)
docker compose up -d postgres mongo redis
pytest tests -k "integration" -v
```

## Dependencies (Key Packages)

| Package | Version | Purpose |
|---------|---------|---------|
| fastapi | Latest | API framework |
| sqlalchemy | 2.0+ | PostgreSQL ORM (async) |
| beanie | Latest | MongoDB ODM |
| pydantic | v2 | Validation + settings |
| taskiq | Latest | Task queue (Redis broker) |
| httpx | Latest | Async HTTP client |
| websockets | 16.0 | WebSocket streaming |
| google-generativeai | Latest | Gemini API client |
| tenacity | Latest | Retry logic |
| structlog | Latest | Structured logging |
| pytest | Latest | Test framework |
| pytest-asyncio | Latest | Async test support |
| alembic | Latest | Database migrations |

## Configuration (src/core/config.py)

All settings loaded from `.env` via Pydantic:

```python
FINNHUB_API_KEY          # Required
MARKETAUX_API_KEY        # Required
GEMINI_API_KEY           # Required
POSTGRES_URL             # Default: postgresql+asyncpg://...
MONGO_URL                # Default: mongodb://mongo:27017/...
REDIS_URL                # Default: redis://redis:6379
API_PORT                 # Default: 8200
LOG_LEVEL                # Default: INFO
```

## Development Workflow

1. **Code locally** → Run API with `uv run uvicorn`
2. **Run tests** → `pytest tests -v` (Docker services running)
3. **Lint & format** → `ruff check . --fix`
4. **Type check** → `mypy src`
5. **Commit** → Conventional commits (`feat:`, `fix:`, `docs:`, etc)
6. **Deploy** → `docker compose up -d` in production

## Next Steps / TODOs

- [ ] Web dashboard (React/TypeScript in `src/webapp/`)
- [ ] Discord bot integration for notifications
- [ ] Sentiment analysis model fine-tuning
- [ ] Watchlist management (user accounts)
- [ ] Trading signal generation
- [ ] Production monitoring (Prometheus, DataDog)
- [ ] Database backups and recovery procedures
