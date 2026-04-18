# Phase 2: Data Sources Tier 1 (High ROI, Free)

## Context Links

- Parent: [plan.md](plan.md)
- Depends on: [Phase 1 - Adaptive Scheduling](phase-01-adaptive-scheduling.md)
- Research: [Free Data Sources](../reports/researcher-260418-1452-free-stock-data-sources-research.md)

## Overview

- **Priority:** P1
- **Status:** complete
- **Effort:** ~1.5 weeks
- **Description:** Add 4 new collectors (Reddit, OpenInsider, Earnings Calendar, RSS Feeds), 3 new PostgreSQL models, 2 new parsers. All free-tier sources providing unique data types not in existing pipeline.

## Key Insights

- Reddit PRAW: 60 req/min free, excellent small-cap WSB coverage
- OpenInsider: no API, BeautifulSoup scraper, insider buys/sells signal before news
- API Ninjas Earnings: 1,700 req/day free, simple REST
- RSS feeds: unlimited, zero auth, multiple finance outlets
- Each adds unique data type: social sentiment, insider trades, earnings, supplementary news

## Requirements

### Functional

- 4 new collectors following BaseCollector pattern
- 3 new PostgreSQL models: InsiderTrade, EarningsEvent, SocialSentiment
- 2 new parsers: social-sentiment-parser, insider-trade-parser
- Extend process_raw_articles for new source types
- Register all 4 in adaptive scheduler config (Phase 1)
- New API endpoints for each data type

### Non-Functional

- All async operations
- Pydantic validation on all inputs
- structlog logging with source context
- tenacity retries on HTTP failures
- Rate limit compliance per source

## Architecture

```
Reddit API (PRAW)  ──────► reddit-praw.py ──► MongoDB (RawSocialPost)
OpenInsider (HTML) ──────► openinsider-scraper.py ──► MongoDB (RawInsiderTrade)
API Ninjas (REST)  ──────► earnings-calendar.py ──► MongoDB (RawArticle)
Yahoo/CNBC RSS     ──────► rss-feeds.py ──► MongoDB (RawArticle)
                                                     │
                                         ┌───────────▼───────────┐
                                         │ process_raw_articles  │
                                         │ (extended for new     │
                                         │  source types)        │
                                         └───────────┬───────────┘
                                                     │
                              ┌───────────┬──────────┼──────────┐
                              ▼           ▼          ▼          ▼
                         InsiderTrade  EarningsEvent  SocialSentiment  Article
                         (PostgreSQL)  (PostgreSQL)   (PostgreSQL)    (existing)
```

### New MongoDB Documents

```python
# Can reuse RawArticle for RSS/Earnings (same shape: source, source_id, payload)
# Need new docs for structurally different data:

class RawSocialPost(Document):  # src/core/models/raw-social-post.py
    source: Indexed(str)  # "reddit" | "stocktwits"
    source_id: str
    payload: dict
    collected_at: datetime
    is_processed: bool = False

class RawInsiderTrade(Document):  # src/core/models/raw-insider-trade.py
    source: Indexed(str)  # "openinsider"
    source_id: str
    payload: dict
    collected_at: datetime
    is_processed: bool = False
```

### New PostgreSQL Models

```python
class InsiderTrade(Base):  # src/core/models/insider-trade.py
    id: UUID
    ticker: str
    officer_name: str
    officer_title: str
    transaction_type: str  # "buy" | "sell" | "exercise"
    shares: int
    price: float
    value: float
    filing_date: datetime
    source: str  # "openinsider"
    source_id: str
    raw_data: dict | None  # JSONB

class EarningsEvent(Base):  # src/core/models/earnings-event.py
    id: UUID
    ticker: str
    report_date: datetime
    estimated_eps: float | None
    actual_eps: float | None
    estimated_revenue: float | None
    actual_revenue: float | None
    surprise_pct: float | None
    source: str
    source_id: str

class SocialSentiment(Base):  # src/core/models/social-sentiment.py
    id: UUID
    ticker: str
    platform: str  # "reddit" | "stocktwits"
    post_title: str
    post_score: int
    mentions_count: int
    sentiment_score: float  # -1.0 to 1.0
    sentiment_label: str
    period_start: datetime
    period_end: datetime
    source_id: str
    raw_data: dict | None  # JSONB
```

## Related Code Files

### Files to Create

| File | LOC | Purpose |
|------|-----|---------|
| `src/collectors/reddit-praw.py` | ~120 | Reddit collector (r/wallstreetbets, r/stocks) |
| `src/collectors/openinsider-scraper.py` | ~140 | OpenInsider HTML scraper |
| `src/collectors/earnings-calendar.py` | ~90 | API Ninjas earnings REST |
| `src/collectors/rss-feeds.py` | ~110 | Yahoo/CNBC/SeekingAlpha RSS |
| `src/core/models/raw-social-post.py` | ~25 | MongoDB doc for social posts |
| `src/core/models/raw-insider-trade.py` | ~25 | MongoDB doc for insider trades |
| `src/core/models/insider-trade.py` | ~50 | PostgreSQL insider trade model |
| `src/core/models/earnings-event.py` | ~40 | PostgreSQL earnings model |
| `src/core/models/social-sentiment.py` | ~45 | PostgreSQL social sentiment model |
| `src/parsers/social-sentiment-parser.py` | ~80 | VADER sentiment + ticker extraction |
| `src/parsers/insider-trade-parser.py` | ~70 | Parse OpenInsider HTML to structured data |
| `src/api/routes/insider-trades-routes.py` | ~60 | GET /api/insider-trades |
| `src/api/routes/earnings-routes.py` | ~50 | GET /api/earnings |
| `src/api/routes/sentiment-routes.py` | ~60 | GET /api/sentiment/social |
| `tests/test-collectors/test-reddit-praw.py` | ~50 | Reddit collector tests |
| `tests/test-collectors/test-openinsider.py` | ~50 | OpenInsider tests |
| `tests/test-collectors/test-earnings.py` | ~40 | Earnings tests |
| `tests/test-collectors/test-rss-feeds.py` | ~40 | RSS tests |

### Files to Modify

| File | Changes |
|------|---------|
| `src/core/config.py` | Add reddit_client_id, reddit_client_secret, api_ninjas_key, rss_feed_urls |
| `src/core/models/__init__.py` | Export new models |
| `src/core/database.py` | Register new Beanie docs in init_mongo() |
| `src/jobs/taskiq_app.py` | Add 4 new collector tasks + extend process_raw_articles |
| `src/api/main.py` | Register 3 new routers |
| `pyproject.toml` | Add praw, feedparser, vaderSentiment deps |
| `migrations/` | New Alembic migration for 3 new tables |

## Implementation Steps

### Collector 1: Reddit PRAW (~120 LOC)

1. Add `praw` to pyproject.toml
2. Add `reddit_client_id`, `reddit_client_secret` to Settings
3. Create `src/collectors/reddit-praw.py`:
   - Extend BaseCollector, source_name = "reddit"
   - `collect()`: poll r/wallstreetbets + r/stocks new posts (limit=50)
   - Extract tickers via regex `\b[A-Z]{1,5}\b` (filter common words: I, A, THE, etc.)
   - Save each post as RawSocialPost with payload: title, body, score, author, subreddit, created_utc
   - Use PRAW read-only mode (no auth required for public posts)
4. Create `src/parsers/social-sentiment-parser.py`:
   - VADER sentiment on title + body
   - Ticker extraction + normalization
   - Map to SocialSentiment PostgreSQL model
5. Register in scheduler config (default interval: 300s / 5 min)

### Collector 2: OpenInsider Scraper (~140 LOC)

1. Create `src/collectors/openinsider-scraper.py`:
   - Extend BaseCollector, source_name = "openinsider"
   - `collect()`: GET http://openinsider.com/screener with params (min_value, etc.)
   - Parse HTML table with BeautifulSoup
   - Extract: filing_date, ticker, officer, title, trade_type, price, shares, value
   - Save as RawInsiderTrade, source_id = f"{ticker}_{filing_date}_{officer}"
2. Create `src/parsers/insider-trade-parser.py`:
   - Parse raw payload -> InsiderTrade PostgreSQL model
   - Normalize transaction_type: "P - Purchase" -> "buy", "S - Sale" -> "sell"
3. Register in scheduler config (default interval: 600s / 10 min)

### Collector 3: Earnings Calendar (~90 LOC)

1. Add `api_ninjas_key` to Settings
2. Create `src/collectors/earnings-calendar.py`:
   - Extend BaseCollector, source_name = "earnings_calendar"
   - `collect()`: GET https://api.api-ninjas.com/v1/earningscalendar
   - Query for watchlist tickers + upcoming dates
   - Save as RawArticle (reuse existing doc), source_id = f"{ticker}_{report_date}"
3. Extend process_raw_articles to handle source="earnings_calendar" -> EarningsEvent
4. Register in scheduler config (default interval: 21600s / 6 hours)

### Collector 4: RSS Feeds (~110 LOC)

1. Add `feedparser` to pyproject.toml
2. Add `rss_feed_urls: list[str]` to Settings with defaults
3. Create `src/collectors/rss-feeds.py`:
   - Extend BaseCollector, source_name = "rss_feeds"
   - `collect()`: parse multiple RSS feeds (Yahoo Finance, CNBC, Seeking Alpha)
   - Dedup via URL (source_id = url hash)
   - Save as RawArticle with payload: title, link, summary, published, source_feed
4. RSS articles go through existing Article pipeline (headline parser)
5. Register in scheduler config (default interval: 300s / 5 min)

### Database & API Steps

6. Create 2 new MongoDB documents (RawSocialPost, RawInsiderTrade)
7. Register in `init_mongo()` Beanie init
8. Create 3 new PostgreSQL models (InsiderTrade, EarningsEvent, SocialSentiment)
9. Generate Alembic migration: `uv run alembic revision --autogenerate -m "add insider earnings sentiment tables"`
10. Run migration: `uv run alembic upgrade head`
11. Create API routes for each new data type
12. Register routers in main.py
13. Extend `process_raw_articles` in taskiq_app.py:
    - Add handlers for source="reddit", "openinsider", "earnings_calendar", "rss_feeds"
    - Reddit/StockTwits -> social-sentiment-parser -> SocialSentiment
    - OpenInsider -> insider-trade-parser -> InsiderTrade
    - Earnings -> direct mapping -> EarningsEvent
    - RSS -> existing headline-parser -> Article

### Dependencies

14. Update pyproject.toml: add praw, feedparser, vaderSentiment, beautifulsoup4 (if not present)
15. Run `uv sync --all-extras`

## Todo List

- [ ] Add praw, feedparser, vaderSentiment to pyproject.toml
- [ ] Add Reddit + API Ninjas config to Settings
- [ ] Create RawSocialPost MongoDB document
- [ ] Create RawInsiderTrade MongoDB document
- [ ] Register new Beanie docs in init_mongo()
- [ ] Create InsiderTrade PostgreSQL model
- [ ] Create EarningsEvent PostgreSQL model
- [ ] Create SocialSentiment PostgreSQL model
- [ ] Run Alembic migration
- [ ] Implement reddit-praw collector
- [ ] Implement openinsider-scraper collector
- [ ] Implement earnings-calendar collector
- [ ] Implement rss-feeds collector
- [ ] Implement social-sentiment-parser
- [ ] Implement insider-trade-parser
- [ ] Extend process_raw_articles for new sources
- [ ] Create insider-trades API routes
- [ ] Create earnings API routes
- [ ] Create sentiment API routes
- [ ] Register scheduler configs for 4 new sources
- [ ] Write tests for each collector
- [ ] Integration test: full pipeline for each source

## Test Cases

### Happy Path

- Reddit: poll r/wallstreetbets -> extract posts with tickers -> save RawSocialPost -> parse sentiment -> SocialSentiment in PG
- OpenInsider: scrape latest trades -> save RawInsiderTrade -> parse -> InsiderTrade in PG
- Earnings: fetch AAPL earnings -> save RawArticle -> parse -> EarningsEvent in PG
- RSS: fetch Yahoo Finance feed -> save RawArticle -> dedup by URL -> Article in PG
- API: GET /api/insider-trades?ticker=AAPL returns recent insider trades

### Edge Cases

- Reddit post with no ticker mentions -> skip (don't save to PG)
- OpenInsider returns empty table (weekend) -> log, no error
- Duplicate RSS article (same URL) -> dedup catches it
- API Ninjas returns no earnings for ticker -> empty response, no error
- Ticker "I" or "A" from Reddit -> filtered by common-word exclusion list

### Error Scenarios

- Reddit API rate limited (429) -> tenacity retry with backoff
- OpenInsider site down -> timeout, log error, metrics-tracker records failure
- API Ninjas key invalid -> 401, log error, don't crash
- feedparser malformed XML -> skip entry, continue with others
- VADER fails on non-English text -> default sentiment 0.0

## Verification Steps

### Manual

1. Set Reddit API credentials in .env, run reddit-praw collector manually
2. Check MongoDB for RawSocialPost documents
3. Run process_raw_articles, check SocialSentiment in PostgreSQL
4. Hit GET /api/sentiment/social?ticker=TSLA -> returns results
5. Same flow for OpenInsider, Earnings, RSS

### Automated

```bash
uv run pytest tests/test-collectors/test-reddit-praw.py -v
uv run pytest tests/test-collectors/test-openinsider.py -v
uv run pytest tests/test-collectors/test-earnings.py -v
uv run pytest tests/test-collectors/test-rss-feeds.py -v
uv run alembic upgrade head  # Verify migration
```

## Acceptance Criteria

- [ ] 4 new collectors implemented and tested
- [ ] 3 new PostgreSQL tables created via Alembic
- [ ] process_raw_articles handles all 4 new source types
- [ ] API endpoints return data for each new type
- [ ] All sources registered in adaptive scheduler (Phase 1)
- [ ] Dedup works across sources (no duplicate insider trades, etc.)
- [ ] Rate limits respected (verified via logs)
- [ ] All tests pass

## Success Criteria

- 10 total data sources active (6 existing + 4 new)
- Unique data types available: social sentiment, insider trades, earnings calendar
- RSS supplements existing news with zero duplicate articles

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Reddit API access revoked | High | StockTwits (Phase 3) as backup; ApeWisdom API fallback |
| OpenInsider ToS violation | Medium | Switch to SEC EDGAR Form 4 direct parsing |
| VADER sentiment inaccuracy | Low | Upgrade to FinBERT or Gemini sentiment later |
| feedparser breaking on malformed XML | Low | try/except per entry, skip bad entries |
| BeautifulSoup selector changes | Medium | Monitor OpenInsider HTML; selector tests |

## Security Considerations

- Reddit credentials in .env only (reddit_client_id, reddit_client_secret)
- API Ninjas key in .env only
- OpenInsider scraper uses polite User-Agent
- No user data stored from Reddit (only public post metadata)
- Rate limit compliance prevents IP bans

## Next Steps

- Phase 3 adds StockTwits (reuses SocialSentiment model), ORTEX short interest, Unusual Whales
- Phase 4 UI creates pages for insider trades, earnings, sentiment
