# Phase 1: Project Setup + Layout

## Context Links

- [Plan overview](plan.md)
- [System Architecture](../../docs/system-architecture.md)
- [Code Standards](../../docs/code-standards.md)
- [FastAPI main.py](../../src/api/main.py)

## Overview

- **Priority:** P1 (blocker for all other phases)
- **Status:** pending
- **Effort:** 2.5h
- **Description:** Initialize Next.js 15 app in `src/webapp/`, configure dark theme, build root layout with sidebar navigation, create API client library and TypeScript types, add CORS to FastAPI.

## Key Insights

- FastAPI runs port 8200, webapp port 8210 — CORS required
- Existing Pydantic schemas (`ArticleResponse`, `ArticleStats`, `TickerResponse`, `SourceResponse`) define API contract — TypeScript types must mirror these exactly
- Dark theme aligns with finance/trading aesthetic (slate bg, green bullish, red bearish)
- Server Components fetch data SSR; Client Components only for interactivity

## Requirements

### Functional

- Next.js 15 App Router project in `src/webapp/`
- Collapsible sidebar with nav links: Dashboard, Feed, Ticker, Sentiment, Sources
- API client (`lib/api.ts`) wrapping fetch for FastAPI endpoints
- TypeScript types matching all existing API response schemas
- CORS middleware on FastAPI allowing `localhost:8210`

### Non-functional

- Port 8210 via next.config.ts
- Dark mode by default (no light mode toggle needed)
- Fast cold start < 3s
- File size < 200 lines per file

## Architecture

```
src/webapp/
├── package.json
├── next.config.ts           # port 8210, API rewrites optional
├── tailwind.config.ts       # dark theme colors
├── tsconfig.json
├── app/
│   ├── globals.css          # Tailwind imports + dark theme vars
│   ├── layout.tsx           # Root layout: sidebar + main content
│   └── page.tsx             # Placeholder (Phase 2)
├── components/
│   ├── ui/                  # shadcn/ui components (Button, Card, etc.)
│   └── layout/
│       ├── sidebar.tsx      # Collapsible sidebar nav
│       └── header.tsx       # Top bar with page title
├── lib/
│   ├── api.ts               # Fetch wrapper for FastAPI
│   └── utils.ts             # cn(), sentiment color helpers
└── types/
    └── index.ts             # Article, Ticker, Source, Stats types
```

## Related Code Files

### Modify

- `src/api/main.py` — add CORSMiddleware

### Create

- `src/webapp/` — entire directory (all files above)

## Implementation Steps

1. **Init Next.js project**
   ```bash
   cd src && npx create-next-app@latest webapp --typescript --tailwind --eslint --app --src-dir=false --import-alias="@/*"
   ```

2. **Install dependencies**
   ```bash
   cd src/webapp && npm install @tremor/react recharts
   npx shadcn@latest init  # select dark theme, slate palette
   npx shadcn@latest add button card badge separator sheet scroll-area input select
   ```

3. **Configure next.config.ts**
   - Set dev server port to 8210 in `package.json` scripts: `"dev": "next dev -p 8210"`
   - No API rewrites — direct fetch to `http://localhost:8200`

4. **Configure tailwind.config.ts**
   - Extend colors: `bullish: '#22c55e'`, `bearish: '#ef4444'`, `neutral-accent: '#3b82f6'`
   - Dark background: slate-900/950

5. **Create globals.css**
   - Tailwind directives
   - CSS variables for dark theme (shadcn convention)
   - Force dark mode via `html` class

6. **Create TypeScript types (`types/index.ts`)**
   - Mirror Pydantic schemas exactly:
     - `Article` (from `ArticleResponse`): id, source, source_id, headline, summary, url, published_at, tickers, sentiment, sentiment_label, market_cap, category
     - `ArticleStats`: total_count, by_source, avg_sentiment, articles_today
     - `Ticker`: symbol, name, exchange, market_cap, sector, is_active
     - `Source`: name, source_type, base_url, is_active, article_count
   - Add new types for Phase 2 aggregation endpoints:
     - `SentimentTrendPoint`: timestamp, avg_sentiment, article_count
     - `TopTicker`: symbol, count, avg_sentiment
     - `HourlyBucket`: hour, count

7. **Create API client (`lib/api.ts`)**
   - `API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8200'`
   - Generic `fetchApi<T>(path, params?)` with error handling
   - Typed functions: `getArticles()`, `getLatestArticles()`, `getArticleStats()`, `getTickers()`, `getTickerNews(symbol)`, `getSources()`
   - Add placeholder functions for Phase 2 endpoints

8. **Create utils (`lib/utils.ts`)**
   - `cn()` — classnames merge (shadcn standard)
   - `sentimentColor(label)` — returns tailwind class
   - `sentimentBgColor(label)` — returns bg class
   - `formatTimeAgo(date)` — relative time
   - `formatSentiment(value)` — format to 2 decimal places with +/- sign

9. **Create sidebar (`components/layout/sidebar.tsx`)**
   - Client component (uses useState for collapse)
   - Nav items: Dashboard (/), Feed (/feed), Sentiment (/sentiment), Sources (/sources)
   - Icons from lucide-react (already in shadcn)
   - Active state via `usePathname()`
   - Collapsible: icon-only when collapsed

10. **Create header (`components/layout/header.tsx`)**
    - Page title (can derive from pathname or pass as prop)
    - Refresh button
    - Optional: last updated timestamp

11. **Create root layout (`app/layout.tsx`)**
    - Import globals.css
    - Inter font from next/font/google
    - `<html className="dark">` — force dark mode
    - Sidebar + main content area with padding
    - Metadata: title "AlphaSniper", description

12. **Create placeholder page (`app/page.tsx`)**
    - Simple "Dashboard coming in Phase 2" with loading skeleton

13. **Add CORS to FastAPI (`src/api/main.py`)**
    ```python
    from fastapi.middleware.cors import CORSMiddleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:8210"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    ```

14. **Verify setup**
    - Run `npm run dev` in src/webapp/
    - Confirm sidebar renders, navigation works
    - Confirm API client can reach FastAPI health endpoint

## Todo List

- [ ] Init Next.js 15 project in src/webapp/
- [ ] Install shadcn/ui, Tremor, Recharts
- [ ] Configure dark theme (tailwind + globals.css)
- [ ] Create TypeScript types matching API schemas
- [ ] Create API client library (lib/api.ts)
- [ ] Create utility functions (lib/utils.ts)
- [ ] Build collapsible sidebar navigation
- [ ] Build header component
- [ ] Create root layout with sidebar + main area
- [ ] Add CORS middleware to FastAPI
- [ ] Verify dev server runs on port 8210
- [ ] Verify API connectivity from webapp

## Test Cases

- Sidebar renders all nav items, click navigates correctly
- Active nav item highlighted based on current route
- Sidebar collapse/expand toggles between icon-only and full
- API client fetches /health endpoint successfully
- API client handles network errors gracefully (shows error state)
- Dark theme applied consistently (no white flashes)
- TypeScript types compile without errors

## Verification Steps

1. `cd src/webapp && npm run build` — no build errors
2. `npm run dev` — opens on port 8210
3. Navigate to each route — sidebar highlights correctly
4. Browser devtools: fetch to `localhost:8200/health` returns 200
5. No CORS errors in console

## Success Criteria

- [ ] Next.js app builds and runs on port 8210
- [ ] Dark theme renders consistently
- [ ] Sidebar navigation works for all 5 routes
- [ ] API client successfully connects to FastAPI
- [ ] No TypeScript errors
- [ ] All files < 200 lines

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|-----------|
| shadcn/ui init conflicts with Tremor | Medium | Install Tremor after shadcn, check for Tailwind conflicts |
| CORS not working in SSR | Low | Server Components run server-side, no CORS needed; only Client Components need it |
| Port conflict | Low | Configurable via env var |

## Security Considerations

- No auth required (internal tool)
- API URL configurable via env var (not hardcoded for production)
- No sensitive data exposed in client bundle

## Next Steps

- Phase 2: Dashboard page with KPI cards and charts
- Phase 2 depends on: new FastAPI aggregation endpoints
