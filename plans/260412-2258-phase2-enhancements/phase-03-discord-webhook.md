# Phase 3: Discord Webhook (Outbound Alerts)

## Context Links

- [Brainstorm — Part 2B](../reports/brainstorm-260412-2258-ui-upgrade-discord.md)
- [Taskiq Jobs](../../src/jobs/taskiq_app.py)
- [Config](../../src/core/config.py)

## Overview

- **Priority**: P2
- **Status**: pending
- **Effort**: 1h
- **Description**: Push filtered article alerts to a Discord channel via webhook. Rich embeds with sentiment color-coding.

## Key Insights

- Discord webhooks are simple HTTP POST — no bot/library needed
- httpx already available for async HTTP
- Filter rules: only send articles with strong sentiment or specific tickers
- Can integrate directly into `process_raw_articles` job after article insert
- Embed color: green (0x22C55E) for bullish, red (0xEF4444) for bearish, gray (0x6B7280) for neutral

## Requirements

### Functional
- Send rich embed to Discord webhook when article matches filter rules
- Filter: sentiment > 0.5 or < -0.5, or article has watched ticker
- Embed fields: ticker, sentiment score + label, source, category, URL
- Color-coded border: green/red/gray by sentiment

### Non-Functional
- Non-blocking: webhook failure must not block article processing
- Rate limit: Discord allows 30 webhooks/min — unlikely to hit
- Configurable: webhook URL + filter rules via env vars

## Architecture

```
process_raw_articles (existing)
  → Article inserted to PostgreSQL
  → Check filter rules (sentiment threshold, ticker watchlist)
  → If match: POST Discord webhook with embed JSON
  → Log success/failure, never block pipeline
```

## Related Code Files

### Modify
- `src/core/config.py` — add DISCORD_WEBHOOK_URL, DISCORD_SENTIMENT_THRESHOLD
- `src/jobs/taskiq_app.py` — call discord_notify after article insert

### Create
- `src/jobs/discord_notify.py` — send_discord_alert() function

## Implementation Steps

### Step 1: Config (5min)

Add to `Settings` in `src/core/config.py`:
```python
discord_webhook_url: str = ""  # Empty = disabled
discord_sentiment_threshold: float = 0.5  # Only send if |sentiment| > threshold
```

### Step 2: Discord Notify Module (30min)

Create `src/jobs/discord_notify.py` (<100 lines):

1. `async def send_discord_alert(article: Article) -> bool`
   - Build embed JSON with:
     - title: "{emoji} ${TICKER} {sentiment_label}" (e.g., "🟢 $AAPL Bullish +0.85")
     - description: article.headline
     - color: 0x22C55E (bullish), 0xEF4444 (bearish), 0x6B7280 (neutral)
     - fields: Source, Category, Sentiment (inline)
     - url: article.url
     - timestamp: article.published_at.isoformat()
   - POST to webhook URL with httpx
   - Return True on success, False on failure
   - Log errors, never raise

2. `def should_notify(article: Article) -> bool`
   - Return False if no webhook URL configured
   - Return True if `abs(sentiment) > threshold`
   - Return True if any ticker in watchlist (future, from admin settings)

### Step 3: Integrate into Pipeline (15min)

In `src/jobs/taskiq_app.py`, after `session.add(article); await session.commit()`:
```python
from src.jobs.discord_notify import should_notify, send_discord_alert

if should_notify(article):
    await send_discord_alert(article)
```

### Step 4: Add .env (5min)

Add to `.env.example`:
```
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/xxx/yyy
DISCORD_SENTIMENT_THRESHOLD=0.5
```

## Todo List

- [ ] Add Discord config to Settings
- [ ] Create discord_notify.py module
- [ ] Integrate should_notify + send_discord_alert into process_raw_articles
- [ ] Add to .env.example
- [ ] Test with real webhook URL

## Test Cases

- **Bullish article**: sentiment 0.8 → green embed sent with correct fields
- **Bearish article**: sentiment -0.7 → red embed sent
- **Neutral article**: sentiment 0.2 → not sent (below threshold)
- **No webhook URL**: All articles skipped silently
- **Webhook failure**: Error logged, pipeline continues

## Verification Steps

1. Create test webhook in Discord server (Settings → Integrations → Webhooks)
2. Set DISCORD_WEBHOOK_URL in .env
3. Process an article with high sentiment
4. Verify embed appears in Discord channel with correct color/fields
5. Test with invalid webhook URL — verify pipeline doesn't break

## Acceptance Criteria

- [ ] Discord embeds sent for high-sentiment articles
- [ ] Color matches sentiment (green/red/gray)
- [ ] Pipeline never blocks on webhook failure
- [ ] Disabled when DISCORD_WEBHOOK_URL is empty

## Success Criteria

- Alerts appear in Discord within seconds of article processing
- Zero pipeline failures due to webhook errors

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Discord rate limit | Low — 30/min is generous | Unlikely to hit with current volume |
| Webhook URL leaked | High — anyone can post to channel | Store in .env, never commit |
| Alert fatigue | Medium — too many alerts | Configurable threshold, future: ticker filter |

## Security Considerations

- DISCORD_WEBHOOK_URL is a secret — never log or expose
- Validate URL format before POSTing

## Next Steps

- Phase 4 (Discord bot) reuses config pattern
- Phase 5 (admin) adds UI for configuring threshold + watchlist
