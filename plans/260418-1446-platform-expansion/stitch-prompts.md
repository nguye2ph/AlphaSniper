# Google Stitch — Prompt Catalog for AlphaSniper UI

## Shared Base Prompt (prepend to every screen prompt)

```
Dark professional stock trading terminal dashboard. Background #0f172a (dark navy slate). Surface cards #1e293b with subtle border #334155. Text #f1f5f9 white. Primary accent #14b8a6 teal. Green #10b981 for bullish/positive/buy. Red #ef4444 for bearish/negative/sell. Neutral gray #64748b. Dense data layout. Use JetBrains Mono font for numbers/data, Inter for labels/headings. No gradients. Minimal rounded corners (6px). Clean table layouts with hover states. WCAG AA 4.5:1 contrast minimum. Modern fintech aesthetic like TradingView or Bloomberg terminal.
```

---

## Screen 1: Main Dashboard

```
[BASE PROMPT] + Stock news analytics dashboard with 4 KPI cards at top: "Articles Today" (newspaper icon), "Total Articles", "Avg Sentiment" (color-coded green/red), "Active Sources" (activity pulse icon). Below KPIs: 2x2 grid of chart cards — sentiment trend line chart (7 days, green/red area fill), articles per hour bar chart (24h, teal bars), top tickers horizontal bar chart, category breakdown donut chart. Bottom section: scrollable latest news feed with sentiment indicator dots (green/red/gray), market cap badges, truncated headlines. Left sidebar: dark vertical nav with app logo "ALPHASNIPER" crosshair icon, nav items with icons (Dashboard, News Feed, Sentiment, Insider Trades, Earnings, Short Interest, Options Flow, Sources, Scheduler, Settings). Sidebar is collapsible. Desktop 1440px width.
```

## Screen 2: Insider Trades Table

```
[BASE PROMPT] + Insider trades data table page. Header: "Insider Trades" title with subtitle "Recent SEC Form 4 filings". Full-width table with columns: Ticker (teal monospace bold), Officer Name, Title (dimmed), Type (badge: BUY green pill, SELL red pill, EXERCISE gray pill), Shares (right-aligned monospace with comma formatting), Price (dollar format), Value (color-coded green/red based on buy/sell), Filing Date (relative time "2h ago"). Table has alternating row hover states. Filter bar at top with ticker search input, transaction type dropdown (All/Buy/Sell), date range selector. Dense rows, professional data terminal feel. Show 15-20 sample rows with realistic stock data.
```

## Screen 3: Earnings Calendar

```
[BASE PROMPT] + Earnings calendar page. Header: "Earnings Calendar". Two sections: "Upcoming" (sorted by date ascending) and "Recent Results" (sorted by date descending). Table columns: Ticker (teal bold monospace), Report Date, Estimated EPS ($format), Actual EPS (shown only in Recent), Surprise % (green for positive surprise "+5.2%", red for negative "-3.1%", dash for pending). Upcoming section has countdown badges "in 3 days" "tomorrow". Card-style summary at top: total upcoming this week, average surprise %, most anticipated ticker. Clean timeline feel. Show 10 upcoming + 10 recent sample entries.
```

## Screen 4: Social Sentiment

```
[BASE PROMPT] + Social sentiment analysis page. Header: "Social Sentiment" subtitle "Reddit & StockTwits analysis". Top row: sentiment summary cards per platform — Reddit card (orange Reddit icon, post count, avg sentiment gauge), StockTwits card (StockTwits icon, message count, bullish/bearish ratio). Main content: scrollable feed of social posts with: platform icon, post title (truncated), sentiment badge (BULLISH green, BEARISH red, NEUTRAL gray), ticker tags (teal pills), post score/upvotes, subreddit name, relative time. Right sidebar or top: ticker search input. Sentiment breakdown pie chart (bullish vs bearish vs neutral). Professional analytics dashboard, not social media feed.
```

## Screen 5: Short Interest

```
[BASE PROMPT] + Short interest data page. Header: "Short Interest" subtitle "Daily ORTEX data". Feature cards at top: highest squeeze score ticker (with large number badge, red glow if >70), most shorted stock (% float), average days to cover. Main table: Ticker (teal bold), Short % of Float (color-coded: >20% red, 10-20% amber, <10% normal), Days to Cover (decimal), Borrow Fee % (decimal), Squeeze Score (circular badge: 0-100, red>70, amber 40-70, green<40), Report Date. Table sortable by any column. Squeeze score badges should be prominent — this is the key metric for traders. Show 10-15 sample rows.
```

## Screen 6: Options Flow

```
[BASE PROMPT] + Options flow page. Header: "Options Flow" subtitle "Unusual Whales data". Table: Ticker (teal), Contract (monospace, e.g. "TSLA 250425C180"), Strike Price, Expiry Date, Call/Put (badge: CALL green, PUT red), Volume (large number), Open Interest, Premium ($format, large values highlighted), Sentiment (bullish/bearish badge). Filter bar: ticker input, call/put toggle, date range. Summary cards: total volume today, total premium, call/put ratio, most active ticker. Dense professional options terminal layout.
```

## Screen 7: Scheduler Admin

```
[BASE PROMPT] + Admin scheduler configuration page. Header: "Adaptive Scheduler" subtitle "Source configuration & metrics". Table of all data sources: Source Name (bold), Status (green "Active" / red "Disabled" toggle badge), Current Interval (e.g. "5 min", "1 hr"), Min/Max bounds, Strategy (badge: "Auto" teal, "Manual" gray), EMA (decimal), Last Poll (relative time), Total Polls, Errors. Each row has an edit button that opens inline config. Metrics section below: polling activity sparklines per source, error rate badges. Clean admin panel aesthetic, not consumer-facing.
```

## Screen 8: Ticker Detail (Combined View)

```
[BASE PROMPT] + Single ticker detail page for "TSLA". Header: large ticker symbol "TSLA" with company name, price change badge. Below: tabbed or sectioned layout combining ALL data sources. Section 1: Latest News (3-5 articles with sentiment). Section 2: Social Sentiment (Reddit + StockTwits sentiment gauges, recent mentions). Section 3: Insider Activity (mini table of recent trades, buy/sell badges). Section 4: Short Interest (short % float, squeeze score, days to cover — card format). Section 5: Earnings (next earnings date, last EPS surprise). Section 6: Options Flow (recent unusual activity). All sections in a 2-column or 3-column grid. Dense but scannable. One-stop view for a trader evaluating a ticker.
```

---

## Component Prompts (Individual)

### Sentiment Gauge
```
[BASE PROMPT] + Circular or half-circle gauge showing sentiment score -1.0 to +1.0. Needle pointing to current value. Left side red "Bearish", right side green "Bullish", center gray "Neutral". Current value displayed large in center. Compact, 150x150px size. Used as a dashboard widget.
```

### Squeeze Score Badge
```
[BASE PROMPT] + Circular badge showing squeeze score 0-100. Number displayed large in center. Ring color: green (0-39, safe), amber (40-69, elevated), red (70-100, high squeeze risk). Pulsing glow effect on red scores. Small label below "Squeeze Score". Compact widget, 80x80px.
```

### KPI Card
```
[BASE PROMPT] + Single KPI metric card. Top: small icon + label in gray. Center: large bold number. Bottom: small trend indicator (up arrow green, down arrow red) with % change. Card background #1e293b, border #334155. Subtle hover lift effect. 200x120px size.
```

---

## Usage Instructions

1. Open Google Stitch (stitch.withgoogle.com)
2. Paste the **Shared Base Prompt** first
3. Append the screen-specific prompt
4. Generate 3-5 variants per screen
5. Select best direction, iterate
6. Export as HTML/CSS or Figma
7. Convert to React/shadcn/ui components
