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

# Start all services
docker compose up -d

# Dev mode (local Python)
uv sync --all-extras
uv run uvicorn src.api.main:app --reload

# Run collector
uv run python -m src.collectors.finnhub_ws

# Run workers
uv run taskiq worker src.jobs.celery_app:broker
```

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
| Finnhub | Primary (WebSocket) | 1-5s | Free (60 calls/min) |
| MarketAux | Secondary (REST) | 5-10s | Free (100 req/day) |
| SEC EDGAR | Background (RSS) | 10min | Free (unlimited) |

## Development

```bash
uv run ruff check . --fix    # Lint
uv run mypy src              # Type check
uv run pytest tests -v       # Tests
uv run alembic upgrade head  # Migrations
```
