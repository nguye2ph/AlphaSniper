# CLAUDE.md - AlphaSniper

## Project Overview
AlphaSniper is a real-time stock news data pipeline for personal trading.
Focus: small-cap stocks. Pipeline: Collect -> Store (raw) -> Parse (AI) -> Clean -> Query -> Notify.

## Tech Stack
- **Language**: Python 3.12+ (uv package manager)
- **API**: FastAPI (async)
- **Task Queue**: Taskiq + Redis
- **Raw DB**: MongoDB 7 (Beanie ODM, Pydantic v2 models)
- **Clean DB**: PostgreSQL 16 (SQLAlchemy 2.0 async, Alembic migrations)
- **Cache**: Redis 7 (dedup sets, Taskiq broker)
- **WebSocket**: websockets 16.0 (Finnhub streaming)
- **HTTP**: httpx (async+sync)
- **AI Parser**: Google Gemini API (structured output extraction)
- **Validation**: Pydantic v2
- **Config**: pydantic-settings (.env)
- **Deploy**: Docker Compose (7 containers)

## Data Sources
1. **Finnhub** (primary): WebSocket real-time stream, 60 calls/min free, 50 symbols max
2. **MarketAux** (secondary): REST polling every 15min, 100 req/day free
3. **SEC EDGAR** (background): RSS feed + XBRL API, unlimited, 10 req/sec

## Project Structure
```
src/
  core/           # config.py, database.py, models/, schemas/
  collectors/     # finnhub-ws.py, marketaux-rest.py, sec-edgar-rss.py
  parsers/        # headline-parser.py, gemini-parser.py, dedup.py
  api/            # FastAPI routes (articles, tickers, health)
  jobs/           # Taskiq tasks + scheduler (collect, parse, cleanup)
  webapp/         # (Future) TypeScript web UI
research/         # API samples, source evaluations, data analysis
plans/            # Implementation plans + reports
docs/             # Project documentation
migrations/       # Alembic (PostgreSQL only)
tests/            # pytest + pytest-asyncio
```

## Database Schema

### MongoDB (Raw Zone) - Beanie Documents
```python
class RawArticle(Document):
    source: str          # "finnhub" | "marketaux" | "sec_edgar"
    source_id: str       # Original ID for dedup
    payload: dict        # Raw API response as-is
    collected_at: datetime
    is_processed: bool = False
    class Settings:
        collection = "raw_articles"
```

### PostgreSQL (Clean Zone) - SQLAlchemy Models
```python
class Article(Base):
    id: UUID
    source: str
    source_id: str       # Dedup reference
    headline: str
    summary: str | None
    url: str
    published_at: datetime
    tickers: list[str]   # ["AAPL", "TSLA"]
    sentiment: float     # -1.0 to 1.0
    sentiment_label: str # "bullish" | "bearish" | "neutral"
    market_cap: float | None
    category: str        # "earnings" | "insider" | "merger" | etc.
    raw_article_id: str  # Reference to MongoDB document
```

## Coding Standards
- **File naming**: kebab-case for Python files (e.g., `finnhub-ws.py`)
- **File size**: Keep under 200 lines, split into modules
- **Async**: All DB operations and HTTP calls must be async
- **Error handling**: Use tenacity for retries, structured logging
- **Validation**: Pydantic models for all I/O boundaries
- **Config**: All secrets via pydantic-settings + .env, never hardcode

## Development Commands
```bash
# Dependencies
uv sync --all-extras

# Run services
docker compose up -d

# Dev API
uv run uvicorn src.api.main:app --reload --port 8200

# Collector (separate process)
uv run python -m src.collectors.finnhub_ws

# Workers
uv run taskiq worker src.jobs.celery_app:broker --concurrency 8

# Scheduler
uv run taskiq scheduler src.jobs.celery_app:broker

# Tests
uv run pytest tests -v --cov=src

# Lint
uv run ruff check . --fix

# Migrations
uv run alembic revision --autogenerate -m "description"
uv run alembic upgrade head
```

## Docker Compose Services
```
postgres   - PostgreSQL 16 (port 5432)
mongo      - MongoDB 7 (port 27017)
redis      - Redis 7 Alpine (port 6379)
api        - FastAPI (port 8200)
collector  - Finnhub WS + REST pollers
worker     - Taskiq workers
beat       - Taskiq scheduler
```

## Key Workflows

### Adding a New Data Source
1. Create collector in `src/collectors/{source-name}.py`
2. Implement `BaseCollector` interface
3. Add Beanie document model if response format differs
4. Register in Taskiq scheduler (for REST) or run as service (for WebSocket)
5. Add parser logic in `src/parsers/`
6. Test with `uv run pytest tests/test-collectors/`

### Data Flow
```
Source API -> Collector -> MongoDB (raw) -> Taskiq Queue -> Parser Worker
-> PostgreSQL (clean) -> FastAPI (query) / Discord (notify)
```

### Dedup Strategy
- Redis SET stores seen `source:source_id` combinations
- TTL: 7 days (articles older than 7d are assumed processed)
- Check before MongoDB insert to avoid duplicates

## API Keys Required
- `FINNHUB_API_KEY` - Get free at https://finnhub.io/register
- `MARKETAUX_API_KEY` - Get free at https://www.marketaux.com/register
- `GEMINI_API_KEY` - Google AI Studio (Phase 2)

## Research Context
- Brainstorm: `plans/reports/brainstorm-260411-2304-alphasniper-architecture.md`
- API research: `plans/reports/researcher-260411-2315-stock-news-api-research.md`
- Stack analysis: `plans/reports/researcher-260411-2353-python-stack-analysis.md`
- Finnhub deep dive: `research/api-samples/finnhub-api-analysis.md`
- MarketAux + SEC: `research/api-samples/marketaux-sec-edgar-analysis.md`
- Live tests: `research/api-samples/live-test-results.md`
