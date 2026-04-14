# Live Data Source Research — Results

## Finding: Free WebSocket NEWS Streaming Does Not Exist

All free-tier WebSocket APIs (Finnhub, Tiingo, Polygon, EODHD, FCS) provide **trade/quote** streaming only. News delivery is REST-only across all providers.

## Evaluation

| Source | News WS? | Free Tier | Verdict |
|--------|----------|-----------|---------|
| Finnhub | No (trades only) | Yes | Already integrated (REST poll) |
| Tiingo | No (IEX trades) | Yes | News REST only, no WS for news |
| Polygon.io | No (trades only) | Delayed free | Not useful for news |
| EODHD | No | Paid only | Skip |
| FMP | Possible (paid) | Limited free | $29/mo for WS |
| Benzinga | No | Paid only | Skip |
| Alpha Vantage | No WS at all | Yes (limited) | REST only, skip |
| IEX Cloud | SSE (trades) | Sandbox | News not via SSE |

## Recommendation

**No new collector needed.** Instead optimize existing sources:

1. **Discord NuntioBot** (already built) — truly live, deploy it
2. **TickerTick** — reduce poll from 2min → 1min (still within 10 req/min limit)
3. **Finnhub REST** — keep at 5min, reliable

## Action Items
- [x] Research complete — no viable free WS news source exists
- [ ] Reduce TickerTick poll interval to 1min
- [ ] Document Discord NuntioBot as primary live source in docs

Sources:
- https://finnhub.io/docs/api/websocket-news
- https://www.tiingo.com/products/news-api
- https://site.financialmodelingprep.com/datasets/websocket
