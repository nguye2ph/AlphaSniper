---
title: "Market Cap UI + Live Data Sources"
description: "Add market cap badges to UI and integrate additional live streaming data source"
status: pending
priority: P1
effort: 4.5h
branch: main
tags: [ui, market-cap, live-data, streaming]
created: 2026-04-14
---

# Market Cap UI + Live Data Sources

## Phases

| # | Phase | Effort | Status |
|---|-------|--------|--------|
| 1 | [Market Cap UI Badges](./phase-01-market-cap-ui-badges.md) | 1.5h | pending |
| 2 | [Live Data Source Integration](./phase-02-live-data-source.md) | 3h | pending |

## Key Dependencies

- Phase 1: `market_cap` field already exists in `Article` model + TS type — no schema changes needed
- Phase 2: Research must complete before collector implementation; BaseCollector contract must be followed
- Backend `GET /api/articles` already supports filtering — only `market_cap_gte`/`market_cap_lte` params need adding

## Execution Order

Phase 1 → Phase 2 (sequential; no blockers between phases)
