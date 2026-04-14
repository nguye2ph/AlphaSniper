---
title: "Phase 2: Live Data Source Research + Integration"
status: pending
effort: 3h (1h research + 2h integration)
---

## Context Links

- BaseCollector: `src/collectors/base_collector.py`
- Finnhub WS reference impl: `src/collectors/finnhub_ws.py`
- TickerTick REST: `src/collectors/tickertick_rest.py`
- MarketAux REST: `src/collectors/marketaux_rest.py`
- Discord NuntioBot (undeployed): `src/collectors/discord-nuntio.py`
- Config: `src/core/config.py` — `settings.market_cap_limit = 100M`
- Docker Compose: `docker-compose.yml` — `collector` service runs WS + REST pollers

## Overview

Research free/cheap streaming APIs for small-cap stock news, pick the best candidate, and integrate as a new WebSocket collector following `FinnhubWebSocket` pattern.

**Priority:** P1 — more live sources = better signal coverage  
**Status:** pending  
**Client priority:** Live connection > polling. Small-cap coverage critical.

## Key Insights

- Only Finnhub WS is live-streaming today; everything else polls
- Free tier constraints are the primary filter — must confirm before integration
- Pattern is well-established: extend `BaseCollector`, implement `collect()`, use `save_raw()`
- `discord-nuntio.py` exists but is undeployed — check if it's viable before adding a new source
- Dedup handled by `BaseCollector.save_raw()` — new collector gets it for free
- New collector runs in the existing `collector` Docker service alongside `finnhub_ws.py`

## Research Targets & Evaluation Criteria

| Source | Type | Free Tier | Small-cap? | Priority |
|--------|------|-----------|------------|---------|
| Tiingo | WS (news) | Yes (free plan) | Unknown | HIGH |
| Polygon.io | WS | Delayed only on free | Limited | MEDIUM |
| Unusual Whales | REST/WS | Paid | Yes (focus) | LOW (cost) |
| Benzinga | WS | Paid | Yes | LOW (cost) |
| Alpha Vantage | REST only | Yes | Limited | LOW (no WS) |
| IEX Cloud | SSE | Sandbox free | Unknown | MEDIUM |
| stocknewsapi.com | REST | Yes (limited) | Unknown | LOW (no WS) |
| Discord NuntioBot | WS (Discord) | Already in codebase | Yes | HIGH (free, deploy first) |

**Research questions per candidate:**
1. Does free tier include real-time WebSocket news (not just delayed)?
2. Small-cap / penny stock coverage (tickers < $100M mcap)?
3. Message format — can it map to `RawArticle.payload`?
4. Rate limits / symbol limits on free tier?

## Architecture

```
New collector (WebSocket preferred):
  src/collectors/{source}-ws.py  OR  src/collectors/{source}-sse.py

Class structure (mirrors finnhub_ws.py):
  class {Source}WebSocket(BaseCollector):
    source_name = "{source}"
    async def collect() → main reconnect loop
    async def _stream() → connect + subscribe + process
    async def _handle_message(raw) → parse + save_raw()
    def shutdown() → set _shutdown event

Docker: add to collector service entrypoint alongside finnhub_ws.py
  (run both collectors concurrently via asyncio.gather or separate process)
```

**Parser mapping** — new source payload → `RawArticle.payload` dict:
- Must include: headline/title, url, published_at, tickers (if available)
- AI parser (`gemini-parser.py`) handles structured extraction from raw payload
- No changes to parser needed if payload stored as-is

## Related Code Files

**Create:**
- `src/collectors/{chosen-source}-ws.py` — new WebSocket collector

**Modify:**
- `src/core/config.py` — add API key setting for new source
- `docker-compose.yml` — add new API key env var to `collector` service
- `.env.example` — document new API key
- `src/collectors/__init__.py` — register new collector if needed

**Check (may need modify):**
- `src/collectors/discord-nuntio.py` — evaluate deploying existing implementation first

## Implementation Steps

### Step 1 — Research (1h)

1. Test Tiingo free tier: `curl "https://api.tiingo.com/tiingo/news?token=YOUR_KEY"` — check if WS endpoint exists at `wss://api.tiingo.com/iex`
2. Test IEX Cloud sandbox SSE: check news SSE endpoint availability
3. Check Discord NuntioBot (`discord-nuntio.py`) — is it complete? What's blocking deployment?
4. Document findings: free tier limits, WS availability, message format sample
5. Pick winner: prefer WS > SSE > polling; prefer free > cheap; prefer small-cap coverage

### Step 2 — Integration (2h)

1. Add API key to `src/core/config.py`:
   ```python
   {source}_api_key: str = Field(default="", env="{SOURCE}_API_KEY")
   ```

2. Create `src/collectors/{source}-ws.py` extending `BaseCollector`:
   - Copy structure from `finnhub_ws.py`
   - Implement `source_name`, `__init__`, `collect`, `_stream`, `_handle_message`, `shutdown`
   - `_handle_message` must call `self.save_raw(source_id=..., payload=raw_dict)`
   - Handle ping/pong, reconnect backoff (same pattern: 2s → 60s max)

3. Add env var to `docker-compose.yml` collector service environment block

4. Update `.env.example` with new key

5. Test standalone: `uv run python -m src.collectors.{source}_ws`
   - Verify articles appear in MongoDB `raw_articles` collection
   - Verify dedup works (run twice, no duplicate `source_id`)

6. Add to collector service startup alongside Finnhub WS:
   ```python
   # In collector entrypoint or docker CMD
   await asyncio.gather(finnhub.collect(), new_source.collect())
   ```

## Todo List

### Research
- [ ] Evaluate Discord NuntioBot (`discord-nuntio.py`) — completion status?
- [ ] Test Tiingo WS free tier + message format
- [ ] Test IEX Cloud SSE free tier
- [ ] Check Polygon.io free WS (delayed vs real-time)
- [ ] Document winner choice with rationale

### Integration
- [ ] Add `{source}_api_key` to `config.py`
- [ ] Create `src/collectors/{source}-ws.py`
- [ ] Add env var to `docker-compose.yml` + `.env.example`
- [ ] Standalone test: verify MongoDB ingestion
- [ ] Dedup test: verify no duplicates on re-run
- [ ] Integrate into collector service startup

## Success Criteria

- [ ] Research doc produced with clear winner + rationale
- [ ] New collector connects, streams, and saves to MongoDB `raw_articles`
- [ ] `source` field correctly set (e.g., `"tiingo"`) — distinct from `"finnhub"`
- [ ] Reconnect backoff works on connection drop
- [ ] No duplicate articles in MongoDB from same source
- [ ] Existing Finnhub WS unaffected (run concurrently)
- [ ] `uv run pytest tests -v` passes (no regressions)

## Risk Assessment

- **Free tier bait-and-switch**: Many sources advertise "free" but WS requires paid plan — confirm before building
- **Small-cap coverage gap**: Some sources focus on large-cap; verify with test symbols (e.g., SOUN, MARA, LUNR)
- **Discord NuntioBot**: May already be the best free option — evaluate before adding new dependency
- **asyncio.gather in collector**: If one collector crashes, may take down the other — use `asyncio.create_task` with independent error handling

## Security Considerations

- New API key must be in `.env` only — never hardcoded or committed
- Add to `.gitignore` check if `.env` not already excluded

## Next Steps

- After integration: update `feed/page.tsx` source filter to include new source name
- Monitor MongoDB ingestion rate; tune poll/reconnect if needed
- If Tiingo or IEX chosen: evaluate their market cap data for enriching `Article.market_cap` directly (may reduce dependency on `market-cap-cache.py`)

## Unresolved Questions

1. Is `discord-nuntio.py` production-ready or a skeleton? If complete, deploying it may satisfy this phase with zero new code.
2. Tiingo's WS endpoint (`wss://api.tiingo.com/iex`) is for IEX trade data — is there a separate news WS, or is it REST-only for news?
3. Should the new collector run as a separate Docker service or share the existing `collector` service? (Shared is simpler; separate is more resilient.)
