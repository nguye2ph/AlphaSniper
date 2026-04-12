---
title: "AlphaSniper Analytics Webapp"
description: "Next.js dashboard for stock news visualization and analysis"
status: pending
priority: P1
effort: 12h
branch: main
tags: [webapp, nextjs, analytics, dashboard]
created: 2026-04-12
---

# AlphaSniper Analytics Webapp

## Overview

Next.js 15 dashboard (port 8210) consuming existing FastAPI backend (port 8200). Five pages: dashboard, news feed, ticker detail, sentiment analysis, sources. Dark finance theme with shadcn/ui + Tremor + Recharts.

## Data Flow

```
FastAPI (8200) <-- fetch <-- Next.js SSR (8210) --> Browser (interactive charts)
     |
  PostgreSQL
```

## Phases

| Phase | Name | Status | Effort | File |
|-------|------|--------|--------|------|
| 1 | Project Setup + Layout | pending | 2.5h | [phase-01](phase-01-setup-layout.md) |
| 2 | Dashboard Page | pending | 3.5h | [phase-02](phase-02-dashboard.md) |
| 3 | News Feed | pending | 2.5h | [phase-03](phase-03-news-feed.md) |
| 4 | Ticker Detail | pending | 2h | [phase-04](phase-04-ticker-detail.md) |
| 5 | Sentiment + Sources | pending | 2h | [phase-05](phase-05-sentiment-sources.md) |

## Key Dependencies

- FastAPI backend running on port 8200 with PostgreSQL
- 4 new aggregation endpoints needed (Phase 2)
- CORS middleware on FastAPI (Phase 1)

## File Structure

```
src/webapp/
├── app/
│   ├── layout.tsx, page.tsx, feed/, ticker/[symbol]/, sentiment/, sources/
├── components/
│   ├── ui/, charts/, dashboard/, feed/, layout/
├── lib/
│   ├── api.ts, utils.ts
└── types/
    └── index.ts
```

## Reports

- [Brainstorm](../reports/brainstorm-260412-2217-webapp-analytics.md)
