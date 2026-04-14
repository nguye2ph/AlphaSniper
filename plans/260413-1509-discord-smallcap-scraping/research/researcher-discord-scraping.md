# Discord Selfbot/Scraping Research
Date: 2026-04-12

## 1. Selfbot Libraries — Comparison

| Library | Repo | Stars (approx) | Last Active | Python | Status |
|---|---|---|---|---|---|
| **discord.py-self** | [dolfies/discord.py-self](https://github.com/dolfies/discord.py-self) | ~2k | 2024–2025 | 3.10+ | Active, best maintained |
| selfcord | [EvieePy/selfcord](https://github.com/EvieePy/selfcord) | ~300 | 2023, stale | 3.10+ | Abandoned |
| selfbot.py | [AstraaDev/selfbot.py](https://github.com/AstraaDev/selfbot.py) | ~100 | 2024 | 3.10+ | Novelty/toy project |
| discord.py-self forks | stevenbank, regulad, Stranger172 | <100 | 2022–2023 | — | Dead forks |

**Winner: `discord.py-self` by dolfies** — only actively maintained option. PyPI: `discord.py-self 2.1.0`.

### Key Features (discord.py-self)
- Async API, mirrors discord.py interface (easy migration)
- User-account automation detection avoidance built-in
- Read messages, react, monitor channels, DMs
- Mostly compatible with discord.py bots codebase
- Does NOT support bot tokens (user tokens only)

---

## 2. GitHub Repos — Stock/Discord Scraping

No repos found specifically parsing **NuntioBot** message format — this is a gap/opportunity.

| Repo | Description | Relevance |
|---|---|---|
| [StockBot](https://github.com/ianmartensen/StockBot) | Discord bot, Yahoo Finance scraping | Low — price only, no news |
| [StonkBot](https://github.com/ethanosmundson/StonkBot) | Discord bot, Finnhub data, charts | Low — uses API not scraping |
| [Stock-News-Scraper](https://github.com/JehronPett/Stock-News-Scraper) | Python day-trading news scraper | Medium — news focus, no Discord |
| [Python-Stock-News-Scraper](https://github.com/meticulousCraftman/Python-Stock-News-Scraper) | MoneyControl scraper | Low — India market |
| [discord-scraper](https://github.com/dfrnoch/discord-scraper) | Generic Discord message scraper to txt | Medium — baseline pattern |
| [Stocker](https://github.com/dwallach1/Stocker) | Financial scraper + sentiment | Medium — pipeline reference |

**Finding:** No existing repo combines discord selfbot + small-cap stock news parsing. Custom implementation required.

---

## 3. Discord Scraping — Risks & Best Practices

### ToS / Legal Risk
- **Automating user accounts is explicitly against Discord ToS** (Section 3, Community Guidelines)
- Discord can ban the account (not IP). Account loss is primary risk.
- No known legal prosecutions for read-only scraping (CFAA risk is theoretical for personal use)
- Using a **dedicated throwaway account** is standard mitigation

### Ban Risk by Activity Type

| Action | Ban Risk |
|---|---|
| Read messages only, no typing indicator | Very Low |
| Read + mark as read | Low |
| React to messages | Medium |
| Send messages | High |
| Bulk actions / mass DMs | Very High |

### Rate Limiting Recommendations
- Add `asyncio.sleep(0.5–1.0)` between channel reads
- Never read >50 messages/second
- Avoid reading history (`get_history`) excessively — prefer `on_message` listener
- Use `on_message` event (real-time push) not polling — far safer, no rate limit concern

### Recommended Pattern for AlphaSniper
```python
# Safest approach: passive listener, no sends, no reactions
@client.event
async def on_message(message):
    if message.channel.id in TARGET_CHANNELS:
        # parse NuntioBot message format
        await process_stock_alert(message)
```

### Detection Avoidance
- Set realistic `status` (online vs idle)
- Don't run 24/7 from obvious datacenter IP — use residential proxy or local machine
- `discord.py-self` has built-in fingerprinting mitigations
- Avoid custom User-Agent overrides

---

## 4. Recommended Approach

1. **Library**: `discord.py-self` (pip: `discord.py-self`)
2. **Pattern**: `on_message` passive listener only — no sends, no reactions
3. **Account**: Dedicated throwaway Discord account (not personal)
4. **Channels**: Monitor NuntioBot output channels + small-cap alert channels
5. **Output**: Push parsed messages to existing AlphaSniper pipeline (MongoDB raw → Taskiq)
6. **Run location**: Local machine or residential VPS to minimize ban risk

### Install
```bash
uv add "discord.py-self"
```

### Minimal Skeleton
```python
import discord

client = discord.Client()

@client.event
async def on_ready():
    print(f"Listening as {client.user}")

@client.event
async def on_message(message):
    if message.author.id == NUNTIO_BOT_ID and message.channel.id in WATCH_CHANNELS:
        # parse embed or text -> push to pipeline
        pass

client.run(USER_TOKEN)
```

---

## Unresolved Questions

1. **NuntioBot message format** — unknown embed structure; need sample messages to build parser
2. **Which Discord servers/channels** carry NuntioBot small-cap alerts — requires manual discovery
3. **Token acquisition** — storing user token securely (env var, not hardcoded)
4. **Selfcord revival** — no active alternative if discord.py-self breaks on API changes
5. **Discord API version stability** — user API (v9/v10) undocumented, can break silently
