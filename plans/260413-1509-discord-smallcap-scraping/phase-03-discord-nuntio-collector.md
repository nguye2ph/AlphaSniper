# Phase 02 — Discord NuntioBot Collector

## Context Links
- Base collector: `src/collectors/base_collector.py`
- Finnhub WS (shutdown pattern reference): `src/collectors/finnhub_ws.py`
- Market cap cache (Phase 1): `src/collectors/market-cap-cache.py`
- Config: `src/core/config.py`
- Docker: `docker-compose.yml`
- Discord research: `plans/260413-1509-discord-smallcap-scraping/research/researcher-discord-scraping.md`
- Brainstorm: `plans/reports/brainstorm-260413-1509-discord-nuntio-scraping.md`

## Overview
- **Priority**: P1
- **Status**: pending
- **Effort**: 3h
- **Depends on**: Phase 1 (MarketCapCache must exist)
- Passive Discord selfbot listener using `discord.py-self`. Monitors NuntioBot output channels, parses message format, filters by market cap, saves to MongoDB raw zone.

## Key Insights
- `discord.py-self` conflicts with `discord.py` bot library — ensure only one is installed
- NuntioBot message format (from brainstorm): `4.6 M 🇺🇸 RBNE : Robin Energy Ltd. Announces...`
  - Pattern: `{mc_value} {mc_unit} {country_flag} {TICKER} : {headline} - {link}`
  - mc_unit: `M` = millions, `B` = billions, `K` = thousands
- NuntioBot may use Discord embeds OR plain text — parser must handle both
- `on_message` passive listener only — **no sends, no reactions** (Very Low ban risk)
- Run in `discord-listener` Docker service separate from `collector` (avoids conflict)
- User token stored in `.env` as `DISCORD_TOKEN` — never in code
- `DISCORD_CHANNEL_IDS` is a comma-separated list of channel IDs (strings)

## Requirements

### Functional
- `discord_token: str = ""` in Settings
- `discord_channel_ids: list[str] = []` in Settings
- `DiscordNuntioCollector` extends `BaseCollector`, `source_name = "discord_nuntio"`
- On message: check channel ID in watched list + author is NuntioBot
- Parse message text via `NuntioMessageParser`
- Skip if market_cap > limit (use direct parsed value, not API call)
- `save_raw()` with structured payload
- Graceful SIGTERM/SIGINT shutdown (mirror `finnhub_ws.py` pattern)

### Non-functional
- `discord.py-self` is user-account only — use throwaway account
- No message history reads — `on_message` only (safest pattern)
- Bot detection: do not set custom User-Agent or fingerprint overrides

## Architecture

```
Discord Gateway (WSS) ← discord.py-self client
        ↓ on_message event
  channel_id in DISCORD_CHANNEL_IDS?
        ↓ yes
  message.author matches NuntioBot?
        ↓ yes
  NuntioMessageParser.parse(message)
        ↓
  parsed.market_cap > settings.market_cap_limit? → skip
        ↓
  BaseCollector.save_raw(source_id=msg_id, payload=parsed_dict)
        ↓
  MongoDB raw_articles (source="discord_nuntio")
```

## Related Code Files

### Create
- `src/collectors/discord-nuntio.py` — Discord selfbot collector
- `src/parsers/nuntio-message-parser.py` — NuntioBot message regex parser

### Modify
- `src/core/config.py` — add `discord_token`, `discord_channel_ids`, `nuntio_bot_name`
- `docker-compose.yml` — add `discord-listener` service
- `.env.example` — add Discord vars

### pyproject.toml
- Add `"discord.py-self>=2.1.0"` to `[project.dependencies]`

## Implementation Steps

### 1. pyproject.toml
Add to `[project.dependencies]`:
```toml
"discord.py-self>=2.1.0",
```
Run `uv sync` to install.

### 2. config.py additions
```python
# Discord listener (NuntioBot scraping)
discord_token: str = ""
discord_channel_ids: list[str] = []
nuntio_bot_name: str = "NuntioBot"  # Match by username; fallback if ID unknown
```

### 3. Create `src/parsers/nuntio-message-parser.py`

**NuntioBot message formats to handle:**
```
# Format A (plain text, most common):
4.6 M 🇺🇸 RBNE : Robin Energy Ltd. Announces Availability of its Annual Report - https://...

# Format B (no link):
12.3 M 🇨🇦 XYZ : Some Company Announces Q1 Results

# Format C (embed) — content in embed.description or embed.fields
# Handle embed fallback: if message.content empty, check message.embeds[0].description
```

**Regex patterns:**
```python
# Market cap: "4.6 M", "1.2 B", "850 K"
MC_PATTERN = re.compile(r'^([\d,]+\.?\d*)\s+([KMB])\b', re.IGNORECASE)

# Country flag emoji (Unicode regional indicators A-Z)
FLAG_PATTERN = re.compile(r'[\U0001F1E0-\U0001F1FF]{2}')

# Ticker: 1-5 uppercase letters after flag
TICKER_PATTERN = re.compile(r'\b([A-Z]{1,5})\s*:')

# Link at end
LINK_PATTERN = re.compile(r'(https?://\S+)$')
```

**`NuntioMessageParser` class:**
```python
# parse(content: str) -> NuntioAlert | None
# NuntioAlert(BaseModel):
#   market_cap: float
#   market_cap_raw: str  # "4.6 M" for debugging
#   ticker: str
#   country_flag: str
#   headline: str
#   link: str | None
# Returns None if parse fails (log warning)
```

Unit multiply: K=1_000, M=1_000_000, B=1_000_000_000

### 4. Create `src/collectors/discord-nuntio.py`

```python
class DiscordNuntioCollector(BaseCollector):
    source_name = "discord_nuntio"

    def __init__(self):
        self.token = settings.discord_token
        self.channel_ids = set(settings.discord_channel_ids)
        self.bot_name = settings.nuntio_bot_name
        self.limit = settings.market_cap_limit
        self._shutdown = asyncio.Event()
        self._client: discord.Client | None = None

    async def collect(self) -> None:
        # Create discord.Client (discord.py-self)
        # Register on_ready and on_message events
        # Run client with self.token
        # Handle shutdown via _shutdown event

    async def _on_ready(self):
        logger.info("discord_connected", user=str(self._client.user))

    async def _on_message(self, message):
        # 1. Check channel
        if str(message.channel.id) not in self.channel_ids:
            return
        # 2. Check author is NuntioBot
        if message.author.bot and self.bot_name.lower() in message.author.name.lower():
            content = message.content or _get_embed_text(message)
            if not content:
                return
            # 3. Parse
            alert = NuntioMessageParser().parse(content)
            if not alert:
                return
            # 4. Market cap filter
            if alert.market_cap > self.limit:
                logger.debug("mcap_filtered", ticker=alert.ticker, mc=alert.market_cap)
                return
            # 5. Save
            await self.save_raw(
                source_id=str(message.id),
                payload=alert.model_dump() | {"channel_id": str(message.channel.id)}
            )

    def shutdown(self) -> None:
        self._shutdown.set()
        if self._client:
            asyncio.create_task(self._client.close())
```

**`_get_embed_text(message) -> str`** — extract text from first embed description/fields if message.content is empty.

**`main()`** — mirrors `finnhub_ws.py`:
```python
async def main():
    collector = DiscordNuntioCollector()
    await collector.setup()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, collector.shutdown)
    try:
        await collector.collect()
    finally:
        await collector.teardown()
```

### 5. docker-compose.yml — add service
```yaml
discord-listener:
  build: .
  env_file: .env
  environment:
    MONGO_URI: mongodb://mongo:27017
    REDIS_URL: redis://redis:6379/0
  depends_on:
    mongo:
      condition: service_healthy
    redis:
      condition: service_healthy
  command: uv run python -m src.collectors.discord_nuntio
  restart: unless-stopped
```

### 6. taskiq_app.py — add source handlers

In `_extract_headline()`:
```python
elif source == "discord_nuntio":
    return payload.get("headline", "")
```

In `_extract_timestamp()`:
```python
elif source == "discord_nuntio":
    # payload has no timestamp; use collected_at (already set by BaseCollector)
    return datetime.now(timezone.utc)
```

In `_extract_payload_tickers()`:
```python
elif source == "discord_nuntio":
    ticker = payload.get("ticker")
    return [ticker] if ticker else []
```

In `_extract_market_cap()` (new helper from Phase 1):
```python
elif source == "discord_nuntio":
    return payload.get("market_cap")
```

## Todo List
- [ ] Add `discord.py-self>=2.1.0` to `pyproject.toml` and run `uv sync`
- [ ] Add `discord_token`, `discord_channel_ids`, `nuntio_bot_name` to `config.py`
- [ ] Create `src/parsers/nuntio-message-parser.py` with `NuntioAlert` model + `NuntioMessageParser`
- [ ] Create `src/collectors/discord-nuntio.py` with `DiscordNuntioCollector`
- [ ] Add `discord-listener` service to `docker-compose.yml`
- [ ] Add Discord vars to `.env.example`
- [ ] Update `taskiq_app.py` `_extract_*` helpers for `discord_nuntio` source
- [ ] Write `tests/test_parsers/test_nuntio_message_parser.py` unit tests
- [ ] Write `tests/test_collectors/test_discord_nuntio.py` unit tests (mock discord client)

## Test Cases

### NuntioMessageParser

| Input | Expected ticker | Expected mc | Expected headline |
|-------|----------------|-------------|-------------------|
| `4.6 M 🇺🇸 RBNE : Robin Energy Ltd. Announces...` | RBNE | 4_600_000 | "Robin Energy Ltd. Announces..." |
| `1.2 B 🇨🇦 XYZ : Company Announces Q1` | XYZ | 1_200_000_000 | "Company Announces Q1" |
| `850 K 🇬🇧 AB : Small firm news - https://...` | AB | 850_000 | "Small firm news" |
| `invalid text no pattern` | None (parse fail) | — | — |
| Empty string | None | — | — |
| Embed description with valid format | Parsed normally | — | — |

### DiscordNuntioCollector

| Scenario | Expected |
|----------|----------|
| Message from wrong channel | Ignored (no save) |
| Message from non-NuntioBot author | Ignored |
| Valid NuntioBot message, mc=4.6M < 100M | `save_raw()` called |
| Valid NuntioBot message, mc=200M > 100M | Filtered, no save |
| Parse failure on malformed message | No save, warning logged |
| SIGTERM received | `shutdown()` called, client closed |

## Verification Steps
1. `uv run python -c "import discord; print(discord.__version__)"` — confirm discord.py-self installed
2. Set `DISCORD_TOKEN` and `DISCORD_CHANNEL_IDS` in `.env`
3. `uv run python -m src.collectors.discord_nuntio` — logs "discord_connected"
4. Send test message in watched channel (or wait for NuntioBot) — verify MongoDB insert
5. `docker compose up discord-listener -d` — service starts, no crash
6. `uv run pytest tests/test_parsers/test_nuntio_message_parser.py -v` — all pass

## Acceptance Criteria
- [ ] `NuntioMessageParser.parse("4.6 M 🇺🇸 RBNE : Headline - https://link")` returns NuntioAlert with mc=4_600_000, ticker="RBNE"
- [ ] Messages from non-NuntioBot authors not saved
- [ ] Messages in unlisted channels not saved
- [ ] Articles with mc > 100M not saved (filtered at collector)
- [ ] `docker compose up discord-listener` runs without error
- [ ] `source="discord_nuntio"` articles appear in MongoDB after valid message

## Risk Assessment
| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| NuntioBot message format differs from expected | High | Build parser with fallback; log raw content on parse fail for inspection |
| Discord bans throwaway account | Low | Read-only, on_message only; use residential IP |
| discord.py-self API changes silently | Medium | Pin to `2.1.0`; monitor repo for breaking changes |
| Embed-only messages missed | Medium | `_get_embed_text()` fallback handles embed content |
| Token leaked in logs | Low | Never log `discord_token`; log only `user.id` |

## Security Considerations
- `DISCORD_TOKEN` loaded from `.env` only, never hardcoded or logged
- Throwaway account only — not personal Discord account
- Read-only: no message sends, reactions, or history reads
- Docker service has no external port exposure

## Next Steps
- After deploy: monitor MongoDB for `source="discord_nuntio"` documents
- If NuntioBot format differs from regex assumptions: update `nuntio-message-parser.py` and re-deploy
- Phase 4: wire `discord-listener` into full docker-compose deploy
