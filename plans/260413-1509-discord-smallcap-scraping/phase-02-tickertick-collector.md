# Phase 2: TickerTick API Collector

## Context Links
- [Plan overview](plan.md)
- [Phase 1 — Market Cap Filter](phase-01-market-cap-filter.md)
- [TickerTick API docs](https://github.com/hczhu/TickerTick-API)

## Overview
- **Priority:** P1
- **Status:** pending
- **Effort:** 1.5h
- **Description:** Add TickerTick API as a free, high-coverage news source. 10K US stocks, thousands of sources, query language, 10 req/min free.

## Key Insights
- Completely free, no API key needed
- Query language: `tt:TICKER` (broad), `z:TICKER` (strict), story type filters (SEC, earnings, etc.)
- Returns: id, title, url, site, time, tags (tickers array)
- No market cap in response — use MarketCapCache from Phase 1
- Rate limit: 10 req/min — poll every 2 min per query is safe
- PyTickerTick Python wrapper available on pip

## Requirements

### Functional
- Poll TickerTick `/feed` endpoint for watchlist tickers
- Extract articles with tickers, deduplicate
- Filter by market cap < 100M using Phase 1 cache
- Save raw to MongoDB

### Non-functional
- Stay under 10 req/min rate limit
- Graceful error handling on rate limit (429)

## Architecture

```
Taskiq Scheduler (every 2 min)
  → TickerTickRest.collect()
    → GET /feed?q=(or tt:AAPL tt:TSLA ...)&n=50
    → For each article:
      → Dedup check (Redis)
      → Market cap check (MarketCapCache)
      → save_raw() to MongoDB
```

## Related Code Files

### Create
- `src/collectors/tickertick-rest.py` — TickerTick REST collector

### Modify
- `src/jobs/taskiq_app.py` — add scheduled task
- `src/core/config.py` — add tickertick watchlist config (optional, reuse finnhub_symbols)
- `pyproject.toml` — add `PyTickerTick` dependency (or use raw httpx)

## Implementation Steps

1. **Create collector** (`src/collectors/tickertick-rest.py`)
   - Extend BaseCollector, source_name = "tickertick"
   - **Dual query strategy (Validation Session 1):**
     - Query 1: watchlist tickers `(or tt:AAPL tt:TSLA ...)`
     - Query 2: broad small-cap sources `(or (and tt:* s:sec.gov) (and tt:* s:globenewswire.com))`
     - 2 requests per cycle, well within 10 req/min limit
   - Use httpx to GET `https://api.tickertick.com/feed?q={query}&n=50`
<!-- Updated: Validation Session 1 - dual query strategy confirmed -->
   - Parse response: extract id (use as source_id), title (headline), url, time, tags (tickers)
   - Dedup by source_id
   - For each ticker in tags → lookup market cap → skip if > limit
   - save_raw() with payload

2. **Register in Taskiq** (`src/jobs/taskiq_app.py`)
   - Add `collect_tickertick` task with `schedule=[{"cron": "*/2 * * * *"}]`

3. **Handle rate limiting**
   - If 429 response, log warning and skip cycle
   - Use tenacity retry with exponential backoff (max 3 retries)

## Todo List
- [ ] Create tickertick-rest.py collector
- [ ] Register Taskiq scheduled task (every 2 min)
- [ ] Handle rate limiting gracefully
- [ ] Test with live API

## Test Cases
- Collector fetches articles from TickerTick API
- Articles with tickers in response are correctly extracted
- Market cap filter skips articles > 100M
- Rate limit (429) handled without crash
- Dedup prevents duplicate saves

## Verification Steps
1. `uv run python -m src.collectors.tickertick_rest` — fetches articles
2. Check MongoDB: `db.raw_articles.find({source: "tickertick"}).count()`
3. Run process_raw_articles — articles appear in PostgreSQL

## Success Criteria
- [ ] Collector fetches and saves articles from TickerTick
- [ ] Market cap filter applied correctly
- [ ] Rate limit respected (< 10 req/min)
- [ ] Registered in Taskiq scheduler

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|-----------|
| API goes down or changes | Medium | It's a bonus source, not primary |
| Rate limit too strict | Low | 10 req/min is generous for 2-min polling |
| No market cap in response | Low | Use MarketCapCache from Phase 1 |

## Security Considerations
- No API key needed — no secrets to manage
- All requests are read-only GET

## Next Steps
- Phase 3: Discord NuntioBot collector (parallel)
- Phase 4: RSS collectors (parallel)
