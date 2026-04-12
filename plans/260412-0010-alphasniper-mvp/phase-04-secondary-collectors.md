# Phase 4: MarketAux + SEC EDGAR Collectors

## Overview
- **Priority**: High
- **Status**: pending
- **Description**: Build REST poller for MarketAux (sentiment-tagged news) and SEC EDGAR RSS parser (8-K filings). Extends BaseCollector from Phase 3.

## Key Insights

### MarketAux
- Free: 100 req/day, no API key required for basic access
- Endpoint: `GET https://api.marketaux.com/v1/news/all`
- Params: `symbols`, `sentiment_gte`, `sentiment_lte`, `published_after`, `api_token`
- Response includes: entities with ticker, sentiment_score, exchange, industry
- OTC coverage: unconfirmed — test with known OTC tickers
- Strategy: 100 reqs spread across day = ~1 req every 15 minutes

### SEC EDGAR
- Free: unlimited (10 req/sec rate limit)
- MUST include User-Agent header with app name + email
- Endpoints:
  - Submissions: `https://data.sec.gov/submissions/CIK{10-digit}.json`
  - Company tickers: `https://www.sec.gov/files/company_tickers.json` (daily cache)
  - 8-K RSS feed for press releases
- Latency: 10+ minutes for new filings
- Value: catches insider activity, press releases that news APIs miss

## Related Code Files
- **Create**: `src/collectors/marketaux-rest.py`
- **Create**: `src/collectors/sec-edgar-rss.py`
- **Create**: `src/core/models/ticker-lookup.py` (SEC CIK-to-ticker mapping cache)

## Implementation Steps

### MarketAux
1. Create `MarketAuxCollector(BaseCollector)` in `marketaux-rest.py`
2. Implement `fetch_news(symbols, sentiment_range, published_after)`
3. Rate limiter: max 1 request per 15 minutes (100/day budget)
4. Parse entities array → extract ticker, sentiment_score, exchange
5. Save raw response to MongoDB

### SEC EDGAR
1. Create `SecEdgarCollector(BaseCollector)` in `sec-edgar-rss.py`
2. Download + cache `company_tickers.json` (daily refresh)
3. Implement CIK ↔ ticker lookup
4. Poll 8-K RSS feed every 10 minutes
5. Extract filing metadata: CIK, form type, filed date, accession number
6. Save to MongoDB with resolved ticker symbol

## Todo List
- [ ] MarketAuxCollector with rate limiting
- [ ] SEC EDGAR RSS parser
- [ ] CIK-to-ticker mapping cache
- [ ] User-Agent header for SEC compliance
- [ ] Tests for both collectors

## Test Cases
- MarketAux: fetch news, response contains entities with ticker + sentiment
- MarketAux: rate limiter blocks requests beyond 100/day
- SEC EDGAR: CIK lookup resolves "0000320193" → "AAPL"
- SEC EDGAR: 8-K RSS returns recent filings
- Both: data saved to MongoDB `raw_articles` with correct source field

## Acceptance Criteria
- [ ] MarketAux poller runs on 15-min schedule
- [ ] SEC EDGAR poller runs on 10-min schedule
- [ ] Both save to MongoDB with source="marketaux" / "sec_edgar"
- [ ] CIK-ticker cache refreshes daily
- [ ] SEC requests include proper User-Agent

## Next Steps
- Phase 5: Dedup + Taskiq pipeline (process raw → clean)
