# MarketAux vs SEC EDGAR API Analysis for AlphaSniper

## Executive Summary

Real-time small-cap stock news pipeline requires dual data sources for complete coverage: **MarketAux** for sentiment-tagged news aggregation, **SEC EDGAR** for official filings & 8-K press releases. Each has distinct strengths; combined they provide comprehensive micro-cap intelligence.

---

## Part 1: MarketAux API

### Endpoints
- **`GET /news/all`** - Global financial news with entity filtering
- **`GET /news/sources`** - Available news sources for filtering  
- **`GET /similar`** - Find articles similar to UUID

### Free Tier Limits
- **100 requests/day** (strict daily cap)
- **No per-request article limit** stated
- **No API key required** for free access

### Filtering Capabilities
- **Ticker/Symbol**: `symbols=AAPL,MSFT` (comma-separated)
- **Sentiment**: `sentiment_gte=0.1`, `sentiment_lte=-0.1` (range -1 to +1)
- **Entity filtering**: Filter by matched companies within articles
- **Language**: Multi-language support (30+ languages)
- **Date range**: `published_after` parameter
- **Market cap, industry, country**: Available through entity response fields

### JSON Response Schema
```json
{
  "meta": {
    "found": 1234,
    "returned": 10,
    "limit": 10,
    "page": 1
  },
  "data": [
    {
      "uuid": "article-uuid",
      "title": "Company announces earnings",
      "description": "Brief summary",
      "source": "Reuters",
      "published_at": "2026-04-11T14:32:00Z",
      "updated_at": "2026-04-11T14:32:00Z",
      "url": "https://...",
      "entities": [
        {
          "symbol": "ACME",
          "name": "ACME Corp",
          "exchange": "NASDAQ",
          "exchange_long": "NASDAQ Stock Market",
          "country": "US",
          "type": "equity",
          "industry": "Technology",
          "match_score": 0.95,
          "sentiment_score": 0.85,
          "highlights": ["ACME", "earnings beat"]
        }
      ],
      "sentiment": 0.85,
      "tags": ["earnings", "technology"]
    }
  ]
}
```

### Small-Cap Coverage
- **Exchanges supported**: 80+ global markets via 5,000+ sources
- **OTC/Pink Sheets**: **Not explicitly stated in available documentation** - requires direct API testing
- **Coverage gap**: No confirmation of OTCQX, OTCQB, or Pink Limited tier coverage
- **Entity types**: Stocks, indices, ETFs, commodities, mutual funds, futures, currencies, crypto

### Parsing Complexity
- **Low** - Direct JSON, entity extraction per article
- **Challenge**: Sentiment is article-level only; entity-level sentiment_score available but granularity unclear

---

## Part 2: SEC EDGAR APIs

### Core Endpoints

#### 1. **Company Filings Submissions**
```
GET https://data.sec.gov/submissions/CIK{10-digit}.json
```
- Returns all filings history for entity
- Format: CIK with leading zeros (e.g., `CIK0000789019`)
- Real-time updates (< 1 second latency)

#### 2. **XBRL Company-Concept**
```
GET https://data.sec.gov/api/xbrl/companyconcept/CIK{}/us-gaap/{concept}.json
```
- Single company, single accounting concept (e.g., `AccountsPayableCurrent`)
- All disclosures with unit measures (USD, CAD, etc.)

#### 3. **XBRL Company-Facts**
```
GET https://data.sec.gov/api/xbrl/companyfacts/CIK{}.json
```
- All XBRL concepts for a company in one call
- Large response (financial statements complete)

#### 4. **XBRL Frames**
```
GET https://data.sec.gov/api/xbrl/frames/us-gaap/{concept}/USD/CY{YYYY}Q{#}I.json
```
- Cross-company aggregation by period
- Period format: `CY2026` (annual), `CY2026Q1` (quarterly), `CY2026Q1I` (instantaneous)

#### 5. **Company Tickers Lookup**
```
GET https://www.sec.gov/files/company_tickers.json
GET https://www.sec.gov/files/company_tickers_exchange.json
```
- Static ticker → CIK mapping (daily updates)

### RSS Feeds
- **Latest Filings**: Subscribe to all or filtered by company/CIK/form type
- **Form Types**: 8-K, 10-K, 10-Q, S-1, 20-F, 40-F, etc.
- **Real-time**: Filings pushed as submitted

### Rate Limits
- **10 requests/second per IP** (enforced)
- **Fair Access Policy**: SEC reserves right to block excessive requests
- **Compliance**: Use efficient scripting, download only needed data
- **User-Agent requirement**: MUST include header identifying app + email

### 8-K Filing Structure
- **Form Type**: 8-K (current report of unregistered events)
- **Item types**: Can filter by `Item 1.01` (bankruptcy), `Item 8.01` (other events), etc.
- **Press release access**: Often in Item 8.01 or Exhibit 99
- **Response**: JSON array of filings with accession numbers (link to full filing HTML/XML)

### XBRL Data Access
- **Taxonomies**: `us-gaap`, `ifrs`, `dei` (document entity info)
- **Concepts**: Account names like `NetIncomeLoss`, `Assets`, `Revenues`
- **Update latency**: < 1 minute for XBRL APIs (vs. < 1 second for submissions)
- **No authentication**: All APIs public, no key required

---

## Part 3: Comparative Analysis Table

| **Attribute** | **MarketAux** | **SEC EDGAR** |
|---|---|---|
| **Real-time latency** | Seconds (news aggregation) | Seconds-1min (filings crawl → XBRL parse) |
| **News articles** | Yes (5000+ sources, 30+ langs) | No (filings only, text extraction needed) |
| **Sentiment tags** | Yes (automated, -1 to +1 scale) | No (must NLP-score 8-K text) |
| **Small-cap coverage** | **Unclear** - likely limited | **Complete** - all public filers (OTC, NASDAQ, NYSE) |
| **OTC/Pink Sheets explicit** | **Not documented** | **Yes** - all SEC-filers included |
| **Parsing difficulty** | Easy (flat JSON) | Medium (multi-level XBRL/XML) |
| **Free tier cost** | 100 req/day (strict) | Unlimited (10 req/sec rate limit) |
| **Authentication** | None required | None required |
| **8-K press releases** | No | Yes (Item 8.01, Exhibit 99) |
| **Structured financials** | No | Yes (XBRL, 10-K/10-Q) |
| **Entity linking** | Per-article tickers | CIK-based, ticker lookup table |
| **Bulk download** | Via pagination + daily limit | Via FTP (legacy) or API polling |
| **Update frequency** | Daily (news published) | Real-time (filing dissemination) |

---

## Part 4: AlphaSniper Architecture Recommendation

### Dual-Source Pipeline
1. **MarketAux** (primary news source)
   - Ingest 100 reqs/day on rotation (sleeping 15-20min between batches)
   - Filter by sentiment > 0.3 and < -0.2 (eliminate neutral noise)
   - Store article UUID, ticker, headline, source, sentiment
   - Skip: detailed entity.sentiment_score parsing (insufficient granularity)

2. **SEC EDGAR** (confirmation + filings)
   - Subscribe to 8-K RSS feed (real-time push)
   - Extract accession → filing HTML, regex-parse Item 8.01 for press releases
   - CIK ↔ ticker mapping via `company_tickers.json` (cache daily)
   - Enrich MarketAux stories with filing dates/links
   - Secondary: XBRL financials for fundamental context (10-K quarterly snapshots)

### Data Quality Notes
- **MarketAux limitation**: No OTC/Pink Sheets confirmation → may miss micro-caps
- **SEC EDGAR limitation**: Latency 15-60min for text extraction (faster for metadata)
- **Hybrid approach**: Cross-validate tickers across both sources to reduce false positives

---

## Unresolved Questions
- Does MarketAux cover OTCQX, OTCQB, or Pink Limited explicitly? (Docs silent; requires API testing with known OTC tickers like PINK, FTHK)
- What is MarketAux entity.sentiment_score granularity vs. article.sentiment? (Unclear if per-entity or duplicate)
- SEC EDGAR: Are 8-K Item types parsed in RSS feed metadata or only in full filing HTML? (Affects filtering efficiency)
- Rate limit enforcement: Does SEC block entire IP or just throttle? (Affects multi-user shared IP scenarios)

---

## Sources
- [MarketAux API Documentation](https://www.marketaux.com/documentation)
- [SEC EDGAR APIs](https://www.sec.gov/search-filings/edgar-application-programming-interfaces)
- [data.sec.gov Documentation](https://data.sec.gov/)
- [SEC Developer Resources](https://www.sec.gov/developer)
- [SEC RSS Feeds](https://www.sec.gov/about/rss-feeds)
- [SEC Fair Access Policy](https://www.sec.gov/about/webmaster-frequently-asked-questions)
- [XBRL/Frames API Reference](https://data.sec.gov/api/xbrl/frames/us-gaap/AccountsPayableCurrent/USD/CY2026Q1I.json)
