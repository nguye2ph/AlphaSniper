# Research Report: Free Stock News & Market Data Sources for AlphaSniper

**Research Date:** April 18, 2026  
**Research Scope:** Free and freemium APIs for stock news, sentiment, insider trading, options flow, earnings, short interest, and alternative data  
**Target Use Case:** Real-time trading news pipeline for small-cap stocks (market cap < 1B)  
**Existing Sources:** Finnhub, MarketAux, SEC EDGAR, TickerTick, Discord NuntioBot, URL scraper

---

## Executive Summary

Research identified **15+ viable free/freemium data sources** across 8 categories NOT available in your current 6-source integration. Highest-priority additions for small-cap focus:

1. **Reddit/Social Sentiment** - PRAW + ApeWisdom API (stock mentions + sentiment from r/wallstreetbets, r/stocks)
2. **Insider Trading (SEC Form 4)** - Direct EDGAR parsing or sec-api.io + OpenInsider data feed
3. **Options Flow** - Unusual Whales API (real-time unusual options activity) or Barchart free tier
4. **Earnings Calendar** - API Ninjas or Financial Modeling Prep (upcoming earnings + estimates)
5. **Short Interest** - ORTEX public API or ShortSqueeze.com data (short squeeze signals)
6. **Financial RSS Feeds** - CNBC, Yahoo Finance, Seeking Alpha (supplement existing sources)
7. **Alternative Data** - PyTrends (Google search interest), Wikipedia pageviews, patent filing trends

**Key Finding:** Most sources available at free tier with rate limits 50-1000 req/day. Reddit/social & insider trading are unique data not covered by current 6 sources. Options flow API access limited but useful for premium signal detection.

---

## 1. Social Sentiment (Reddit, StockTwits, Twitter/X)

### 1.1 Reddit API - PRAW + Custom Scraping

**Platform:** r/wallstreetbets, r/stocks, r/investing  
**Official Tool:** PRAW (Python Reddit API Wrapper)

| Aspect | Details |
|--------|---------|
| **API Type** | Official Reddit API (OAuth2) |
| **Rate Limits** | 60 requests/minute (standard), unauthenticated reads allowed |
| **Authentication** | Reddit account + API credentials (free, instant) |
| **Data Available** | Post titles, bodies, comments, upvotes, timestamps, author |
| **Real-time Capability** | ~1-5 min latency (polling posts), not push-based |
| **Small-cap Coverage** | Excellent for micro/small-cap (r/wallstreetbets focuses on 0-10B range) |
| **Cost** | **FREE** |
| **Implementation Complexity** | Low (PRAW wrapper handles auth) |

**Key Details:**
- PRAW supports wildcard searches: `submission in subreddit.new(limit=100)` 
- Stock ticker extraction via regex: `[A-Z]{1,4}\b` (filter noise)
- Sentiment analysis doable via VADER or TextBlob
- Historical data: Pushshift API (deprecated Jan 2023, but some mirrors exist)

**Overlap Check:** NEW DATA - Not covered by existing 6 sources  
**Small-cap Signal:** Excellent - WSB focuses on undervalued/volatile small-caps  
**Latency:** 1-5 min (post ingestion), polling-based

**Code Snippet:**
```python
import praw
reddit = praw.Reddit(
    client_id='xxx',
    client_secret='xxx', 
    user_agent='stocksniper/1.0'
)
for submission in reddit.subreddit('wallstreetbets').new(limit=100):
    # Extract tickers, sentiment
    print(submission.title, submission.score)
```

---

### 1.2 ApeWisdom API

**Platform:** Aggregated Reddit + 4chan sentiment

| Aspect | Details |
|--------|---------|
| **API Endpoint** | https://apewisdom.io/api/ |
| **Rate Limits** | Free tier: ~100 req/day (verify in docs) |
| **Data Format** | JSON - ticker mentions, sentiment score, discussion volume |
| **Real-time** | Near real-time (aggregates Reddit/4chan hourly) |
| **Cost** | Freemium (free tier + paid premium) |
| **Small-cap Coverage** | Strong on meme stocks + micro-caps |
| **Overlap** | NEW - Sentiment aggregation not in existing sources |

**Key Metrics:** Mention count, sentiment distribution, trending tickers, community engagement  
**Latency:** 30-60 min aggregation window  
**Implementation:** REST API, straightforward JSON responses

---

### 1.3 StockTwits API

**Platform:** Stock-focused social network

| Aspect | Details |
|--------|---------|
| **Endpoints** | Public symbol stream (unauthenticated) |
| **Rate Limits** | Unauthenticated: ~100 req/min documented |
| **Data Available** | Messages, sentiment (bullish/bearish), user engagement |
| **Authentication** | Optional (public read available) |
| **Real-time** | True real-time (message stream) |
| **Cost** | **FREE** (public read-only endpoints) |
| **Overlap** | NEW - Different sentiment source from Reddit |

**Available via RapidAPI & official endpoints**  
**Small-cap focus:** Moderate (larger audience than Reddit WSB)  
**Latency:** <1 minute

---

## 2. Insider Trading Data (SEC Form 4)

### 2.1 Direct EDGAR Access (SEC EDGAR RSS)

**Data Source:** SEC EDGAR Form 4 filings (you already have RSS, but full API parsing is new)

| Aspect | Details |
|--------|---------|
| **Format** | XML/RSS feeds + REST API |
| **Rate Limits** | 10 req/sec (SEC compliance) |
| **Data** | Officer/insider name, transaction type, shares, price, date |
| **Real-time** | Within 5 min of SEC posting |
| **Cost** | **FREE** |
| **Coverage** | All public companies (but small-caps less frequent filing rate) |
| **Parsing Complexity** | Medium (XBRL + XML parsing required) |

**Current Status:** You have RSS feed. Enhancement = extract structured data from XBRL payload + parse transaction details  
**Latency:** 5-15 min from SEC posting  
**Small-cap Signal Value:** HIGH (insider buys/sells signal confidence before news propagates)

---

### 2.2 OpenInsider (Web Scraping or API)

**Platform:** Real-time insider trading aggregator

| Aspect | Details |
|--------|---------|
| **URL** | http://openinsider.com/ |
| **Data Type** | Form 4 data + analysis (trade type, value, filing date) |
| **Real-time** | Real-time Form 4 scraping from EDGAR |
| **API** | No official API; web scraping required |
| **Rate Limits** | ~5-10 req/min (web scraping) |
| **Cost** | **FREE** (website), alternative APIs exist |
| **Small-cap Coverage** | Excellent (all public companies) |

**Alternatives:**
- **sec-api.io** - Official SEC API wrapper (freemium tier, $9/mo paid)
- **SEC-API.io Insider Trading Endpoint** - Structured Form 3/4/5 parsing
- **InsiderAnalytics.ai** - AI-enriched insider data (free tier available)

**Overlap:** Enhances existing SEC EDGAR with structure + real-time scraping  
**Latency:** <1 min from EDGAR RSS  
**Implementation:** Python `requests` + BeautifulSoup for OpenInsider OR REST API call to sec-api.io

**Code Snippet (OpenInsider scraping):**
```python
import requests
from bs4 import BeautifulSoup

url = "http://openinsider.com/latest-insider-trades"
response = requests.get(url, timeout=10)
soup = BeautifulSoup(response.content, 'html.parser')
# Parse insider trade table
rows = soup.find_all('tr')[1:]  # Skip header
for row in rows:
    cols = row.find_all('td')
    ticker, officer, shares, price, date = [col.text.strip() for col in cols[:5]]
    # Store in MongoDB
```

---

## 3. Options Flow & Unusual Activity

### 3.1 Unusual Whales API

**Platform:** Real-time options flow + dark pool data

| Aspect | Details |
|--------|---------|
| **API URL** | https://unusualwhales.com/public-api |
| **Endpoints** | Options flow, dark pool prints, unusual activity |
| **Rate Limits** | Free tier: 100-500 req/day (check docs) |
| **Data Format** | JSON - contract, volume, premium, OI ratio |
| **Real-time** | True real-time (sub-second for major flows) |
| **Cost** | Freemium (free tier + paid for premium signals) |
| **Small-cap Coverage** | Moderate (primarily liquid contracts) |
| **Overlap** | NEW - Options flow not in existing 6 sources |

**Key Metrics:**
- Unusual volume (spike detection)
- Premium paid / collected
- Open interest change
- Implied move

**Latency:** <100ms  
**Implementation Complexity:** Medium (real-time websocket + REST API)

---

### 3.2 InsiderFinance.io

**Platform:** Unusual options activity detection + dark pool

| Aspect | Details |
|--------|---------|
| **Data** | Real-time options flow, smart money detection |
| **Free Tier** | Limited to 10-20 alerts/day |
| **Rate Limits** | Web scraping or API (check availability) |
| **Cost** | Freemium |
| **Overlap** | NEW - Smart money options detection |

---

### 3.3 Barchart.com - Free Tier

| Aspect | Details |
|--------|---------|
| **URL** | https://www.barchart.com/options/unusual-activity |
| **Data** | Unusual options volume, implied volatility spikes |
| **Format** | Web scraping or API |
| **Cost** | **FREE** (web) |
| **Rate Limits** | N/A for web, API ~100 req/day |

---

## 4. Earnings Data (Calendar, Estimates, Whispers)

### 4.1 API Ninjas - Earnings Calendar

| Aspect | Details |
|--------|---------|
| **API Endpoint** | https://api-ninjas.com/api/earningscalendar |
| **Rate Limits** | Free tier: 50,000 req/month (~1,700 req/day) |
| **Data Available** | Ticker, report date, estimated EPS, estimated revenue |
| **Historical** | Past & upcoming earnings |
| **Cost** | **FREE** (generous rate limit) |
| **Response Format** | JSON array |
| **Small-cap Coverage** | YES (includes OTC, NASDAQ, NYSE) |
| **Overlap** | NEW - Earnings calendar not in existing sources |

**Code Snippet:**
```python
import requests

response = requests.get(
    'https://api.api-ninjas.com/v1/earningscalendar',
    params={'ticker': 'AAPL', 'limit': 10},
    headers={'X-Api-Key': 'YOUR_API_KEY'}
)
earnings = response.json()
# earnings[0] = {"ticker": "AAPL", "reportDate": "2026-05-01", "estimatedEps": 1.23, ...}
```

---

### 4.2 Financial Modeling Prep (FMP) - Earnings Calendar API

| Aspect | Details |
|--------|---------|
| **Endpoint** | `/earnings-calendar-confirmed` |
| **Rate Limits** | Free: 250 req/day |
| **Data** | Confirmed & estimated earnings dates, EPS, revenue |
| **Cost** | **FREE** (generous for free tier) |
| **Auth** | API key required (free signup) |
| **Small-cap** | YES |

---

### 4.3 Earnings Whispers / The Whisper Number

| Aspect | Details |
|--------|---------|
| **Platform** | https://www.earningswhispers.com/ |
| **Data** | Whisper numbers (crowd-sourced EPS estimates) vs official consensus |
| **Format** | Web scraping (no official API) |
| **Cost** | **FREE** (website) |
| **Latency** | Real-time during earnings season |
| **Overlap** | NEW - Crowdsourced earnings estimates |

**Value:** "Whisper numbers" often beat consensus; useful contrarian signal

---

## 5. Short Interest & Float Data

### 5.1 ORTEX - Public API

**Platform:** Professional-grade short interest data

| Aspect | Details |
|--------|---------|
| **URL** | https://public.ortex.com |
| **Data** | Short interest %, days-to-cover, borrow rates, short squeeze score |
| **API** | REST API (public access available) |
| **Rate Limits** | Free: ~100 req/day (verify) |
| **Cost** | Freemium (free public data, premium for real-time) |
| **Update Frequency** | Daily (T+2 settlement standard, but ORTEX faster) |
| **Small-cap Coverage** | Strong |
| **Overlap** | NEW - Short data not in existing sources |

**Key Metrics:**
- Short % of float
- Days to cover
- Borrow fee %
- Squeeze score (0-100)

**Latency:** Daily updates (faster than official FINRA data)  
**Implementation:** REST API, JSON responses

---

### 5.2 ShortSqueeze.com

| Aspect | Details |
|--------|---------|
| **URL** | https://shortsqueeze.com/ |
| **Data** | Short interest by ticker, squeeze alerts, rankings |
| **Format** | Web scraping or API (check availability) |
| **Cost** | **FREE** (website) |
| **Coverage** | 16,000+ stocks (NYSE, NASDAQ, AMEX, OTC) |
| **Update** | Updated multiple times daily |
| **Small-cap** | YES (includes OTC) |

---

### 5.3 Fintel

**Platform:** Professional short interest + technical analysis

| Aspect | Details |
|--------|---------|
| **URL** | https://fintel.io/short-interest-data |
| **Data** | Short %, short volume, short % float, borrow rates |
| **Squeeze Score** | 0-100 quantitative model |
| **API** | Limited API availability (mostly web scraping) |
| **Cost** | Freemium (free web data, API premium) |
| **Small-cap** | YES |

---

## 6. Financial News RSS Feeds

### 6.1 Official Free RSS Feeds

| Source | Feed URL | Coverage | Update Freq | Format |
|--------|----------|----------|------------|--------|
| **Yahoo Finance** | finance.yahoo.com/news/rssindex | General market + breaking news | Real-time | RSS/Atom |
| **CNBC** | cnbc.com/rss-feeds | Business + tech news | Real-time | RSS |
| **Seeking Alpha** | seekingalpha.com/feed | Stock analysis + news | Real-time | RSS |
| **MarketWatch** | marketwatch.com | Market commentary | Real-time | RSS |
| **Reuters** | reuters.com/finance | Global financial news | Real-time | RSS |
| **Bloomberg Markets** | bloomberg.com/markets | Professional market data | Real-time | RSS |

**Overlap:** Supplements existing MarketAux + TickerTick feeds  
**Small-cap Coverage:** Varies (Yahoo/Seeking Alpha best for small-caps)  
**Cost:** **ALL FREE**

**RSS Benefits:**
- No rate limits (standard RSS polling)
- Ticker extraction from headlines
- Supplement to REST APIs
- Multiple streams = redundancy

---

## 7. Alternative Data Sources

### 7.1 Google Trends (PyTrends)

**Platform:** Public Google search interest

| Aspect | Details |
|--------|---------|
| **Tool** | PyTrends (Python library) |
| **Rate Limits** | ~10 req/min (undocumented, use delays) |
| **Data** | Search volume index (0-100), trending up/down |
| **Cost** | **FREE** |
| **Latency** | 24-48 hours (Google Trends is historical) |
| **Use Case** | Macro sentiment, IPO hype, tech trends |
| **Small-cap Signal** | Weak direct signal, useful for macro context |

**Limitations:** Not real-time, does NOT provide ticker volumes  
**Alternative:** Use Apify Google Trends API (paid tier, ~$10/1000 requests)

**Code:**
```python
from pytrends.request import TrendReq
gt = TrendReq(hl='en-US', tz=360)
gt.build_payload(['tesla', 'ethereum'], timeframe='now 1d')
data = gt.interest_over_time()
```

---

### 7.2 Wikipedia Pageview Statistics API

| Aspect | Details |
|--------|---------|
| **Endpoint** | https://pageviews.toolforge.org/api/v2/top |
| **Data** | Hourly pageview counts for Wikipedia articles |
| **Cost** | **FREE** |
| **Use Case** | Detect attention spikes on company/topic articles |
| **Real-time** | Near real-time (hourly aggregation) |
| **Rate Limits** | Unlimited (Wikimedia best-effort) |

**Idea:** Spike in "Tesla" Wikipedia pageviews might correlate with news/trading volume  
**Latency:** 1-2 hours

---

### 7.3 Patent Filing Data

**Sources:**
- **Google Patents** (google.com/patents) - no API, web scraping required
- **USPTO Patent Search** - SOAP API available (complex)
- **AlphaSense** - patent feeds (premium, enterprise-only)

**Free Approach:** Monitor patent filing trends via web scraping USPTO or Google Patents  
**Latency:** 2-3 weeks after filing  
**Small-cap Use:** Useful for biotech/pharma small-caps (FDA approvals, drug patents)

---

### 7.4 GitHub Trending Repositories

**Platform:** Detect tech adoption early (for software/SaaS small-caps)

| Aspect | Details |
|--------|---------|
| **Endpoint** | https://github.com/trending |
| **Format** | Web scraping (no official API) |
| **Cost** | **FREE** |
| **Use Case** | Detect emerging frameworks, libraries, companies |
| **Latency** | Daily |
| **Small-cap Relevance** | HIGH for developer-tools + open-source startups |

**Idea:** Rising GitHub stars for "langchain", "anthropic", "together-ai" = early signal for LLM infra plays  

---

## 8. Crypto/Macro Data (Optional for small-cap correlation)

### 8.1 CoinGecko API

| Aspect | Details |
|--------|---------|
| **Endpoint** | api.coingecko.com/api/v3 |
| **Rate Limits** | 10-50 calls/minute (free) |
| **Data** | Crypto prices, market cap, trading volume, dominance |
| **Cost** | **FREE** |
| **Use Case** | Detect macro risk-on/risk-off sentiment |

**Small-cap Correlation:** Risk sentiment from crypto (BTC dominance, alt season) correlates with small-cap inflows

---

## Summary Table: All Sources

| Category | Source | Free Tier | Rate Limit | Real-time | Unique Data | Implementation | Small-cap |
|----------|--------|-----------|-----------|-----------|-------------|-----------------|-----------|
| **Social** | Reddit PRAW | ✓ | 60 req/min | 1-5 min | Discussions | Low | **Excellent** |
| **Social** | ApeWisdom API | ✓ | ~100/day | 30-60 min | Sentiment agg | Low | **Good** |
| **Social** | StockTwits | ✓ | 100/min | <1 min | Sentiment msgs | Low | **Good** |
| **Insider** | SEC EDGAR (direct) | ✓ | 10/sec | 5 min | Form 4 raw | High | **Good** |
| **Insider** | OpenInsider scrape | ✓ | 5-10/min | <1 min | Parsed Form 4 | Medium | **Good** |
| **Insider** | sec-api.io | ✓/$ | ~100/day | <1 min | API Form 4 | Low | **Good** |
| **Options** | Unusual Whales | ✓/$ | 100-500/day | <100ms | Real-time options | Medium | **Moderate** |
| **Options** | Barchart | ✓ | ~100/day | Real-time | Unusual activity | Medium | **Moderate** |
| **Earnings** | API Ninjas | ✓ | 1,700/day | N/A | Earnings calendar | Low | **Yes** |
| **Earnings** | FMP API | ✓ | 250/day | N/A | Confirmed earnings | Low | **Yes** |
| **Earnings** | Whispers web | ✓ | N/A | Real-time | Whisper numbers | Medium | **Moderate** |
| **Short** | ORTEX | ✓/$ | ~100/day | Daily | Short %, days-cover | Low | **Yes** |
| **Short** | ShortSqueeze.com | ✓ | N/A | Multi-daily | Short data | Medium | **Yes** |
| **Short** | Fintel | ✓/$ | Limited | Daily | Squeeze score | Medium | **Yes** |
| **News RSS** | Yahoo/CNBC/etc | ✓ | Unlimited | Real-time | Feeds | Low | **Good** |
| **Alt Data** | PyTrends | ✓ | 10/min | 24-48h | Search trends | Low | **Weak** |
| **Alt Data** | Wiki Pageviews | ✓ | Unlimited | 1-2h | Attention spikes | Low | **Weak** |
| **Alt Data** | Patents | ✓ | N/A | 2-3w | Patent filings | High | **Niche** |
| **Alt Data** | GitHub Trending | ✓ | N/A | Daily | Tech adoption | Medium | **Dev-tools** |
| **Macro** | CoinGecko API | ✓ | 50/min | Real-time | Crypto sentiment | Low | **Indirect** |

---

## Priority Ranking for Implementation

### **Tier 1 (High ROI, Low Effort)** - Implement First
1. **Reddit PRAW** - Free, real sentiment from WSB/r/stocks, excellent small-cap coverage
   - Effort: 2-3 hours (setup + ticker extraction + sentiment)
   - Expected impact: HIGH (unique micro-cap sentiment)
   
2. **API Ninjas Earnings Calendar** - Free, generous rate limit, simple REST API
   - Effort: 1-2 hours (REST call + DB insert)
   - Expected impact: MEDIUM (earnings date triggers)

3. **RSS Feeds (Yahoo, CNBC, Seeking Alpha)** - Free, supplement existing news sources
   - Effort: 1-2 hours (RSS parsing + dedup against MarketAux)
   - Expected impact: MEDIUM (redundancy + small-cap coverage)

4. **OpenInsider Web Scraping** - Free, real-time insider data
   - Effort: 3-4 hours (BeautifulSoup + scheduling)
   - Expected impact: HIGH (insider signal often precedes news)

### **Tier 2 (Medium ROI, Medium Effort)** - Implement Next
5. **Unusual Whales API** - Freemium, real-time options flow (if rate limit acceptable)
   - Effort: 4-5 hours (websocket + flow parsing)
   - Expected impact: MEDIUM-HIGH (smart money signals)

6. **ORTEX Public API** - Free tier available, short squeeze signals
   - Effort: 2-3 hours (daily data fetch + trend detection)
   - Expected impact: MEDIUM (short squeeze plays)

7. **StockTwits API** - Free public endpoints, real-time sentiment
   - Effort: 2-3 hours (similar to Reddit PRAW)
   - Expected impact: MEDIUM (confirmation of Reddit sentiment)

### **Tier 3 (Lower ROI or High Effort)** - Optional/Future
8. **PyTrends** - Free but not real-time; macro context only
   - Effort: 2-3 hours (setup + interpretation)
   - Expected impact: LOW (24-48h delay, weak signal)

9. **Patent Filings** - Niche use (biotech/pharma small-caps)
   - Effort: 5-6 hours (scraping + parsing)
   - Expected impact: LOW-MEDIUM (only for specific sectors)

10. **GitHub Trending** - Dev-tools startups only
    - Effort: 3-4 hours (scraping)
    - Expected impact: LOW (narrow audience)

---

## Data Overlap Analysis

### Existing Sources Coverage
1. **Finnhub** - Market news, company news, price alerts
2. **MarketAux** - Global news aggregation + entity extraction
3. **SEC EDGAR** - 8-K filings (raw RSS)
4. **TickerTick** - Small-cap aggregation (assume similar to MarketAux)
5. **Discord NuntioBot** - User-generated alerts
6. **Content scraper** - URL body extraction

### NEW Data from Recommended Sources
| Data Type | Existing? | New Source | Value |
|-----------|-----------|-----------|-------|
| Social sentiment (Reddit/Twitter) | ✗ | PRAW + StockTwits | HIGH |
| Insider trading details (Form 4) | Partial* | OpenInsider scrape | HIGH |
| Options flow/unusual activity | ✗ | Unusual Whales | MEDIUM-HIGH |
| Earnings calendar + whispers | ✗ | API Ninjas + Whispers | MEDIUM |
| Short interest trends | ✗ | ORTEX/ShortSqueeze | MEDIUM |
| Financial news RSS | Partial* | Yahoo/CNBC RSS | MEDIUM |
| Google search trends | ✗ | PyTrends | LOW |
| Patent filings | ✗ | USPTO scraping | LOW (niche) |
| GitHub trends | ✗ | GitHub scraping | LOW (niche) |

*Partial = You have raw data (SEC EDGAR RSS) but not parsed/enriched  
*Partial = MarketAux covers some news, but RSS feeds provide redundancy + direct source access

---

## Implementation Roadmap

### Phase 1: Social Sentiment + Insider Data (Week 1-2)
- [ ] Integrate PRAW for Reddit sentiment (r/wallstreetbets, r/stocks)
- [ ] Build OpenInsider scraper for Form 4 data
- [ ] Add StockTwits API for real-time sentiment comparison
- [ ] Parser task: Extract tickers + map to MongoDB articles

### Phase 2: Earnings + Short Interest (Week 2-3)
- [ ] Add API Ninjas Earnings Calendar endpoint
- [ ] Integrate ORTEX short interest feed
- [ ] Build earnings announcement trigger logic
- [ ] Create short-squeeze alert rules

### Phase 3: Options Flow (Week 3-4, if needed)
- [ ] Integrate Unusual Whales API (check free tier)
- [ ] Build unusual activity detection
- [ ] Optional: Add Barchart options scraper as fallback

### Phase 4: Redundancy + Alternative Data (Week 4+)
- [ ] Add Yahoo/CNBC/Seeking Alpha RSS feeds
- [ ] Optional: PyTrends for macro context
- [ ] Optional: GitHub/Patent scraping (niche signals)

---

## Technical Considerations

### Rate Limit Management
- **Reddit PRAW:** 60 req/min = 1 req/sec safe; use with delays between ticker checks
- **API Ninjas:** 1,700 req/day = ~70 req/hour; batch earnings calendar updates
- **OpenInsider:** 5-10 req/min = stagger scrapes, cache results 15 min
- **Unusual Whales:** 100-500 req/day depends on free tier; verify before integration
- **ORTEX:** ~100 req/day = single daily fetch, cache 24h

### Data Validation & Dedup
- **Reddit:** Normalize ticker mentions (handle $AAPL, AAPL, aapl)
- **SEC Form 4:** Dedup by source_id (CIK + form ID + transaction date)
- **Earnings:** Dedup by ticker + report date
- **Short interest:** Dedup by ticker + report date

### Storage Strategy
- **Social/Sentiment:** MongoDB (raw posts/comments) + PostgreSQL (parsed sentiment + ticker list)
- **Insider trades:** PostgreSQL (structured Form 4 data)
- **Earnings:** PostgreSQL (calendar + estimates)
- **Short interest:** PostgreSQL (daily snapshots for trend analysis)
- **Options flow:** PostgreSQL (real-time unusual activity, purge daily)
- **RSS feeds:** MongoDB (raw articles) + PostgreSQL (parsed, deduplicated)

### Error Handling
- **Rate limit hits:** Implement exponential backoff (Tenacity library, already in stack)
- **Source outages:** Fallback to cached data + alert
- **Web scraping failures:** Retry with delays; consider rotating User-Agents
- **API timeouts:** 30-sec timeout, 3 retries before skip

---

## Cost Analysis: Free vs. Paid Tiers

| Source | Free Tier | Paid Tier | When to Upgrade |
|--------|-----------|-----------|-----------------|
| Reddit PRAW | ✓ Full | N/A | N/A |
| API Ninjas | ✓ 50K req/mo | $9/mo (1M req/mo) | If testing >1,700 req/day |
| ApeWisdom | ✓ Limited | $99-499/mo | If premium sentiment needed |
| Unusual Whales | ✓ Limited (100-500/day) | $49-199/mo | If real-time options >free tier |
| sec-api.io | ✓ Limited | $9/mo (2K req/mo) | If parsing >250/day |
| ORTEX | ✓ Public data | $299+/mo | If real-time short data |
| FMP | ✓ 250 req/day | $49/mo (unlimited) | If earnings >250/day |

**Recommendation:** Start with all **Free Tier** sources; upgrade only if testing reveals insufficient data volume.

---

## Unresolved Questions

1. **ApeWisdom exact rate limits?** - Search results don't specify exact free tier limits. Verify via API docs or signup.

2. **Unusual Whales free tier sufficiency?** - Results indicate "100-500 req/day" but exact free tier not confirmed. Need to test API.

3. **ORTEX public API availability?** - Results mention public access but unclear if data is real-time or delayed. Verify current status.

4. **StockTwits public endpoints vs. deprecation?** - Check if public symbol stream still available (some third-party APIs claim access).

5. **OpenInsider scraping legality?** - While openinsider.com is public, verify no ToS violations before deploying scraper.

6. **Earnings Whispers scraping reliability?** - No official API; web scraping may break with site redesign. Consider fallback to paid whisper APIs.

7. **Small-cap coverage across sources?** - Most sources claim small-cap support, but actual coverage % unknown. Recommend testing with 10-20 micro-cap tickers.

8. **Latency quantification?** - Most latency estimates are approximate. Recommend benchmarking each source in production after integration.

9. **Dedup strategy across 9 sources?** - Current 6 sources need overlap analysis; adding 8+ more = complex dedup logic needed.

10. **Real-time vs. batch architecture?** - PRAW polling, StockTwits websocket, Unusual Whales REST - mixed patterns. Clarify preferred data ingestion model.

---

## Sources & References

### Official APIs & Documentation
- [PRAW Documentation](https://praw.readthedocs.io/)
- [Reddit API](https://www.reddit.com/dev/api)
- [StockTwits Sentiment API](https://sentiment-v2-api.stocktwits.com/)
- [API Ninjas Earnings Calendar](https://api-ninjas.com/api/earningscalendar)
- [Financial Modeling Prep API](https://site.financialmodelingprep.com/developer/docs/)
- [Unusual Whales API](https://unusualwhales.com/public-api)
- [ORTEX Public Access](https://public.ortex.com)
- [SEC EDGAR API](https://www.sec.gov/cgi-bin/browse-edgar)
- [SEC Form 4 API](https://sec-api.io/docs/insider-ownership-trading-api)
- [Wikipedia Pageview API](https://pageviews.toolforge.org/api/v2/top)

### Aggregators & Reviews
- [ApeWisdom API](https://apewisdom.io/api/)
- [OpenInsider](http://openinsider.com/)
- [ShortSqueeze.com](https://shortsqueeze.com/)
- [Fintel Short Interest](https://fintel.io/short-interest-data)
- [Earnings Whispers](https://www.earningswhispers.com/)

### Community Resources & Tutorials
- [GitHub - wsbtrends (Reddit WSB scraper)](https://github.com/wbollock/wsbtrends)
- [GitHub - reddit-stock-scraper (Node.js)](https://github.com/Greg-Finnegan/reddit-stock-scraper)
- [GitHub - RedditStockPredictions (NLP analysis)](https://github.com/DMilmont/RedditStockPredictions)
- [GitHub - pytrends](https://github.com/GeneralMills/pytrends)
- [AlgoTrading101 - Reddit WSB Web Scraping](https://algotrading101.com/learn/reddit-wallstreetbets-web-scraping/)
- [Medium - Using PRAW for stock mentions](https://medium.com/@financial_python/how-to-get-trending-stock-tickers-from-reddit-using-praw-and-python-1fccc7f06748)

### Alternative Data & Rankings
- [Bright Data - Best Alternative Data Providers 2026](https://brightdata.com/blog/web-data/best-alternative-data-providers)
- [StartUs Insights - Google Trends Alternatives](https://www.startus-insights.com/innovators-guide/google-trends-alternatives/)
- [RSS.app - Top 20 Finance RSS Feeds](https://rss.app/en/blog/top-rss-feeds/20-best-finance-websites-to-get-rss-feeds-from/)
- [RSS Feedspot - Stock Market News RSS](https://rss.feedspot.com/stock_market_news_rss_feeds/)
- [Barchart - Unusual Options Activity](https://www.barchart.com/options/unusual-activity)
- [InsiderFinance.io - Unusual Options Activity](https://www.insiderfinance.io/flow)

### Comparison Resources
- [SaaSHub - SEC Form 4 Alternatives](https://www.saashub.com/sec-form-4-alternatives)
- [TIKR.com - 5 Best Free Insider Trading Tools](https://www.tikr.com/blog/5-best-free-tools-to-track-insider-trading-in-stocks)
- [Find My Moat - OpenInsider vs SEC API](https://www.findmymoat.com/vs/openinsider-vs-sec-api-sec-api-io)

---

## Appendix: Quick API Examples

### Reddit PRAW Setup
```python
import praw
import re

reddit = praw.Reddit(
    client_id='YOUR_CLIENT_ID',
    client_secret='YOUR_CLIENT_SECRET',
    user_agent='alphasniper/1.0'
)

def extract_tickers(text):
    """Extract stock tickers (A-Z, 1-4 chars)"""
    return re.findall(r'\b[A-Z]{1,4}\b', text)

# Stream posts from r/wallstreetbets
for submission in reddit.subreddit('wallstreetbets').stream.submissions():
    tickers = extract_tickers(submission.title + ' ' + submission.selftext)
    print(f"Post: {submission.title}, Tickers: {tickers}, Score: {submission.score}")
    # Save to MongoDB with sentiment analysis
```

### API Ninjas Earnings
```python
import requests

api_key = 'YOUR_API_NINJAS_KEY'
ticker = 'TSLA'

response = requests.get(
    'https://api.api-ninjas.com/v1/earningscalendar',
    params={'ticker': ticker},
    headers={'X-Api-Key': api_key}
)

earnings_list = response.json()
for earning in earnings_list:
    print(f"{earning['ticker']} reports on {earning['report_date']}")
    print(f"  Est. EPS: {earning['eps_estimate']}, Revenue: {earning['revenue_estimate']}")
```

### ORTEX Short Interest
```python
import requests

response = requests.get('https://public.ortex.com/api/v1/short_interest', params={'ticker': 'TSLA'})
data = response.json()
# Example response structure (verify against API docs):
# {"ticker": "TSLA", "short_pct_float": 3.5, "days_to_cover": 2.1, "squeeze_score": 65}
print(f"Short % of float: {data['short_pct_float']}%")
print(f"Days to cover: {data['days_to_cover']}")
print(f"Squeeze score: {data['squeeze_score']}/100")
```

---

**Report Generated:** 2026-04-18 14:52 UTC  
**Research Completed By:** Researcher Agent  
**Status:** Ready for implementation planning phase
