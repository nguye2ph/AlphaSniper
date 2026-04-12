# AlphaSniper Architecture Brainstorm
**Date:** 2026-04-11 | **Status:** Complete

---

## Problem Statement

Build a real-time stock news data pipeline for personal trading, focusing on small-cap stocks. System must:
- Collect news from multiple sources (APIs + potential scraping)
- Extract structured data: ticker, headline, sentiment, market_cap
- Store in queryable database with time-series optimization
- Eventually: filter, notify, and feed into trading algorithms

**MVP Goal:** Data pipeline + structured DB with clean schema. No notification yet.

---

## Research Findings (Key Takeaways)

### Data Sources Verdict
| Source | Status | Why |
|--------|--------|-----|
| **Finnhub** | PRIMARY | Free 60 calls/min, WebSocket real-time (1-5s latency), covers all NASDAQ/NYSE |
| **MarketAux** | SECONDARY | Free 100 req/day, 5000+ sources, global small-cap including OTC |
| **SEC EDGAR RSS** | BACKGROUND | Free unlimited, 10-min latency, insider signals from 8-K filings |
| **Alpha Vantage** | OPTIONAL | Only 25 req/day, AI sentiment scores, use for backfill |
| **NuntioBot** | SKIP | Discord-only, no API, no web interface. Dead end. |
| **Discord scraping** | SKIP | 100% banned in 2026, automated detection, permanent bans |
| **Twitter/X API** | SKIP | $200/mo minimum, free tier removed |

**Estimated free capacity: ~3,500 articles/day at $0 cost.**

Full research: `plans/reports/researcher-260411-2315-stock-news-api-research.md`

---

## Evaluated Approaches

### Approach A: Python Monorepo (RECOMMENDED)
```
FastAPI (API) + Celery/Redis (jobs) + asyncio WebSocket consumers
```
**Pros:**
- Richest ecosystem for scraping (Scrapy, Playwright, BeautifulSoup)
- Native asyncio for WebSocket streaming (Finnhub)
- Best LLM/AI libraries (Gemini SDK, transformers)
- Single language = simpler deployment
- FastAPI performance comparable to Node.js

**Cons:**
- Web UI will need separate TypeScript project later
- Less type-safety than TypeScript (mitigated by Pydantic)

### Approach B: NestJS + Python Workers
**Pros:** Type-safe API, good for future web platform
**Cons:** Two runtimes in Docker, complex IPC, overkill for MVP data pipeline

### Approach C: Full TypeScript
**Pros:** Unified stack
**Cons:** Weak scraping ecosystem, no good async WebSocket patterns, poor AI/ML libs

**Decision: Approach A** — Python-first. TypeScript webapp added later when needed.

---

## Recommended Architecture

### Tech Stack (Finalized from Research)
| Layer | Technology | Why |
|-------|-----------|-----|
| **Language** | Python 3.12+ | Best for scraping + AI |
| **API Framework** | FastAPI | Async, fast, auto-docs |
| **Task Queue** | Taskiq + Redis | 10x Celery perf, async-native, FastAPI integrated |
| **Raw DB** | MongoDB + Beanie ODM | 45k QPS async, Pydantic v2 models, Motor deprecation-proof |
| **Clean DB** | PostgreSQL + SQLAlchemy 2.0 | 19yr maturity, flexible async queries |
| **Cache/Queue** | Redis | Dedup sets, Taskiq broker, response caching |
| **WebSocket** | websockets 16.0 | RFC 6455, minimal API, long-lived connections |
| **HTTP Client** | httpx | Async+sync, HTTP/2, requests-compatible |
| **AI Parser** | Google Gemini API | Structured output extraction (Phase 2) |
| **Scraping** | httpx + BeautifulSoup | SEC EDGAR HTML parsing |
| **Validation** | Pydantic v2 | 5-50x faster (Rust core), everywhere integrated |
| **Config** | pydantic-settings | Type-safe env, .env file support |
| **Migrations** | Alembic | Postgres schema versioning |
| **Deps** | uv | Ultra-fast package manager, 2026 standard |
| **Container** | Docker Compose | All services orchestrated |

### Database Architecture: Two-Zone Design
- **MongoDB (Landing Zone)**: Raw API responses stored as-is. Beanie ODM w/ Pydantic models. Flexible schema handles Finnhub/MarketAux/SEC format differences.
- **PostgreSQL (Clean Zone)**: Parsed, normalized data. Strict schema: ticker, sentiment, market_cap, headline. SQLAlchemy 2.0 async + Alembic migrations.
- **Redis**: Article ID dedup sets, Taskiq broker, API response caching.

**Key insight**: Motor (MongoDB async driver) deprecates May 2026. Beanie abstracts this transition while delivering 45k QPS async vs Motor's 25k.

---

## Project Structure

```
alpha-sniper/
├── CLAUDE.md                    # Project-specific agent instructions
├── AGENTS.md                    # Agent definitions & capabilities
├── README.md                    # Project overview
├── docker-compose.yml           # All services
├── .env.example                 # Environment template
├── pyproject.toml               # Python dependencies (uv)
│
├── docs/                        # Project documentation
│   ├── project-overview-pdr.md
│   ├── system-architecture.md
│   ├── code-standards.md
│   ├── codebase-summary.md
│   └── deployment-guide.md
│
├── plans/                       # Implementation plans
│   ├── reports/                 # Research & brainstorm reports
│   └── {date}-{slug}/           # Phase plans
│
├── research/                    # Research data & samples
│   ├── api-samples/             # Sample API responses
│   ├── data-analysis/           # Data quality analysis
│   └── source-evaluation/       # Source comparison results
│
├── src/
│   ├── core/                    # Shared foundation
│   │   ├── config.py            # Settings (pydantic-settings)
│   │   ├── database.py          # DB connection + session
│   │   ├── models/              # SQLAlchemy models
│   │   │   ├── article.py       # News article model
│   │   │   ├── ticker.py        # Ticker/symbol model
│   │   │   └── source.py        # Data source model
│   │   └── schemas/             # Pydantic schemas
│   │       ├── article.py       # Article I/O schemas
│   │       └── common.py        # Shared schemas
│   │
│   ├── collectors/              # Data collection workers
│   │   ├── base.py              # Abstract collector interface
│   │   ├── finnhub-ws.py        # Finnhub WebSocket consumer
│   │   ├── marketaux-rest.py    # MarketAux REST poller
│   │   ├── sec-edgar-rss.py     # SEC EDGAR RSS parser
│   │   └── alphavantage-rest.py # Alpha Vantage sentiment
│   │
│   ├── parsers/                 # Data extraction & enrichment
│   │   ├── headline-parser.py   # Extract ticker, sentiment from headline
│   │   ├── gemini-parser.py     # Gemini API structured extraction
│   │   └── dedup.py             # Cross-source deduplication
│   │
│   ├── api/                     # FastAPI service
│   │   ├── main.py              # App entrypoint
│   │   ├── routes/
│   │   │   ├── articles.py      # CRUD + query endpoints
│   │   │   ├── tickers.py       # Ticker lookup
│   │   │   └── health.py        # Health check
│   │   └── deps.py              # Dependencies
│   │
│   ├── jobs/                    # Celery tasks
│   │   ├── celery-app.py        # Celery config
│   │   ├── collect-news.py      # Scheduled collection tasks
│   │   ├── parse-articles.py    # AI parsing pipeline
│   │   └── cleanup.py           # Data retention cleanup
│   │
│   └── webapp/                  # (Future) TypeScript web UI
│       └── .gitkeep
│
├── scripts/                     # Utility scripts
│   ├── seed-tickers.py          # Populate ticker watchlist
│   ├── test-api-sources.py      # Validate API connections
│   └── export-data.py           # Export to CSV/JSON
│
├── migrations/                  # Alembic migrations
│   ├── alembic.ini
│   └── versions/
│
└── tests/
    ├── test-collectors/
    ├── test-parsers/
    └── test-api/
```

---

## Data Schema (Core)

```python
# articles hypertable (TimescaleDB)
class Article:
    id: UUID
    source: str              # "finnhub", "marketaux", "sec_edgar"
    source_id: str           # Original article ID for dedup
    headline: str
    summary: str | None
    url: str
    published_at: datetime   # TimescaleDB partition key
    collected_at: datetime
    
    # Extracted data
    tickers: list[str]       # ["AAPL", "TSLA"]
    sentiment: float | None  # -1.0 to 1.0
    sentiment_label: str     # "bullish", "bearish", "neutral"
    market_cap: float | None # USD
    
    # Metadata
    category: str            # "earnings", "insider", "merger", etc.
    raw_data: dict           # Original API response (JSONB)
    is_parsed: bool          # AI parsing completed?
    
    # Indexes: (published_at, tickers, sentiment, source)
```

---

## Real-time Data Flow

```
┌─────────────────────────────────────────────────────┐
│                    COLLECTORS                        │
│                                                      │
│  Finnhub WS ──(1-5s)──┐                             │
│  MarketAux  ──(15min)──┼──→ Redis Queue ──→ Celery  │
│  SEC EDGAR  ──(10min)──┤        │          Workers   │
│  AlphaVantage ─(1hr)───┘        │            │       │
│                                  │            ▼       │
│                            Dedup Check    Parse +    │
│                            (Redis SET)    Enrich     │
│                                              │       │
│                                              ▼       │
│                                    TimescaleDB       │
│                                    (articles)        │
│                                        │             │
│                              ┌─────────┼─────────┐   │
│                              ▼         ▼         ▼   │
│                          FastAPI   Discord    Algo   │
│                          (query)   (notify)  (feed)  │
│                                   [future]  [future] │
└─────────────────────────────────────────────────────┘
```

---

## Docker Compose Services (6 containers)

```yaml
services:
  postgres:    # PostgreSQL 16 (clean zone)
  mongo:       # MongoDB 7 (raw landing zone)
  redis:       # Queue broker + cache + dedup
  api:         # FastAPI server (port 8000)
  collector:   # Finnhub WebSocket + REST pollers
  worker:      # Taskiq task workers (parse, enrich)
  beat:        # Taskiq scheduler (cron polling)
```

Full docker-compose.yml blueprint: `plans/reports/researcher-260411-2353-python-stack-analysis.md`

---

## Agent Architecture (for Claude Code automation)

### CLAUDE.md Scope
- Project context, tech stack, coding standards
- Database schema reference
- API source configurations
- Development workflow

### AGENTS.md Scope
Define specialized agents for pipeline tasks:

| Agent | Purpose | Trigger |
|-------|---------|---------|
| **collector-agent** | Add new data sources, fix broken collectors | New API found, collector fails |
| **parser-agent** | Improve AI parsing accuracy | Parse errors spike |
| **data-quality-agent** | Validate data integrity, dedup | Scheduled daily |
| **schema-agent** | Evolve DB schema, run migrations | New data fields needed |

### Pipeline Automation
- **CI/CD**: GitHub Actions for lint + test on PR
- **Scheduled**: Celery Beat for polling collectors
- **Event-driven**: WebSocket consumers run as long-lived workers
- **Monitoring**: Health endpoints + error rate tracking

---

## Implementation Phases (High-level)

### Phase 1: Foundation (Week 1)
- Project scaffold (pyproject.toml, Docker Compose, DB)
- TimescaleDB schema + migrations
- Core models + Pydantic schemas
- Basic FastAPI with health check

### Phase 2: Collectors (Week 1-2)
- Finnhub WebSocket consumer (primary, real-time)
- MarketAux REST poller (secondary, 15-min)
- SEC EDGAR RSS parser (background, 10-min)
- Redis dedup logic

### Phase 3: Storage & Query (Week 2)
- Celery workers for article processing
- TimescaleDB continuous aggregates
- FastAPI CRUD endpoints
- Data export scripts

### Phase 4: AI Parsing (Week 3)
- Gemini API integration for headline parsing
- Ticker extraction + validation
- Sentiment scoring pipeline
- Batch processing for historical data

### Phase 5: Notification & Integration (Week 4+)
- Discord webhook bot (legitimate, outbound only)
- Filter rules engine (market_cap < 100M, sentiment > threshold)
- WebSocket API for real-time frontend consumption

---

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Finnhub rate limit hit | Primary source blocked | Graceful fallback to MarketAux, exponential backoff |
| API format changes | Parser breaks | Store raw_data JSONB, version parsers, alert on parse failures |
| TimescaleDB complexity | Learning curve | Start with plain Postgres, add hypertable later |
| Gemini API cost | Budget overrun | Batch parsing, cache results, rule-based fallback for simple headlines |
| Data quality variance | Bad trading signals | Cross-source verification, confidence scoring |

---

## Success Metrics (MVP)

- [ ] Collect 500+ unique articles/day from 3 sources
- [ ] < 10s latency from Finnhub publish to DB insert
- [ ] 95%+ ticker extraction accuracy
- [ ] Zero duplicate articles in DB (dedup working)
- [ ] Docker Compose `up` brings entire system online
- [ ] FastAPI query returns articles by ticker, date range, sentiment

---

## Unresolved Questions

1. **Finnhub free tier WebSocket**: Does it stream ALL symbols or limited set? Need to test with microcaps < $10M
2. **MarketAux OTC coverage**: Does free tier include Pink Sheets? Need API test
3. **TimescaleDB vs plain Postgres**: When exactly to enable hypertables? Data volume threshold?
4. **Gemini API pricing**: Cost per 1000 headline parses? Need calculator
5. **Agent automation scope**: How autonomous should pipeline agents be? (deferred to phase evaluation)
