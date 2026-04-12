# Phase 6: FastAPI Query Endpoints

## Overview
- **Priority**: Medium
- **Status**: pending
- **Description**: REST API to query parsed articles from PostgreSQL. Supports filtering by ticker, date range, sentiment, source.

## Key Insights
- Can start in parallel with Phase 3-4 (only needs Phase 2 DB models)
- FastAPI auto-generates OpenAPI docs at /docs
- Pagination via cursor-based (published_at) for time-series data
- Keep endpoints simple — this is a data query layer, not a full web app

## Related Code Files
- **Create**: `src/api/routes/articles-routes.py`
- **Create**: `src/api/routes/tickers-routes.py`
- **Create**: `src/api/routes/sources-routes.py`
- **Create**: `src/api/routes/health-routes.py`
- **Create**: `src/api/deps.py` (DB session dependency)
- **Modify**: `src/api/main.py` (register routers)

## Endpoints

### Articles
- `GET /api/articles` — list articles with filters (ticker, date, sentiment, source, limit)
- `GET /api/articles/{id}` — single article detail
- `GET /api/articles/latest` — most recent N articles
- `GET /api/articles/stats` — count by source, avg sentiment, articles/day

### Tickers
- `GET /api/tickers` — list tracked tickers
- `GET /api/tickers/{symbol}/news` — articles for specific ticker
- `GET /api/tickers/{symbol}/sentiment` — sentiment trend over time

### Sources
- `GET /api/sources` — list data sources with status + last_collected_at

### Health
- `GET /health` — basic health check (DB connections, Redis, worker status)

## Implementation Steps
1. Create `deps.py` with async PostgreSQL session dependency
2. Create `health-routes.py` — ping postgres, mongo, redis
3. Create `articles-routes.py` — CRUD with query filters
4. Create `tickers-routes.py` — ticker lookup + news
5. Create `sources-routes.py` — source status
6. Register all routers in `main.py`
7. Test all endpoints with sample data

## Todo List
- [ ] DB session dependency injection
- [ ] Health endpoint (postgres + mongo + redis)
- [ ] Articles list/detail/latest/stats
- [ ] Tickers list/news/sentiment
- [ ] Sources status
- [ ] Pagination (cursor-based)
- [ ] Swagger docs verification

## Test Cases
- `GET /api/articles?ticker=AAPL` returns only AAPL articles
- `GET /api/articles?sentiment_gte=0.5` returns only bullish articles
- `GET /api/articles?from=2026-04-01&to=2026-04-12` filters by date
- `GET /api/articles/latest?limit=10` returns 10 most recent
- `GET /api/tickers/AAPL/sentiment` returns time-series sentiment data
- `GET /health` returns status of all services
- Pagination: next cursor returns next page correctly

## Acceptance Criteria
- [ ] All endpoints respond with correct JSON
- [ ] Filtering by ticker, date, sentiment works
- [ ] Swagger UI at /docs shows all endpoints
- [ ] Health check verifies all 3 database connections
- [ ] Pagination works for large result sets

## Next Steps
- Phase 7: AI parser (Gemini) replaces rule-based
