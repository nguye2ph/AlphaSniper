---
title: "Phase 1: Market Cap UI Badges"
status: pending
effort: 1.5h
---

## Context Links
- Utils: `src/webapp/lib/utils.ts`
- ArticleCard: `src/webapp/components/feed/article-card.tsx`
- Dashboard: `src/webapp/app/page.tsx`
- Ticker detail: `src/webapp/app/ticker/[symbol]/page.tsx`
- Feed page: `src/webapp/app/feed/page.tsx`
- TS types: `src/webapp/types/index.ts` — `Article.market_cap: number | null` already present
- API routes: `src/api/routes/articles_routes.py`
- ArticleFilters type: `src/webapp/types/index.ts` — needs `market_cap_gte`/`market_cap_lte`

## Overview

Add visual market cap indicators across the frontend. `market_cap` already flows end-to-end (DB model → API schema → TS type). Work is purely display + one API param addition.

**Priority:** P1 — direct trading utility  
**Status:** pending

## Key Insights

- `Article.market_cap` is `number | null` in TS; show "N/A" on null, never throw
- Pattern mirrors `sentimentColor`/`formatSentiment` in `utils.ts` — follow exactly
- Feed page uses `<a href>` filter links (not router), so MC filters are query params on `/feed`
- `articles_routes.py` `list_articles` has no MC filter — needs 2 new Query params added
- Dashboard "Latest Articles" section is minimal (headline + sentiment letter) — add MC badge inline
- Ticker detail has a `StatCard` grid (2×4) — add MC as 5th stat

## Requirements

**Functional:**
- Format: null→"N/A", <1M→"$XXXk", <1B→"$X.XM", >=1B→"$X.XB"
- Color tiers: micro <10M→blue, small 10-100M→green, mid 100M-2B→yellow/amber, large >2B→zinc/gray
- ArticleCard collapsed view: MC badge after sentiment span, only when non-null
- Feed page: 3 new filter links (Micro-cap, Small-cap, Mid-cap) using `market_cap_tier` param or direct range params
- Ticker detail header: MC stat card
- Dashboard latest articles: MC inline tag

**Non-functional:**
- No new components — use existing `Badge` from shadcn/ui + inline spans
- Keep `utils.ts` under 80 lines after additions (currently 52 lines, adding ~18)

## Architecture

```
utils.ts
  formatMarketCap(v: number | null) → "$4.6M" | "N/A"
  marketCapColor(v: number | null) → tailwind text color class
  marketCapTier(v: number | null) → "micro"|"small"|"mid"|"large"|null

article-card.tsx
  collapsed row: [...ticker badges] [sentiment] [MC badge] [source] [time]

feed/page.tsx
  searchParams: add mcap_tier (micro|small|mid|large)
  FilterLinks: +Micro-cap, +Small-cap, +Mid-cap
  getArticles() call: map mcap_tier → market_cap_gte/market_cap_lte

types/index.ts
  ArticleFilters: + market_cap_gte?: number, market_cap_lte?: number

articles_routes.py
  list_articles: + market_cap_gte/market_cap_lte Query params → filter Article.market_cap
```

## Related Code Files

**Modify:**
- `src/webapp/lib/utils.ts` — add 3 MC helpers
- `src/webapp/components/feed/article-card.tsx` — add MC badge in collapsed row
- `src/webapp/app/feed/page.tsx` — add MC filter links + pass params to getArticles
- `src/webapp/app/ticker/[symbol]/page.tsx` — add MC StatCard
- `src/webapp/app/page.tsx` — add MC tag in latest articles list
- `src/webapp/types/index.ts` — extend ArticleFilters
- `src/api/routes/articles_routes.py` — add market_cap_gte/market_cap_lte params

## Implementation Steps

1. **`utils.ts`** — add after `sentimentChartColor`:
   ```ts
   export function formatMarketCap(v: number | null): string
   export function marketCapColor(v: number | null): string  // tailwind text-* class
   export function marketCapTier(v: number | null): "micro"|"small"|"mid"|"large"|null
   ```
   Tier thresholds: micro <10M, small 10-100M, mid 100-2000M, large ≥2000M

2. **`types/index.ts`** — add to `ArticleFilters`:
   ```ts
   market_cap_gte?: number;
   market_cap_lte?: number;
   ```

3. **`articles_routes.py`** — add two Query params to `list_articles`:
   ```python
   market_cap_gte: float | None = Query(None, ge=0)
   market_cap_lte: float | None = Query(None, ge=0)
   ```
   Add corresponding `.where(Article.market_cap >= market_cap_gte)` filters

4. **`article-card.tsx`** — in collapsed row after sentiment span, add:
   ```tsx
   {article.market_cap !== null && (
     <span className={cn("text-xs font-mono", marketCapColor(article.market_cap))}>
       [{formatMarketCap(article.market_cap)}]
     </span>
   )}
   ```
   Import `formatMarketCap`, `marketCapColor` from `@/lib/utils`

5. **`feed/page.tsx`** — read `mcap_tier` from searchParams, map to range constants, add 3 FilterLink rows, pass ranges to `getArticles()`

6. **`ticker/[symbol]/page.tsx`** — derive `market_cap` from first article with non-null value, add `<StatCard label="Market Cap" value={formatMarketCap(marketCap)} />` to stats grid

7. **`app/page.tsx`** — in latest articles list, after sentiment letter span, add MC inline (only if non-null)

## Todo List

- [ ] Add `formatMarketCap`, `marketCapColor`, `marketCapTier` to `utils.ts`
- [ ] Extend `ArticleFilters` in `types/index.ts`
- [ ] Add `market_cap_gte`/`market_cap_lte` params to `articles_routes.py`
- [ ] Add MC badge to `article-card.tsx` collapsed row
- [ ] Add MC filter links to `feed/page.tsx`
- [ ] Add MC StatCard to `ticker/[symbol]/page.tsx`
- [ ] Add MC inline tag to `app/page.tsx` latest articles section

## Success Criteria

- [ ] MC badge renders with correct tier color on ArticleCard
- [ ] null market_cap → badge hidden (not "N/A" shown)
- [ ] Feed MC filter links correctly query API with price ranges
- [ ] Ticker detail shows market cap stat
- [ ] No TypeScript compile errors (`tsc --noEmit`)
- [ ] No new components created — all reuse existing Badge/span

## Risk Assessment

- `Article.market_cap` may be null for most articles if market-cap-cache hasn't populated — UI handles gracefully via null guards
- Tier cutoffs (10M/100M/2B) are opinionated; document in utils comment for easy tuning

## Security Considerations

- MC filter params are float — FastAPI Query validation (`ge=0`) prevents negative/malformed values

## Next Steps

- After Phase 1: proceed to Phase 2 live source research
- Future: add market cap to `ArticleStats` aggregation endpoint
