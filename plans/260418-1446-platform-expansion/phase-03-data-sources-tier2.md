# Phase 3: Data Sources Tier 2 (Medium ROI)

## Context Links

- Parent: [plan.md](plan.md)
- Depends on: [Phase 1 - Adaptive Scheduling](phase-01-adaptive-scheduling.md)
- Related: [Phase 2 - Tier 1 Sources](phase-02-data-sources-tier1.md)
- Research: [Free Data Sources](../reports/researcher-260418-1452-free-stock-data-sources-research.md)

## Overview

- **Priority:** P2
- **Status:** complete
- **Effort:** ~1 week
- **Description:** Add 3 more collectors: StockTwits sentiment (reuse SocialSentiment model from P2), ORTEX short interest, Unusual Whales options flow. New PostgreSQL model: ShortInterest.

## Key Insights

- StockTwits: free public endpoint, unauthenticated read, bullish/bearish labels built-in
- ORTEX: public API ~100 req/day, daily short %, squeeze score (high value for small-cap)
- Unusual Whales: free tier 100-500 req/day, unclear if sufficient; treat as experimental
- StockTwits reuses SocialSentiment model from Phase 2 (platform="stocktwits")

## Requirements

### Functional

- 3 new collectors following BaseCollector pattern
- 1 new PostgreSQL model: ShortInterest
- StockTwits reuses SocialSentiment (platform="stocktwits")
- Extend process_raw_articles for 3 new source types
- Register all in adaptive scheduler config
- New API endpoints for short interest and options flow

### Non-Functional

- Rate limit compliance: ORTEX ~100/day, StockTwits 100/min, Unusual Whales 100-500/day
- Graceful degradation if Unusual Whales free tier insufficient
- All async, Pydantic validated, structlog logged

## Architecture

```
StockTwits API ──────► stocktwits-rest.py ──► MongoDB (RawSocialPost)
                                                  │
                                        social-sentiment-parser (reuse P2)
                                                  │
                                           SocialSentiment (PG, platform="stocktwits")

ORTEX Public API ────► ortex-short-interest.py ──► MongoDB (RawArticle)
                                                       │
                                                  ShortInterest (PG, new model)

Unusual Whales API ──► unusual-whales.py ──► MongoDB (RawArticle)
                                                  │
                                             Article (PG, category="options_flow")
```

### New PostgreSQL Model

```python
class ShortInterest(Base):  # src/core/models/short-interest.py
    id: UUID
    ticker: str
    short_pct_float: float
    days_to_cover: float
    borrow_fee_pct: float | None
    squeeze_score: int | None  # 0-100
    report_date: datetime
    source: str  # "ortex"
    source_id: str
    raw_data: dict | None  # JSONB
```

## Related Code Files

### Files to Create

| File | LOC | Purpose |
|------|-----|---------|
| `src/collectors/stocktwits-rest.py` | ~100 | StockTwits public symbol stream |
| `src/collectors/ortex-short-interest.py` | ~100 | ORTEX daily short interest |
| `src/collectors/unusual-whales.py` | ~110 | Options flow (experimental) |
| `src/core/models/short-interest.py` | ~40 | PostgreSQL short interest model |
| `src/api/routes/short-interest-routes.py` | ~55 | GET /api/short-interest |
| `src/api/routes/options-flow-routes.py` | ~50 | GET /api/options-flow |
| `tests/test-collectors/test-stocktwits.py` | ~40 | StockTwits tests |
| `tests/test-collectors/test-ortex.py` | ~40 | ORTEX tests |
| `tests/test-collectors/test-unusual-whales.py` | ~40 | Unusual Whales tests |

### Files to Modify

| File | Changes |
|------|---------|
| `src/core/config.py` | Add stocktwits_symbols, ortex_api_url, unusual_whales_api_key |
| `src/core/models/__init__.py` | Export ShortInterest |
| `src/jobs/taskiq_app.py` | Add 3 collector tasks, extend process_raw_articles |
| `src/api/main.py` | Register 2 new routers |
| `migrations/` | New Alembic migration for short_interest table |

## Implementation Steps

### Collector 1: StockTwits (~100 LOC)

1. Create `src/collectors/stocktwits-rest.py`:
   - source_name = "stocktwits"
   - `collect()`: GET https://api.stocktwits.com/api/2/streams/symbol/{symbol}.json
   - Iterate watchlist tickers (from settings)
   - Save each message as RawSocialPost, source_id = message.id
   - Payload: body, sentiment (bullish/bearish/neutral), created_at, user
2. Reuse social-sentiment-parser from Phase 2
   - StockTwits provides sentiment labels directly (no VADER needed)
   - Map to SocialSentiment with platform="stocktwits"
3. Register in scheduler (default interval: 300s)

### Collector 2: ORTEX Short Interest (~100 LOC)

1. Create `src/collectors/ortex-short-interest.py`:
   - source_name = "ortex"
   - `collect()`: GET https://public.ortex.com/api/v1/short_interest?ticker={ticker}
   - Query watchlist tickers daily
   - Save as RawArticle, source_id = f"{ticker}_{report_date}"
   - Payload: short_pct_float, days_to_cover, borrow_fee_pct, squeeze_score
2. Extend process_raw_articles:
   - source="ortex" -> map directly to ShortInterest model
3. Register in scheduler (default interval: 86400s / 24h, daily data)

### Collector 3: Unusual Whales (~110 LOC)

1. Add `unusual_whales_api_key` to Settings (optional, empty = disabled)
2. Create `src/collectors/unusual-whales.py`:
   - source_name = "unusual_whales"
   - `collect()`: GET https://api.unusualwhales.com/api/stock/{ticker}/options-flow
   - Check if API key is set; skip if empty
   - Save as RawArticle, source_id = f"{contract_id}_{timestamp}"
   - Payload: contract, volume, premium, oi_ratio, implied_move
3. Map to Article with category="options_flow" in process_raw_articles
4. Register in scheduler (default interval: 3600s / 1h, limited quota)

### Database & API

5. Create ShortInterest PostgreSQL model
6. Generate Alembic migration: `uv run alembic revision --autogenerate -m "add short_interest table"`
7. Create short-interest API routes: GET /api/short-interest?ticker=X&days=30
8. Create options-flow API routes: GET /api/options-flow?ticker=X
9. Register routers in main.py
10. Seed scheduler configs for 3 new sources

## Todo List

- [ ] Create stocktwits-rest collector
- [ ] Create ortex-short-interest collector
- [ ] Create unusual-whales collector (experimental)
- [ ] Create ShortInterest PostgreSQL model
- [ ] Run Alembic migration
- [ ] Extend process_raw_articles for 3 new sources
- [ ] Create short-interest API routes
- [ ] Create options-flow API routes
- [ ] Register routers in main.py
- [ ] Add config settings for new sources
- [ ] Register scheduler configs
- [ ] Write tests
- [ ] Verify Unusual Whales free tier viability

## Test Cases

### Happy Path

- StockTwits: fetch AAPL stream -> save messages -> parse -> SocialSentiment rows
- ORTEX: fetch TSLA short data -> save -> parse -> ShortInterest row
- Unusual Whales: fetch options flow -> save -> parse -> Article with category="options_flow"
- API: GET /api/short-interest?ticker=TSLA returns squeeze score + short %

### Edge Cases

- StockTwits returns empty stream (no messages) -> log, no error
- ORTEX returns no data for obscure ticker -> skip, log
- Unusual Whales API key empty -> collector skips entirely (disabled)
- Duplicate short interest for same ticker+date -> upsert or skip

### Error Scenarios

- StockTwits rate limited -> tenacity backoff
- ORTEX API down -> timeout, log, metrics-tracker records failure
- Unusual Whales 401 (bad key) -> disable collector, alert
- Network timeout on any source -> retry 3x then skip

## Verification Steps

### Manual

1. Run each collector manually with test tickers
2. Verify MongoDB documents saved correctly
3. Run process_raw_articles, verify PG rows
4. Hit API endpoints, verify JSON responses
5. Check scheduler metrics for new sources

### Automated

```bash
uv run pytest tests/test-collectors/test-stocktwits.py -v
uv run pytest tests/test-collectors/test-ortex.py -v
uv run pytest tests/test-collectors/test-unusual-whales.py -v
uv run alembic upgrade head
```

## Acceptance Criteria

- [ ] StockTwits collector works, sentiment data in PostgreSQL
- [ ] ORTEX collector provides daily short interest
- [ ] Unusual Whales collector works OR documented as insufficient free tier
- [ ] ShortInterest table populated with daily snapshots
- [ ] API endpoints return data for all new types
- [ ] All registered in adaptive scheduler
- [ ] Tests pass

## Success Criteria

- 13 total data sources (6 original + 4 Tier 1 + 3 Tier 2)
- Short interest data enables squeeze detection
- StockTwits confirms/contradicts Reddit sentiment (cross-validation)

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| StockTwits public API deprecated | Medium | ApeWisdom API as alternative |
| ORTEX rate limit too restrictive | Low | Cache 24h, only query watchlist |
| Unusual Whales free tier insufficient | Medium | Mark experimental; Barchart as fallback |
| ORTEX API response format changes | Low | Pydantic validation catches mismatches |

## Security Considerations

- Unusual Whales API key in .env only
- StockTwits no auth needed (public endpoints)
- ORTEX public API, no key required
- Polite User-Agent on all HTTP requests

## Next Steps

- Phase 4 UI creates pages for short interest, options flow
- Phase 5 combines short interest + sentiment for ticker health score
