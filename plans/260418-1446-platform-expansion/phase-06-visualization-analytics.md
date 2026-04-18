# Phase 6: Visualization & Analytics

## Context Links

- Parent: [plan.md](plan.md)
- Depends on: [Phase 4 - UI Redesign](phase-04-ui-redesign.md), [Phase 5 - LLM Advisor](phase-05-llm-advisor-pipeline.md)
- Related: All previous phases provide data for visualization

## Overview

- **Priority:** P3
- **Status:** pending
- **Effort:** ~1.5 weeks
- **Description:** Add sentiment heatmap, alert rules engine, scheduler metrics dashboard, combined ticker overview. Final polish layer that makes all collected data actionable.

## Key Insights

- Sentiment heatmap: sector-level view helps spot market rotation
- Alert rules engine: user-defined triggers (e.g., insider buy > $1M AND bullish sentiment)
- Scheduler dashboard: visualize source health, frequency, throughput
- Combined ticker overview: single page showing all data types for one symbol
- All data already available via FastAPI; this phase is frontend-heavy

## Requirements

### Functional

- **Sentiment Heatmap**: grid view by sector/ticker, color-coded sentiment (-1 to 1)
- **Alert Rules Engine**: configurable rules with conditions + actions (Discord notify)
- **Scheduler Dashboard**: source status, metrics charts, config editor
- **Ticker Overview**: combined view (news + sentiment + insider + short + earnings)
- **Portfolio Analytics**: aggregated stats (avg sentiment, top movers, risk exposure)

### Non-Functional

- Charts render < 500ms
- Alert evaluation < 200ms per rule
- Dashboard auto-refreshes every 60s
- Mobile-friendly charts (responsive SVG/canvas)

## Architecture

```
Frontend (Next.js)
  ├── Sentiment Heatmap ──── GET /api/sentiment/heatmap?sector=technology
  ├── Alert Rules Panel ──── GET/POST /api/alerts/rules
  ├── Scheduler Dashboard ── GET /admin/scheduler/metrics + /admin/sources
  ├── Ticker Overview ────── GET /api/ticker/{symbol}/overview
  └── Portfolio Analytics ── GET /api/portfolio/stats

Backend (FastAPI)
  ├── /api/sentiment/heatmap → aggregate SocialSentiment by sector
  ├── /api/alerts/rules → CRUD alert rules (PostgreSQL)
  ├── /api/alerts/evaluate → run rules against latest data
  ├── /api/ticker/{symbol}/overview → join all data sources
  └── /api/portfolio/stats → aggregate watchlist metrics

Alert Engine (Taskiq task)
  Every 5 min: evaluate all active rules → trigger actions (Discord webhook)
```

### Alert Rule Schema

```python
class AlertRule(Base):  # src/core/models/alert-rule.py
    id: UUID
    name: str
    enabled: bool = True
    conditions: dict  # JSONB: {"field": "sentiment", "op": ">", "value": 0.7}
    ticker_filter: list[str] | None  # specific tickers or None = all
    action: str  # "discord_webhook" | "log"
    cooldown_minutes: int = 60
    last_triggered_at: datetime | None
    created_at: datetime

# Example rule:
# "Insider Buy > $500K on small-cap with bullish sentiment"
# conditions: [
#   {"source": "insider_trade", "field": "value", "op": ">", "value": 500000},
#   {"source": "insider_trade", "field": "transaction_type", "op": "==", "value": "buy"},
#   {"source": "article", "field": "sentiment", "op": ">", "value": 0.3}
# ]
```

### Heatmap Data Shape

```python
class HeatmapCell(BaseModel):
    ticker: str
    sector: str | None
    sentiment_avg: float  # -1 to 1
    mention_count: int
    change_24h: float  # sentiment change
    health_score: int  # 0-100 from Phase 5
```

## Related Code Files

### Files to Create

| File | LOC | Purpose |
|------|-----|---------|
| **Backend** | | |
| `src/core/models/alert-rule.py` | ~40 | PostgreSQL alert rule model |
| `src/api/routes/alerts-routes.py` | ~90 | CRUD alert rules + evaluate |
| `src/api/routes/heatmap-routes.py` | ~60 | Sentiment heatmap aggregation |
| `src/api/routes/portfolio-routes.py` | ~60 | Portfolio stats aggregation |
| `src/jobs/alert-evaluator.py` | ~100 | Taskiq task: evaluate rules every 5 min |
| **Frontend** | | |
| `src/webapp/app/alerts/page.tsx` | ~120 | Alert rules management page |
| `src/webapp/app/analytics/page.tsx` | ~120 | Portfolio analytics page |
| `src/webapp/components/analytics/sentiment-heatmap.tsx` | ~100 | Heatmap grid component |
| `src/webapp/components/analytics/source-health-chart.tsx` | ~80 | Scheduler source status |
| `src/webapp/components/analytics/alert-rule-editor.tsx` | ~90 | Rule creation form |
| `src/webapp/components/analytics/portfolio-stats.tsx` | ~70 | Portfolio KPI cards |
| `src/webapp/components/analytics/ticker-sparkline.tsx` | ~40 | Mini chart component |
| **Tests** | | |
| `tests/test-api/test-alerts.py` | ~60 | Alert CRUD + evaluation tests |
| `tests/test-api/test-heatmap.py` | ~40 | Heatmap aggregation tests |
| `tests/test-jobs/test-alert-evaluator.py` | ~50 | Alert engine tests |

### Files to Modify

| File | Changes |
|------|---------|
| `src/jobs/taskiq_app.py` | Add alert evaluation task (every 5 min) |
| `src/api/main.py` | Register alerts, heatmap, portfolio routers |
| `src/webapp/app/layout.tsx` | Add navigation: Alerts, Analytics |
| `src/webapp/app/admin/scheduler/page.tsx` | Add metrics charts |
| `migrations/` | New migration for alert_rules table |

## Implementation Steps

### Week 1: Backend + Alert Engine

1. **Create AlertRule model** + Alembic migration
2. **Create alerts API routes**:
   - GET /api/alerts/rules -> list rules
   - POST /api/alerts/rules -> create rule
   - PUT /api/alerts/rules/{id} -> update rule
   - DELETE /api/alerts/rules/{id} -> delete rule
   - POST /api/alerts/evaluate -> manual trigger
3. **Create alert evaluator task**:
   - Every 5 min: fetch active rules
   - For each rule: query relevant data (sentiment, insider, short interest)
   - Evaluate conditions (field op value)
   - If all conditions met AND cooldown expired -> trigger action
   - Action: send Discord webhook (reuse discord_notify.py)
4. **Create heatmap API**:
   - Aggregate SocialSentiment + Article sentiment by ticker
   - Group by sector (if sector data available, else flat grid)
   - Return HeatmapCell array
5. **Create portfolio stats API**:
   - Average sentiment across watchlist
   - Top 5 movers (biggest sentiment change 24h)
   - Risk exposure: count tickers with high short interest
   - Upcoming earnings count

### Week 2: Frontend Components

6. **Sentiment heatmap component**:
   - Grid of colored cells (green=bullish, red=bearish, gray=neutral)
   - Cell size proportional to mention count
   - Hover: tooltip with details
   - Click: navigate to ticker detail
7. **Alert rule editor**:
   - Form: name, conditions (add/remove rows), ticker filter, action
   - Condition row: source dropdown, field dropdown, operator, value input
   - Toggle enabled/disabled
   - Show last triggered timestamp
8. **Scheduler dashboard enhancements**:
   - Bar chart: articles/hour per source (last 24h)
   - Status indicators: green=healthy, yellow=degraded, red=circuit-breaker
   - Config editor: inline interval adjustment
9. **Portfolio analytics page**:
   - KPI cards: total articles, avg sentiment, upcoming earnings, risk alerts
   - Mini sparklines per watchlist ticker
   - Top movers table (sentiment change)
10. **Navigation + integration**:
    - Add Alerts, Analytics links to sidebar
    - Auto-refresh dashboard every 60s
    - Loading skeletons for charts

## Todo List

- [ ] Create AlertRule PostgreSQL model + migration
- [ ] Implement alerts CRUD API routes
- [ ] Implement alert evaluator Taskiq task
- [ ] Create heatmap aggregation API
- [ ] Create portfolio stats API
- [ ] Build sentiment heatmap component
- [ ] Build alert rule editor component
- [ ] Enhance scheduler dashboard with charts
- [ ] Build portfolio analytics page
- [ ] Add navigation links
- [ ] Auto-refresh dashboard
- [ ] Write backend tests
- [ ] E2E test: create rule -> trigger -> Discord notification

## Test Cases

### Happy Path

- Create alert rule "Insider buy > $500K" -> saves to PG
- Insider buy $1M recorded -> alert evaluator triggers -> Discord message sent
- Heatmap shows 20 tickers with color-coded sentiment
- Portfolio stats show 5 upcoming earnings, avg sentiment 0.3
- Scheduler dashboard shows all 13 sources with current intervals

### Edge Cases

- Alert rule with no matching data -> not triggered, no error
- Heatmap with only 2 tickers having sentiment data -> sparse grid
- Alert cooldown: triggered 30 min ago (cooldown 60 min) -> skip
- Source with no metrics yet (just added) -> show "N/A" in dashboard

### Error Scenarios

- Alert evaluation fails for one rule -> continue with others, log error
- Discord webhook URL invalid -> log error, don't crash evaluator
- Heatmap query timeout (too much data) -> paginate or limit to watchlist
- Portfolio stats with empty watchlist -> return zeros

## Verification Steps

### Manual

1. Create alert rule via UI, verify saved in PG
2. Manually insert matching data, run evaluator, check Discord notification
3. View heatmap page, verify colors match sentiment values
4. Check scheduler dashboard, verify source metrics match reality
5. View portfolio analytics, verify KPI numbers are plausible

### Automated

```bash
uv run pytest tests/test-api/test-alerts.py -v
uv run pytest tests/test-api/test-heatmap.py -v
uv run pytest tests/test-jobs/test-alert-evaluator.py -v
cd src/webapp && npm run build
```

## Acceptance Criteria

- [ ] Sentiment heatmap renders with real data
- [ ] Alert rules CRUD works (create, read, update, delete)
- [ ] Alert evaluator triggers Discord notifications on matching conditions
- [ ] Scheduler dashboard shows source health + metrics
- [ ] Portfolio analytics shows aggregated stats
- [ ] Auto-refresh works on dashboard (60s interval)
- [ ] All tests pass

## Success Criteria

- Users get Discord alerts for actionable trading signals
- Heatmap provides at-a-glance market sentiment view
- Scheduler dashboard confirms all 13 sources are healthy
- Portfolio page replaces manual ticker-by-ticker checking

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Alert rules too complex for users | Low | Start with simple UI; preset templates |
| Heatmap performance with 100+ tickers | Medium | Limit to watchlist; paginate |
| Alert spam (too many notifications) | Medium | Cooldown per rule; daily limit |
| Chart library bundle size | Low | Lazy-load chart components |

## Security Considerations

- Alert rules per-user if auth added (currently single-user)
- Discord webhook URL stored in .env (not user-configurable via UI)
- Alert evaluation server-side only (no client-side data access)
- Rate limit on alert evaluation (max 1 per 5 min)

## Next Steps

- Future: email/SMS notification channels
- Future: backtest alert rules against historical data
- Future: ML-based alert suggestions
- Future: real-time WebSocket push for alert triggers
