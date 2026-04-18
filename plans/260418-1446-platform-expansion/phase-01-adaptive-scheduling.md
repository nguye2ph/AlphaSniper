# Phase 1: Adaptive Scheduling Infrastructure

## Context Links

- Parent: [plan.md](plan.md)
- Research: [Adaptive Scheduling Design](../reports/researcher-260418-1453-adaptive-scheduling-system-design.md)
- Dependencies: None (foundation phase)

## Overview

- **Priority:** P1 (critical path - all future sources depend on this)
- **Status:** complete
- **Effort:** ~1 week
- **Description:** Replace hardcoded Taskiq `LabelScheduleSource` cron with dynamic `ListRedisScheduleSource`. Add per-source config in Redis JSON, EMA-based metrics tracking, auto-tuning with circuit breaker, and admin API.

## Key Insights

- Taskiq `ListRedisScheduleSource` supports runtime schedule changes without restart
- EMA (alpha=0.3) outperforms complex ML for polling frequency optimization
- Circuit breaker pattern prevents cascading rate-limit failures
- ~300 LOC total across 4 new modules

## Requirements

### Functional

- Per-source config stored in Redis JSON (min/max/current interval, enabled flag)
- Admin API: CRUD source config, view metrics
- Metrics tracking: articles/hour (EMA), empty responses, API errors
- Auto-tuning engine: threshold rules adjust interval within bounds
- Circuit breaker: 5x rate-limit errors -> 2x backoff
- Cooldown: no adjustment more than once per 5 min
- Migrate existing 6 sources from hardcoded cron -> Redis config

### Non-Functional

- Config reads <5ms (Redis)
- Adjustment task <500ms per run
- No scheduler restart on config change
- Atomic Redis updates (no race conditions)

## Architecture

```
Redis JSON Store
  scheduler:sources:{name} = {min_interval, max_interval, current_interval, enabled, ...}
  scheduler:metrics:{name} = {articles_hour, ema, empty_count, api_errors, ...}

                    ┌─────────────────┐
                    │ Admin API       │  GET/POST /admin/sources/{name}/config
                    │ (FastAPI)       │  GET /admin/scheduler/metrics
                    └────────┬────────┘
                             │ reads/writes
                    ┌────────▼────────┐
                    │ Config Manager  │  Redis JSON CRUD + Pydantic validation
                    └────────┬────────┘
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
     ┌────────────┐  ┌──────────────┐  ┌────────────────┐
     │ Scheduler  │  │ Metrics      │  │ Adjustment     │
     │ Integration│  │ Tracker      │  │ Engine (hourly) │
     │ (Taskiq)   │  │ (per-poll)   │  │ EMA + rules    │
     └────────────┘  └──────────────┘  └────────────────┘
```

### Pydantic Models

```python
class SourceScheduleConfig(BaseModel):
    name: str
    enabled: bool = True
    min_interval_seconds: int = 60
    max_interval_seconds: int = 3600
    current_interval_seconds: int = 300
    strategy: Literal["rate_based", "manual"] = "rate_based"
    ema_alpha: float = 0.3
    articles_per_hour_high: int = 50
    articles_per_hour_low: int = 5
    max_rate_errors: int = 5
    adjustment_cooldown_seconds: int = 300
    last_adjustment_at: datetime | None = None

class SourceMetrics(BaseModel):
    articles_last_hour: int = 0
    ema: float = 0.0
    empty_responses_count: int = 0
    api_errors_last_hour: int = 0
    last_poll_at: datetime | None = None
```

## Related Code Files

### Files to Create

| File | LOC | Purpose |
|------|-----|---------|
| `src/scheduler/__init__.py` | 0 | Package init |
| `src/scheduler/config-manager.py` | ~80 | Redis JSON CRUD for per-source config |
| `src/scheduler/metrics-tracker.py` | ~100 | Articles/hour tracking, EMA calculation |
| `src/scheduler/adjustment-engine.py` | ~120 | Threshold rules, circuit breaker, cooldown |
| `src/scheduler/scheduler-integration.py` | ~60 | Taskiq ListRedisScheduleSource setup |
| `src/scheduler/models.py` | ~50 | Pydantic schemas (SourceScheduleConfig, SourceMetrics) |
| `src/api/routes/admin-scheduler-routes.py` | ~80 | Admin API endpoints |
| `tests/test-scheduler/test-config-manager.py` | ~60 | Config CRUD tests |
| `tests/test-scheduler/test-adjustment-engine.py` | ~80 | Rules + circuit breaker tests |

### Files to Modify

| File | Changes |
|------|---------|
| `src/core/config.py` | Add scheduler env vars (scheduler_poll_interval, default source configs) |
| `src/jobs/taskiq_app.py` | Replace LabelScheduleSource with ListRedisScheduleSource; remove hardcoded cron decorators; add hourly adjustment task |
| `src/api/main.py` | Register admin scheduler router |
| `src/collectors/base_collector.py` | Add `report_metrics()` hook called after each `collect()` |
| `docker-compose.yml` | No changes needed (Redis already running) |

## Implementation Steps

1. **Create `src/scheduler/models.py`** - Pydantic schemas for SourceScheduleConfig + SourceMetrics
2. **Create `src/scheduler/config-manager.py`** - Redis JSON CRUD
   - `get_config(source_name) -> SourceScheduleConfig`
   - `set_config(source_name, config) -> None`
   - `list_configs() -> list[SourceScheduleConfig]`
   - `delete_config(source_name) -> None`
   - `seed_defaults()` - populate Redis with 6 existing source configs
3. **Create `src/scheduler/metrics-tracker.py`** - Per-poll metrics
   - `record_poll(source, articles_count, had_error, error_type)`
   - `get_metrics(source) -> SourceMetrics`
   - `compute_ema(current_value, previous_ema, alpha) -> float`
   - Store in Redis HASH `scheduler:metrics:{source_name}`
4. **Create `src/scheduler/adjustment-engine.py`** - Auto-tuning logic
   - `evaluate_source(source_name) -> AdjustmentResult`
   - Rule: EMA > high_threshold -> decrease interval (poll faster, min bound)
   - Rule: EMA < low_threshold -> increase interval (poll slower, max bound)
   - Circuit breaker: errors >= max_rate_errors -> 2x current interval
   - Cooldown check: skip if last_adjustment < cooldown_seconds ago
   - `apply_adjustments()` - run for all enabled sources
5. **Create `src/scheduler/scheduler-integration.py`** - Taskiq bridge
   - Replace LabelScheduleSource with ListRedisScheduleSource
   - `sync_schedules()` - read all configs, generate cron expressions, push to Redis list
   - Called on startup + after any config change
6. **Modify `src/collectors/base_collector.py`** - Add metrics hook
   - `report_metrics(articles_count, had_error=False)` calls metrics-tracker
7. **Modify `src/jobs/taskiq_app.py`** - Migration
   - Remove `@broker.task(schedule=[...])` decorators from all 6 tasks
   - Keep tasks as regular `@broker.task()` (no schedule)
   - Add `adjust_schedules` hourly task
   - Update broker setup to use ListRedisScheduleSource
8. **Create `src/api/routes/admin-scheduler-routes.py`** - Admin endpoints
   - `GET /admin/sources` - list all source configs
   - `GET /admin/sources/{name}/config` - get config
   - `POST /admin/sources/{name}/config` - update config
   - `GET /admin/scheduler/metrics` - all source metrics
9. **Modify `src/api/main.py`** - Register new router
10. **Modify `src/core/config.py`** - Add scheduler settings
    - `scheduler_poll_interval: int = 5`
    - `scheduler_adjustment_enabled: bool = True`
11. **Create seed script** - Populate Redis with default configs for 6 existing sources
12. **Write tests** - config CRUD, EMA calc, threshold logic, circuit breaker

## Todo List

- [ ] Create `src/scheduler/` package with `__init__.py`
- [ ] Create Pydantic models (SourceScheduleConfig, SourceMetrics)
- [ ] Implement config-manager (Redis JSON CRUD)
- [ ] Implement metrics-tracker (EMA, counters)
- [ ] Implement adjustment-engine (rules, circuit breaker, cooldown)
- [ ] Implement scheduler-integration (ListRedisScheduleSource bridge)
- [ ] Modify base_collector to call metrics after collect()
- [ ] Migrate taskiq_app from hardcoded cron to dynamic config
- [ ] Create admin scheduler API routes
- [ ] Register router in main.py
- [ ] Add scheduler settings to config.py
- [ ] Seed default configs for 6 existing sources
- [ ] Write unit tests
- [ ] Integration test: config change -> schedule update

## Test Cases

### Happy Path

- Seed 6 source configs -> all appear in Redis
- Update Finnhub interval to 120s -> scheduler picks up within 2s
- Record 50 articles in 1h -> EMA rises above threshold -> interval decreases
- Admin GET /admin/sources returns all 6 configs with current metrics

### Edge Cases

- Set interval below min_interval -> rejected by Pydantic validation
- Set interval above max_interval -> rejected
- Disable source -> scheduler stops polling
- Re-enable source -> scheduling resumes
- Two rapid config updates -> no race condition (atomic Redis)

### Error Scenarios

- Redis connection lost -> graceful fallback to last known config
- 5x consecutive 429 errors -> circuit breaker doubles interval
- Cooldown prevents thrashing (change within 5 min -> skipped)
- Invalid JSON in Redis -> config-manager returns defaults

## Verification Steps

### Manual

1. Start docker compose, verify Redis running
2. Run seed script, verify 6 configs in Redis (`redis-cli JSON.GET scheduler:sources:finnhub_rest`)
3. Start scheduler, verify polls at configured intervals
4. Hit `POST /admin/sources/finnhub_rest/config` with interval=120, verify schedule updates
5. Check `GET /admin/scheduler/metrics` shows live EMA values

### Automated

```bash
uv run pytest tests/test-scheduler/ -v
uv run pytest tests/test-scheduler/test-config-manager.py -v
uv run pytest tests/test-scheduler/test-adjustment-engine.py -v
```

## Acceptance Criteria

- [ ] All 6 existing sources migrated to Redis config (no hardcoded cron)
- [ ] Admin API: CRUD config + view metrics works
- [ ] EMA auto-tuning adjusts interval within bounds
- [ ] Circuit breaker triggers on rate-limit errors
- [ ] Cooldown prevents rapid thrashing
- [ ] No scheduler restart needed for config changes
- [ ] All tests pass

## Success Criteria

- Scheduler dynamically adjusts polling frequency based on source activity
- Admin can manually override any source interval via API
- Foundation ready for Phase 2-3 (new sources just add a config entry)

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| ListRedisScheduleSource API change | High | Pin taskiq-redis version; integration test |
| Redis config desync | Medium | Always read from Redis at poll time, never cache |
| EMA thrashing | Medium | Wide thresholds (5-50 articles/hr); 5min cooldown |
| Migration breaks existing schedule | High | Deploy config seed before switching schedule source |

## Security Considerations

- Admin endpoints restricted (add auth middleware later or IP whitelist)
- No secrets stored in Redis config (API keys stay in .env)
- Config changes logged via structlog (audit trail)
- Redis bound to localhost in Docker network

## Next Steps

- Phase 2 and 3 register new sources by adding config entries
- Phase 5 adds LLM advisor as alternative to rule-based adjustment
