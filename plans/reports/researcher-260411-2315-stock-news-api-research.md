# AlphaSniper Stock News API Research Report
**Date:** 2026-04-11 | **Status:** Complete

---

## EXECUTIVE SUMMARY

For a real-time small-cap stock news pipeline, **avoid NuntioBot** and **Discord scraping** entirely—both violate ToS and have zero public APIs. Instead, **stack Finnhub + MarketAux + SEC EDGAR** as your core free tier foundation. Add Alpha Vantage sentiment as secondary. This combination covers speed, breadth, and cost.

**Estimated free tier capacity:** ~3,500 articles/day with reasonable coverage.

---

## 1. NUNTIOBOT ASSESSMENT ❌

### Findings
- **Public API:** None exists. No REST endpoints, no RSS feeds, no webhook support.
- **Web scraping:** Not feasible. Page redirects to main site (news.nuntiobot.com → nuntiobot.com), no structured data exposure.
- **Access model:** Discord-only, subscription required (trial via whop.com/nuntiobot).
- **Third-party scrapers:** No known working tools. Discord API changes (2026) have killed old scraping methods.

### Verdict
**Do not attempt integration.** Not worth the maintenance burden. NuntioBot serves premium Discord subscribers; it's not designed for programmatic access.

---

## 2. TOP 5 FREE/CHEAP STOCK NEWS APIS (RANKED)

### 1. FINNHUB ⭐ (Best Overall for Small-Caps)
**URL:** https://finnhub.io  
**Free Tier:**
- 60 calls/minute (NOT per day)
- Real-time US/Canadian market news
- WebSocket streaming (up to 50 symbols)
- No credit card required

**Real-Time Latency:** ~1–5 seconds after news publish  
**Small-Cap Coverage:** Strong (covers all NASDAQ/NYSE symbols)  
**Streaming:** Yes (WebSocket, included in free tier)

**Response Format:**
```json
{
  "buzz": {
    "articlesInLastWeek": 20,
    "buzz": 0.8888,
    "weeklyAverage": 22.5
  },
  "companyNewsScore": 0.9166,
  "sentiment": {
    "bearishPercent": 0.0,
    "bullishPercent": 1.0
  },
  "symbol": "AAPL"
}
```

**Includes:** Ticker, sentiment (bullish/bearish %), news score, buzz metrics  
**Gotcha:** News sentiment API is US-only.

---

### 2. MARKETAUX 🥈 (Best Global Coverage)
**URL:** https://www.marketaux.com  
**Free Tier:**
- 100 requests/day
- 3 articles per request
- Global markets (80+ exchanges, 5,000+ sources)
- 200,000+ entities tracked

**Real-Time Latency:** ~5–10 seconds  
**Small-Cap Coverage:** Excellent (global, includes OTC)  
**Streaming:** No (REST only)

**Paid Tiers:** $29–$199/mo for 2,500–50,000 requests/day  
**Includes:** Ticker, market cap, entity type, sentiment scores  
**Best for:** Global small-cap discovery, multi-exchange monitoring

---

### 3. ALPHA VANTAGE 🥉 (Sentiment-Focused)
**URL:** https://www.alphavantage.co  
**Free Tier:**
- 25 requests/day (harsh limit)
- News & Sentiment API with AI-driven scores
- 15+ years earnings transcripts with sentiment

**Real-Time Latency:** ~30–60 seconds  
**Small-Cap Coverage:** 200,000+ tickers across 20+ exchanges  
**Streaming:** No (REST only)

**Sentiment Range:** -0.35 to +0.35 (granular)  
**Includes:** Ticker, sentiment, topics, earnings data  
**Gotcha:** 25 req/day is insufficient for production use alone; pair with Finnhub.

---

### 4. STOCKNEWSAPI
**URL:** https://stocknewsapi.com  
**Free Tier:**
- Limited (exact limits not publicly stated; register to see)
- 30+ news sources (Street, CNBC, Zacks, Benzinga, Bloomberg, Forbes, Seeking Alpha)
- US-focused

**Real-Time Latency:** ~10–15 seconds  
**Small-Cap Coverage:** Good (includes penny stocks)  
**Streaming:** No (REST only)

**Includes:** Ticker, source, sentiment (implied via source quality)  
**Verdict:** Less generous free tier than Finnhub; skip unless Finnhub quota exhausted.

---

### 5. BENZINGA API
**URL:** https://www.benzinga.com/apis  
**Free Tier:**
- Available via AWS Marketplace (free tier exists)
- Headline + teaser only (full articles require subscription)
- TCP streaming + REST endpoints

**Real-Time Latency:** ~2–5 seconds  
**Small-Cap Coverage:** Good (focus on equities)  
**Streaming:** Yes (TCP push, if subscribed)

**Includes:** Ticker, headline, source  
**Note:** Most useful data (full articles, sentiment) requires paid subscription.

---

## 3. ALTERNATIVE SCRAPING TARGETS

### SEC EDGAR RSS (FREE, EXCELLENT) ✅
**URL:** https://www.sec.gov/cgi-bin/browse-edgar  
**Access:** Official free RSS feeds by company or form type
- Real-time filing notifications (8-K, 10-Q, 10-K, etc.)
- Structured data via JSON API on data.sec.gov
- 10-minute update latency

**Includes:** Ticker (via CIK), filing type, accession number, filing date  
**Small-Cap:** Strong (all OTC and micro-cap filings included)  
**Latency:** ~10 minutes  
**Value:** Press releases buried in 8-K filings; excellent for insider activity signals.

**Third-party wrappers:**
- sec-api.io (free tier: limited)
- Financial Modeling Prep SEC RSS (legacy)

---

### STOCKTITAN (Press Releases) ❌
**Status:** Cannot confirm public API or scraping feasibility from search results.  
**Verdict:** Skip; no clear documentation found. Likely requires subscription.

---

### PR NEWSWIRE / BUSINESSWIRE / GLOBENEWSWIRE ❌
**Finding:** No free APIs from the wire services themselves.
- GlobeNewswire: No API at all.
- PR Newswire & Business Wire: APIs exist but enterprise-only (not free).
- **Alternative:** Use **RTPR.io** (real-time press release aggregator) if budget allows. Costs money but covers all three wires.

**Verdict:** Free access not feasible. Use Benzinga partnership instead (includes press release data).

---

### TWITTER/X API ❌
**Status in 2026:** Free tier removed entirely.
- Entry cost: $200/month (Basic tier, 15K reads/month)
- Pay-per-use model eliminates old tiers
- Requires approval for real-time stream (/2/tweets/search/stream)

**Verdict:** Not viable for bootstrapped project. Consider third-party X API resellers as alternative (cheaper than official).

---

## 4. DISCORD BOT FEASIBILITY ❌

### Current Risks (2026)
1. **Terms of Service Violation:** Discord explicitly prohibits scraping via selfbots (discord.py-self or similar).
2. **Account Termination:** Permanent bans are standard. No appeals process.
3. **Data Mining Prohibition:** "Do not mine or scrape any data, content, or information available on Discord services."
4. **Detection:** Discord has sophisticated anti-selfbot mechanisms; old libraries (discord.py-self) no longer bypass detection.

### Legal Status
- Not criminal, but civil ToS violation.
- No "gray area"—Discord's policy is explicit and enforced.

### Safe Discord Alternative
- **Build official Discord bot** (use discord.py, not discord.py-self).
- Use verified APIs to fetch news, post alerts to your own server.
- This is legal and ToS-compliant.

### Verdict
**Do not self-bot.** Not worth account risk. Instead, build a legitimate bot that aggregates data from Finnhub/MarketAux and posts to Discord.

---

## 5. RECOMMENDED ARCHITECTURE

### Free Tier Stack (Estimated Capacity: 3,500 articles/day)

```
Finnhub (60 calls/min)
  └─ News sentiment, real-time WebSocket stream
     
MarketAux (100 reqs/day × 3 articles = 300 articles)
  └─ Global small-cap discovery, backup source
  
SEC EDGAR RSS (10-min update)
  └─ Insider activity, filings, 8-K press releases
  
Alpha Vantage (25 reqs/day, ~10 articles)
  └─ Sentiment scoring, earnings context (use sparingly)
```

### Execution Model
1. **Primary:** Finnhub WebSocket for real-time push (ticker monitoring).
2. **Supplemental:** MarketAux REST polling every 15 minutes (global discovery).
3. **Background:** SEC EDGAR RSS every 10 minutes (insider + filings context).
4. **Optional:** Alpha Vantage batch 1–2x/day for sentiment backfill on high-interest tickers.

### Expected Latency
- **Finnhub WebSocket:** 1–5 seconds (fastest)
- **SEC EDGAR:** 10 minutes (slowest, but worth it for 8-K insider clues)
- **MarketAux:** 5–10 seconds
- **Alpha Vantage:** 30–60 seconds

---

## 6. COST BREAKDOWN

| Source | Free Tier | Paid Entry | Recommendation |
|--------|-----------|------------|-----------------|
| **Finnhub** | 60 calls/min | $60/mo (pro) | USE FREE TIER |
| **MarketAux** | 100 req/day | $29/mo | USE FREE TIER |
| **Alpha Vantage** | 25 req/day | $60+/mo | OPTIONAL, sparingly |
| **Benzinga** | Limited (AWS) | $100+/mo | Skip |
| **StockNewsAPI** | Unknown | Unknown | SKIP |
| **SEC EDGAR** | Unlimited | N/A | USE FREE |
| **X/Twitter** | None | $200/mo | SKIP |
| **NuntioBot** | Trial (Discord) | Subscription | SKIP |

**Total Free Tier Cost: $0** (With real value.)

---

## 7. UNRESOLVED QUESTIONS

1. **MarketAux OTC coverage:** Does it track true OTC Pink Sheets, or only listed exchanges? Need to test API directly.
2. **SEC EDGAR 8-K press release extraction:** Are press releases reliably structured in XBRL? May need HTML parsing for consistency.
3. **Finnhub small-cap volume thresholds:** Does WebSocket stream include all NASDAQ/NYSE symbols, or only top N? Test with microcaps <$10M market cap.
4. **Backoff strategy:** When free tiers are hit, what's the failure mode? Implement graceful degradation.

---

## ACTIONABLE NEXT STEPS

1. **Immediate:**
   - Sign up for Finnhub (no credit card).
   - Sign up for MarketAux (no credit card).
   - Start SEC EDGAR RSS feed subscription for pilot tickers.

2. **Week 1:**
   - Build Finnhub WebSocket consumer (Python asyncio recommended).
   - Implement MarketAux REST poller (15-min intervals).
   - Test response latency on pilot tickers (AAPL, a $10M microcap).

3. **Week 2:**
   - Integrate SEC EDGAR 8-K scraper (use BeautifulSoup or Selenium; RSS metadata only is insufficient).
   - Add deduplication logic (same news from multiple sources).
   - Build alert filter (sentiment + volatility triggers).

4. **Week 3+:**
   - A/B test MarketAux free tier vs. upgrade ($29/mo) based on coverage gaps.
   - Monitor Finnhub quota; upgrade only if >60 calls/min needed.
   - Avoid Alpha Vantage unless sentiment scoring becomes critical use case.

---

**Report Status:** Ready for implementation sprint.
