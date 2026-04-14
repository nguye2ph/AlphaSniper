# Small-Cap Stock News Sources Research
Date: 2026-04-12

## Source Comparison Table

| Source | Free? | RSS | API | Ticker in Data | Small-Cap Coverage | Rate Limit | Complexity |
|---|---|---|---|---|---|---|---|
| GlobeNewsWire | Yes | Yes (free) | No public API | Partial (in text) | Good — OTC/micro filings | Unlimited RSS | Easy |
| PR Newswire | Yes | Yes (free) | No public API | Partial (in text) | Good — press releases | Unlimited RSS | Easy |
| BusinessWire | Yes | Yes (free) | No public API | Partial (in text) | Good — press releases | Unlimited RSS | Easy |
| OTC Markets | No free API | No | Paid only | Yes (native) | Excellent — penny/micro | Unknown | Hard |
| Newsfilter.io | Yes (limited) | No | Yes (REST) | Yes (native) | Good | 10 req/day free | Medium |
| StockTitan | Free web | Partial | No | Partial | Good — OTC + NASDAQ | N/A | Medium |
| AccessWire | Yes | No | No | No | Moderate | N/A | Hard |
| Yahoo Finance RSS | Yes | Yes (free) | Unofficial | Ticker in URL | Moderate | Unofficial limits | Easy |
| RTPR.io | Paid | No | Yes (REST) | Yes (native) | Excellent | Paid | Medium |
| stocknewsapi.com | Yes (50/day) | No | Yes (REST) | Yes (native) | Good | 50 req/day free | Easy |

---

## Source Details

### 1. GlobeNewsWire (RECOMMENDED)
- **RSS**: `https://www.globenewswire.com/RssFeed/industry/` + category or `https://www.globenewswire.com/RssFeed/keyword/` + term
- **Feed list**: https://www.globenewswire.com/rss/list
- **Free**: Fully free, no auth required
- **Ticker**: Not a native field — must extract from headline/body text with regex `\(([A-Z]{1,5})\)` pattern
- **Small-cap**: Strong — GNW is the wire of choice for micro/small-caps filing IRs
- **Data**: XML/RSS, fields: title, description, pubDate, link, category
- **Verdict**: Best free RSS for OTC/small-cap IR press releases

### 2. PR Newswire
- **RSS**: `https://www.prnewswire.com/rss/news-releases-list.rss` — general feed
- **Industry feeds**: `https://www.prnewswire.com/rss/financial-services-latest-news.rss`
- **Free**: Yes, read-only
- **Ticker**: Not native, extract from text. PRN often formats as `(NYSE: XYZ)` or `(OTC: XYZ)`
- **Small-cap**: Moderate — biased toward larger companies paying for distribution
- **Verdict**: Good secondary source, less small-cap density than GNW

### 3. BusinessWire
- **RSS**: `https://feed.businesswire.com/rss/home/?rss=G1` (general)
- **Customizable**: Yes — filter by keyword, subject, industry via URL params
- **Docs**: https://www.businesswire.com/help/feed-options
- **Free**: Yes
- **Ticker**: Regex extractable — `\(NYSE|NASDAQ|OTC: [A-Z]+\)`
- **Small-cap**: Moderate — more mid/large-cap skewed
- **Verdict**: Good supplemental RSS, lower small-cap signal than GNW

### 4. OTC Markets (otcmarkets.com)
- **API**: Exists but no documented free public tier
- **Data quality**: Excellent — native ticker, market cap tier (Pink/OTCQB/OTCQX), filing type
- **Access**: Requires commercial data agreement
- **Alternative**: Scrape `https://www.otcmarkets.com/research/news/api` (undocumented, fragile)
- **Verdict**: Best data quality but no free path — skip unless budget available

### 5. Newsfilter.io
- **API docs**: https://developers.newsfilter.io/
- **Free tier**: ~10 requests/day (very limited)
- **Paid**: Starts ~$49/month for 1000 req/day
- **Ticker**: Native — filter by `symbols` param
- **Sources**: Aggregates PRN, GNW, BW, SEC, Reuters, AP
- **Data format**: JSON `{ id, title, text, tickers, publishedAt, source }`
- **Verdict**: Best API DX if budget allows; free tier too small for real-time use

### 6. StockTitan
- **URL**: https://www.stocktitan.net/news/live.html
- **RSS**: Limited/unofficial
- **API**: None public
- **Coverage**: NYSE, NASDAQ, OTC, Pink Sheets
- **Verdict**: Good for manual monitoring; no integration path

### 7. stocknewsapi.com (RECOMMENDED for API)
- **Free tier**: 50 requests/day
- **Paid**: $19/month for 500 req/day
- **Ticker filtering**: Yes — `?tickers=AAPL,TSLA`
- **Data**: JSON with title, text, sentiment, tickers, published_at
- **Has sentiment**: Yes (built-in)
- **Small-cap**: Aggregates from multiple wires including OTC-relevant sources
- **Verdict**: Best free API option with native ticker + sentiment

### 8. Yahoo Finance RSS (BONUS)
- **Ticker-specific RSS**: `https://feeds.finance.yahoo.com/rss/2.0/headline?s=AAPL&region=US&lang=en-US`
- **Free**: Yes, no auth
- **Ticker**: Embedded in URL/feed
- **Limits**: Unofficial — throttles aggressively at scale
- **Verdict**: Useful for per-ticker monitoring of specific watchlist stocks; not bulk-scalable

### 9. AccessWire
- **Free RSS**: None public
- **API**: None public
- **Distribution only**: Paid PR distribution service
- **Verdict**: Skip

### 10. RTPR.io
- **API**: REST, aggregates BW + PRN + GNW + AccessWire in one feed
- **Free**: No
- **Pricing**: Not publicly listed (contact)
- **Verdict**: Good if budget exists; single integration for all wires

---

## Recommended Integration Stack

**Priority 1 — Free RSS (zero cost, implement immediately):**
1. **GlobeNewsWire** — best small-cap density, free RSS
2. **BusinessWire** — good supplemental, keyword-filterable RSS
3. **PR Newswire** — secondary coverage, same integration pattern

**Priority 2 — Free API (50 req/day free):**
4. **stocknewsapi.com** — native ticker + sentiment, easy JSON API

**Priority 3 — Consider if budget allows:**
5. **Newsfilter.io** ($49/mo) — best API, aggregates all wires, native ticker filter

---

## Integration Pattern for RSS Sources

```python
# Ticker extraction regex (covers NYSE/NASDAQ/OTC/TSX formats)
import re
TICKER_RE = re.compile(r'\b(?:NYSE|NASDAQ|OTC|OTCQB|OTCQX|TSX|CSE):\s*([A-Z]{1,5})\b')

# GlobeNewsWire RSS URLs
GNW_FEEDS = [
    "https://www.globenewswire.com/RssFeed/industry/financial-services",
    "https://www.globenewswire.com/RssFeed/keyword/OTC",
    "https://www.globenewswire.com/RssFeed/keyword/small-cap",
]
# Poll interval: every 5 minutes (RSS is pull-based, no rate limit documented)
```

**RSS item fields available:**
- `title` — headline (ticker usually here)
- `description` — body text (full or truncated)
- `pubDate` — ISO timestamp
- `link` — canonical URL
- `category` — industry/subject tags

**Ticker extraction success rate:** ~70-80% on GNW (most IR releases include exchange:ticker in headline), ~60% on PRN/BW.

---

## Data Quality vs Cost Matrix

```
Quality
  ^
  |  OTC Markets ●
  |           Newsfilter.io ●
  |       stocknewsapi ●
  |   GlobeNewsWire ●
  |  BusinessWire ●  PR Newswire ●
  +-------------------------> Cost (Free → Paid)
```

---

## Unresolved Questions

1. GNW RSS — no documented rate limit; need to test if aggressive polling (1min) triggers blocks
2. OTC Markets — any undocumented free API endpoint worth reverse-engineering?
3. stocknewsapi.com — does free tier cover OTC/Pink Sheet tickers or only major exchange symbols?
4. Newsfilter.io free tier — exact request count per day needs verification (docs show 10/day but may have changed)
5. Yahoo Finance RSS — real throttle threshold unknown; safe poll rate untested at scale
