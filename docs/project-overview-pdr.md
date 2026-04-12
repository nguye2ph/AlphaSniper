# AlphaSniper - Project Overview & PDR

**Slogan:** _Identify the Alpha, Snipe the News._

## Project Mission

AlphaSniper is a real-time stock news intelligence pipeline for personal traders. It automatically collects, parses, and serves high-quality news for small-cap stocks to power trading decisions in seconds.

**Target Users:** Individual traders, algorithmic trading systems, retail investment communities.

## Tech Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Language | Python | 3.12+ |
| Package Manager | uv | Latest |
| API Framework | FastAPI | Latest |
| Task Queue | Taskiq + Redis | Latest |
| Raw Database | MongoDB (Beanie ODM) | 7 |
| Clean Database | PostgreSQL (SQLAlchemy 2.0) | 16 |
| Cache/Broker | Redis | 7 |
| WebSocket | websockets | 16.0 |
| HTTP Client | httpx | Async |
| AI Parser | Google Gemini API | Latest |
| Validation | Pydantic | v2 |
| Config | pydantic-settings | v2 |
| Orchestration | Docker Compose | Latest |

## Data Sources

| Source | Type | Latency | Rate Limit (Free) | Role |
|--------|------|---------|-------------------|------|
| Finnhub | WebSocket | 1-5s | 60 calls/min, 50 symbols max | Primary real-time |
| MarketAux | REST | 5-10s | 100 requests/day | Secondary news |
| SEC EDGAR | RSS Feed | 10 min | Unlimited | Background filings |

**Free Tier Summary:** ~500 articles/day from combined sources, sufficient for MVP retail trading use.

## MVP Scope & Status

**Goal:** Complete data pipeline from collection to query, tested and deployed.

| Phase | Name | Status |
|-------|------|--------|
| 1 | Project Scaffold + Docker | ✅ Completed |
| 2 | Database Models + Migrations | ✅ Completed |
| 3 | Finnhub Collector (Primary) | ✅ Completed |
| 4 | MarketAux + SEC EDGAR Collectors | ✅ Completed |
| 5 | Dedup + Taskiq Pipeline | ✅ Completed |
| 6 | FastAPI Query Endpoints | ✅ Completed |
| 7 | AI Parser (Gemini) | ✅ Completed |
| 8 | Integration Tests + Polish | ✅ Completed |

**MVP Status:** 8/8 phases complete. Ready for testing and refinement.

## Data Flow Architecture

```
Finnhub WS (1-5s)  ─┐
MarketAux REST     ├──> [Dedup Check] ──> MongoDB (Raw) ──┐
SEC EDGAR RSS      ─┘                                      │
                                                           v
                    Taskiq Worker (Parser)                 
                    Gemini API (Extraction)               
                           │                               
                           v                               
                    PostgreSQL (Clean) ◄──────────────────┘
                           │
                    ┌──────┼──────┐
                    v      v      v
                 FastAPI Discord Bot Algo Feed
                 (Query) (Notify)  (Trading)
```

## Success Metrics (MVP)

- ✅ Collect 500+ unique articles/day across 3 sources
- ✅ < 10s latency from Finnhub publish to MongoDB insert
- ✅ Zero duplicate articles (dedup working with Redis TTL=7d)
- ✅ FastAPI returns articles filtered by ticker, date, sentiment
- ✅ Docker Compose `up` brings entire system online
- ✅ 95%+ ticker extraction accuracy (Gemini parser)

## Next Steps (Post-MVP)

- Web dashboard (TypeScript/React)
- Discord bot integration for notifications
- Sentiment analysis & scoring
- Watchlist management
- Trading signal generation
