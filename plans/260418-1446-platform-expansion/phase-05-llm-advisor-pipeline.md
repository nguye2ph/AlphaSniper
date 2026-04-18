# Phase 5: LLM Advisor + Pipeline Optimization

## Context Links

- Parent: [plan.md](plan.md)
- Depends on: [Phase 1 - Adaptive Scheduling](phase-01-adaptive-scheduling.md)
- Related: [Phase 2](phase-02-data-sources-tier1.md), [Phase 3](phase-03-data-sources-tier2.md)
- Research: [Adaptive Scheduling](../reports/researcher-260418-1453-adaptive-scheduling-system-design.md)

## Overview

- **Priority:** P2
- **Status:** complete
- **Effort:** ~1 week
- **Description:** Add Gemini LLM as Tier 3 scheduling advisor (hourly). Market calendar awareness. Cross-source dedup via headline similarity. Ticker health score computation combining all data sources.

## Key Insights

- Gemini API already integrated (gemini_parser.py exists), reuse client
- LLM advisor cost: ~$0.001/call, hourly = ~$0.72/month
- Template-based prompts > iterative A/B testing for scheduling
- Cross-source dedup critical with 13 sources (same story from MarketAux + Yahoo RSS)
- Ticker health score = weighted combination of sentiment + insider + short interest + earnings

## Requirements

### Functional

- Gemini LLM advisor: hourly task analyzes metrics, suggests schedule adjustments
- Market calendar awareness: suppress polling during market close/weekends for certain sources
- Cross-source headline dedup: detect duplicate stories across sources
- Ticker health score: composite score per ticker combining all data types
- Data enrichment pipeline: aggregate per-ticker data for quick queries

### Non-Functional

- LLM calls batched (all sources in single prompt, not per-source)
- Dedup latency < 100ms per article (lightweight similarity check)
- Health score computation < 1s per ticker
- Graceful fallback if Gemini API fails

## Architecture

```
Hourly Adjustment Task
  ├── Phase 1 Rule Engine (EMA thresholds) ← always runs
  └── Phase 5 LLM Advisor ← optional enhancement
        │
        ▼
   Gemini API (single batched call)
        │
        ▼
   JSON response: [{source, action, new_interval, confidence, reason}]
        │
        ▼
   Apply only high-confidence (>0.8) recommendations
   Log all recommendations for audit

Market Calendar
  ├── is_market_open() → bool
  ├── is_weekend() → bool
  └── Source config: trading_hours_only flag
      SEC EDGAR: skip weekends
      Finnhub: reduce frequency after hours
      Reddit/StockTwits: always active (retail trades 24/7)

Cross-Source Dedup
  Article arrives → extract URL → normalize → check URL set (Redis)
                 → if URL match → mark duplicate (instant)
                 → else → add to headline batch queue
  Every 5 min → batch LLM call → Gemini evaluates headline groups
             → mark cross-source duplicates

Ticker Health Score
  Per ticker: combine latest data from all sources
  Score = weighted(sentiment, insider_activity, short_squeeze, earnings_proximity)
  Cache in Redis, refresh hourly
```

### LLM Prompt Template

```python
ADVISOR_PROMPT = """
You are a data pipeline scheduler advisor. Analyze these source metrics and
recommend frequency adjustments. Output JSON array.

Sources:
{sources_json}

Rules:
- If articles/hour trending up, consider increasing frequency (lower interval)
- If mostly empty responses, decrease frequency (higher interval)
- Consider time of day: market hours (9:30-16:00 ET) vs after-hours
- Never recommend below min_interval or above max_interval

Output format:
[{"source": "name", "action": "increase|keep|decrease",
  "new_interval": N, "confidence": 0.0-1.0, "reason": "..."}]
"""
```

### Ticker Health Score Formula

```python
health_score = (
    sentiment_weight * avg_sentiment +          # -1 to 1 -> 0-100
    insider_weight * insider_signal +            # recent buys = positive
    squeeze_weight * (100 - squeeze_score) +     # high short = risky
    earnings_weight * earnings_proximity_bonus   # upcoming = attention
) / total_weight

# Weights: sentiment=0.3, insider=0.3, squeeze=0.2, earnings=0.2
```

## Related Code Files

### Files to Create

| File | LOC | Purpose |
|------|-----|---------|
| `src/scheduler/llm-advisor.py` | ~100 | Gemini API scheduling advisor |
| `src/scheduler/market-calendar.py` | ~60 | Market hours + weekend detection |
| `src/parsers/cross-source-dedup.py` | ~80 | Headline similarity dedup |
| `src/parsers/ticker-health-score.py` | ~90 | Composite health score |
| `src/api/routes/ticker-health-routes.py` | ~50 | GET /api/ticker/{symbol}/health |
| `tests/test-scheduler/test-llm-advisor.py` | ~50 | LLM advisor tests |
| `tests/test-parsers/test-cross-dedup.py` | ~50 | Dedup tests |
| `tests/test-parsers/test-health-score.py` | ~50 | Health score tests |

### Files to Modify

| File | Changes |
|------|---------|
| `src/scheduler/adjustment-engine.py` | Integrate LLM advisor as optional step after rules |
| `src/scheduler/models.py` | Add trading_hours_only flag to SourceScheduleConfig |
| `src/jobs/taskiq_app.py` | Add health score refresh task (hourly), dedup in process_raw_articles |
| `src/core/config.py` | Add llm_advisor_enabled, market_calendar_enabled settings |
| `src/api/main.py` | Register health routes |

## Implementation Steps

### LLM Advisor

1. **Create `src/scheduler/llm-advisor.py`**:
   - `get_recommendations(sources_metrics: list[dict]) -> list[Recommendation]`
   - Build prompt from template + current metrics JSON
   - Call Gemini API (reuse existing client pattern from gemini_parser.py)
   - Parse JSON response, validate with Pydantic
   - Filter: only return recommendations with confidence > 0.8
   - Fallback: return empty list if API fails
2. **Modify `src/scheduler/adjustment-engine.py`**:
   - After rule-based evaluation, optionally call LLM advisor
   - LLM can override rule-based only if confidence > 0.8 AND within bounds
   - Log both rule-based and LLM recommendations

### Market Calendar

3. **Create `src/scheduler/market-calendar.py`**:
   - `is_market_open() -> bool` (NYSE hours: 9:30-16:00 ET, Mon-Fri)
   - `is_trading_day(date) -> bool` (exclude weekends + US holidays)
   - `get_market_phase() -> Literal["pre_market", "market_open", "after_hours", "closed"]`
4. **Modify `src/scheduler/models.py`**:
   - Add `trading_hours_only: bool = False` to SourceScheduleConfig
5. **Integrate in adjustment engine**:
   - If trading_hours_only=True AND market closed -> set interval to max_interval
   - If market opens -> restore to current_interval

### Cross-Source Dedup
<!-- Updated: Validation Session 1 - Changed from Jaccard to URL + LLM evaluation -->

6. **Create `src/parsers/cross-source-dedup.py`**:
   - `is_duplicate_headline(headline: str, url: str, source: str) -> bool`
   - **Layer 1 (URL dedup):** Redis SET `dedup:urls` — normalize URL (strip query params, trailing slash), check exact match. Catches ~70% of cross-source duplicates.
   - **Layer 2 (LLM evaluation):** For articles not caught by URL dedup, batch recent headlines (last 2h window) and ask Gemini to identify duplicates. News headlines are structured enough for reliable LLM judgment.
   - Gemini prompt: "Given these headlines, identify groups that cover the same news story. Return JSON array of duplicate groups."
   - Batch LLM calls (every 5 min, not per-article) to minimize cost
   - TTL: 48 hours for URL set, 2 hours for headline batch window
7. **Integrate in `process_raw_articles`**:
   - After source-level dedup, run URL dedup (instant)
   - LLM dedup runs as separate batch task (not inline)
   - If cross-source duplicate: still save to PG but mark `is_cross_dupe=True`

### Ticker Health Score

8. **Create `src/parsers/ticker-health-score.py`**:
   - `compute_health_score(ticker: str, session: AsyncSession) -> TickerHealth`
   - Query last 24h: articles sentiment, insider trades, short interest, earnings
   - Compute weighted score (0-100)
   - Return TickerHealth: score, breakdown dict, signals list
9. **Add hourly task** in taskiq_app.py:
   - Compute health scores for all watchlist tickers
   - Cache results in Redis (key: `ticker:health:{symbol}`, TTL: 1h)
10. **Create API endpoint**: GET /api/ticker/{symbol}/health

## Todo List

- [ ] Create LLM advisor module
- [ ] Create market calendar module
- [ ] Add trading_hours_only to scheduler config
- [ ] Integrate LLM advisor in adjustment engine
- [ ] Integrate market calendar in adjustment engine
- [ ] Create cross-source dedup module
- [ ] Integrate cross-source dedup in process_raw_articles
- [ ] Create ticker health score module
- [ ] Add hourly health score refresh task
- [ ] Create health score API endpoint
- [ ] Add settings: llm_advisor_enabled, market_calendar_enabled
- [ ] Write tests for all new modules

## Test Cases

### Happy Path

- LLM advisor receives metrics -> returns valid JSON recommendations
- Market calendar: Monday 10:00 AM ET -> is_market_open() = True
- Market calendar: Saturday -> is_trading_day() = False
- Cross-source dedup: same URL from MarketAux + Yahoo RSS -> URL dedup catches instantly
- Cross-source dedup: different URLs but same story -> LLM batch identifies as duplicate group
- Health score: ticker with bullish sentiment + insider buys + low short = high score (80+)

### Edge Cases

- LLM returns low-confidence recommendations (0.3) -> all filtered out
- Market holiday (MLK Day) -> treated as closed
- Headlines similar but different tickers -> NOT marked duplicate
- Ticker with only 1 data source -> health score still computes (missing data = neutral)
- Empty metrics (new source, no data yet) -> LLM says "keep"

### Error Scenarios

- Gemini API timeout -> fallback to rule-based only, log warning
- Gemini returns malformed JSON -> parse error caught, skip LLM this cycle
- Redis connection lost during dedup -> skip dedup check, allow article through
- Health score query returns no data -> return score=50 (neutral default)

## Verification Steps

### Manual

1. Enable LLM advisor in .env, run adjustment task, check logs for recommendations
2. Verify market calendar: run during market hours vs after hours
3. Insert same headline from 2 sources -> verify cross-source dedup catches it
4. Hit GET /api/ticker/TSLA/health -> verify score and breakdown

### Automated

```bash
uv run pytest tests/test-scheduler/test-llm-advisor.py -v
uv run pytest tests/test-parsers/test-cross-dedup.py -v
uv run pytest tests/test-parsers/test-health-score.py -v
```

## Acceptance Criteria

- [ ] LLM advisor runs hourly, provides recommendations (when enabled)
- [ ] Market calendar suppresses polling during weekends/holidays
- [ ] Cross-source dedup detects duplicate headlines with >85% similarity
- [ ] Ticker health score computes and caches for watchlist tickers
- [ ] API endpoint returns health score with breakdown
- [ ] All features gracefully degraded when disabled or API fails
- [ ] Tests pass

## Success Criteria

- LLM advisor provides at least 1 useful scheduling adjustment per day
- Cross-source dedup eliminates >20% duplicate articles
- Health score provides quick at-a-glance ticker assessment

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Gemini API cost creep | Low | Batch all sources in 1 call; hourly not per-minute |
| LLM hallucinated intervals | Medium | Validate against min/max bounds; confidence filter |
| Jaccard similarity too coarse | Medium | Upgrade to TF-IDF or LLM embeddings if needed |
| Health score weights wrong | Low | Configurable weights; tune with real data |
| Market calendar timezone bugs | Medium | Use pytz/zoneinfo; test ET edge cases |

## Security Considerations

- Gemini API key already in .env (reuse existing)
- No user data sent to LLM (only aggregate metrics)
- Health score cache in Redis (no PII)
- LLM responses validated before applying any changes

## Next Steps

- Phase 6 visualizes health scores on dashboard
- Future: replace Jaccard with embedding-based similarity
- Future: LLM advisor learns from historical accuracy
