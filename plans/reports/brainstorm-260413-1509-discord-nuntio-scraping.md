# Brainstorm: Discord NuntioBot Scraping + Small-Cap Filter

## Problem
Need to crawl stock news from NuntioBot Discord channels (Balanced server) and filter all data sources to small-cap < 100M market cap.

## Constraints
- Discord: read-only member, cannot invite bots
- Focus: small-cap < 100M
- VPS: available with IP, no domain
- FE: deploy to Vercel

## Approach: Dual-Layer (agreed)

### Layer 1 — Direct Source Crawling (primary, stable)
Research NuntioBot's upstream sources (GlobeNewsWire, PR Newswire, OTC Markets, etc.) and crawl directly. More reliable, no Discord dependency.

**Candidate sources:**
- GlobeNewsWire RSS (free, has tickers)
- PR Newswire RSS (free)
- OTC Markets (penny/micro-cap focus)
- Newsfilter.io API (aggregated, paid)

### Layer 2 — Discord Scraping (backup, immediate data)
Use `discord.py-self` library with a separate Discord account to read NuntioBot messages in real-time.

**Channels (full):** #m-mc, #250m-mc, #500m-mc, #marketcap, #select-news, #market-tweets, #halts, #earnings-cal, #nuntio-std, #mosquito

**Message format parsing:**
```
4.6 M 🇺🇸 RBNE : Robin Energy Ltd. Announces Availability of its...
→ market_cap: 4600000, country: US, ticker: RBNE, headline: "Robin Energy..."
```

**Risks:** Account ban (mitigate: secondary account, read-only, rate limited)

## Market Cap Filter (agreed: filter at collect)
- Skip articles with market_cap > 100M at collector level
- Finnhub: lookup ticker quote for market cap, cache in Redis (TTL 24h)
- MarketAux: parse from entities field
- NuntioBot: parse from message text (regex)
- Unknown market cap: keep (don't discard, may be small-cap)

## Deployment
- Backend: VPS with Docker Compose (IP:8200)
- Frontend: Vercel (NEXT_PUBLIC_API_URL=http://VPS_IP:8200)
- CORS: FastAPI allows Vercel domain via FRONTEND_URL env var

## Next Steps
1. Research NuntioBot upstream sources (Layer 1)
2. Build Discord listener collector (Layer 2)
3. Add market cap filter to existing Finnhub/MarketAux collectors
4. Add market cap cache (Redis, per ticker, TTL 24h)
5. Deploy backend to VPS
6. Deploy frontend to Vercel
