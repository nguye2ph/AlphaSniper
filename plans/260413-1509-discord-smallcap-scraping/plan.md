---
title: "Discord NuntioBot Scraping + Small-Cap Sources"
description: "Add Discord scraper, TickerTick API, RSS news sources, and market cap <100M filter"
status: pending
priority: P1
effort: 8h
branch: main
tags: [discord, scraping, small-cap, filter, collectors]
created: 2026-04-13
---

# Discord NuntioBot Scraping + Small-Cap Sources

## Objective
Add market cap filtering (< 100M), TickerTick API collector, Discord NuntioBot passive listener, and RSS news sources.

## Phases

| # | Phase | Effort | Status | Deps |
|---|-------|--------|--------|------|
| 1 | [Market Cap Filter](./phase-01-market-cap-filter.md) | 2h | pending | none |
| 2 | [TickerTick API Collector](./phase-02-tickertick-collector.md) | 1.5h | pending | Phase 1 |
| 3 | [Discord NuntioBot Collector](./phase-03-discord-nuntio-collector.md) | 3h | pending | Phase 1 |
| ~~4~~ | ~~RSS News Collectors~~ | ~~2h~~ | **skipped** | — |
| 4 | [Deploy Config](./phase-04-deploy-config.md) | 1.5h | pending | 1-3 |

## Key Dependencies

- Phase 1 must complete first (market cap cache used by all collectors)
- Phase 2 and 3 can run in parallel after Phase 1
- Phase 4 depends on 1-3

## New Files

```
src/collectors/
  market-cap-cache.py       # Redis-based market cap lookup
  tickertick-rest.py        # TickerTick API collector (FREE, 10 req/min)
  discord-nuntio.py         # Discord selfbot collector
src/parsers/
  nuntio-message-parser.py  # NuntioBot message regex parser
```

## Data Sources Summary

| Source | Type | Cost | Rate Limit | Small-cap? |
|--------|------|------|-----------|-----------|
| TickerTick API | REST poll | **Free** | 10 req/min | Query by ticker |
| Finnhub (existing) | WS + REST | Free | 60/min | All stocks |
| MarketAux (existing) | REST | Free | 100/day | All stocks |
| NuntioBot Discord | Selfbot | Free | Passive | MC in message |
| GlobeNewsWire | RSS | Free | Undocumented | High density |
| BusinessWire | RSS | Free | Undocumented | Moderate |
| Newsfilter.io | REST+WS | Freemium | Unknown | 50M+ articles |

## Research
- [Discord Scraping Research](./research/researcher-discord-scraping.md)
- [News Sources Research](./research/researcher-news-sources.md)
- [Brainstorm](../reports/brainstorm-260413-1509-discord-nuntio-scraping.md)
- [TickerTick API](https://github.com/hczhu/TickerTick-API) — free, query language, 10K US stocks
- [Newsfilter.io Python SDK](https://github.com/FinancialNewsAPI/financial-news-api-python) — optional upgrade path

## Validation Log

### Session 1 — 2026-04-13
**Trigger:** Initial plan validation before implementation
**Questions asked:** 6

#### Questions & Answers

1. **[Architecture]** Finnhub quote API field cho market cap là gì? Plan giả định `mc` nhưng có thể là `marketCapitalization`.
   - Options: Chưa biết, cần test live | Dùng /stock/profile2 thay thế
   - **Answer:** Chưa biết, cần test live
   - **Rationale:** Must verify Finnhub /quote response field name before implementing MarketCapCache. Test during Phase 1 implementation.

2. **[Scope]** TickerTick query strategy — query theo watchlist tickers hay query broad?
   - Options: Watchlist only | Broad: all small-cap sources | Cả hai
   - **Answer:** Cả hai
   - **Rationale:** 2 queries per cycle: watchlist tickers OR + broad small-cap source filter. 2 req per 2-min cycle = 1 req/min, well within 10 req/min limit.

3. **[Risk]** Discord selfbot — đã có throwaway Discord account + token chưa?
   - Options: Có rồi | Chưa, sẽ tạo | Skip Discord phase
   - **Answer:** Chưa, sẽ tạo
   - **Rationale:** Discord phase not blocked but user needs to create account + get token before testing. Document token extraction steps in deploy guide.

4. **[Architecture]** VPS deploy — dùng IP:8200 trực tiếp hay giữ Traefik?
   - Options: IP:8200 trực tiếp | Giữ Traefik
   - **Answer:** Giữ Traefik
   - **Rationale:** Keep Traefik in compose for future domain setup. For IP-only, Traefik runs but without TLS cert. API still accessible via IP:8200.

5. **[Assumptions]** Watchlist tickers hiện tại chỉ có large-cap (AAPL, TSLA...) — đều > 100M, sẽ bị filter hết.
   - Options: Giữ large-cap + thêm small-cap | Thay hết bằng small-cap | Giữ nguyên, filter chỉ cho sources mới
   - **Answer:** Giữ large-cap + thêm small-cap
   - **Rationale:** Keep existing tickers for general market awareness. Add small-cap tickers. Market cap filter should NOT apply to watchlist tickers from existing collectors (Finnhub/MarketAux) — only for new sources.

6. **[Scope]** RSS collectors — GlobeNewsWire feed URLs cần verify. Nếu không hoạt động thì sao?
   - Options: Skip RSS, focus TickerTick + Discord | Vẫn implement RSS | Chỉ GlobeNewsWire
   - **Answer:** Skip RSS, focus TickerTick + Discord
   - **Rationale:** TickerTick already aggregates SEC, GNW, and thousands of sources — RSS is redundant. Reduces scope from 5 to 4 phases, saving 2h effort.

#### Confirmed Decisions
- **Finnhub mc field**: Test live during Phase 1 impl, fallback to /stock/profile2 if /quote lacks mc
- **TickerTick**: Dual query (watchlist + broad), 2 req per 2-min cycle
- **Discord**: User will create throwaway account; phase not blocked
- **Deploy**: Keep Traefik, expose port 8200 for IP-only access
- **Watchlist**: Keep large-cap + add small-cap. Mc filter only for NEW sources (TickerTick, Discord)
- **RSS**: Skipped — TickerTick covers same sources. Add RSS later if needed

#### Action Items
- [x] Remove Phase 4 (RSS) from plan, renumber Phase 5 → Phase 4
- [ ] Phase 1: Test Finnhub /quote response to confirm mc field name
- [ ] Phase 1: Market cap filter should NOT apply to existing Finnhub/MarketAux collectors
- [ ] Phase 2: TickerTick uses dual query strategy (watchlist OR + broad small-cap)
- [ ] Config: Add small-cap tickers to FINNHUB_SYMBOLS default list

#### Impact on Phases
- Phase 1: Market cap filter only applies to NEW sources (TickerTick, Discord), NOT existing Finnhub/MarketAux
- Phase 2: TickerTick uses 2 queries per cycle instead of 1
- Phase 4 (RSS): REMOVED — skipped per validation
- Phase 5 → Phase 4: Deploy config renumbered
