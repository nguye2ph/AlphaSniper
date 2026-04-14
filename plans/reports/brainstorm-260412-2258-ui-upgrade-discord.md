# Brainstorm: UI Upgrade + Discord Integration
**Date:** 2026-04-12 | **Status:** Complete

---

## Part 1: UI Upgrade — Trading Terminal Style

### Problem
Current webapp is functional but plain. Needs "pro trader" aesthetic: data-dense, visually engaging, finance-grade.

### Design Direction: Bloomberg/TradingView Terminal

**Visual Elements:**
- Glassmorphism cards (frosted glass effect with backdrop-blur)
- Neon accent borders (green/red glow for sentiment)
- Grid-based dashboard layout (resizable panels)
- Animated number counters for KPIs
- Subtle gradient backgrounds on cards
- Monospace font for all data values
- Micro-animations on hover/transitions
- Sparkline mini-charts in KPI cards
- Pulsing dot for "live" data indicators
- Color-coded table rows by sentiment

**Specific Improvements per Page:**

#### Dashboard
- Replace flat KPI cards → glassmorphism with neon border glow
- Add sparkline mini-charts inside KPI cards (7-day trend)
- Animated counter for numbers (count up on load)
- Live indicator dot (pulsing green) next to "Articles Today"
- Full-width sentiment trend chart (Recharts area chart with gradient fill)
- Top tickers as horizontal bar chart with sentiment color

#### News Feed
- Ticker badges with colored backgrounds (not just outline)
- Sentiment bar on left edge of each card (vertical color strip)
- Hover effects: card lifts slightly + glow
- Timestamp as relative ("3m ago") with tooltip for absolute
- Source icon/logo next to source name
- Infinite scroll instead of pagination

#### Ticker Detail
- Hero header with large ticker + animated sentiment badge
- Candlestick-style sentiment timeline (up/down bars)
- Stats in horizontal pill badges, not boxes

#### Sentiment
- Replace simple gauge → animated radial gauge (SVG)
- Heatmap grid: tickers × hours, color intensity = sentiment
- Animated transitions between states

### Tech Additions
- `framer-motion` — animations, transitions, layout animations
- `@number-flow/react` — animated number counters
- CSS: backdrop-blur, box-shadow with colored glow, gradients
- Keep shadcn/ui as base, add custom variants

### Implementation Effort: ~4-6h
One phase: iterate on existing components, add animations + glassmorphism.

---

## Part 2: Discord Integration

### A. Inbound: Collecting News FROM Discord

**Approach: Official Discord Bot (discord.py)**

How it works:
1. Create Discord Application + Bot at discord.com/developers
2. Bot joins target server (needs admin invite or user adds it)
3. Bot listens to specific channels for news messages
4. Parses message → extracts ticker, headline, metadata
5. Saves to MongoDB raw zone → same pipeline as other sources

**Feasibility:**
- For YOUR OWN server: 100% feasible, full control
- For Nuntio server: need to check if bots are allowed. Most paid servers block user bots.
- Alternative: If you have subscription, add YOUR bot to their server (if they allow)

**Architecture:**
```
Discord Server (messages) → Discord Bot (discord.py)
  → Parse message → Save to MongoDB → Pipeline → PostgreSQL
```

**Requirements:**
- Discord Bot Token (free at discord.com/developers)
- Bot needs MESSAGE_CONTENT intent (privileged, need verification for 100+ servers)
- For <100 servers: enable intent in developer portal, done
- New collector: `src/collectors/discord_bot.py`

**Risks:**
- Nuntio might not allow bots → need to check their rules
- Bot can only read channels it has access to
- If server bans bot, data source lost

### B. Outbound: Pushing Alerts TO Discord

**Approach: Discord Webhook**

How it works:
1. Create webhook URL in YOUR Discord server (Settings → Integrations → Webhooks)
2. Pipeline sends HTTP POST with formatted message when interesting news detected
3. Rich embed with ticker, sentiment, headline, source link

**Architecture:**
```
PostgreSQL (new article) → Filter rules → Discord Webhook POST
  → Your Discord channel (rich embed message)
```

**Implementation:**
- Add webhook URL to config
- New job: `src/jobs/discord_notify.py`
- Filter: only push articles matching rules (e.g., sentiment > 0.5, specific tickers, category = earnings)
- Format: Discord embed with color-coded sentiment

**This is trivial** — ~1h to implement. Just HTTP POST with JSON payload.

### C. Recommended Combined Approach

```
Phase 1 (Easy, 1h): Outbound webhook — push filtered alerts to YOUR Discord
Phase 2 (Medium, 3h): Inbound bot — create bot, join YOUR server, collect from your curated channels
Phase 3 (Depends): Try joining Nuntio — IF they allow bots, add as data source
```

**Webhook embed example:**
```json
{
  "embeds": [{
    "title": "🟢 $AAPL +0.85 — Bullish",
    "description": "Apple beats Q3 earnings expectations with record revenue",
    "color": 2278665,
    "fields": [
      {"name": "Source", "value": "Finnhub", "inline": true},
      {"name": "Category", "value": "Earnings", "inline": true}
    ],
    "url": "https://example.com/article",
    "timestamp": "2026-04-12T15:00:00Z"
  }]
}
```

---

## Part 3: Article Content Scraping

### Problem
Current pipeline only stores headline + short summary + URL. No full article content. Webapp shows minimal info — not useful for deep analysis.

### Solution: Content Scraper Pipeline

**New step after collector:**
1. Article saved to MongoDB with URL
2. Content Scraper fetches full page from URL
3. Extract: article body text, images, publish date, author
4. AI (Gemini) generates: key_points (3-5 bullets), detailed_sentiment, named_entities
5. Save enriched data to PostgreSQL

**Architecture:**
```
MongoDB (raw, has URL) → Taskiq job → httpx fetch URL
  → BeautifulSoup extract article body
  → Gemini API: extract key_points + entities
  → Update PostgreSQL article with content + key_points
```

**DB Schema additions:**
```sql
ALTER TABLE articles ADD COLUMN content TEXT;          -- full article body
ALTER TABLE articles ADD COLUMN key_points JSONB;      -- AI-extracted bullets
ALTER TABLE articles ADD COLUMN image_url TEXT;         -- thumbnail
ALTER TABLE articles ADD COLUMN author TEXT;            -- article author
ALTER TABLE articles ADD COLUMN content_scraped BOOLEAN DEFAULT FALSE;
```

**Challenges:**
- Some URLs redirect or are paywalled → skip gracefully
- JS-rendered pages need Playwright (heavier) → use httpx first, Playwright fallback
- Rate limiting: don't hammer news sites → 1 req/sec with delays
- Gemini cost: batch multiple articles per API call

**Webapp display improvements with content:**
- Article card expands to show full content (or first 500 chars)
- Key points as colored bullet badges
- Article thumbnail image
- "Read full article" link + inline preview

### Implementation Effort: ~4h
- New Alembic migration for content columns
- Content scraper job in Taskiq
- Gemini enrichment (reuse existing parser)
- Webapp card update to show content

---

## Summary of Next Steps

| Priority | Task | Effort | Type |
|----------|------|--------|------|
| 1 | Article content scraping + AI enrichment | 4h | Backend |
| 2 | UI upgrade: trading terminal style | 4-6h | Design |
| 3 | Discord webhook (outbound alerts) | 1h | Backend |
| 4 | Discord bot (inbound from own server) | 3h | Backend |
| 5 | Test Nuntio bot access | Research | Discovery |

---

## Unresolved Questions
1. Does Nuntio server allow user bots? Need to check their Discord rules
2. Framer Motion vs CSS-only animations? FM adds ~30KB bundle but much easier
3. Should webhook alerts have configurable filter rules? Or hardcode for MVP?
