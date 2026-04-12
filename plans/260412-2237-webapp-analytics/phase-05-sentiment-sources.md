# Phase 5: Sentiment Analysis + Sources Pages

## Context Links

- [Plan overview](plan.md)
- [Phase 2 — Dashboard](phase-02-dashboard.md) (reuse charts)
- [Existing sources_routes.py](../../src/api/routes/sources_routes.py)
- [Existing articles_routes.py](../../src/api/routes/articles_routes.py)

## Overview

- **Priority:** P2
- **Status:** pending
- **Effort:** 2h
- **Description:** Two pages — sentiment analysis (/sentiment) for market mood tracking, and sources (/sources) for data pipeline monitoring.

## Key Insights

- Most data derivable from existing endpoints + Phase 2 aggregation endpoints
- Sentiment page: combine `/articles/stats`, `/articles/sentiment-trend`, `/articles/top-tickers`
- Sources page: use `/api/sources` + `/api/articles/stats` (by_source field)
- Minimal new backend work — 1 optional endpoint for source article counts over time

## Requirements

### Functional — Sentiment Page (`/sentiment`)

- Market sentiment gauge: current avg sentiment visualized as gauge (-1 to +1)
- Bullish vs bearish ratio over time: stacked area chart
- Top movers: tickers with biggest sentiment shift (compare last 24h vs prior 24h)
- Sentiment distribution: histogram of sentiment scores

### Functional — Sources Page (`/sources`)

- Source status cards: name, last collected, article count, active/inactive status
- Articles per source chart: bar chart or stacked area over time
- Source comparison table: sortable table with metrics

### Non-functional

- Both pages load < 2s
- Source health visible at a glance (green=active, red=inactive)

## Architecture

### Sentiment Page

```
app/sentiment/page.tsx (Server Component)
├── Sentiment gauge (custom component or Tremor Tracker)
├── charts/sentiment-distribution-chart.tsx ("use client")
├── charts/sentiment-trend-chart.tsx (reuse from Phase 2)
└── Top movers list (server-rendered table/cards)
```

### Sources Page

```
app/sources/page.tsx (Server Component)
├── Source status cards (server-rendered)
├── charts/source-articles-chart.tsx ("use client")
└── Source comparison table (server-rendered, shadcn Table)
```

### Optional New Backend Endpoint

```
GET /api/articles/by-source-over-time?days=7
Response: [{ source: str, date: ISO, count: int }]
Query: date_trunc('day', published_at), source, count(*)
       WHERE published_at >= now() - interval '{days} days'
       GROUP BY date, source ORDER BY date
```

## Related Code Files

### Modify (optional)

- `src/api/routes/articles_routes.py` — add by-source-over-time endpoint
- `src/core/schemas/article_schema.py` — add response schema if new endpoint added

### Create

- `src/webapp/app/sentiment/page.tsx`
- `src/webapp/app/sources/page.tsx`
- `src/webapp/components/charts/sentiment-distribution-chart.tsx`
- `src/webapp/components/charts/source-articles-chart.tsx`

### Reuse

- `src/webapp/components/charts/sentiment-trend-chart.tsx` (from Phase 2)

## Implementation Steps

### Sentiment Page

1. **Create sentiment page** (`app/sentiment/page.tsx`)
   - Server Component — parallel fetch:
     - `getArticleStats()` — for avg sentiment
     - `getSentimentTrend(7)` — for trend chart
     - `getTopTickers(20)` — for top movers calculation
     - `getArticles({ limit: 200 })` — for distribution histogram

2. **Market sentiment gauge**
   - Visual gauge showing current avg sentiment
   - Scale: -1.0 (bearish) to +1.0 (bullish), 0 = neutral
   - Implementation: CSS-based semicircle gauge or Recharts radial bar
   - Color transitions: red → gray → green
   - Large center text: sentiment value + label

3. **Sentiment distribution histogram** (`components/charts/sentiment-distribution-chart.tsx`)
   - `"use client"` — Recharts BarChart
   - Bucket sentiment scores into ranges: [-1,-0.5], [-0.5,0], [0,0.5], [0.5,1]
   - Or finer: 10 buckets of 0.2 width
   - Color bars by sentiment range (red/gray/green)

4. **Bullish vs bearish ratio**
   - Reuse sentiment-trend-chart with modification
   - Or: simple stat cards showing count of bullish vs bearish articles (today, this week)
   - Percentage bar: "65% Bullish | 35% Bearish"

5. **Top movers**
   - Compare each ticker's avg sentiment (last 24h) vs (prior 24h)
   - Sort by absolute change, show top 5 up + top 5 down
   - Display as cards: symbol, sentiment change (arrow + value), current sentiment
   - Derive from `getTopTickers()` data or fetch articles for two periods

### Sources Page

6. **Create sources page** (`app/sources/page.tsx`)
   - Server Component — fetch:
     - `getSources()` — source list with status
     - `getArticleStats()` — by_source counts

7. **Source status cards**
   - Grid of cards (one per source)
   - Each card: source name, status badge (green "Active" / red "Inactive"), article count, last collection time
   - Use shadcn Card + Badge

8. **Articles per source chart** (`components/charts/source-articles-chart.tsx`)
   - `"use client"` — Recharts BarChart
   - One bar per source, colored uniquely
   - Show total article count per source
   - Optional: stacked by day if by-source-over-time endpoint exists

9. **Source comparison table**
   - shadcn Table component (server-rendered)
   - Columns: Source, Status, Article Count, Avg Sentiment (per source), Last Collection
   - Sortable by clicking column headers (client enhancement if needed)
   - Derive avg sentiment per source from article data

## Todo List

### Sentiment Page
- [ ] Create sentiment page with parallel data fetching
- [ ] Build market sentiment gauge
- [ ] Build sentiment distribution histogram
- [ ] Build bullish vs bearish ratio display
- [ ] Build top movers section (biggest sentiment shifts)

### Sources Page
- [ ] Create sources page with data fetching
- [ ] Build source status cards
- [ ] Build articles per source chart
- [ ] Build source comparison table
- [ ] (Optional) Add by-source-over-time backend endpoint

## Test Cases

### Sentiment Page
- Gauge shows correct avg sentiment value
- Gauge color matches sentiment (green for positive, red for negative)
- Distribution histogram shows correct bucket counts
- Top movers shows tickers with biggest sentiment changes
- Page handles zero articles gracefully

### Sources Page
- All configured sources appear as cards
- Active sources show green badge, inactive show red
- Article counts match actual data
- Comparison table renders with correct metrics
- Page handles no sources gracefully

## Verification Steps

1. Navigate to `/sentiment` — gauge and charts render
2. Verify gauge value matches `/api/articles/stats` avg_sentiment
3. Navigate to `/sources` — source cards render
4. Verify source cards match `/api/sources` data
5. Verify article counts match `/api/articles/stats` by_source
6. Check both pages responsive on mobile

## Success Criteria

- [ ] Sentiment page renders gauge, distribution, and trend
- [ ] Top movers section shows meaningful sentiment shifts
- [ ] Sources page shows all sources with status
- [ ] Article counts per source are accurate
- [ ] Both pages load < 2s
- [ ] Consistent dark theme styling

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Top movers calculation complex | Medium | Simplify: show top tickers by current sentiment instead of shift |
| Source status stale | Low | Source model has last_collection_at, show relative time |
| Not enough data for meaningful sentiment analysis | Low | Show "Insufficient data" message, requires min 10 articles |

## Security Considerations

- Read-only pages, no user input
- No sensitive data displayed

## Next Steps

- All 5 phases complete — integration testing across pages
- Future: WebSocket for real-time updates, authentication, deployment
