# Phase 4: Google Stitch UI Redesign

## Context Links

- Parent: [plan.md](plan.md)
- Depends on: [Phase 2](phase-02-data-sources-tier1.md), [Phase 3](phase-03-data-sources-tier2.md) (new data types)
- Research: [Google Stitch](../reports/researcher-260418-1453-google-stitch-research.md)
- Current webapp: `src/webapp/`

## Overview

- **Priority:** P2
- **Status:** pending
- **Effort:** ~2 weeks
- **Description:** Redesign Next.js webapp as professional trading terminal. Use Google Stitch for design exploration, export to Figma, convert to React/shadcn/ui components. Add pages for all new data types (insider trades, earnings, sentiment, short interest, options flow).

## Key Insights

- Google Stitch: free 350 gen/month, outputs HTML/CSS with Tailwind, Figma export
- No direct React export from Stitch -> use Figma + v0.dev or manual refactor
- Dark mode: slate-900 bg, teal accents, green/red for bullish/bearish
- Current webapp uses Next.js 16, shadcn/ui, Tailwind - compatible with Stitch output
- Stitch design -> Figma -> v0.dev -> shadcn/ui components pipeline

## Requirements

### Functional

- Redesigned dashboard: professional dark-mode trading terminal aesthetic
- New pages: Insider Trades, Earnings Calendar, Social Sentiment, Short Interest, Options Flow
- Enhanced ticker detail page: combined data from all sources
- Watchlist table with sparklines, sentiment badges
- Real-time news feed with sentiment indicators
- Responsive design (desktop-first, mobile-friendly)
- Dark mode toggle (light/dark)

### Non-Functional

- WCAG AA accessibility (4.5:1 contrast ratio)
- Core Web Vitals: LCP < 2.5s, CLS < 0.1
- Code-split pages for performance
- shadcn/ui component library consistency
- All data fetched via existing FastAPI endpoints

## Architecture

```
Google Stitch (design)
  ↓ export
Figma (design system)
  ↓ convert
v0.dev or manual refactor
  ↓ implement
Next.js App Router (src/webapp/)
  ├── app/
  │   ├── page.tsx            (dashboard - redesigned)
  │   ├── ticker/[symbol]/    (enhanced ticker detail)
  │   ├── insider-trades/     (NEW)
  │   ├── earnings/           (NEW)
  │   ├── sentiment/          (NEW)
  │   ├── short-interest/     (NEW)
  │   ├── options-flow/       (NEW)
  │   └── admin/scheduler/    (NEW - scheduler config)
  ├── components/
  │   ├── ui/                 (shadcn/ui base)
  │   ├── dashboard/          (redesigned widgets)
  │   ├── ticker/             (ticker detail components)
  │   ├── insider/            (insider trade components)
  │   ├── earnings/           (earnings components)
  │   ├── sentiment/          (sentiment components)
  │   └── short-interest/     (short interest components)
  └── lib/
      └── api.ts              (FastAPI client)
```

### Color Palette

```
Background:  #0f172a (slate-900)
Surface:     #1e293b (slate-800)
Text:        #f1f5f9 (slate-100)
Accent:      #14b8a6 (teal-500)
Bullish:     #10b981 (emerald-500)
Bearish:     #ef4444 (red-500)
Neutral:     #64748b (slate-500)
Border:      #334155 (slate-700)
```

### New API Endpoints (FastAPI, created in P2/P3)

```
GET /api/insider-trades?ticker=X&days=30
GET /api/earnings?upcoming=true&days=14
GET /api/sentiment/social?ticker=X&platform=reddit
GET /api/short-interest?ticker=X
GET /api/options-flow?ticker=X
GET /api/ticker/{symbol}/overview    # Combined all-source data
GET /admin/scheduler/sources         # Scheduler config
GET /admin/scheduler/metrics         # Scheduler metrics
```

## Related Code Files

### Files to Create

| File | Purpose |
|------|---------|
| `src/webapp/app/insider-trades/page.tsx` | Insider trades page |
| `src/webapp/app/earnings/page.tsx` | Earnings calendar page |
| `src/webapp/app/sentiment/page.tsx` | Social sentiment page |
| `src/webapp/app/short-interest/page.tsx` | Short interest page |
| `src/webapp/app/options-flow/page.tsx` | Options flow page |
| `src/webapp/app/admin/scheduler/page.tsx` | Scheduler admin page |
| `src/webapp/app/ticker/[symbol]/page.tsx` | Enhanced ticker detail |
| `src/webapp/components/dashboard/ticker-header.tsx` | Redesigned ticker widget |
| `src/webapp/components/dashboard/news-feed-card.tsx` | Redesigned news card |
| `src/webapp/components/dashboard/watchlist-table.tsx` | Watchlist with sparklines |
| `src/webapp/components/dashboard/portfolio-kpi.tsx` | Portfolio KPI cards |
| `src/webapp/components/insider/insider-trade-table.tsx` | Insider trades table |
| `src/webapp/components/earnings/earnings-calendar.tsx` | Calendar view |
| `src/webapp/components/sentiment/sentiment-gauge.tsx` | Sentiment visualization |
| `src/webapp/components/short-interest/squeeze-indicator.tsx` | Squeeze score badge |
| `src/webapp/types/insider-trade.ts` | TypeScript types |
| `src/webapp/types/earnings-event.ts` | TypeScript types |
| `src/webapp/types/social-sentiment.ts` | TypeScript types |
| `src/webapp/types/short-interest.ts` | TypeScript types |
| `src/api/routes/ticker-overview-routes.py` | Combined ticker endpoint |

### Files to Modify

| File | Changes |
|------|---------|
| `src/webapp/app/page.tsx` | Redesign main dashboard layout |
| `src/webapp/app/layout.tsx` | Dark mode toggle, updated navigation |
| `src/webapp/lib/api.ts` | Add fetch functions for new endpoints |
| `src/webapp/components/` | Refactor existing components to new design |
| `src/api/main.py` | Register ticker-overview router |

## Implementation Steps

### Week 1: Design Phase (Systematic Prompt Engineering)
<!-- Updated: Validation Session 1 - Full design phase with systematic prompt catalog -->

**Approach:** Create a prompt catalog with shared base prompt (style/theme/constraints) + per-screen prompts. This ensures visual consistency across all generated screens.

1. **Create shared base prompt** (Day 1):
   - Define: color palette (slate-900, teal-500, emerald-500, red-500), typography (JetBrains Mono numbers, Inter labels), spacing, border radius, component style
   - Write DESIGN.md with constraints that prepend every Stitch prompt
   - Example base: "Dark professional trading terminal. Slate-900 bg, teal-500 accents, green gains, red losses. Dense layout, JetBrains Mono for data, Inter for labels. No gradients. 4.5:1 contrast minimum."

2. **Stitch exploration - main dashboard** (Day 1-2):
   - Combine base prompt + dashboard-specific layout description
   - Generate 3-5 variants, select best direction
   - Export screenshots for review

3. **Per-screen prompt catalog** (Day 2-4):
   - Write detailed prompts for each screen:
     - Dashboard (4-section grid: header, chart, news feed, portfolio)
     - Ticker Detail (combined data: news + sentiment + insider + short + earnings)
     - Insider Trades (table with officer, trade type, value, filing date)
     - Earnings Calendar (timeline/calendar view with EPS estimates)
     - Social Sentiment (gauges, Reddit vs StockTwits comparison)
     - Short Interest (squeeze score badges, days-to-cover)
     - Options Flow (volume/premium table)
     - Alerts Management (rule editor, trigger history)
     - Scheduler Admin (source status, metrics charts)
   - Each prompt = base prompt + screen-specific layout + data fields + interactions

4. **Component design** (Day 3-4):
   - Generate individual components with base prompt consistency
   - Insider trades table, earnings calendar, sentiment gauge, squeeze indicator
   - Export HTML/CSS, review Tailwind classes

5. **Figma export + design system** (Day 5):
   - Export all designs to Figma
   - Create design system (colors, typography, spacing tokens)
   - Document component props and states
   - Save prompt catalog in `plans/260418-1446-platform-expansion/stitch-prompts.md`

### Week 2: Implementation Phase

4. **React components** (Day 1-2):
   - Convert Stitch HTML to React/shadcn/ui components
   - Use v0.dev for complex components (optional)
   - Implement dark mode with Tailwind `dark:` classes
5. **New pages** (Day 3-4):
   - Create 5 new pages (insider, earnings, sentiment, short interest, options flow)
   - Enhanced ticker detail page (combined data)
   - Scheduler admin page
   - Wire all to FastAPI endpoints via lib/api.ts
6. **Dashboard redesign** (Day 4-5):
   - Redesign main dashboard layout (4-section grid)
   - Integrate redesigned widgets
   - Add navigation for new pages
7. **Combined ticker endpoint** (Day 5):
   - Create `GET /api/ticker/{symbol}/overview` in FastAPI
   - Aggregate: latest articles, sentiment, insider trades, earnings, short interest
   - Single API call for ticker detail page
8. **Polish** (Day 5+):
   - Responsive testing (mobile/tablet/desktop)
   - Accessibility audit (axe DevTools)
   - Loading states, error boundaries
   - Code splitting for new pages

## Todo List

- [ ] Generate Stitch designs (3-5 dashboard variants)
- [ ] Design individual components in Stitch
- [ ] Export to Figma, create design system
- [ ] Convert to React/shadcn/ui components
- [ ] Create insider trades page
- [ ] Create earnings calendar page
- [ ] Create social sentiment page
- [ ] Create short interest page
- [ ] Create options flow page
- [ ] Create scheduler admin page
- [ ] Redesign main dashboard
- [ ] Create enhanced ticker detail page
- [ ] Create ticker overview API endpoint
- [ ] Implement dark mode toggle
- [ ] Add navigation for new pages
- [ ] Responsive design testing
- [ ] Accessibility audit
- [ ] Performance optimization (code splitting)

## Test Cases

### Happy Path

- Dashboard loads with all widgets showing live data
- Click ticker -> detail page shows combined data from all sources
- Insider trades page shows recent Form 4 filings with officer/trade details
- Earnings page shows upcoming earnings dates with EPS estimates
- Sentiment page shows Reddit + StockTwits sentiment per ticker
- Short interest page shows squeeze scores, short % of float
- Dark mode toggle works, persists across sessions

### Edge Cases

- Ticker with no insider trades -> "No data available" message
- Ticker with no earnings -> "No upcoming earnings" message
- API returns empty arrays -> graceful empty states
- Very long headline text -> truncation with tooltip
- Mobile viewport -> responsive layout, stacked cards

### Error Scenarios

- FastAPI down -> error boundary shows "Service unavailable"
- Slow API response -> loading skeleton shown
- Invalid ticker symbol -> 404 page or redirect
- Network error mid-load -> retry button shown

## Verification Steps

### Manual

1. Run Next.js dev server, verify dashboard loads with dark theme
2. Navigate to each new page, verify data renders
3. Test dark/light mode toggle
4. Test responsive layout at 375px, 768px, 1440px widths
5. Run axe DevTools, verify no critical a11y violations
6. Test ticker detail page with real ticker

### Automated

```bash
cd src/webapp && npm run build  # Verify no build errors
cd src/webapp && npm run lint   # ESLint check
# E2E tests if Playwright configured
```

## Acceptance Criteria

- [ ] Professional dark-mode trading terminal UI
- [ ] 5 new pages for new data types
- [ ] Enhanced ticker detail with combined data
- [ ] Scheduler admin page shows config + metrics
- [ ] Dark/light mode toggle works
- [ ] WCAG AA compliance (no critical violations)
- [ ] Responsive at 375px, 768px, 1440px
- [ ] All pages code-split for performance

## Success Criteria

- UI looks like a professional trading terminal (TradingView-inspired)
- Ticker detail page combines 5+ data sources in one view
- Users can navigate between all data types intuitively

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Stitch React export not ready | Low | Manual refactor HTML -> React, v0.dev as backup |
| Stitch Tailwind v3 vs v4 mismatch | Low | Review generated classes, adjust manually |
| Design iterations exceed 350 gen/month | Low | Pre-plan prompts, combine feedback |
| shadcn/ui components don't match design | Low | Custom CSS overrides, extend theme |
| Too many API calls from dashboard | Medium | Client-side caching (TanStack Query / SWR) |

## Security Considerations

- Admin scheduler page: restrict access (check auth before rendering)
- No sensitive data exposed in client-side code
- API keys never sent to frontend
- CORS properly configured for webapp origin
- CSP headers on all pages

## Next Steps

- Phase 6 adds visualization (sentiment heatmap, alert rules, analytics dashboard)
- Performance monitoring in production
