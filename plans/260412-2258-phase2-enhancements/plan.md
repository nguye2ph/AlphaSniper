---
title: "AlphaSniper Phase 2 — Enhancements"
description: "Content scraping, trading terminal UI, Discord integration, admin settings"
status: pending
priority: P1
effort: 17h
branch: main
tags: [scraping, ui, discord, admin, enhancement]
created: 2026-04-12
---

# AlphaSniper Phase 2 — Enhancements

## Overview

Six enhancement phases expanding AlphaSniper with content scraping, pro-trader UI, Discord integration, and admin controls. All phases build on existing architecture (MongoDB raw → Taskiq → PostgreSQL clean → FastAPI → Next.js).

## Phases

| # | Phase | Effort | Status | Priority |
|---|-------|--------|--------|----------|
| 1 | [Content Scraping](./phase-01-content-scraping.md) | 4h | pending | P1 |
| 2 | [UI Upgrade](./phase-02-ui-upgrade.md) | 5h | pending | P1 |
| 3 | [Discord Webhook](./phase-03-discord-webhook.md) | 1h | pending | P2 |
| 4 | [Discord Bot](./phase-04-discord-bot.md) | 3h | pending | P2 |
| 5 | [Admin Settings](./phase-05-admin-settings.md) | 3h | pending | P2 |
| 6 | [Nuntio Research](./phase-06-nuntio-research.md) | 1h | pending | P3 |

## Dependencies

- Phase 1 (scraping) → Phase 2 (UI shows content/key_points)
- Phase 3 (webhook) → Phase 4 (bot reuses Discord config)
- Phase 5 (admin) independent, can parallelize with 3-4
- Phase 6 (research) blocks on Phase 4 completion

## Key Risks

- Paywalled/JS-rendered URLs may limit scraping yield
- Framer-motion adds ~30KB bundle; justified by UX gains
- Nuntio server may block bots (Phase 6 determines feasibility)
- Discord bot needs MESSAGE_CONTENT privileged intent

## Tech Additions

- **Python**: `beautifulsoup4` (already installed), `discord.py`
- **TypeScript**: `framer-motion`, `recharts` (if not present)
- **Config**: `DISCORD_WEBHOOK_URL`, `DISCORD_BOT_TOKEN`, `DISCORD_CHANNEL_IDS`
