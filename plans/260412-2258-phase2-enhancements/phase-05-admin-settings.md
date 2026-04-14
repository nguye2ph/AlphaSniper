# Phase 5: Admin Settings Panel

## Context Links

- [Dashboard Page](../../src/webapp/app/page.tsx)
- [API Routes](../../src/api/routes/articles_routes.py)
- [Config](../../src/core/config.py)
- [Taskiq App](../../src/jobs/taskiq_app.py)

## Overview

- **Priority**: P2
- **Status**: pending
- **Effort**: 3h
- **Description**: Web-based admin panel for managing jobs, watchlist, alert filters, and viewing system stats. New /settings page + FastAPI admin endpoints.

## Key Insights

- Current system has no runtime configuration — all via .env
- Job management needs ability to trigger collectors manually
- Watchlist (tracked tickers) currently hardcoded in `finnhub_symbols`
- Alert filters (Phase 3 webhook) currently use env var threshold
- Settings persistence: PostgreSQL table or JSON file — KISS: use JSON file first, migrate to DB later
- Single-user app — no auth needed for admin panel

## Requirements

### Functional
- **Job Management**: view collector status, trigger manual runs
- **Watchlist**: view/add/remove tracked ticker symbols
- **Alert Filters**: configure sentiment threshold, enable/disable per-ticker alerts
- **System Stats**: article counts, DB sizes, API health, last collection times

### Non-Functional
- Settings persist across restarts (JSON file or DB)
- UI responsive, consistent with trading terminal style (Phase 2)
- API endpoints follow existing patterns

## Architecture

```
Webapp /settings page
  → Tabs: Jobs | Watchlist | Filters | System
  → Each tab calls FastAPI admin endpoints
  → Settings stored in JSON file: data/settings.json

FastAPI /api/admin/*
  → /jobs/trigger/{job_name} — POST — trigger collector
  → /system/stats — GET — DB counts, health
  → /watchlist — GET/PUT — ticker list
  → /filters — GET/PUT — alert config
```

## Related Code Files

### Modify
- `src/api/main.py` — register admin router

### Create (Backend)
- `src/api/routes/admin_routes.py` — admin API endpoints
- `src/core/models/app_settings.py` — settings load/save (JSON file)

### Create (Frontend)
- `src/webapp/app/settings/page.tsx` — settings page with tabs
- `src/webapp/components/settings/job-management-tab.tsx` — job cards with run buttons
- `src/webapp/components/settings/watchlist-tab.tsx` — ticker list editor
- `src/webapp/components/settings/alert-filters-tab.tsx` — threshold slider + toggles
- `src/webapp/components/settings/system-stats-tab.tsx` — stats display

## Implementation Steps

### Step 1: Settings Model (30min)

Create `src/core/models/app_settings.py` (<100 lines):

1. `AppSettings` Pydantic model:
   ```python
   class AppSettings(BaseModel):
       watchlist: list[str] = ["AAPL", "TSLA", "MSFT", "NVDA", "AMD"]
       alert_sentiment_threshold: float = 0.5
       alert_enabled_tickers: list[str] = []  # Empty = all tickers
       alert_enabled_categories: list[str] = []  # Empty = all categories
   ```

2. `def load_settings() -> AppSettings`:
   - Read from `data/settings.json`
   - Return defaults if file doesn't exist

3. `def save_settings(settings: AppSettings) -> None`:
   - Write to `data/settings.json`
   - Create `data/` directory if needed

### Step 2: Admin API Endpoints (1h)

Create `src/api/routes/admin_routes.py` (<150 lines):

1. `POST /api/admin/jobs/trigger/{job_name}`
   - Validate job_name in ["finnhub_rest", "marketaux", "sec_edgar", "process_raw", "scrape_content"]
   - Enqueue corresponding Taskiq task
   - Return `{"status": "triggered", "job": job_name}`

2. `GET /api/admin/system/stats`
   - Query PostgreSQL: total articles, articles today, articles this week
   - Query by source counts
   - Return last collection timestamp per source
   - Basic health: DB connection OK, Redis ping OK

3. `GET /api/admin/watchlist`
   - Return current watchlist from settings

4. `PUT /api/admin/watchlist`
   - Body: `{"symbols": ["AAPL", "TSLA", ...]}`
   - Validate: uppercase, 1-5 chars each
   - Save to settings

5. `GET /api/admin/filters`
   - Return current alert filter config

6. `PUT /api/admin/filters`
   - Body: `{"sentiment_threshold": 0.5, "enabled_tickers": [...], "enabled_categories": [...]}`
   - Save to settings

Register router in `src/api/main.py`.

### Step 3: Settings Page Layout (30min)

Create `src/webapp/app/settings/page.tsx`:
- Tab navigation: Jobs | Watchlist | Filters | System
- Use shadcn/ui Tabs component
- Each tab renders corresponding component
- "use client" for interactivity

### Step 4: Job Management Tab (20min)

Create `src/webapp/components/settings/job-management-tab.tsx`:
- Cards for each collector: Finnhub REST, MarketAux, SEC EDGAR, Process Raw, Scrape Content
- Each card shows: name, description, "Run Now" button
- Button calls POST /api/admin/jobs/trigger/{name}
- Show success/error toast after trigger
- Future: show last run time, status (requires more backend work)

### Step 5: Watchlist Tab (20min)

Create `src/webapp/components/settings/watchlist-tab.tsx`:
- Current symbols as badges/chips
- "X" button on each to remove
- Input field + "Add" button to add new symbol
- Auto-uppercase input
- Validate: 1-5 chars, letters only
- Save button calls PUT /api/admin/watchlist

### Step 6: Alert Filters Tab (15min)

Create `src/webapp/components/settings/alert-filters-tab.tsx`:
- Sentiment threshold slider (0.0 to 1.0)
- Ticker checkboxes (from watchlist) — which tickers trigger alerts
- Category checkboxes — which categories trigger alerts
- Save button calls PUT /api/admin/filters

### Step 7: System Stats Tab (15min)

Create `src/webapp/components/settings/system-stats-tab.tsx`:
- Cards showing: total articles, today count, this week count
- Source breakdown table
- DB health indicators (green/red dots)
- Auto-refresh every 30 seconds

## Todo List

- [ ] Create app_settings.py (JSON load/save)
- [ ] Create data/ directory for settings.json
- [ ] Create admin_routes.py with all endpoints
- [ ] Register admin router in main.py
- [ ] Create settings page.tsx with tabs
- [ ] Create job-management-tab.tsx
- [ ] Create watchlist-tab.tsx
- [ ] Create alert-filters-tab.tsx
- [ ] Create system-stats-tab.tsx
- [ ] Add /settings link to sidebar navigation
- [ ] Update discord_notify.py to use dynamic settings

## Test Cases

- **Trigger job**: POST /api/admin/jobs/trigger/finnhub_rest → task enqueued
- **Invalid job**: POST /api/admin/jobs/trigger/invalid → 400 error
- **Get watchlist**: Returns current symbols
- **Update watchlist**: PUT with new symbols → saved to JSON, GET reflects change
- **Invalid ticker**: "toolong" rejected (>5 chars)
- **System stats**: Returns correct counts from DB
- **Settings persist**: Restart server → settings unchanged

## Verification Steps

1. Start API server
2. Navigate to /settings in webapp
3. Click "Run Now" on Finnhub job → verify task enqueued (check logs)
4. Add ticker to watchlist → verify saved (refresh page)
5. Adjust sentiment threshold → verify discord notifications respect new threshold
6. Check system stats → verify counts match DB

## Acceptance Criteria

- [ ] /settings page accessible with 4 tabs
- [ ] Jobs can be triggered from UI
- [ ] Watchlist editable (add/remove symbols)
- [ ] Alert filters configurable (threshold + ticker/category)
- [ ] System stats display correctly
- [ ] Settings persist in JSON file
- [ ] Sidebar has /settings link

## Success Criteria

- All admin actions functional from UI
- No need to edit .env for runtime config changes
- Settings survive server restarts

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| JSON file corruption | Medium — settings lost | Default fallback, atomic writes |
| No auth on admin endpoints | Low — single-user app | Add basic auth later if needed |
| Concurrent writes | Low — single user | Atomic file writes |
| Job trigger abuse | Low — single user | Rate limit trigger endpoint |

## Security Considerations

- No auth on admin panel (single-user personal tool)
- If exposed publicly later: add basic auth middleware
- Job trigger should validate job names strictly
- Don't expose internal paths or secrets in system stats

## Next Steps

- Phase 3 webhook uses dynamic settings from admin panel
- Future: auth middleware for admin endpoints
- Future: job scheduling (cron expressions) from UI
- Future: migrate settings from JSON to PostgreSQL table
