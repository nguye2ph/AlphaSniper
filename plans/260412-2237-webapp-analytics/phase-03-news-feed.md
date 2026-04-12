# Phase 3: News Feed

## Context Links

- [Plan overview](plan.md)
- [Phase 2 — Dashboard](phase-02-dashboard.md)
- [Existing list_articles endpoint](../../src/api/routes/articles_routes.py)
- [ArticleListParams schema](../../src/core/schemas/article_schema.py)

## Overview

- **Priority:** P1
- **Status:** pending
- **Effort:** 2.5h
- **Description:** Filterable, auto-refreshing news feed with sentiment color-coding and expandable article cards.

## Key Insights

- Existing `GET /api/articles` already supports all needed filters (ticker, source, sentiment_gte/lte, category, from_date, to_date, limit, offset)
- No new backend endpoints needed — reuse existing
- Auto-refresh = polling every 30s via `setInterval` + React Query or `useEffect`
- Expandable cards: click to reveal summary + raw data + link

## Requirements

### Functional

- Filter bar: ticker search, sentiment range, category dropdown, source dropdown, date range
- Article cards with: headline, tickers (badges), sentiment (color dot + label), source, time ago
- Click card → expand inline to show: summary, article URL, raw data toggle
- Auto-refresh every 30s (with manual refresh button + indicator)
- Pagination (load more button or infinite scroll)

### Non-functional

- Feed renders < 1s after filter change
- Smooth expand/collapse animation
- Filters persist in URL search params (shareable links)

## Architecture

```
app/feed/page.tsx (Server Component — initial fetch)
└── feed/feed-container.tsx ("use client" — manages state)
    ├── feed/feed-filters.tsx — filter controls
    ├── feed/article-card.tsx — individual article card
    └── ui/button.tsx — load more / refresh
```

### State Management

- URL search params as source of truth (via `useSearchParams` + `useRouter`)
- Client-side polling with `setInterval` (refetch current filter state)
- No global state library needed — component-level useState sufficient

## Related Code Files

### Modify

- `src/webapp/lib/api.ts` — add `getArticles(params)` with full filter support

### Create

- `src/webapp/app/feed/page.tsx` — feed page (Server Component shell)
- `src/webapp/components/feed/feed-container.tsx` — client container with state
- `src/webapp/components/feed/feed-filters.tsx` — filter bar
- `src/webapp/components/feed/article-card.tsx` — expandable article card

## Implementation Steps

1. **Update API client** (`lib/api.ts`)
   - `getArticles(params: ArticleFilterParams)` — maps filter state to query params
   - Type `ArticleFilterParams`: ticker?, source?, sentiment_gte?, sentiment_lte?, category?, from_date?, to_date?, limit?, offset?

2. **Create feed page** (`app/feed/page.tsx`)
   - Server Component — minimal shell
   - Passes initial data fetch to client container via props
   - `<Suspense>` wrapper for loading state

3. **Create feed container** (`components/feed/feed-container.tsx`)
   - `"use client"`
   - State: filters, articles[], loading, hasMore, autoRefresh
   - `useSearchParams()` to read/write filters from URL
   - `useEffect` for 30s polling interval (toggleable)
   - Fetch on filter change (debounced 300ms for text inputs)
   - "Load more" increments offset

4. **Create feed filters** (`components/feed/feed-filters.tsx`)
   - `"use client"`
   - Props: current filter values, onChange callbacks
   - Components:
     - Ticker: shadcn Input with search icon
     - Sentiment: dual range (min/max) or preset buttons (Bullish/Neutral/Bearish)
     - Category: shadcn Select dropdown (earnings, insider, merger, etc.)
     - Source: shadcn Select dropdown (finnhub, marketaux, sec_edgar)
     - Date range: shadcn date picker or simple from/to inputs
   - "Clear filters" button
   - Responsive: horizontal on desktop, stack on mobile

5. **Create article card** (`components/feed/article-card.tsx`)
   - `"use client"` (uses useState for expand)
   - Props: `article: Article`
   - Collapsed state:
     - Sentiment dot (colored circle: green/red/gray) + label
     - Headline (truncated if long)
     - Ticker badges (shadcn Badge, click → navigate to /ticker/[symbol])
     - Source name + relative time ("2h ago")
   - Expanded state (click to toggle):
     - Summary text
     - Article URL (external link, opens new tab)
     - Sentiment score (numeric)
     - Category badge
     - "View raw data" collapsible (JSON viewer)
   - Subtle expand/collapse animation via CSS transition (max-height)

6. **Auto-refresh indicator**
   - Small pulse dot + "Auto-refreshing" text in top-right of feed
   - Toggle button to pause/resume
   - Show "Last updated: X seconds ago" timestamp

7. **Pagination**
   - "Load more" button at bottom of feed
   - Appends to existing articles (not replace)
   - Disable when no more results (returned < limit)
   - Show total count from API if available

## Todo List

- [ ] Update API client with typed filter params
- [ ] Create feed page shell (Server Component)
- [ ] Build feed container with state management
- [ ] Build filter bar with all filter controls
- [ ] Build expandable article card
- [ ] Implement auto-refresh polling (30s)
- [ ] Implement pagination (load more)
- [ ] Sync filters with URL search params
- [ ] Test with real data

## Test Cases

- Default feed loads latest articles sorted by date
- Filtering by ticker shows only articles containing that ticker
- Filtering by sentiment (bullish) shows only sentiment > 0.3
- Clearing filters resets to default view
- Auto-refresh fetches new articles every 30s
- Pausing auto-refresh stops polling
- "Load more" appends articles, doesn't duplicate
- Expanding card shows summary and URL
- Ticker badges navigate to /ticker/[symbol]
- URL params persist on page reload
- Empty filter results show "No articles found" message

## Verification Steps

1. Navigate to `/feed` — articles load
2. Apply ticker filter "AAPL" — only AAPL articles shown
3. Apply sentiment filter "bearish" — red-colored articles only
4. Wait 30s — feed updates (check network tab)
5. Click article → expands with summary
6. Click ticker badge → navigates to ticker detail
7. Reload page — filters preserved in URL

## Success Criteria

- [ ] All filters work correctly
- [ ] Auto-refresh polls every 30s
- [ ] Pagination loads more articles
- [ ] Article cards expand/collapse smoothly
- [ ] Filters persist in URL search params
- [ ] Sentiment color-coding: green=bullish, red=bearish, gray=neutral

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Auto-refresh causes UI jank | Medium | Prepend new articles only, don't re-render entire list |
| Too many filter API calls | Low | Debounce text inputs 300ms, dropdowns fire immediately |
| Large article list perf | Low | Limit to 50 per page, virtualize if needed later |

## Security Considerations

- External article URLs open in new tab with `rel="noopener noreferrer"`
- No user input stored — filters are read-only queries

## Next Steps

- Phase 4: Ticker detail page using existing + Phase 2 endpoints
