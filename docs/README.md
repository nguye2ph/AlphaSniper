# AlphaSniper Documentation

Welcome to AlphaSniper—a real-time stock news data pipeline for personal trading.

## Quick Links

| Document | Purpose | Audience |
|----------|---------|----------|
| [Project Overview & PDR](./project-overview-pdr.md) | Mission, scope, MVP status | Everyone |
| [System Architecture](./system-architecture.md) | Database design, service stack, data flow | Architects, Senior Engineers |
| [Code Standards](./code-standards.md) | File structure, async patterns, testing rules | All Developers |
| [Deployment Guide](./deployment-guide.md) | Setup, running, troubleshooting | DevOps, Full-Stack |
| [Codebase Summary](./codebase-summary.md) | Directory structure, key files, patterns | New Developers |

## For New Developers

1. Start with [Project Overview & PDR](./project-overview-pdr.md) — 5 min read
2. Review [Codebase Summary](./codebase-summary.md) — 10 min read
3. Read [Code Standards](./code-standards.md) — 15 min read
4. Follow [Deployment Guide](./deployment-guide.md) to get running locally — 20 min

## For DevOps/Deployment

1. [Deployment Guide](./deployment-guide.md) — Complete setup and troubleshooting
2. [System Architecture](./system-architecture.md) — Service stack and port mapping

## Tech Stack (TL;DR)

- **Language**: Python 3.12+ with uv
- **API**: FastAPI on port 8200
- **Databases**: PostgreSQL (clean) + MongoDB (raw) + Redis (queue)
- **Task Queue**: Taskiq + Redis
- **Data Sources**: Finnhub (WebSocket), MarketAux (REST), SEC EDGAR (RSS)
- **AI Parser**: Google Gemini API
- **Deploy**: Docker Compose (7 containers)

## Key Workflows

### Start Development

```bash
cp .env.example .env
# Edit .env with API keys

docker compose up -d postgres mongo redis
uv sync --all-extras
uv run uvicorn src.api.main:app --reload --port 8200
```

### Run Tests

```bash
docker compose up -d postgres mongo redis
uv run pytest tests -v
```

### Deploy to Production

```bash
# Set production API keys in .env
docker compose up -d
curl http://localhost:8200/health
```

## Current Status

✅ **MVP Complete** — All 8 phases finished

- Data pipeline (Collect → Store → Parse → Query)
- 3 data sources (Finnhub, MarketAux, SEC EDGAR)
- Real-time WebSocket streaming (Finnhub)
- AI-powered parsing (Gemini)
- 6 API endpoints
- Full test coverage
- Docker Compose deployment

## Support & Questions

- **Architecture questions?** See [System Architecture](./system-architecture.md)
- **How do I run it?** See [Deployment Guide](./deployment-guide.md)
- **Code examples?** See [Codebase Summary](./codebase-summary.md)
- **What are the rules?** See [Code Standards](./code-standards.md)

## Project Links

- **Implementation Plans**: `plans/260412-0010-alphasniper-mvp/`
- **Research & API Samples**: `research/api-samples/`
- **Source Code**: `src/`
- **Tests**: `tests/`

---

**Last Updated**: April 12, 2026
**Status**: ✅ MVP Complete, Production Ready
