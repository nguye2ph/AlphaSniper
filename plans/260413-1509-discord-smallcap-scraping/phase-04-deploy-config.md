# Phase 04 — Deploy Config

## Context Links
- Docker Compose: `docker-compose.yml`
- Config: `src/core/config.py`
- FastAPI main: `src/api/main.py`
- Deployment guide: `docs/deployment-guide.md`
- Brainstorm (VPS + Vercel target): `plans/reports/brainstorm-260413-1509-discord-nuntio-scraping.md`

## Overview
- **Priority**: P2
- **Status**: pending
- **Effort**: 1h
- **Depends on**: Phases 1–3 complete
- Wire up all new services in `docker-compose.yml`, update `.env.example`, verify CORS for Vercel frontend, and document VPS deploy steps.

## Key Insights
- Docker Compose already has Traefik for TLS termination with `API_DOMAIN` env var
- Brainstorm notes: VPS with IP only, no domain initially → Traefik TLS may not apply; can expose port 8200 directly or use `API_DOMAIN=<VPS_IP>` (Traefik won't get cert for bare IP, so for IP-only deployment skip TLS and expose port directly)
- `discord-listener` runs as persistent service (like `collector`) — same restart policy
- RSS collectors run via Taskiq scheduler in existing `scheduler` service — **no new service needed** for RSS
- CORS: `src/api/main.py` should already accept `FRONTEND_URL` env var for Vercel domain (`https://your-app.vercel.app`)
- All new env vars need `.env.example` entries with comments

## Requirements

### Functional
- `discord-listener` service added to `docker-compose.yml`
- `.env.example` updated with all new vars from Phases 1–4
- `src/api/main.py` CORS verified: accepts `FRONTEND_URL` (Vercel domain)
- `docs/deployment-guide.md` updated with VPS setup steps
- `docker compose config` passes validation (no YAML errors)
- All 8 services start: `traefik`, `postgres`, `mongo`, `redis`, `api`, `collector`, `worker`, `scheduler`, `discord-listener`

### Non-functional
- `.env.example` entries in logical groups with inline comments
- No secrets in `docker-compose.yml` — all via `env_file: .env`

## Architecture

```
VPS (Docker Compose)
├── traefik          — reverse proxy / TLS (skip for IP-only)
├── postgres         — existing
├── mongo            — existing
├── redis            — existing
├── api              — FastAPI :8200
├── collector        — Finnhub WS (existing)
├── worker           — Taskiq workers (runs RSS + parse tasks)
├── scheduler        — Taskiq beat (schedules RSS + parse tasks)
└── discord-listener — NEW: discord.py-self passive listener

Vercel (Frontend)
└── NEXT_PUBLIC_API_URL=http://{VPS_IP}:8200  (or https if domain set)
```

## Related Code Files

### Modify
- `docker-compose.yml` — add `discord-listener` service
- `.env.example` — add all new env vars
- `src/api/main.py` — verify CORS middleware includes `FRONTEND_URL`
- `docs/deployment-guide.md` — add VPS deploy section

## Implementation Steps

### 1. docker-compose.yml — add discord-listener service

Add after `collector` service:
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

No Traefik labels needed — this is an internal service, no HTTP exposure.

### 2. .env.example — add new vars

Append these sections (grouped by phase):

```bash
# ── Market Cap Filter (Phase 1) ──────────────────────────────────────────────
MARKET_CAP_LIMIT=100000000      # Filter: skip articles > this market cap (100M default)

# ── Discord NuntioBot Scraping (Phase 2) ─────────────────────────────────────
DISCORD_TOKEN=                   # User token from throwaway Discord account (NOT bot token)
DISCORD_CHANNEL_IDS=             # Comma-separated channel IDs, e.g.: 123456789,987654321
NUNTIO_BOT_NAME=NuntioBot        # NuntioBot username to match (default: NuntioBot)

# ── Deployment ────────────────────────────────────────────────────────────────
FRONTEND_URL=https://your-app.vercel.app   # Vercel frontend URL for CORS
API_DOMAIN=your-domain.com                 # Domain for Traefik TLS (leave empty for IP-only)
ACME_EMAIL=admin@example.com               # LetsEncrypt contact email
```

### 3. Verify CORS in src/api/main.py

Check that `CORSMiddleware` uses `settings.frontend_url`. Expected pattern:
```python
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url] if settings.frontend_url else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```
If `frontend_url` is already used: no change needed.
If CORS is hardcoded or missing `frontend_url`: update to use `settings.frontend_url`.

### 4. IP-only VPS: skip Traefik TLS

For VPS with no domain, expose API port directly. Add to `api` service in docker-compose.yml:
```yaml
ports:
  - "8200:8200"
```
And set `API_DOMAIN=` (empty) in `.env` so Traefik label has no effect.
Document this in `docs/deployment-guide.md`.

### 5. docs/deployment-guide.md — VPS section

Add section:
```markdown
## VPS Deployment (IP-only, no domain)

1. SSH into VPS
2. Clone repo: `git clone ...`
3. Copy `.env.example` to `.env`, fill in all required values
4. For IP-only (no domain): set `API_DOMAIN=` (empty), ensure `api` service exposes port 8200
5. `docker compose pull` (or `docker compose build`)
6. `docker compose up -d`
7. Verify: `docker compose ps` — all 9 services `Up`
8. Check API: `curl http://{VPS_IP}:8200/health`

### Discord Listener Setup
1. Create throwaway Discord account
2. Join server with NuntioBot (e.g., Balanced server)
3. Get user token (browser devtools → Network → Authorization header)
4. Set `DISCORD_TOKEN` and `DISCORD_CHANNEL_IDS` in `.env`
5. Restart discord-listener: `docker compose restart discord-listener`
6. Monitor: `docker compose logs -f discord-listener`

### Vercel Frontend
Set in Vercel project env vars:
- `NEXT_PUBLIC_API_URL=http://{VPS_IP}:8200`
```

## Todo List
- [ ] Add `discord-listener` service to `docker-compose.yml`
- [ ] Add port `8200:8200` to `api` service for IP-only VPS access
- [ ] Add all new `.env.example` entries (grouped, with comments)
- [ ] Verify/update CORS in `src/api/main.py` to use `settings.frontend_url`
- [ ] Run `docker compose config` — confirms YAML is valid
- [ ] Update `docs/deployment-guide.md` with VPS + Vercel section
- [ ] Test: `docker compose up -d` on VPS, all 9 services start cleanly
- [ ] Test: `curl http://{VPS_IP}:8200/health` returns 200
- [ ] Test: Vercel frontend connects to VPS API (CORS works)

## Test Cases

| Scenario | Expected |
|----------|----------|
| `docker compose config` | No YAML validation errors |
| `docker compose up -d` | All 9 services reach `Up` state |
| `docker compose logs discord-listener` | Logs "discord_connected", no crash loop |
| `curl http://{VPS_IP}:8200/health` | `{"status": "ok"}` |
| Vercel frontend → `GET /articles` | 200 response, no CORS error |
| `.env` missing `DISCORD_TOKEN` | `discord-listener` logs warning, exits cleanly (not crash loop) |

## Verification Steps
1. Local: `docker compose config` — exits 0
2. Local: `docker compose up -d` — `docker compose ps` shows all services `Up`
3. Local: `curl http://localhost:8200/health`
4. VPS: repeat steps 2–3
5. Set `FRONTEND_URL` to Vercel preview URL; test CORS with browser devtools (no `Access-Control` error)
6. `docker compose logs -f discord-listener` — shows `discord_connected` after token is set

## Acceptance Criteria
- [ ] `docker compose config` passes with no errors
- [ ] 9 services start successfully: `traefik`, `postgres`, `mongo`, `redis`, `api`, `collector`, `worker`, `scheduler`, `discord-listener`
- [ ] `GET /health` returns 200 from VPS IP
- [ ] Vercel frontend can call API without CORS error
- [ ] `.env.example` documents all new variables
- [ ] `docs/deployment-guide.md` has VPS + Discord listener setup instructions

## Risk Assessment
| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| Traefik misconfiguration on IP-only VPS | Medium | Expose port 8200 directly; Traefik labels are no-op without valid domain |
| discord-listener crash loop if token invalid | Medium | Add guard: if `DISCORD_TOKEN` empty, log error + exit 0 (not 1) to prevent restart loop |
| CORS blocking Vercel → VPS | Low | Verify `FRONTEND_URL` matches exact Vercel domain (including `https://`) |
| Port 8200 blocked by VPS firewall | Low | Ensure UFW/iptables allows `0.0.0.0:8200` |

## Security Considerations
- `DISCORD_TOKEN` and all secrets only in `.env` (git-ignored), never in `docker-compose.yml`
- Port 8200 exposed to internet for Vercel access — consider IP allowlist or auth token if sensitive
- `.env.example` must NOT contain real tokens/passwords — only placeholders

## Next Steps
- After successful deploy: monitor `docker compose logs -f` for all services
- Set up log rotation if running long-term on VPS
- If domain obtained later: configure `API_DOMAIN` and `ACME_EMAIL` for Traefik TLS
- Consider adding `GET /sources` endpoint stats to frontend for collector health monitoring
