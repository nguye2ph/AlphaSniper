# Brainstorm: AlphaSniper Analytics Webapp
**Date:** 2026-04-12 | **Status:** Complete

---

## Problem Statement
Build a web-based analytics dashboard to visualize stock news data collected by AlphaSniper pipeline. Target user: stock news analyst making trading decisions on small-cap stocks. No authentication required.

## Decisions

| Decision | Choice |
|----------|--------|
| Framework | Next.js 15 (App Router) |
| UI | shadcn/ui + Tailwind CSS |
| Charts | Tremor (KPIs/cards) + Recharts (custom) |
| Data source | FastAPI backend (port 8200) |
| Port | 8210 |
| Auth | None |
| Location | `src/webapp/` |

---

## Pages & Features

### 1. Dashboard (`/`)
Main overview — analyst's "command center"

**KPI Cards (Tremor):**
- Total articles today / this week
- Average sentiment score (with trend arrow)
- Most active ticker (by article count)
- Source health (articles per source)

**Charts:**
- Sentiment trend line (last 7 days, hourly buckets)
- Articles per hour bar chart (last 24h)
- Category distribution donut chart
- Top 10 tickers by mention count (horizontal bar)

### 2. News Feed (`/feed`)
Real-time scrollable news feed — analyst's "radar"

- Filterable by: ticker, sentiment, category, source, date range
- Each card shows: headline, tickers (badges), sentiment (color-coded), source, time ago
- Click → expand to see summary + raw data + article URL
- Auto-refresh every 30s or manual refresh button
- Color coding: green (bullish), red (bearish), gray (neutral)

### 3. Ticker Detail (`/ticker/[symbol]`)
Deep dive into single stock — analyst's "sniper scope"

- Ticker header: symbol, name, exchange, market cap
- Sentiment timeline chart (articles over time, colored by sentiment)
- News list filtered to this ticker
- Category breakdown pie chart
- Source distribution

### 4. Sentiment Analysis (`/sentiment`)
Sentiment trends — analyst's "mood meter"

- Overall market sentiment gauge (-1 to +1)
- Sentiment heatmap: tickers × time (red/green grid)
- Bullish vs bearish article ratio over time
- Top movers: tickers with biggest sentiment shift

### 5. Sources (`/sources`)
Data source monitoring

- Source status cards (last collected, article count, health)
- Articles per source over time chart
- Source comparison table

---

## Architecture

```
Next.js App (port 8210)
  ├── app/
  │   ├── layout.tsx          # Root layout + nav sidebar
  │   ├── page.tsx            # Dashboard
  │   ├── feed/page.tsx       # News feed
  │   ├── ticker/[symbol]/page.tsx  # Ticker detail
  │   ├── sentiment/page.tsx  # Sentiment analysis
  │   └── sources/page.tsx    # Source monitoring
  ├── components/
  │   ├── ui/                 # shadcn components
  │   ├── charts/             # Recharts wrappers
  │   ├── dashboard/          # Dashboard-specific
  │   ├── feed/               # News feed components
  │   └── layout/             # Nav, sidebar, header
  ├── lib/
  │   ├── api.ts              # FastAPI client (fetch wrapper)
  │   └── utils.ts            # Formatters, colors, helpers
  └── types/
      └── index.ts            # TypeScript interfaces matching API
```

### Data Flow
```
FastAPI (8200) ←── fetch ←── Next.js Server Components (8210)
     ↓                              ↓
  PostgreSQL              Rendered HTML + client hydration
                                    ↓
                           User browser (charts interactive)
```

---

## API Requirements (from existing FastAPI)

Current endpoints sufficient for MVP:
- `GET /api/articles` — list with filters ✓
- `GET /api/articles/latest` — recent ✓
- `GET /api/articles/stats` — overview stats ✓
- `GET /api/tickers/{symbol}/news` — per-ticker ✓

**Need to add to FastAPI:**
- `GET /api/articles/sentiment-trend?days=7` — sentiment over time (hourly buckets)
- `GET /api/articles/top-tickers?limit=10` — most mentioned tickers
- `GET /api/articles/by-hour?hours=24` — articles per hour histogram
- `GET /api/tickers/{symbol}/sentiment-history` — per-ticker sentiment timeline

---

## Design Direction

- **Dark theme** — finance/trading aesthetic (dark bg, neon accents)
- **Color palette:** dark slate bg, green (#22c55e) bullish, red (#ef4444) bearish, blue (#3b82f6) neutral
- **Typography:** Inter or JetBrains Mono for data
- **Layout:** sidebar nav (collapsible) + main content area
- **Responsive:** desktop-first but mobile-friendly

---

## Implementation Phases

### Phase 1: Project Setup + Layout (Est. 2-3h)
- Next.js init in src/webapp/
- shadcn/ui + Tailwind + Tremor setup
- Root layout with sidebar navigation
- API client library (fetch wrapper for FastAPI)
- TypeScript types matching API responses

### Phase 2: Dashboard Page (Est. 3-4h)
- KPI cards (Tremor)
- Sentiment trend chart (Recharts)
- Articles per hour chart
- Category donut chart
- Top tickers bar chart
- Add new FastAPI endpoints for aggregations

### Phase 3: News Feed (Est. 2-3h)
- Filterable article list
- Sentiment color coding
- Expandable article cards
- Auto-refresh

### Phase 4: Ticker Detail (Est. 2h)
- Dynamic route /ticker/[symbol]
- Sentiment timeline
- Filtered news list
- Category breakdown

### Phase 5: Sentiment + Sources (Est. 2h)
- Sentiment analysis page
- Sources monitoring page

---

## Risk Assessment

| Risk | Mitigation |
|------|-----------|
| FastAPI missing aggregation endpoints | Add 4 new endpoints in Phase 2 |
| Chart performance with large datasets | Limit to 7-day window, paginate |
| CORS between Next.js (8210) and FastAPI (8200) | Add CORS middleware to FastAPI |
| Real-time updates | Polling every 30s, WebSocket later if needed |

---

## Success Metrics
- Dashboard loads < 2s
- All 5 pages render with real data
- Filters work correctly on feed page
- Charts update when new data collected
- Dark theme consistent across all pages
