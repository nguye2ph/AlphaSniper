# Phase 2: Trading Terminal UI Upgrade

## Context Links

- [Brainstorm — Part 1](../reports/brainstorm-260412-2258-ui-upgrade-discord.md)
- [Dashboard Page](../../src/webapp/app/page.tsx)
- [Article Card](../../src/webapp/components/feed/article-card.tsx)
- [Types](../../src/webapp/types/index.ts)
- [Webapp Components](../../src/webapp/components/)

## Overview

- **Priority**: P1
- **Status**: pending
- **Effort**: 5h
- **Description**: Transform flat UI into Bloomberg/TradingView-style trading terminal. Glassmorphism cards, animated counters, sparklines, sentiment charts, hover effects.

## Key Insights

- Current dashboard is functional but plain — flat zinc-900 cards, no animations
- shadcn/ui already installed — extend with custom glassmorphism variants
- Recharts likely needed for sparklines + area charts (check if already in deps)
- framer-motion for layout animations, number counters, transitions
- Keep SSR-compatible: wrap animated components in "use client" boundaries
- Current pages: dashboard, feed, sentiment, ticker detail, sources

## Requirements

### Functional
- Glassmorphism KPI cards with backdrop-blur + neon sentiment glow
- Animated number counters on KPI values (count up on load)
- Sparkline mini-charts inside KPI cards (7-day trend)
- Pulsing green dot for "live" indicator next to "Articles Today"
- Sentiment trend area chart (gradient fill green → red)
- Top tickers horizontal bar chart with sentiment coloring
- Category donut chart with center label
- Feed cards: vertical sentiment strip on left, hover lift + glow
- Ticker detail: hero header with animated sentiment badge
- Sentiment page: animated radial gauge (SVG)

### Non-Functional
- Bundle size: framer-motion ~30KB gzipped — acceptable tradeoff
- Animations should be subtle, not distracting
- All animations respect `prefers-reduced-motion`
- Mobile responsive — glassmorphism degrades gracefully

## Architecture

```
src/webapp/
├── app/
│   ├── page.tsx                    # Dashboard (upgrade KPI + charts)
│   ├── sentiment/page.tsx          # Sentiment (add radial gauge)
│   └── ticker/[symbol]/page.tsx    # Ticker detail (hero header)
├── components/
│   ├── charts/
│   │   ├── sparkline-chart.tsx     # NEW: mini sparkline for KPI cards
│   │   ├── sentiment-area-chart.tsx # NEW: gradient area chart
│   │   ├── top-tickers-bar-chart.tsx # NEW: horizontal bar chart
│   │   ├── category-donut-chart.tsx # NEW: donut with center label
│   │   └── radial-gauge.tsx        # NEW: SVG animated gauge
│   ├── dashboard/
│   │   ├── glassmorphism-kpi-card.tsx # NEW: glass KPI with sparkline
│   │   ├── animated-counter.tsx    # NEW: number count-up animation
│   │   └── live-indicator.tsx      # NEW: pulsing green dot
│   ├── feed/
│   │   └── article-card.tsx        # MODIFY: add sentiment strip + hover
│   └── ui/
│       └── glassmorphism.tsx       # NEW: glassmorphism base styles
├── lib/
│   └── styles/
│       └── glassmorphism.css       # NEW: CSS classes
```

## Related Code Files

### Modify
- `src/webapp/app/page.tsx` — replace flat KPIs with glassmorphism, add charts
- `src/webapp/app/sentiment/page.tsx` — add radial gauge
- `src/webapp/app/ticker/[symbol]/page.tsx` — hero header + sentiment badge
- `src/webapp/components/feed/article-card.tsx` — sentiment strip, hover effects
- `src/webapp/app/globals.css` — add glassmorphism + neon glow CSS classes

### Create
- `src/webapp/components/charts/sparkline-chart.tsx`
- `src/webapp/components/charts/sentiment-area-chart.tsx`
- `src/webapp/components/charts/top-tickers-bar-chart.tsx`
- `src/webapp/components/charts/category-donut-chart.tsx`
- `src/webapp/components/charts/radial-gauge.tsx`
- `src/webapp/components/dashboard/glassmorphism-kpi-card.tsx`
- `src/webapp/components/dashboard/animated-counter.tsx`
- `src/webapp/components/dashboard/live-indicator.tsx`

### Dependencies to Install
- `framer-motion` — animations/transitions
- `recharts` — charts (check if already installed)

## Implementation Steps

### Step 1: Install Dependencies (5min)

```bash
cd src/webapp && npm install framer-motion recharts
```

### Step 2: Glassmorphism CSS (15min)

Add to `globals.css`:
- `.glass-card` — `backdrop-blur-xl bg-white/5 border border-white/10 shadow-lg`
- `.neon-glow-green` — `shadow-[0_0_15px_rgba(34,197,94,0.3)]`
- `.neon-glow-red` — `shadow-[0_0_15px_rgba(239,68,68,0.3)]`
- `.pulse-dot` — keyframe animation for pulsing green dot
- Respect `prefers-reduced-motion: reduce`

### Step 3: Dashboard Components (1.5h)

1. **animated-counter.tsx** ("use client")
   - framer-motion `useSpring` + `useTransform` for count-up
   - Props: `value: number`, `duration?: number`, `prefix?: string`
   - Format large numbers with commas

2. **live-indicator.tsx** ("use client")
   - Pulsing green dot using CSS animation
   - Small circle with expanding ring effect

3. **glassmorphism-kpi-card.tsx** ("use client")
   - Glass background with backdrop-blur
   - Neon border glow based on sentiment (green/red/neutral)
   - Slot for sparkline chart below value
   - Uses AnimatedCounter for value display

### Step 4: Chart Components (1.5h)

1. **sparkline-chart.tsx** ("use client")
   - Recharts `<AreaChart>` tiny (100x40px), no axes/labels
   - Gradient fill matching sentiment color
   - Props: `data: number[]`, `color: string`

2. **sentiment-area-chart.tsx** ("use client")
   - Full-width Recharts `<AreaChart>`
   - Gradient fill from green (positive) to red (negative)
   - X-axis: dates, Y-axis: sentiment score
   - Tooltip with date + exact sentiment

3. **top-tickers-bar-chart.tsx** ("use client")
   - Horizontal `<BarChart>` from Recharts
   - Bar color based on avg sentiment per ticker
   - Show count + sentiment label

4. **category-donut-chart.tsx** ("use client")
   - Recharts `<PieChart>` with inner radius (donut)
   - Center label showing total count
   - Colored segments per category

5. **radial-gauge.tsx** ("use client")
   - Custom SVG arc from -1.0 to +1.0
   - framer-motion animate arc fill
   - Color transitions: red → yellow → green
   - Center text with sentiment score

### Step 5: Dashboard Page Upgrade (45min)

Update `src/webapp/app/page.tsx`:
1. Replace `KpiCard` with `GlassmorphismKpiCard` + `AnimatedCounter`
2. Add `LiveIndicator` next to "Articles Today" title
3. Add `SparklineChart` inside each KPI card (pass 7-day trend data)
4. New API endpoint needed: `GET /api/articles/trends` (sparkline data)
5. Replace "Articles by Source" with `CategoryDonutChart`
6. Replace "Latest Articles" list with `SentimentAreaChart` + smaller list
7. Add `TopTickersBarChart` section

### Step 6: Feed Card Upgrade (30min)

Update `src/webapp/components/feed/article-card.tsx`:
1. Add 4px vertical strip on left edge, colored by sentiment
   - Green (bullish), red (bearish), gray (neutral)
2. framer-motion `whileHover={{ y: -2, transition: { duration: 0.2 } }}`
3. Hover glow: add sentiment-colored box-shadow on hover
4. Ticker badges: filled background instead of outline variant
5. Wrap card in `motion.div` for layout animation

### Step 7: Ticker Detail + Sentiment Page (30min)

1. Ticker detail hero header:
   - Large ticker symbol + name
   - Animated sentiment badge (framer-motion scale + color)
   - Stats in horizontal pill badges
2. Sentiment page:
   - Replace existing gauge with `RadialGauge` component
   - Add `SentimentAreaChart` for timeline view

### Step 8: New API Endpoint (15min)

Add to FastAPI `articles_routes.py`:
- `GET /api/articles/trends` — returns daily avg sentiment + count for last 7 days
- Used by sparkline charts and sentiment area chart

## Todo List

- [ ] Install framer-motion + recharts
- [ ] Add glassmorphism CSS classes to globals.css
- [ ] Create animated-counter.tsx
- [ ] Create live-indicator.tsx
- [ ] Create glassmorphism-kpi-card.tsx
- [ ] Create sparkline-chart.tsx
- [ ] Create sentiment-area-chart.tsx
- [ ] Create top-tickers-bar-chart.tsx
- [ ] Create category-donut-chart.tsx
- [ ] Create radial-gauge.tsx
- [ ] Upgrade dashboard page.tsx
- [ ] Upgrade article-card.tsx with sentiment strip + hover
- [ ] Upgrade ticker detail page
- [ ] Upgrade sentiment page with radial gauge
- [ ] Add /api/articles/trends endpoint
- [ ] Test responsive layout on mobile

## Test Cases

- **KPI animation**: Counter counts from 0 to actual value on mount
- **Live indicator**: Dot pulses continuously
- **Glassmorphism**: Cards show frosted glass effect on dark background
- **Hover effects**: Feed cards lift and glow on hover
- **Responsive**: Cards stack on mobile, charts resize
- **Reduced motion**: Animations disabled when prefers-reduced-motion is set
- **Empty state**: Charts handle empty data gracefully

## Verification Steps

1. `cd src/webapp && npm run build` — no build errors
2. Open dashboard — KPI cards show glass effect + animated counters
3. Hover feed cards — lift + glow visible
4. Check mobile viewport — responsive layout correct
5. Set `prefers-reduced-motion: reduce` — animations disabled

## Acceptance Criteria

- [ ] All KPI cards use glassmorphism styling
- [ ] Number values animate on page load
- [ ] Sparklines visible inside KPI cards
- [ ] Sentiment area chart renders with gradient
- [ ] Feed cards have sentiment strip + hover effects
- [ ] Radial gauge on sentiment page
- [ ] Bundle size increase < 50KB gzipped
- [ ] Mobile responsive

## Success Criteria

- Visual upgrade obvious — "trader terminal" feel achieved
- No layout regressions on existing pages
- Performance: LCP < 2s on dashboard

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Bundle bloat | Medium | Tree-shake framer-motion, lazy load charts |
| SSR hydration mismatches | Medium | All animated components are "use client" |
| Chart data loading | Low | Suspense boundaries + skeleton states |
| Mobile glassmorphism perf | Low | Reduce backdrop-blur on mobile if needed |

## Security Considerations

- No security concerns — purely presentational changes
- Charts display read-only data from existing API

## Next Steps

- Depends on Phase 1 for content/key_points display in cards
- Future: resizable grid panels (like Bloomberg terminal)
- Future: real-time updates via WebSocket (live chart updates)
