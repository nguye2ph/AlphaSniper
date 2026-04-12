# Finnhub API Analysis for AlphaSniper
**Research Date:** 2026-04-11 | **Scope:** Real-time Small-Cap Stock News Pipeline

---

## Executive Summary

Finnhub provides **three primary news endpoints** (Market News, Company News, News Sentiment) plus **WebSocket real-time streaming**. Free tier offers 60 API calls/min with limited features; sentiment endpoint requires premium. Small-cap filtering unavailable via direct market cap range parameter.

---

## 1. NEWS ENDPOINTS

### 1.1 Market News Endpoint
**Base URL:** `GET /api/v1/news`

**Parameters:**
- `category` (required): "general" | "forex" | "crypto" | "merger"
- `minId` (optional): Integer pagination ID; fetch news after specified ID
- `token` (required): API key (query param or `X-Finnhub-Token` header)

**Response Schema (Array of objects):**
```json
{
  "id": 12345678,
  "headline": "Market Update: Tech Stocks Rise",
  "summary": "Technology sector shows strong momentum...",
  "source": "Reuters",
  "url": "https://example.com/article",
  "image": "https://example.com/image.jpg",
  "category": "general",
  "datetime": 1609459200,
  "related": "AAPL,MSFT"
}
```

**Rate Limit:** 30 API calls/second (global limit)
**Free Tier:** Available; broad market news only

---

### 1.2 Company News Endpoint
**Base URL:** `GET /api/v1/company-news`

**Parameters:**
- `symbol` (required): Stock ticker (e.g., "AAPL")
- `from` (required): Date format YYYY-MM-DD
- `to` (required): Date format YYYY-MM-DD
- `token` (required): API key
- `limit` (optional): Max results to return

**Response Schema (Array of objects):**
```json
{
  "id": 87654321,
  "headline": "Apple Reports Q3 Earnings",
  "summary": "Apple Inc. announced strong Q3 results...",
  "source": "Bloomberg",
  "url": "https://example.com/article",
  "image": "https://example.com/image.jpg",
  "category": "company",
  "datetime": 1609545600,
  "related": "AAPL"
}
```

**Constraints:**
- **North American companies only** (US/Canada)
- Date-based pagination via `from`/`to`
- No market cap filtering available
- `id` field enables pagination for large result sets

**Rate Limit:** 30 API calls/second
**Free Tier:** Available

---

### 1.3 News Sentiment Endpoint
**Base URL:** `GET /api/v1/news-sentiment`

**Parameters:**
- `symbol` (required): US company ticker only
- `token` (required): API key

**Response Schema:**
```json
{
  "symbol": "AAPL",
  "companyNewsScore": 0.75,
  "sentiment": {
    "bullishPercent": 0.68,
    "bearishPercent": 0.32
  },
  "buzz": {
    "articlesInLastWeek": 145,
    "weeklyAverage": 20.7,
    "buzz": 1.23
  },
  "sectorAverageNewsScore": 0.62,
  "sectorAverageBullishPercent": 0.65
}
```

**Field Definitions:**
- `companyNewsScore`: Aggregated sentiment metric (0-1 range implied)
- `sentiment.bullishPercent`: % positive sentiment articles
- `sentiment.bearishPercent`: % negative sentiment articles
- `buzz.articlesInLastWeek`: News volume count
- `buzz.buzz`: Momentum coefficient (>1 indicates increasing activity)
- `weeklyAverage`: Historical trend baseline

**Constraints:**
- **US companies only** (no Canada/international)
- **Premium access required** (not free tier)
- Symbol must have sufficient news history

**Rate Limit:** 30 API calls/second
**Free Tier:** ❌ Not available

---

## 2. WEBSOCKET REAL-TIME STREAMING

### 2.1 Connection Details
**Endpoint:** `wss://ws.finnhub.io` (production)

**Protocol Selection:**
- Automatic: `wss://` (HTTPS) or `ws://` (HTTP)
- **Authentication:** Send API token with subscription message

### 2.2 Message Format - News Subscribe
**Subscription Message (Client → Server):**
```json
{
  "type": "subscribe-news",
  "symbol": "AAPL"
}
```

**Subscribe to All News (if available):**
```json
{
  "type": "subscribe-news"
}
```

**Unsubscribe:**
```json
{
  "type": "unsubscribe-news",
  "symbol": "AAPL"
}
```

### 2.3 News Event Format
**Real-time News Message (Server → Client):**
```json
{
  "type": "news",
  "data": [
    {
      "id": 99999999,
      "headline": "Breaking: AAPL Announces Acquisition",
      "summary": "Apple has acquired startup...",
      "source": "TechCrunch",
      "url": "https://techcrunch.com/article",
      "image": "https://example.com/thumb.jpg",
      "category": "company",
      "datetime": 1712839200,
      "symbol": "AAPL",
      "related": "AAPL,MSFT"
    }
  ]
}
```

### 2.4 Heartbeat & Connection Management
**Ping (Server → Client, every ~30 seconds):**
```json
{
  "type": "ping"
}
```

**Pong Response (Client → Server, required):**
```json
{
  "type": "pong"
}
```

**Failure to pong within timeout** = automatic disconnection

### 2.5 Rate Limits & Availability
- **Free Tier:** Limited to **50 simultaneous symbols**
- **Paid Tier:** Unlimited symbol subscriptions
- **Global:** 30 API calls/second aggregate across all methods
- **Connection Limit:** 1 WebSocket connection per token (verify)

**Important:** Free tier WebSocket does **NOT** support all-news subscription; must specify symbols explicitly.

---

## 3. SMALL-CAP SPECIFIC ANALYSIS

### ❌ Market Cap Filtering
**Direct Parameter:** NOT AVAILABLE

- Finnhub news endpoints cannot filter by market cap range
- No `marketCapMin`, `marketCapMax`, `marketCapRange` parameters
- Alternative: Use company profile endpoint separately to get market cap, then cross-reference news

### ✅ Workaround: Two-Step Approach
1. **Step 1:** Fetch small-cap company list via `/api/v1/company-profile2` or `/api/v1/screener/composite` with market cap criteria
2. **Step 2:** Subscribe to WebSocket news for identified symbols or batch query via `/company-news`

### 📊 News Volume Expectations (Free Tier)
- **Market News:** ~20-50 articles/day across all categories
- **Company News:** Varies by ticker; FAANG ~50+/week, small-caps ~0-10/week
- **Coverage Gap:** Many small-caps have minimal news coverage in Finnhub data
- **Solution:** Combine with additional news sources for comprehensive coverage

### 🎯 Categories (No Market Cap Grouping)
Available news categories:
- "general" - Market-wide news
- "forex" - Currency movements
- "crypto" - Cryptocurrency
- "merger" - M&A activity

No built-in small-cap category; requires manual filtering by company size.

---

## 4. AUTHENTICATION & RATE LIMITS

### API Key Usage
```bash
# Query Parameter Method
curl "https://finnhub.io/api/v1/news?category=general&token=YOUR_API_KEY"

# Header Method (Recommended)
curl -H "X-Finnhub-Token: YOUR_API_KEY" https://finnhub.io/api/v1/news?category=general
```

### Global Rate Limiting
- **30 API calls/second** across ALL endpoints
- **60 API calls/minute** on free tier (softer limit)
- HTTP 429 returned when limits exceeded
- Implement exponential backoff for retry logic

### Free Tier Boundaries
- **Included:** Market news, company news, WebSocket (50 symbols)
- **Excluded:** News sentiment, historical sentiment, real-time quotes premium features
- **Quota:** 60 calls/minute (tight for high-frequency polling)

### Paid Tiers (Approx Pricing)
- Premium: $11.99-$99.99/month
- Adds: News sentiment, international coverage, unlimited WebSocket symbols
- Exact tiers vary; check Finnhub dashboard

---

## 5. IMPLEMENTATION RECOMMENDATIONS

### For AlphaSniper Pipeline

#### Primary Strategy: Hybrid Approach
1. **REST API** for batch small-cap company news (`company-news` with date ranges)
2. **WebSocket** for real-time alerts on subscribed symbols (free: 50 max)
3. **Secondary source** for small-cap coverage gaps (Finnhub has limited small-cap news)

#### Query Pattern for Small-Caps
```
1. Daily batch: GET /company-news?symbol=TICKER&from=TODAY&to=TODAY
2. Real-time: WS subscribe to top 50 small-cap tickers by volume
3. Fallback: Poll market-news?category=general for mentions of watched tickers
```

#### Optimization for Free Tier
- Batch requests during off-peak hours (non-market hours)
- Implement caching (news IDs don't repeat; minId prevents duplicates)
- Use WebSocket for real-time; REST only for backfill
- Cap simultaneous WebSocket subscriptions to 45-48 (leave buffer)

---

## 6. UNRESOLVED QUESTIONS

1. **WebSocket reconnection:** Finnhub docs lack explicit backoff strategy. Test empirically.
2. **Small-cap news coverage:** Unknown % of US small-caps with >0 news articles. Requires sampling.
3. **News deduplication:** Does Finnhub news ID guarantee uniqueness across endpoints? Test.
4. **Sentiment availability:** Does news-sentiment require premium tier or specific company profile? Verify.
5. **Symbol subscription limits:** Is 50 symbol limit hard or soft on free tier? Test under load.
6. **Market cap filtering:** Confirm no hidden parameter for market cap range queries.

---

## References

- [Finnhub API Documentation](https://finnhub.io/docs/api)
- [WebSocket News Streaming](https://finnhub.io/docs/api/websocket-news)
- [Market News Endpoint](https://finnhub.io/docs/api/market-news)
- [Company News Endpoint](https://finnhub.io/docs/api/news-sentiment)
- [Finnhub Pricing](https://finnhub.io/pricing)
- [Finnhub Python Client (GitHub)](https://github.com/Finnhub-Stock-API/finnhub-python)

---

**Next Actions for Implementation Phase:**
- [ ] Verify news-sentiment premium tier requirement
- [ ] Test WebSocket reconnection behavior
- [ ] Validate small-cap news coverage with sample tickers
- [ ] Implement caching layer for news ID deduplication
- [ ] Design hybrid REST + WebSocket polling strategy
