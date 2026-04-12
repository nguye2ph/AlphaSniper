# Phase 5: Dedup + Taskiq Pipeline

## Overview
- **Priority**: High
- **Status**: pending
- **Description**: Build the processing pipeline: dedup raw articles, enqueue parsing tasks via Taskiq, move parsed data from MongoDB to PostgreSQL.

## Key Insights
- Dedup: Redis SET with key `dedup:{source}:{source_id}`, TTL 7 days
- Taskiq: async-native, 10x Celery perf, Redis broker
- Pipeline: Raw MongoDB → Dedup check → Parse headline → Insert PostgreSQL
- Taskiq scheduler (beat) handles cron-based polling triggers

## Related Code Files
- **Create**: `src/parsers/dedup.py` (Redis-based deduplication)
- **Create**: `src/parsers/headline-parser.py` (rule-based ticker + sentiment extraction)
- **Create**: `src/jobs/taskiq-app.py` (broker config)
- **Create**: `src/jobs/collect-news-tasks.py` (scheduled collection triggers)
- **Create**: `src/jobs/parse-article-tasks.py` (process raw → clean)
- **Create**: `src/jobs/cleanup-tasks.py` (data retention)

## Implementation Steps

1. Setup Taskiq broker in `taskiq-app.py`:
   - Redis broker, concurrency=8
   - Scheduled tasks config (cron expressions)
2. Create dedup module in `dedup.py`:
   - `is_duplicate(source, source_id) -> bool` (check Redis SET)
   - `mark_seen(source, source_id)` (add to Redis SET, TTL 7d)
3. Create headline parser in `headline-parser.py`:
   - Rule-based: regex extract $TICKER patterns
   - Keyword sentiment: positive/negative word lists
   - Output: `ParsedArticle` Pydantic model
4. Create collection tasks in `collect-news-tasks.py`:
   - `poll_marketaux` — every 15 min
   - `poll_sec_edgar` — every 10 min
   - `poll_finnhub_rest` — every 5 min (supplement WebSocket)
5. Create parsing task in `parse-article-tasks.py`:
   - `process_raw_article(raw_id)` — fetch from MongoDB, dedup, parse, insert PostgreSQL
   - `process_batch()` — find unprocessed raw articles, process each
6. Create cleanup task in `cleanup-tasks.py`:
   - Mark old raw articles as archived (30 days)
   - Clear Redis dedup keys older than TTL

## Data Flow
```
Collector saves to MongoDB (raw)
    ↓
Taskiq picks up unprocessed documents
    ↓
Dedup check (Redis SET)
    ↓ (if new)
Headline parser extracts ticker, sentiment
    ↓
Insert into PostgreSQL (clean)
    ↓
Mark MongoDB document as processed
```

## Todo List
- [ ] Taskiq broker config
- [ ] Redis dedup module
- [ ] Rule-based headline parser
- [ ] Scheduled collection tasks (cron)
- [ ] Article processing task (raw → clean)
- [ ] Batch processor for backfill
- [ ] Cleanup/archival task
- [ ] Worker Docker entrypoint

## Test Cases
- Dedup: same (source, source_id) returns True on second check
- Dedup: different source_id returns False
- Parser: "$AAPL surges on earnings" → ticker=["AAPL"], sentiment="bullish"
- Parser: "CEO of XYZ Corp resigns" → ticker=["XYZ"], sentiment="bearish"
- Task: raw article processed → appears in PostgreSQL
- Task: duplicate raw article skipped → not in PostgreSQL
- Scheduler: tasks fire at configured intervals

## Acceptance Criteria
- [ ] Taskiq workers process raw articles into clean PostgreSQL records
- [ ] Dedup prevents duplicate articles (same source+id)
- [ ] Headline parser extracts tickers with >80% accuracy (rule-based)
- [ ] Scheduled tasks fire on configured cron intervals
- [ ] Worker runs as Docker service, processes queue continuously

## Next Steps
- Phase 6: FastAPI endpoints to query clean data
- Phase 7: Replace rule-based parser with Gemini AI
