# Brainstorm: AlphaSniper Platform Expansion

**Date:** 2026-04-18
**Context:** Expand data sources, redesign UI, add adaptive scheduling, optimize pipeline
**Current State:** 6 collectors, full pipeline, Next.js webapp, Docker stack - all working

---

## Problem Statement

AlphaSniper MVP complete with 6 data sources (Finnhub, MarketAux, SEC EDGAR, TickerTick, Discord, content scraper). Need to:
1. **Expand data coverage** - add unique data types (social sentiment, insider trades, options flow, earnings, short interest)
2. **Redesign UI** - professional trading terminal via Google Stitch + Figma → Next.js
3. **Adaptive scheduling** - dynamic job frequency based on source activity + LLM advisor
4. **Pipeline optimization** - handle 10+ sources efficiently, prepare data for future algo

---

## Evaluated Approaches

### A. Data Source Expansion

**Research identified 15+ viable free sources across 8 categories:**

| Priority | Source | Category | Unique Data | Free Limit | Effort |
|----------|--------|----------|-------------|------------|--------|
| **T1** | Reddit PRAW | Social | WSB/r/stocks sentiment | 60 req/min | Low |
| **T1** | OpenInsider | Insider | Form 4 parsed trades | 5-10 req/min | Med |
| **T1** | API Ninjas | Earnings | Calendar + EPS estimates | 1,700/day | Low |
| **T1** | RSS Feeds | News | Yahoo/CNBC/SeekingAlpha | Unlimited | Low |
| **T2** | StockTwits | Social | Bullish/bearish sentiment | 100/min | Low |
| **T2** | Unusual Whales | Options | Options flow, dark pool | 100-500/day | Med |
| **T2** | ORTEX | Short | Short %, squeeze score | ~100/day | Low |
| **T3** | ApeWisdom | Social | Reddit+4chan aggregation | ~100/day | Low |
| **T3** | PyTrends | Alt | Google search trends | 10/min | Low |
| **T3** | CoinGecko | Macro | Crypto risk sentiment | 50/min | Low |

**Key Insight:** Social sentiment (Reddit/StockTwits) + Insider trading (OpenInsider) = highest unique value. Options flow + short interest = high value but rate-limited free tiers.

**Dedup Strategy:** Each new source needs unique `source:source_id` format. Redis SET already handles this. Cross-source dedup (same article from MarketAux AND Yahoo RSS) needs headline similarity check or URL dedup.

### B. UI Redesign via Google Stitch

**Google Stitch** (stitch.withgoogle.com) = free AI design tool, 350 gen/month.

**Recommended Workflow:**
```
Stitch (design exploration) → Figma (design system) → v0.dev or manual (React) → Next.js
```

**Why Stitch + v0 combo:**
- Stitch = design-first (visual quality, dark mode toggle, Figma export)
- v0.dev = code-first (production React, shadcn/ui, Tailwind)
- Use both: Stitch for exploring designs → v0 for converting to React

**Output:** Professional trading terminal with dark theme (slate-900 + teal accents), components: ticker header, news feed cards, watchlist table, portfolio KPIs, alert panel.

**Timeline:** ~2 weeks (1wk design + 1wk implementation)

### C. Adaptive Job Scheduling

**3-Tier Architecture:**

1. **Tier 1 - Config Store (Redis JSON)**
   - Per-source: `min_interval`, `max_interval`, `current_interval`, `enabled`
   - Admin API: GET/POST `/admin/sources/{name}/config`
   - Manual override always available

2. **Tier 2 - Metrics-Based Auto-Tuning (EMA)**
   - Track articles/hour per source via Exponential Moving Average
   - Rules: high volume → decrease interval (poll faster); low volume → increase interval
   - Circuit breaker: 5x rate-limit errors → immediate 2x backoff
   - Cooldown: no adjustment more than once per 5 min

3. **Tier 3 - LLM Advisor (optional, hourly)**
   - Gemini API analyzes volume patterns + suggests optimal frequencies
   - Template-based prompts, ~$0.001/call
   - Only override rules when LLM has high confidence

**Key Finding:** Taskiq supports dynamic schedule changes at runtime via `ListRedisScheduleSource`. No restart needed.

**Implementation:** ~300 LOC across 4 modules (config-manager, metrics-tracker, adjustment-engine, scheduler-integration).

---

## Recommended Solution: Phased Implementation

### Phase 1: Adaptive Scheduling Infrastructure (Week 1-2)
**Why first:** Foundation for all future source additions. Build once, use for every new collector.

- Redis config schema + Pydantic models
- Admin API endpoints for source config CRUD
- Metrics collection (articles/hour, empty responses, errors)
- EMA-based auto-tuning with safety bounds
- Migrate existing 6 sources to new config system
- Dashboard metrics endpoint

### Phase 2: Data Source Expansion - Tier 1 (Week 2-3)
**4 new unique data types, all free:**

- **Reddit PRAW collector** - r/wallstreetbets, r/stocks sentiment
  - New MongoDB doc type: `RawSocialPost`
  - Parser: ticker extraction + VADER/TextBlob sentiment
  - Schedule: every 5 min (configurable)

- **OpenInsider collector** - Form 4 insider trades
  - BeautifulSoup scraper → structured insider trade data
  - New PostgreSQL model: `InsiderTrade` (officer, shares, price, date)
  - Schedule: every 10 min

- **Earnings Calendar collector** - API Ninjas
  - REST API → upcoming earnings dates + EPS estimates
  - New PostgreSQL model: `EarningsEvent`
  - Schedule: every 6 hours (data doesn't change fast)

- **RSS Feed collector** - Yahoo Finance, CNBC, Seeking Alpha
  - feedparser library → news articles
  - Dedup via URL against existing articles
  - Schedule: every 5 min

### Phase 3: Data Source Expansion - Tier 2 (Week 3-4)

- **StockTwits collector** - real-time bullish/bearish
- **ORTEX short interest** - daily short %, squeeze score
- **Unusual Whales** - options flow (if free tier sufficient)

### Phase 4: Google Stitch UI Redesign (Week 4-6)

- Design exploration in Stitch (3-5 dashboard variants)
- Component design: ticker, news card, watchlist, portfolio, alerts
- Export → Figma design system
- Convert to React via v0.dev or manual refactor
- Wire real data (existing FastAPI + new data types)
- Dark mode + accessibility audit

### Phase 5: LLM Advisor + Pipeline Optimization (Week 6-7)

- Gemini API integration for scheduling advice
- Market calendar awareness (no SEC polling on weekends)
- Cross-source dedup optimization (headline similarity)
- Data enrichment pipeline (combine sentiment + insider + earnings per ticker)
- Aggregate "ticker health score" endpoint

### Phase 6: Visualization & Analytics (Week 7-8)

- New dashboard pages: Insider Trades, Options Flow, Earnings Calendar
- Ticker detail page: combined view (news + sentiment + insider + short interest)
- Sentiment heatmap (by sector, by time)
- Alert rules engine (e.g., "insider buy > $1M AND sentiment bullish → notify")

---

## Implementation Considerations

### New Database Models (PostgreSQL)

```python
# Insider trades
class InsiderTrade(Base):
    ticker: str
    officer_name: str
    officer_title: str
    transaction_type: str  # "buy" | "sell" | "exercise"
    shares: int
    price: float
    value: float
    filing_date: datetime
    source: str  # "openinsider" | "sec_edgar_form4"

# Earnings events
class EarningsEvent(Base):
    ticker: str
    report_date: datetime
    estimated_eps: float | None
    actual_eps: float | None
    estimated_revenue: float | None
    actual_revenue: float | None
    surprise_pct: float | None

# Social sentiment
class SocialSentiment(Base):
    ticker: str
    platform: str  # "reddit" | "stocktwits"
    mentions_count: int
    sentiment_score: float  # -1.0 to 1.0
    bullish_pct: float
    period_start: datetime
    period_end: datetime

# Short interest
class ShortInterest(Base):
    ticker: str
    short_pct_float: float
    days_to_cover: float
    borrow_fee_pct: float
    squeeze_score: int  # 0-100
    report_date: datetime
```

### New MongoDB Documents

```python
class RawSocialPost(Document):
    source: str  # "reddit" | "stocktwits"
    source_id: str
    payload: dict
    collected_at: datetime
    is_processed: bool = False

class RawInsiderTrade(Document):
    source: str  # "openinsider"
    source_id: str
    payload: dict
    collected_at: datetime
    is_processed: bool = False
```

### API Extensions

```
GET /api/insider-trades?ticker=AAPL&days=30
GET /api/earnings?upcoming=true&days=14
GET /api/sentiment/social?ticker=AAPL&platform=reddit
GET /api/short-interest?ticker=AAPL
GET /api/ticker/{symbol}/overview  # Combined: news + sentiment + insider + short
GET /admin/scheduler/sources  # Config CRUD
GET /admin/scheduler/metrics  # Real-time metrics
```

### Dependencies to Add

```toml
# pyproject.toml additions
praw = "^7.0"           # Reddit API
feedparser = "^6.0"     # RSS parsing
vaderSentiment = "^3.3"  # Sentiment analysis (lightweight)
```

---

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Reddit API rate limit changes | Medium | Monitor PRAW changelog, have StockTwits as backup |
| OpenInsider ToS changes | Medium | Fallback to direct SEC EDGAR Form 4 parsing |
| Stitch React export not ready | Low | Manual refactor HTML→React, or use v0.dev |
| Too many sources → dedup complexity | High | URL-based dedup + headline cosine similarity |
| Adaptive scheduling thrashing | Medium | Wide thresholds + 5min cooldown + circuit breaker |
| Free tier quotas exhausted | Medium | Track usage per source, alert at 80% quota |

---

## Success Metrics

- [ ] 10+ data sources active with zero duplicate articles
- [ ] Adaptive scheduling reduces empty API calls by >30%
- [ ] New UI achieves "professional trading terminal" look
- [ ] Ticker overview page shows combined data from 5+ sources
- [ ] End-to-end latency (source publish → dashboard) < 5 min
- [ ] All free tier quotas respected (zero rate limit errors)

---

## Unresolved Questions

1. **Reddit API pricing changes?** - Reddit tightened API access in 2023. PRAW still works for read-only, but monitor for changes.
2. **OpenInsider scraping legality?** - Public website but no explicit API permission. Consider sec-api.io ($9/mo) as safe alternative.
3. **Unusual Whales free tier sufficiency?** - Need to test: is 100-500 req/day enough for meaningful options flow data?
4. **Cross-source dedup at scale** - With 10+ sources, need benchmark headline similarity approach (TF-IDF? Jaccard? LLM embeddings?)
5. **Stitch Tailwind version** - Does Stitch export Tailwind v3 or v4? Need to verify compatibility with current Next.js setup.
6. **Market hours scheduling** - Should collectors stop during market close? Or continue for after-hours news?
7. **Data retention policy** - How long to keep raw MongoDB docs? Currently no TTL. Need cleanup strategy.

---

## Research Reports

1. **Data Sources:** `plans/reports/researcher-260418-1452-free-stock-data-sources-research.md`
2. **Adaptive Scheduling:** `plans/reports/researcher-260418-1453-adaptive-scheduling-system-design.md`
3. **Google Stitch:** `plans/reports/researcher-260418-1453-google-stitch-research.md`
