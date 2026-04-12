# Phase 2: Dashboard Page

## Context Links

- [Plan overview](plan.md)
- [Phase 1 — Setup](phase-01-setup-layout.md)
- [Existing articles_routes.py](../../src/api/routes/articles_routes.py)
- [Article model](../../src/core/models/article.py)
- [Article schemas](../../src/core/schemas/article_schema.py)

## Overview

- **Priority:** P1
- **Status:** pending
- **Effort:** 3.5h
- **Description:** Build main dashboard with KPI cards and 4 charts. Requires 4 new FastAPI aggregation endpoints.

## Key Insights

- Existing `/api/articles/stats` provides total_count, by_source, avg_sentiment, articles_today — reuse for KPIs
- New aggregation queries use SQLAlchemy `func.date_trunc` for time bucketing
- Tremor `Card` + `Metric` for KPIs; Recharts for custom chart components
- Dashboard page can be Server Component — fetch data SSR, pass to client chart components

## Requirements

### Functional

- 4 KPI cards: articles today, avg sentiment, most active ticker, source count
- Sentiment trend line chart (7 days, hourly buckets)
- Articles per hour bar chart (last 24h)
- Category distribution donut chart
- Top 10 tickers horizontal bar chart

### Non-functional

- Dashboard loads < 2s
- Charts responsive (resize with container)
- Graceful handling when no data available

## Architecture

### New FastAPI Endpoints

```
GET /api/articles/sentiment-trend?days=7
  Response: [{ timestamp: ISO, avg_sentiment: float, count: int }]
  Query: date_trunc('hour', published_at), avg(sentiment), count(*)
         WHERE published_at >= now() - interval '{days} days'
         GROUP BY hour ORDER BY hour

GET /api/articles/top-tickers?limit=10
  Response: [{ symbol: str, count: int, avg_sentiment: float }]
  Query: unnest(tickers), count(*), avg(sentiment)
         GROUP BY symbol ORDER BY count DESC LIMIT {limit}

GET /api/articles/by-hour?hours=24
  Response: [{ hour: ISO, count: int }]
  Query: date_trunc('hour', published_at), count(*)
         WHERE published_at >= now() - interval '{hours} hours'
         GROUP BY hour ORDER BY hour

GET /api/tickers/{symbol}/sentiment-history?days=7
  Response: [{ timestamp: ISO, sentiment: float, headline: str }]
  Query: SELECT published_at, sentiment, headline
         WHERE tickers @> ARRAY[{symbol}]
         AND published_at >= now() - interval '{days} days'
         ORDER BY published_at
```

### Dashboard Component Tree

```
app/page.tsx (Server Component)
├── fetch: getArticleStats(), getSentimentTrend(), getTopTickers(), getByHour(), getArticles(category grouping)
└── renders:
    ├── dashboard/kpi-cards.tsx (Server Component — static display)
    ├── charts/sentiment-trend-chart.tsx ("use client" — Recharts)
    ├── charts/articles-per-hour-chart.tsx ("use client" — Recharts)
    ├── charts/category-donut-chart.tsx ("use client" — Recharts)
    └── charts/top-tickers-chart.tsx ("use client" — Recharts)
```

## Related Code Files

### Modify

- `src/api/routes/articles_routes.py` — add 3 new endpoints
- `src/api/routes/tickers_routes.py` — add sentiment-history endpoint
- `src/core/schemas/article_schema.py` — add response schemas for new endpoints

### Create

- `src/webapp/app/page.tsx` — dashboard page
- `src/webapp/components/dashboard/kpi-cards.tsx`
- `src/webapp/components/charts/sentiment-trend-chart.tsx`
- `src/webapp/components/charts/articles-per-hour-chart.tsx`
- `src/webapp/components/charts/category-donut-chart.tsx`
- `src/webapp/components/charts/top-tickers-chart.tsx`
- `src/webapp/lib/api.ts` — add new endpoint functions

## Implementation Steps

### Backend (FastAPI)

1. **Add Pydantic response schemas** (`src/core/schemas/article_schema.py`)
   ```python
   class SentimentTrendPoint(BaseModel):
       timestamp: datetime
       avg_sentiment: float
       count: int

   class TopTicker(BaseModel):
       symbol: str
       count: int
       avg_sentiment: float | None = None

   class HourlyBucket(BaseModel):
       hour: datetime
       count: int

   class TickerSentimentPoint(BaseModel):
       timestamp: datetime
       sentiment: float | None
       headline: str
   ```

2. **Add sentiment-trend endpoint** (`articles_routes.py`)
   - `@router.get("/sentiment-trend")`
   - Query params: `days: int = Query(7, ge=1, le=30)`
   - SQL: `date_trunc('hour', published_at)` grouped, avg sentiment, count
   - Return `list[SentimentTrendPoint]`

3. **Add top-tickers endpoint** (`articles_routes.py`)
   - `@router.get("/top-tickers")`
   - Query params: `limit: int = Query(10, ge=1, le=50)`
   - SQL: `unnest(tickers)` as symbol, count, avg sentiment
   - Return `list[TopTicker]`

4. **Add by-hour endpoint** (`articles_routes.py`)
   - `@router.get("/by-hour")`
   - Query params: `hours: int = Query(24, ge=1, le=168)`
   - SQL: `date_trunc('hour', published_at)`, count
   - Return `list[HourlyBucket]`

5. **Add ticker sentiment-history** (`tickers_routes.py`)
   - `@router.get("/{symbol}/sentiment-history")`
   - Query params: `days: int = Query(7, ge=1, le=90)`
   - SQL: select published_at, sentiment, headline where tickers contains symbol
   - Return `list[TickerSentimentPoint]`

### Frontend (Next.js)

6. **Update API client** (`lib/api.ts`)
   - `getSentimentTrend(days)`, `getTopTickers(limit)`, `getByHour(hours)`
   - `getTickerSentimentHistory(symbol, days)`

7. **Create KPI cards** (`components/dashboard/kpi-cards.tsx`)
   - Uses shadcn Card component
   - Props: `stats: ArticleStats`, `topTicker: TopTicker | null`
   - 4 cards in responsive grid (2x2 on desktop, stack on mobile)
   - Cards: Articles Today (with delta badge), Avg Sentiment (color-coded), Most Active Ticker, Total Sources

8. **Create sentiment trend chart** (`components/charts/sentiment-trend-chart.tsx`)
   - `"use client"` — Recharts LineChart
   - Props: `data: SentimentTrendPoint[]`
   - X-axis: time (formatted), Y-axis: sentiment (-1 to 1)
   - Reference line at 0 (neutral)
   - Green above 0, red below (gradient area)
   - Tooltip with date, sentiment, article count

9. **Create articles per hour chart** (`components/charts/articles-per-hour-chart.tsx`)
   - `"use client"` — Recharts BarChart
   - Props: `data: HourlyBucket[]`
   - X-axis: hour (HH:mm), Y-axis: count
   - Blue bars, rounded corners

10. **Create category donut chart** (`components/charts/category-donut-chart.tsx`)
    - `"use client"` — Recharts PieChart (donut variant)
    - Props: `articles: Article[]` — compute category counts client-side from article list
    - Or: derive from existing `/api/articles` with category grouping
    - Center label: total count
    - Legend with category names + counts

11. **Create top tickers chart** (`components/charts/top-tickers-chart.tsx`)
    - `"use client"` — Recharts BarChart (horizontal/layout="vertical")
    - Props: `data: TopTicker[]`
    - Y-axis: ticker symbol, X-axis: count
    - Bar color based on avg_sentiment (green/red)
    - Click bar → navigate to /ticker/[symbol]

12. **Build dashboard page** (`app/page.tsx`)
    - Server Component — fetches all data with `Promise.all`
    - Responsive grid layout: KPIs top row, charts 2x2 below
    - Each chart wrapped in shadcn Card with title
    - Error boundary per section (partial failure OK)
    - Loading handled by Suspense boundaries

## Todo List

- [ ] Add 4 Pydantic response schemas
- [ ] Implement /api/articles/sentiment-trend endpoint
- [ ] Implement /api/articles/top-tickers endpoint
- [ ] Implement /api/articles/by-hour endpoint
- [ ] Implement /api/tickers/{symbol}/sentiment-history endpoint
- [ ] Update API client with new endpoint functions
- [ ] Build KPI cards component
- [ ] Build sentiment trend line chart
- [ ] Build articles per hour bar chart
- [ ] Build category donut chart
- [ ] Build top tickers horizontal bar chart
- [ ] Assemble dashboard page with grid layout
- [ ] Test with real data from running FastAPI

## Test Cases

### Backend
- `/sentiment-trend?days=7` returns hourly buckets sorted by timestamp
- `/sentiment-trend?days=0` returns 422 validation error
- `/top-tickers?limit=5` returns exactly 5 results (if enough data)
- `/top-tickers` with no data returns empty array
- `/by-hour?hours=24` returns up to 24 buckets
- `/{symbol}/sentiment-history` filters correctly by ticker symbol
- All endpoints return proper JSON with correct field types

### Frontend
- KPI cards render with correct values from API
- KPI cards show "N/A" when data missing
- Sentiment chart renders line with correct data points
- Charts resize on window resize
- Dashboard handles API errors gracefully (shows error cards)
- Page loads under 2s with SSR

## Verification Steps

1. Start FastAPI: `uv run uvicorn src.api.main:app --port 8200`
2. Test endpoints via curl:
   - `curl localhost:8200/api/articles/sentiment-trend?days=7`
   - `curl localhost:8200/api/articles/top-tickers?limit=10`
   - `curl localhost:8200/api/articles/by-hour?hours=24`
3. Start webapp: `cd src/webapp && npm run dev`
4. Open `localhost:8210` — dashboard renders with real data
5. Inspect network tab — all API calls succeed (200)
6. Resize browser — charts adapt

## Success Criteria

- [ ] All 4 new FastAPI endpoints return correct data
- [ ] KPI cards display real-time stats
- [ ] All 4 charts render with data from API
- [ ] Dashboard page loads < 2s
- [ ] No console errors
- [ ] Responsive layout works

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|-----------|
| `unnest(tickers)` perf on large dataset | Medium | Add LIMIT, index on tickers (GIN index exists) |
| Recharts bundle size | Low | Tree-shake, import only needed components |
| Empty data state | Medium | Show empty state placeholders in charts |

## Security Considerations

- Aggregation endpoints read-only, no auth needed
- No PII in article data
- SQL injection prevented by SQLAlchemy parameterized queries

## Next Steps

- Phase 3: News feed page with filters and auto-refresh
