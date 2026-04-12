# Phase 4: Ticker Detail

## Context Links

- [Plan overview](plan.md)
- [Phase 2 — Dashboard](phase-02-dashboard.md) (sentiment-history endpoint)
- [Phase 3 — Feed](phase-03-news-feed.md) (article card reuse)
- [Existing tickers_routes.py](../../src/api/routes/tickers_routes.py)

## Overview

- **Priority:** P2
- **Status:** pending
- **Effort:** 2h
- **Description:** Dynamic route `/ticker/[symbol]` showing ticker-specific sentiment timeline, news feed, and category breakdown.

## Key Insights

- Reuse article-card component from Phase 3
- Reuse sentiment-timeline-chart pattern from Phase 2
- Existing endpoints: `GET /api/tickers/{symbol}/news`, `GET /api/tickers` (for metadata)
- Phase 2 endpoint: `GET /api/tickers/{symbol}/sentiment-history` — already built
- No new backend endpoints needed

## Requirements

### Functional

- Ticker header: symbol, name, exchange, market cap (from Ticker data)
- Sentiment timeline chart: scatter/line of article sentiments over time
- News list: filtered articles for this ticker (reuse article-card)
- Category breakdown: pie chart of article categories

### Non-functional

- Page loads < 1.5s
- Handle unknown ticker gracefully (404 message)

## Architecture

```
app/ticker/[symbol]/page.tsx (Server Component)
├── ticker-header.tsx — symbol, name, metadata
├── charts/sentiment-timeline-chart.tsx ("use client" — Recharts)
├── charts/category-donut-chart.tsx (reuse from Phase 2)
└── feed/article-card.tsx (reuse from Phase 3)
```

## Related Code Files

### Modify

- `src/webapp/lib/api.ts` — ensure `getTickerNews()` and `getTickerSentimentHistory()` are available

### Create

- `src/webapp/app/ticker/[symbol]/page.tsx`
- `src/webapp/components/charts/sentiment-timeline-chart.tsx`

### Reuse

- `src/webapp/components/feed/article-card.tsx` (from Phase 3)
- `src/webapp/components/charts/category-donut-chart.tsx` (from Phase 2)

## Implementation Steps

1. **Create sentiment timeline chart** (`components/charts/sentiment-timeline-chart.tsx`)
   - `"use client"` — Recharts ScatterChart or ComposedChart
   - Props: `data: TickerSentimentPoint[]`
   - X-axis: time, Y-axis: sentiment (-1 to 1)
   - Each dot = one article, colored by sentiment (green/red/gray)
   - Tooltip: headline, sentiment value, date
   - Reference line at 0

2. **Create ticker detail page** (`app/ticker/[symbol]/page.tsx`)
   - Server Component with async params (Next.js 15 pattern)
   - `const { symbol } = await params`
   - Parallel fetch with `Promise.all`:
     - `getTickers()` → find matching ticker for metadata
     - `getTickerNews(symbol, 50)` → articles
     - `getTickerSentimentHistory(symbol, 30)` → timeline data
   - Handle ticker not found: show not-found message

3. **Ticker header section**
   - Large symbol text (e.g., "AAPL")
   - Subtitle: company name, exchange
   - Market cap badge (formatted: "$2.8T")
   - Overall sentiment indicator (avg from articles)

4. **Layout**
   - Header row: ticker metadata
   - Two-column below:
     - Left (2/3): sentiment timeline chart + news list
     - Right (1/3): category breakdown pie chart + stats
   - News list: map articles through article-card component
   - Limit news to 20, "View all" link to /feed?ticker=SYMBOL

5. **Category breakdown**
   - Reuse category-donut-chart from Phase 2
   - Compute category counts from ticker's articles
   - Pass as props

## Todo List

- [ ] Create sentiment timeline chart component
- [ ] Create ticker detail page with async params
- [ ] Build ticker header with metadata
- [ ] Wire up parallel data fetching
- [ ] Reuse article-card for news list
- [ ] Reuse category-donut for breakdown
- [ ] Handle unknown ticker (not-found state)
- [ ] Add "View all news" link to feed page

## Test Cases

- `/ticker/AAPL` renders with AAPL data
- Sentiment timeline shows correct data points
- Article cards render for this ticker only
- Category pie chart shows correct distribution
- `/ticker/NONEXISTENT` shows "Ticker not found" message
- Clicking article card expands with details
- "View all" links to `/feed?ticker=AAPL`

## Verification Steps

1. Navigate to `/ticker/AAPL` (or any ticker with data)
2. Verify header shows correct ticker info
3. Verify sentiment chart renders timeline
4. Verify news list shows only AAPL articles
5. Verify category chart shows categories
6. Test with ticker that has no articles — empty states render

## Success Criteria

- [ ] Dynamic route resolves correctly
- [ ] Ticker metadata displays in header
- [ ] Sentiment timeline chart renders
- [ ] News list shows filtered articles
- [ ] Category breakdown shows distribution
- [ ] Unknown ticker shows friendly error

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Ticker metadata missing (no Ticker record) | Low | Fallback to symbol-only header, fetch what's available |
| Large number of articles for popular ticker | Medium | Limit to 20, paginate or link to feed |

## Security Considerations

- Symbol param sanitized (uppercase, max 10 chars)
- No user-generated content displayed unsanitized

## Next Steps

- Phase 5: Sentiment analysis + Sources monitoring pages
