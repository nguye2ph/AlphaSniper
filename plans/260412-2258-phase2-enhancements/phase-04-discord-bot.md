# Phase 4: Discord Bot (Inbound Collection)

## Context Links

- [Brainstorm — Part 2A](../reports/brainstorm-260412-2258-ui-upgrade-discord.md)
- [BaseCollector](../../src/collectors/base_collector.py)
- [Config](../../src/core/config.py)
- [Docker Compose](../../docker-compose.yml)

## Overview

- **Priority**: P2
- **Status**: pending
- **Effort**: 3h
- **Description**: Discord bot that joins server(s), listens for news messages in specific channels, extracts tickers + text, saves to MongoDB raw zone for pipeline processing.

## Key Insights

- `discord.py` is the standard Python Discord library — async, well-maintained
- Bot extends `BaseCollector` pattern — save_raw() to MongoDB, pipeline handles rest
- Needs `MESSAGE_CONTENT` privileged intent (enable in Discord Developer Portal)
- For <100 servers: just enable intent in portal, no verification needed
- Bot runs as standalone Docker service (like collector)
- Message parsing: extract `$TICKER` patterns, URLs, full text as payload

## Requirements

### Functional
- Bot connects to Discord, monitors configured channels
- Extract from messages: text, `$TICKER` mentions, embedded URLs, author
- Save raw message payload to MongoDB `raw_articles` collection
- Dedup: skip if message ID already processed
- Graceful reconnect on disconnect
- Configurable channel IDs via env var

### Non-Functional
- Persistent connection — auto-reconnect with exponential backoff
- Low memory footprint — don't cache message history
- Graceful shutdown on SIGTERM

## Architecture

```
Discord Server
  → Bot (discord.py Client)
    → on_message event
    → Filter: only configured channel IDs
    → Parse: extract tickers ($XXX), URLs, text
    → Dedup: check message.id in MongoDB
    → save_raw(source_id=message.id, payload={...})
    → Enqueue to Taskiq for parsing
```

```
Docker Compose:
  discord-bot:
    command: uv run python -m src.collectors.discord_bot
    depends_on: [mongo, redis]
```

## Related Code Files

### Modify
- `src/core/config.py` — add DISCORD_BOT_TOKEN, DISCORD_CHANNEL_IDS
- `docker-compose.yml` — add discord-bot service
- `src/jobs/taskiq_app.py` — handle source="discord" in _extract_headline, _extract_timestamp, _extract_payload_tickers

### Create
- `src/collectors/discord_bot.py` — DiscordCollector class

## Implementation Steps

### Step 1: Add discord.py Dependency (5min)

```bash
uv add discord.py
```

### Step 2: Config (10min)

Add to `Settings` in `src/core/config.py`:
```python
discord_bot_token: str = ""  # Empty = bot disabled
discord_channel_ids: list[str] = []  # Channel IDs to monitor
```

### Step 3: Discord Bot Collector (2h)

Create `src/collectors/discord_bot.py` (<200 lines):

1. `class DiscordCollector(BaseCollector)`:
   - `source_name = "discord"`
   - `__init__`: init discord.Client with intents (MESSAGE_CONTENT, GUILDS)

2. `async def collect(self)`:
   - Setup on_ready, on_message handlers
   - Start bot with `self.client.start(token)`
   - Handle KeyboardInterrupt → graceful shutdown

3. `async def on_message(self, message)`:
   - Skip bot messages (`message.author.bot`)
   - Skip channels not in `DISCORD_CHANNEL_IDS`
   - Extract payload:
     ```python
     payload = {
         "text": message.content,
         "author": str(message.author),
         "channel": str(message.channel),
         "guild": str(message.guild),
         "tickers": extract_tickers_from_text(message.content),
         "urls": extract_urls(message.content),
         "attachments": [a.url for a in message.attachments],
         "timestamp": message.created_at.isoformat(),
     }
     ```
   - Call `self.save_raw(source_id=str(message.id), payload=payload)`
   - Enqueue to Taskiq for processing

4. `def extract_tickers_from_text(text: str) -> list[str]`:
   - Regex: `\$([A-Z]{1,5})` — match $AAPL, $TSLA patterns
   - Return list of symbols (without $)

5. `def extract_urls(text: str) -> list[str]`:
   - Regex: `https?://[^\s]+`
   - Return list of URLs found in message

6. `if __name__ == "__main__"`:
   - Entry point for Docker service
   - `asyncio.run(main())` — init collector, setup, collect

### Step 4: Pipeline Integration (30min)

Update `src/jobs/taskiq_app.py`:

1. In `_extract_headline(source, payload)`:
   ```python
   elif source == "discord":
       return payload.get("text", "")[:200]  # Truncate long messages
   ```

2. In `_extract_timestamp(source, payload)`:
   ```python
   elif source == "discord":
       ts = payload.get("timestamp", "")
       if ts:
           return datetime.fromisoformat(ts)
   ```

3. In `_extract_payload_tickers(source, payload)`:
   ```python
   elif source == "discord":
       return payload.get("tickers", [])
   ```

### Step 5: Docker Service (15min)

Add to `docker-compose.yml`:
```yaml
discord-bot:
  build: .
  command: uv run python -m src.collectors.discord_bot
  env_file: .env
  depends_on:
    - mongo
    - redis
  restart: unless-stopped
```

## Todo List

- [ ] Add discord.py to pyproject.toml
- [ ] Add Discord bot config to Settings
- [ ] Create discord_bot.py collector
- [ ] Update taskiq_app.py for source="discord"
- [ ] Add discord-bot service to docker-compose.yml
- [ ] Create Discord Application at discord.com/developers
- [ ] Enable MESSAGE_CONTENT intent
- [ ] Test with own server

## Test Cases

- **Normal message**: "$AAPL breaking news" → saved with ticker=["AAPL"], text stored
- **No tickers**: "Market update" → saved with empty tickers, text stored
- **Bot message**: Skipped (author.bot = True)
- **Wrong channel**: Message in non-monitored channel → skipped
- **Multiple tickers**: "$AAPL $TSLA merger" → tickers=["AAPL", "TSLA"]
- **URL extraction**: Message with link → urls field populated
- **Disconnect**: Bot reconnects automatically
- **Duplicate message ID**: Skipped by save_raw dedup

## Verification Steps

1. Create Discord Application at discord.com/developers
2. Create Bot user, copy token to .env
3. Enable MESSAGE_CONTENT intent in Bot settings
4. Invite bot to test server with correct permissions
5. Set DISCORD_CHANNEL_IDS to test channel ID
6. Run: `uv run python -m src.collectors.discord_bot`
7. Post message with $TICKER in channel
8. Check MongoDB: `raw_articles` has new document with source="discord"
9. Run process_raw_articles → check PostgreSQL has article

## Acceptance Criteria

- [ ] Bot connects and stays connected to Discord
- [ ] Messages from configured channels saved to MongoDB
- [ ] Tickers extracted from $SYMBOL patterns
- [ ] URLs extracted from message content
- [ ] Bot messages ignored
- [ ] Non-configured channels ignored
- [ ] Auto-reconnect on disconnect
- [ ] Pipeline processes discord source correctly

## Success Criteria

- Bot stays connected 24/7 with auto-reconnect
- All messages from monitored channels captured
- Pipeline processes discord articles same as other sources

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Bot token leaked | Critical — full bot access | .env only, never commit |
| Server bans bot | High — data source lost | Own server: full control |
| MESSAGE_CONTENT denied | High — can't read messages | Enable in developer portal |
| High message volume | Medium — MongoDB bloat | Consider filtering (keywords/tickers only) |

## Security Considerations

- DISCORD_BOT_TOKEN is a critical secret — .env only
- Bot should have minimal permissions (Read Messages only)
- Don't store user PII beyond username
- Rate limit processing if message volume is high

## Next Steps

- Phase 6 determines if Nuntio server allows this bot
- Future: slash commands for querying articles from Discord
- Future: reaction-based sentiment tagging
