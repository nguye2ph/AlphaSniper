# Phase 01 — Market Cap Filter

## Context Links
- Base collector: `src/collectors/base_collector.py`
- Config: `src/core/config.py`
- Finnhub REST: `src/collectors/finnhub_rest.py`
- MarketAux REST: `src/collectors/marketaux_rest.py`
- Pipeline task: `src/jobs/taskiq_app.py` → `process_raw_articles`

## Overview
- **Priority**: P1 (blocker for all other phases)
- **Status**: pending
- **Effort**: 2h
- Add `market_cap_limit` config, a Redis-backed market cap cache, and apply filtering in existing collectors + parse task.

## Key Insights
- Finnhub `/quote` endpoint returns `mc` (market cap) field — use this for per-ticker lookups
- MarketAux `entities[].market_cap` is already in payload — parse directly, no extra API call needed
- Cache TTL 24h is appropriate: small-cap market cap rarely jumps > 100M overnight
- `None` market cap = unknown → **keep** (don't discard; may be small-cap with no data)
- Filter at collect time (before MongoDB insert) to reduce pipeline load
- Also filter in `process_raw_articles` as secondary gate for articles already in MongoDB
- **IMPORTANT (Validation Session 1):** Market cap filter only applies to NEW sources (TickerTick, Discord). Existing Finnhub/MarketAux collectors keep all articles regardless of market cap — user wants large-cap coverage too
<!-- Updated: Validation Session 1 - mc filter scope limited to new sources only -->

## Requirements

### Functional
- `market_cap_limit: int = 100_000_000` in `Settings`
- Redis cache: `mcap:{TICKER}` → float string, TTL 86400s
- `get_market_cap(ticker) -> float | None` — fetch from Finnhub quote, cache result
- `is_within_limit(market_cap) -> bool` — None → True (keep), > limit → False
- ~~`finnhub_rest.py`: after fetching each article, lookup tickers from `related` field, skip if all tickers exceed limit~~ — **REMOVED (Validation): keep all Finnhub articles**
- ~~`marketaux_rest.py`: parse `entities[].market_cap`, skip if > limit~~ — **REMOVED (Validation): keep all MarketAux articles**
- `process_raw_articles`: enrich Article with `market_cap` field from cache during parse

### Non-functional
- Cache miss → Finnhub API call → re-cache → max 1 extra API call per unknown ticker
- Graceful: if Finnhub quote call fails, treat as unknown (keep article)
- No blocking: cache lookups are async, non-blocking

## Architecture

```
Article arrives → extract tickers from payload
        ↓
for each ticker → Redis GET mcap:{TICKER}
        ↓ (cache miss)
  Finnhub /quote?symbol={TICKER} → mc field
        ↓
  Redis SET mcap:{TICKER} {value} EX 86400
        ↓
is_within_limit(mc) → False? → skip article
```

## Related Code Files

### Modify
- `src/core/config.py` — add `market_cap_limit`, `finnhub_quote_url`
- `src/collectors/finnhub_rest.py` — inject `MarketCapCache`, filter per article
- `src/collectors/marketaux_rest.py` — parse entity market_cap, filter per article
- `src/jobs/taskiq_app.py` — enrich `Article.market_cap` from cache in `process_raw_articles`

### Create
- `src/collectors/market-cap-cache.py` — Redis cache + Finnhub quote lookup

### Alembic migration (if Article model lacks market_cap column)
- Check `src/core/models/article.py` — add `market_cap: float | None` column if missing
- Run `uv run alembic revision --autogenerate -m "add market_cap to article"`

## Implementation Steps

1. **config.py** — add two fields:
   ```python
   market_cap_limit: int = 100_000_000
   # Note: finnhub_api_key already exists, reuse for quote calls
   ```

2. **Create `src/collectors/market-cap-cache.py`**:
   ```python
   # MarketCapCache class
   # __init__(self, redis_client, api_key, limit)
   # async get_market_cap(ticker: str) -> float | None
   #   - Redis GET mcap:{ticker}
   #   - cache hit: return float(cached)
   #   - cache miss: GET https://finnhub.io/api/v1/quote?symbol={ticker}&token={key}
   #   - extract response["mc"] (market cap field)
   #   - SET mcap:{ticker} with EX 86400
   #   - if API error: return None
   # async is_within_limit(ticker: str) -> bool
   #   - mc = await get_market_cap(ticker)
   #   - return mc is None or mc <= self.limit
   # async are_tickers_within_limit(tickers: list[str]) -> bool
   #   - any(await is_within_limit(t) for t in tickers)  # keep if ANY ticker qualifies
   ```
   - Use `httpx.AsyncClient` with `tenacity.retry` (3 attempts, wait_exponential 1-10s)
   - Keep file under 80 lines; no extra methods

3. **finnhub_rest.py** — in `_fetch_market_news` and `_fetch_company_news`:
   - Instantiate `MarketCapCache` once per `collect()` call (pass redis client)
   - After building `article_id`, extract tickers from `article.get("related", "")`
   - Call `await mcap.are_tickers_within_limit(tickers)` — if False: skip
   - If no tickers: keep (unknown)

4. **marketaux_rest.py** — in `_fetch_news`:
   - Extract entities market cap: `entities = article.get("entities", [])`, `mcs = [e["market_cap"] for e in entities if e.get("market_cap")]`
   - If any mc present and ALL > limit: skip
   - If no mc data: keep

5. **taskiq_app.py** — in `process_raw_articles` loop, after building `Article`:
   - Add: `market_cap = _extract_market_cap(raw.source, raw.payload)`
   - Set `article.market_cap = market_cap`
   - Add `_extract_market_cap(source, payload) -> float | None` helper at bottom

6. **Article model** — verify `market_cap: float | None` column exists; add if missing + generate migration

## Todo List
- [ ] Add `market_cap_limit: int = 100_000_000` to `Settings` in `config.py`
- [ ] Create `src/collectors/market-cap-cache.py` with `MarketCapCache` class
- [ ] Update `finnhub_rest.py` to filter by market cap
- [ ] Update `marketaux_rest.py` to filter by market cap
- [ ] Update `process_raw_articles` in `taskiq_app.py` to enrich `market_cap`
- [ ] Add `_extract_market_cap()` helper to `taskiq_app.py`
- [ ] Check `src/core/models/article.py` for `market_cap` column; add + migrate if missing
- [ ] Add `.env.example` entry: `MARKET_CAP_LIMIT=100000000`

## Test Cases

| Scenario | Input | Expected |
|----------|-------|----------|
| Ticker with mc=50M | tickers=["RBNE"], mc=50_000_000 | keep (within limit) |
| Ticker with mc=200M | tickers=["AAPL"], mc=200_000_000 | skip |
| Unknown mc (API fail) | tickers=["XYZ"], Finnhub 404 | keep (None = unknown) |
| No tickers in article | tickers=[] | keep |
| Mixed: one small, one large | tickers=["RBNE","AAPL"] | keep (any within limit) |
| Cache hit | Redis has "mcap:RBNE" = "50000000" | no API call, return 50M |
| Cache miss | Redis empty for ticker | Finnhub call, then cache set |
| MarketAux entity mc present | entities=[{market_cap: 80M}] | keep |
| MarketAux all entities > limit | entities=[{market_cap: 500M}] | skip |

## Verification Steps
1. `uv run python -c "from src.collectors.market_cap_cache import MarketCapCache; print('import ok')"` — no errors
2. Start Redis + Finnhub key in `.env`
3. `uv run python -c "import asyncio; from src.collectors.market_cap_cache import MarketCapCache; ..."` — test cache miss/hit
4. Run `uv run pytest tests/test_collectors/test_market_cap_cache.py -v`
5. Run full pipeline, check MongoDB: articles with mc > 100M should not appear

## Acceptance Criteria
- [ ] `market_cap_limit` config field exists with default 100M
- [ ] `MarketCapCache.get_market_cap("AAPL")` returns float (or None on error)
- [ ] Redis key `mcap:AAPL` set after first lookup
- [ ] Second call to `get_market_cap("AAPL")` does NOT hit Finnhub API (cache hit)
- [ ] Articles with known mc > 100M are not saved to MongoDB
- [ ] Articles with unknown mc are saved to MongoDB
- [ ] No existing tests broken

## Risk Assessment
| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| Finnhub quote API uses different mc field name | Medium | Check live response; fallback to `c * sharesOutstanding` if needed |
| Rate limit hit during bulk ticker lookups | Low | Cache + 0.1s sleep between calls |
| Article missing tickers field | Low | Default to keep (already handled by `are_tickers_within_limit([])`) |

## Security Considerations
- Finnhub API key already in `.env`; no new secrets
- Redis cache values are floats — no injection surface

## Next Steps
- Phase 2 and Phase 3 can begin after `MarketCapCache` is complete
- Phase 2 (Discord) will call `is_within_limit()` with pre-parsed mc from message text — does NOT need API call
