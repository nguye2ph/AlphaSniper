# Phase 3: Finnhub Collector (Primary Source)

## Overview
- **Priority**: High
- **Status**: pending
- **Description**: Build Finnhub WebSocket consumer + REST poller. Primary real-time data source.

## Key Insights
- Finnhub free tier: 60 calls/min REST, 50 symbols WebSocket
- WebSocket endpoint: `wss://ws.finnhub.io?token=API_KEY`
- Heartbeat: server pings every ~30s, client must pong back
- Company News REST: `/api/v1/company-news?symbol=X&from=DATE&to=DATE`
- Market News REST: `/api/v1/news?category=general`
- News ID field enables dedup + pagination via `minId`
- Small-cap coverage is LIMITED — this is why we need Phase 4 sources

## Requirements

### Functional
- WebSocket consumer: persistent connection, auto-reconnect, subscribe to N symbols
- REST poller: batch fetch company news for watchlist tickers
- Market news poller: fetch general market news (catches small-cap mentions)
- Store all responses in MongoDB `raw_articles` via Beanie
- Enqueue parsing tasks via Taskiq (Phase 5)

### Non-functional
- WebSocket reconnect with exponential backoff (2s, 4s, 8s, max 60s)
- Graceful shutdown on SIGTERM/SIGINT
- Structured logging (JSON format)
- Rate limit awareness (30 calls/sec global)

## Related Code Files
- **Create**: `src/collectors/base-collector.py` (abstract interface)
- **Create**: `src/collectors/finnhub-ws.py` (WebSocket consumer)
- **Create**: `src/collectors/finnhub-rest.py` (REST poller)
- **Modify**: `src/core/config.py` (add FINNHUB_API_KEY, FINNHUB_SYMBOLS)

## Implementation Steps

1. Create `BaseCollector` ABC in `base-collector.py`:
   - `async def collect()` — main loop
   - `async def save_raw(data)` — save to MongoDB
   - `async def shutdown()` — cleanup
2. Create `FinnhubWebSocket` in `finnhub-ws.py`:
   - Connect to `wss://ws.finnhub.io`
   - Subscribe to symbols from config
   - Handle ping/pong heartbeat
   - On news message: save to MongoDB, log
   - Auto-reconnect with backoff on disconnect
3. Create `FinnhubRest` in `finnhub-rest.py`:
   - `fetch_market_news()` — GET /api/v1/news?category=general
   - `fetch_company_news(symbol, from_date, to_date)` — per-ticker
   - `poll_watchlist()` — iterate watchlist, fetch each ticker's news
   - Track `minId` for pagination (avoid re-fetching)
4. Add Finnhub config to `src/core/config.py`
5. Create Docker entrypoint for collector service
6. Test: run collector, verify data appears in MongoDB

## Todo List
- [ ] BaseCollector ABC
- [ ] FinnhubWebSocket consumer
- [ ] FinnhubRest poller
- [ ] Config: FINNHUB_API_KEY, FINNHUB_SYMBOLS
- [ ] Reconnect + backoff logic
- [ ] Graceful shutdown handler
- [ ] Docker entrypoint for collector
- [ ] Integration test with real API (needs key)

## Test Cases
- WebSocket connects and receives ping within 30s
- WebSocket auto-reconnects after simulated disconnect
- REST poller fetches market news, returns list of articles
- REST poller respects rate limit (no 429 errors)
- All fetched articles saved to MongoDB with correct schema
- `minId` tracking prevents duplicate fetches
- Graceful shutdown closes WebSocket cleanly

## Acceptance Criteria
- [ ] WebSocket consumer runs as long-lived process
- [ ] REST poller fetches news for configurable symbol list
- [ ] All data saved to MongoDB `raw_articles`
- [ ] No duplicate articles (minId tracking)
- [ ] Reconnect works within 60s of disconnect
- [ ] Logs show connection status, articles collected, errors

## Risk Assessment
- **API key not set**: Fail fast with clear error message
- **Rate limit exceeded**: Implement backoff, degrade to slower polling
- **WebSocket 50 symbol limit**: Prioritize most-active tickers, rotate others via REST

## Next Steps
- Phase 4: MarketAux + SEC EDGAR collectors (same pattern)
