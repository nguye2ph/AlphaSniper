---
title: "AlphaSniper Platform Expansion"
description: "6-phase expansion: adaptive scheduling, 7 new data sources, UI redesign, LLM advisor, analytics"
status: pending
priority: P2
effort: 8w
branch: main
tags: [expansion, scheduling, collectors, ui, analytics]
created: 2026-04-18
---

# AlphaSniper Platform Expansion

## Overview

Expand from 6 collectors to 13+, add adaptive scheduling, redesign webapp, integrate LLM advisor, build analytics dashboard. All free-tier data sources.

## Research Reports

- [Brainstorm](../reports/brainstorm-260418-1500-alphasniper-expansion.md)
- [Data Sources](../reports/researcher-260418-1452-free-stock-data-sources-research.md)
- [Adaptive Scheduling](../reports/researcher-260418-1453-adaptive-scheduling-system-design.md)
- [Google Stitch UI](../reports/researcher-260418-1453-google-stitch-research.md)

## Phases

| # | Phase | Status | Effort | Deps |
|---|-------|--------|--------|------|
| 1 | [Adaptive Scheduling Infrastructure](phase-01-adaptive-scheduling.md) | complete | 1w | none |
| 2 | [Data Sources Tier 1](phase-02-data-sources-tier1.md) | complete | 1.5w | P1 |
| 3 | [Data Sources Tier 2](phase-03-data-sources-tier2.md) | complete | 1w | P1 |
| 4 | [UI Redesign (Stitch)](phase-04-ui-redesign.md) | complete | 2w | P2,P3 |
| 5 | [LLM Advisor + Pipeline](phase-05-llm-advisor-pipeline.md) | pending | 1w | P1 |
| 6 | [Visualization & Analytics](phase-06-visualization-analytics.md) | pending | 1.5w | P4,P5 |

## Key Dependencies

- Redis 7 (already running) - config store for scheduler
- Taskiq `ListRedisScheduleSource` - dynamic cron support
- Google Stitch (free 350 gen/month) - UI design
- PRAW, feedparser, vaderSentiment - new Python deps
- API keys: Reddit, API Ninjas (free signup)

## Success Metrics

- 13+ data sources active, zero duplicates
- Adaptive scheduling reduces empty API calls by >30%
- Professional trading terminal UI (dark mode)
- Ticker overview combines 5+ sources
- All free-tier quotas respected

## Architecture

```
Source APIs -> Collectors -> MongoDB (raw) -> Taskiq Queue -> Parser Workers
  -> PostgreSQL (clean) -> FastAPI (query) / Discord (notify) / Next.js (webapp)

NEW: Redis JSON config store -> Adaptive Scheduler -> Dynamic cron updates
NEW: Gemini LLM Advisor (hourly) -> Scheduling recommendations
```

## Validation Log

### Session 1 — 2026-04-18
**Trigger:** Initial plan creation validation
**Questions asked:** 7

#### Questions & Answers

1. **[Architecture]** Phase 1 migrates Taskiq from hardcoded LabelScheduleSource to dynamic ListRedisScheduleSource. This affects ALL 6 existing collectors. How should we handle the migration?
   - Options: Big-bang switch | Gradual migration | Shadow mode first
   - **Answer:** Big-bang switch
   - **Rationale:** Simpler code, single deployment. Seed Redis configs before switching. Rollback = revert single commit.

2. **[Architecture]** Phase 2 creates separate PostgreSQL tables for InsiderTrade, EarningsEvent, SocialSentiment instead of extending the existing Article table. Confirm approach?
   - Options: Separate tables | Extend Article | Hybrid approach
   - **Answer:** Separate tables
   - **Rationale:** Clean schema, dedicated indexes, clear separation per data type. Combined views via JOIN or API aggregation.

3. **[Risk]** OpenInsider scraping has legal/ToS risk. Which approach for insider trading data?
   - Options: OpenInsider scraper first | SEC EDGAR Form 4 direct | sec-api.io ($9/mo)
   - **Answer:** OpenInsider scraper first
   - **Rationale:** Free, works now. Monitor for issues, switch to sec-api.io if blocked.

4. **[Scope]** Phases 2 and 3 both depend on Phase 1 only. Sequential or parallel?
   - Options: Sequential (P2 then P3) | Parallel | P2 full, P3 partial overlap
   - **Answer:** Sequential (P2 then P3)
   - **Rationale:** Finish Tier 1 fully, validate pipeline. Then add Tier 2. Easier debugging.

5. **[Architecture]** Cross-source dedup approach with 13+ sources?
   - Options: Jaccard word tokens | URL-only | TF-IDF | LLM embedding
   - **Answer:** Hybrid: URL dedup + LLM evaluation
   - **Custom input:** "dùng thêm LLM để đánh giá vì chủ yếu news cũng khá dễ track"
   - **Rationale:** URL dedup catches most cases. LLM evaluation for ambiguous cases. News headlines are structured enough for LLM to judge efficiently.

6. **[Scope]** Unusual Whales free tier (100-500 req/day) may not be enough. Include or defer?
   - Options: Include experimental | Defer | Replace with Barchart
   - **Answer:** Include as experimental in Phase 3
   - **Rationale:** Low effort to add. Auto-disable if quota exhausted.

7. **[Tradeoff]** UI redesign design time investment?
   - Options: Quick (3 days) | Full phase (1 week) | Minimal
   - **Answer:** Full design phase with systematic prompts
   - **Custom input:** "thật đẹp, hệ thống hoá các màn cần làm và prompt chung và prompt riêng cho từng cái, thật chi tiết"
   - **Rationale:** Invest in detailed, systematic Stitch prompts. Shared style prompt + per-screen prompts for consistency. Beautiful professional result is priority.

#### Confirmed Decisions
- **Migration:** Big-bang Taskiq switch with Redis config seeding
- **Schema:** Separate PG tables per data type (not extending Article)
- **Insider data:** OpenInsider scraper (free, monitor ToS)
- **Execution order:** Sequential P1 → P2 → P3 → P4 → P5 → P6
- **Dedup:** URL dedup + LLM-based headline evaluation (not Jaccard)
- **Unusual Whales:** Keep in P3 as experimental
- **UI design:** Full design phase, systematic prompt engineering for Stitch

#### Action Items
- [ ] Phase 5: Change cross-source dedup from Jaccard to URL + LLM evaluation
- [ ] Phase 4: Add systematic prompt engineering section (shared style + per-screen prompts)
- [ ] Phase 4: Extend design phase to full week with detailed prompt catalog

#### Impact on Phases
- Phase 5: Replace Jaccard headline similarity with URL dedup + Gemini LLM evaluation for ambiguous cases
- Phase 4: Restructure design approach — create prompt catalog (shared base prompt + per-screen prompts) for consistent Stitch output
