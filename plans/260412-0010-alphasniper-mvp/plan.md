---
status: completed
created: 2026-04-12
slug: alphasniper-mvp
---

# AlphaSniper MVP Implementation Plan

## Goal
Data pipeline that collects real-time stock news from 3 free sources, stores raw in MongoDB, parses to structured data in PostgreSQL, and serves via FastAPI.

## Phases Overview

| Phase | Name | Status | Dependencies |
|-------|------|--------|-------------|
| 1 | Project Scaffold + Docker | **completed** | None |
| 2 | Database Models + Migrations | **completed** | Phase 1 |
| 3 | Finnhub Collector (Primary) | **completed** | Phase 2 |
| 4 | MarketAux + SEC EDGAR Collectors | **completed** | Phase 2 |
| 5 | Dedup + Taskiq Pipeline | **completed** | Phase 3, 4 |
| 6 | FastAPI Query Endpoints | **completed** | Phase 2 |
| 7 | AI Parser (Gemini) | **completed** | Phase 5 |
| 8 | Integration Tests + Polish | **completed** | All |

## Key Decisions
- **Tech stack**: Python 3.12+, FastAPI, Taskiq, Beanie, SQLAlchemy 2.0
- **DB**: MongoDB (raw) + PostgreSQL (clean) + Redis (queue/cache)
- **Deploy**: Docker Compose (7 containers)
- **AI**: Google Gemini API for headline parsing
- **Package manager**: uv

## Research References
- [Brainstorm](../reports/brainstorm-260411-2304-alphasniper-architecture.md)
- [API Research](../reports/researcher-260411-2315-stock-news-api-research.md)
- [Python Stack](../reports/researcher-260411-2353-python-stack-analysis.md)
- [Finnhub Analysis](../../research/api-samples/finnhub-api-analysis.md)
- [MarketAux + SEC](../../research/api-samples/marketaux-sec-edgar-analysis.md)

## Success Criteria
- [ ] Collect 500+ unique articles/day from 3 sources
- [ ] < 10s latency from Finnhub publish to MongoDB insert
- [ ] Zero duplicate articles (dedup working)
- [ ] FastAPI returns articles by ticker, date, sentiment
- [ ] Docker Compose `up` brings entire system online
- [ ] 95%+ ticker extraction accuracy (Phase 7)
