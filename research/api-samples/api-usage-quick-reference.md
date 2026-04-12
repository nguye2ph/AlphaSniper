# AlphaSniper: Stock News API Quick Reference
**Working APIs & Implementation Guide**

---

## 1. SEC EDGAR (✅ Working Now - No Auth)

### Basic Usage
```bash
# Get Apple's filing history
curl -H "User-Agent: AlphaSniper/1.0" \
  "https://data.sec.gov/submissions/CIK0000320193.json" \
  | jq '.filings.recent | {accessionNumber, form, filingDate}'

# Get Tesla's insider transactions (Form 4)
curl -H "User-Agent: AlphaSniper/1.0" \
  "https://data.sec.gov/submissions/CIK0001652044.json" \
  | jq '.filings.recent | map(select(.form=="4")) | .[0:5]'
```

### Python Integration
```python
import requests
import json
from datetime import datetime

class SECEdgarAPI:
    BASE_URL = "https://data.sec.gov/submissions"
    HEADERS = {"User-Agent": "AlphaSniper/1.0 (Research Bot)"}
    
    def get_company_filings(self, cik: str):
        """Fetch all recent filings for a company"""
        url = f"{self.BASE_URL}/CIK{cik.zfill(10)}.json"
        response = requests.get(url, headers=self.HEADERS)
        return response.json()
    
    def extract_insider_transactions(self, company_data: dict):
        """Extract Form 4 insider transactions"""
        recent = company_data['filings']['recent']
        form_4_indices = [i for i, form in enumerate(recent['form']) 
                          if form == '4']
        
        transactions = []
        for idx in form_4_indices[:10]:  # Last 10
            transactions.append({
                'accession': recent['accessionNumber'][idx],
                'date': recent['filingDate'][idx],
                'form': recent['form'][idx],
                'url': f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={company_data['cik']}&type=4&dateb=&owner=exclude&count=100"
            })
        return transactions
    
    def extract_8k_filings(self, company_data: dict):
        """Extract Form 8-K material events"""
        recent = company_data['filings']['recent']
        form_8k_indices = [i for i, form in enumerate(recent['form']) 
                           if form == '8-K']
        
        events = []
        for idx in form_8k_indices[:5]:  # Last 5
            events.append({
                'accession': recent['accessionNumber'][idx],
                'date': recent['filingDate'][idx],
                'form': '8-K (Material Event)',
                'link': recent['primaryDocument'][idx] if idx < len(recent.get('primaryDocument', [])) else None
            })
        return events

# Usage
api = SECEdgarAPI()
aapl_data = api.get_company_filings("0000320193")
print("AAPL Insider Transactions:")
print(json.dumps(api.extract_insider_transactions(aapl_data), indent=2))
```

### Key Data Points
| Field | Type | Usage |
|-------|------|-------|
| cik | string | Company ID |
| name | string | Company name |
| tickers | array | Stock symbols |
| filings.recent.form | array | Form type (4, 8-K, 10-K, etc.) |
| filings.recent.filingDate | array | When filed |
| filings.recent.accessionNumber | array | Unique filing ID |

### CIK Numbers (Common Small-Caps)
```
AAPL: 0000320193
TSLA: 0001652044
NVDA: 0001045810
AMD:  0000002488
MSFT: 0000789019
AMZN: 0001018724
```

---

## 2. Finnhub (⏳ Sign Up Required - 5 min)

### Setup
1. Register: https://finnhub.io/register
2. Copy API key from Dashboard
3. Store: `export FINNHUB_API_KEY="your_key_here"`

### Basic Usage
```bash
# Get latest news
curl "https://finnhub.io/api/v1/news?category=general&limit=10&token=$FINNHUB_API_KEY"

# Get company-specific news
curl "https://finnhub.io/api/v1/company-news?symbol=AAPL&from=2026-04-01&to=2026-04-12&token=$FINNHUB_API_KEY"

# Get insider transactions
curl "https://finnhub.io/api/v1/insider-transactions?symbol=TSLA&limit=10&token=$FINNHUB_API_KEY"

# Stream real-time quotes (WebSocket)
wscat -c "wss://ws.finnhub.io?token=$FINNHUB_API_KEY"
# Then: {"type":"subscribe","symbol":"AAPL"}
```

### Python Integration
```python
import requests
from datetime import datetime, timedelta

class FinnhubAPI:
    BASE_URL = "https://finnhub.io/api/v1"
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.params = {"token": api_key}
    
    def get_company_news(self, symbol: str, days_back: int = 7):
        """Get news for a specific company"""
        to_date = datetime.now().strftime("%Y-%m-%d")
        from_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
        
        params = {
            **self.params,
            "symbol": symbol,
            "from": from_date,
            "to": to_date,
            "limit": 20
        }
        resp = requests.get(f"{self.BASE_URL}/company-news", params=params)
        return resp.json()
    
    def get_insider_transactions(self, symbol: str, limit: int = 10):
        """Get insider trading activity"""
        params = {**self.params, "symbol": symbol, "limit": limit}
        resp = requests.get(f"{self.BASE_URL}/insider-transactions", params=params)
        return resp.json()
    
    def get_insider_sentiment(self, symbol: str):
        """Get insider sentiment for stock"""
        params = {**self.params, "symbol": symbol}
        resp = requests.get(f"{self.BASE_URL}/insider-sentiment", params=params)
        return resp.json()
    
    def get_general_news(self, category: str = "general", limit: int = 20):
        """Get general market news"""
        params = {**self.params, "category": category, "limit": limit}
        resp = requests.get(f"{self.BASE_URL}/news", params=params)
        return resp.json()

# Usage
import os
fh = FinnhubAPI(os.environ['FINNHUB_API_KEY'])
news = fh.get_company_news("AAPL", days_back=3)
print(f"Found {len(news)} articles about AAPL")
for article in news[:3]:
    print(f"  - {article['headline']} ({article['source']})")
```

### Endpoints
| Endpoint | Purpose | Free Tier |
|----------|---------|-----------|
| `/news` | General market news | ✅ |
| `/company-news` | Stock-specific news | ✅ |
| `/insider-transactions` | Form 4/insider trades | ✅ |
| `/insider-sentiment` | Insider sentiment score | ✅ |
| `/quote` | Real-time quote | ✅ |
| `/earnings-calendar` | Earnings dates | ✅ |

---

## 3. MarketAux (⏳ Sign Up Required - 5 min)

### Setup
1. Register: https://www.marketaux.com/
2. Copy API token
3. Store: `export MARKETAUX_API_TOKEN="your_token_here"`

### Basic Usage
```bash
# Get all news (limit 50)
curl "https://api.marketaux.com/v1/news/all?api_token=$MARKETAUX_API_TOKEN&limit=50"

# Get news for specific stocks
curl "https://api.marketaux.com/v1/news/all?symbols=AAPL,TSLA&api_token=$MARKETAUX_API_TOKEN"

# Get news by category
curl "https://api.marketaux.com/v1/news/all?category=earnings&api_token=$MARKETAUX_API_TOKEN"
```

### Python Integration
```python
import requests
import json

class MarketAuxAPI:
    BASE_URL = "https://api.marketaux.com/v1"
    
    def __init__(self, api_token: str):
        self.api_token = api_token
    
    def get_news(self, symbols: list = None, category: str = None, limit: int = 50, page: int = 1):
        """Get news articles"""
        params = {
            "api_token": self.api_token,
            "limit": limit,
            "page": page
        }
        if symbols:
            params["symbols"] = ",".join(symbols)
        if category:
            params["category"] = category
        
        resp = requests.get(f"{self.BASE_URL}/news/all", params=params)
        return resp.json()
    
    def get_stock_news(self, symbol: str, limit: int = 20):
        """Get news for specific stock"""
        return self.get_news(symbols=[symbol], limit=limit)
    
    def get_earnings_news(self, limit: int = 50):
        """Get earnings-related news"""
        return self.get_news(category="earnings", limit=limit)
    
    def parse_entities(self, article: dict):
        """Extract stock symbols from article"""
        return article.get("entities", [])

# Usage
import os
ma = MarketAuxAPI(os.environ['MARKETAUX_API_TOKEN'])
articles = ma.get_stock_news("TSLA", limit=5)
print(f"Found {articles['count']} articles about TSLA")
for article in articles.get('data', [])[:3]:
    print(f"  - {article['title']}")
    print(f"    Source: {article['source']}")
    print(f"    Published: {article['published_at']}")
```

---

## 4. Combined Implementation (Recommended)

```python
import os
import requests
import json
from typing import List, Dict
from datetime import datetime, timedelta

class AlphaSniperDataAggregator:
    """Aggregate data from multiple APIs for signal detection"""
    
    def __init__(self):
        self.sec = SECEdgarAPI()
        self.finnhub = FinnhubAPI(os.environ.get('FINNHUB_API_KEY', ''))
        self.marketaux = MarketAuxAPI(os.environ.get('MARKETAUX_API_TOKEN', ''))
    
    def scan_insider_activity(self, symbol: str, cik: str) -> Dict:
        """Check for recent insider transactions"""
        company_data = self.sec.get_company_filings(cik)
        insider_txns = self.sec.extract_insider_transactions(company_data)
        
        return {
            'symbol': symbol,
            'cik': cik,
            'recent_insider_filings': insider_txns,
            'insider_sentiment': self.finnhub.get_insider_sentiment(symbol)
        }
    
    def scan_material_events(self, symbol: str, cik: str) -> Dict:
        """Check for 8-K material events"""
        company_data = self.sec.get_company_filings(cik)
        eight_k = self.sec.extract_8k_filings(company_data)
        
        return {
            'symbol': symbol,
            'material_events_8k': eight_k,
            'latest_news': self.finnhub.get_company_news(symbol, days_back=7)
        }
    
    def scan_market_reaction(self, symbol: str) -> Dict:
        """Check market news and sentiment"""
        finnhub_news = self.finnhub.get_company_news(symbol)
        marketaux_news = self.marketaux.get_stock_news(symbol)
        
        return {
            'symbol': symbol,
            'finnhub_articles': len(finnhub_news),
            'marketaux_articles': marketaux_news.get('count', 0),
            'latest_sources': list(set([
                a.get('source') for a in finnhub_news[:5]
            ]))
        }
    
    def full_scan(self, symbol: str, cik: str) -> Dict:
        """Run complete analysis"""
        print(f"Scanning {symbol}...")
        
        return {
            'timestamp': datetime.now().isoformat(),
            'symbol': symbol,
            'insider_activity': self.scan_insider_activity(symbol, cik),
            'material_events': self.scan_material_events(symbol, cik),
            'market_reaction': self.scan_market_reaction(symbol),
        }

# Usage Example
if __name__ == "__main__":
    # Set environment variables first:
    # export FINNHUB_API_KEY="your_key"
    # export MARKETAUX_API_TOKEN="your_token"
    
    scanner = AlphaSniperDataAggregator()
    
    # Scan AAPL
    results = scanner.full_scan("AAPL", "0000320193")
    print(json.dumps(results, indent=2))
```

---

## 5. Environment Setup

### Create `.env` file
```bash
# SEC EDGAR (no auth needed)
SEC_EDGAR_USER_AGENT="AlphaSniper/1.0 (Research Bot)"

# Finnhub (sign up at https://finnhub.io/register)
FINNHUB_API_KEY="your_api_key_here"

# MarketAux (sign up at https://www.marketaux.com/)
MARKETAUX_API_TOKEN="your_token_here"
```

### Load environment
```bash
# Create .env
cat > .env << 'EOF'
FINNHUB_API_KEY="your_key"
MARKETAUX_API_TOKEN="your_token"
EOF

# Load
set -a
source .env
set +a
```

---

## 6. Rate Limiting & Best Practices

### Request Limits
| API | Limit | Recommendation |
|-----|-------|-----------------|
| SEC EDGAR | 10 req/sec | Poll every 60 seconds |
| Finnhub | 60 req/min | 1 req/sec safe |
| MarketAux | 60 req/min | 1 req/sec safe |

### Implementation
```python
import time
from functools import wraps

def rate_limit(calls_per_second: float):
    """Decorator to rate limit API calls"""
    min_interval = 1.0 / calls_per_second
    last_called = [0.0]
    
    def decorator(func):
        def wrapper(*args, **kwargs):
            elapsed = time.time() - last_called[0]
            if elapsed < min_interval:
                time.sleep(min_interval - elapsed)
            result = func(*args, **kwargs)
            last_called[0] = time.time()
            return result
        return wrapper
    return decorator

class RateLimitedAPI:
    @rate_limit(1)  # 1 request per second
    def get_data(self, url: str):
        return requests.get(url).json()
```

---

## 7. Error Handling

```python
def safe_api_call(func, max_retries: int = 3, backoff: float = 2.0):
    """Retry logic with exponential backoff"""
    for attempt in range(max_retries):
        try:
            return func()
        except requests.exceptions.ConnectionError:
            if attempt < max_retries - 1:
                wait_time = backoff ** attempt
                print(f"Connection error, retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                raise
        except requests.exceptions.Timeout:
            print("Request timeout")
            return None
        except Exception as e:
            print(f"Unexpected error: {e}")
            return None
```

---

## Quick Start Checklist

- [ ] Download SEC EDGAR samples from `/research/api-samples/`
- [ ] Test SEC EDGAR API (no auth needed)
- [ ] Sign up for Finnhub free tier (~5 min)
- [ ] Sign up for MarketAux free tier (~5 min)
- [ ] Create `.env` with API keys
- [ ] Test each API individually
- [ ] Implement data aggregator
- [ ] Set up alert system for insider activity
- [ ] Set up alert system for material events (8-K)
- [ ] Monitor market sentiment from news feeds

---

## References

- SEC EDGAR: https://data.sec.gov/
- Finnhub: https://finnhub.io/docs/api
- MarketAux: https://www.marketaux.com/

**Last Updated:** 2026-04-11
