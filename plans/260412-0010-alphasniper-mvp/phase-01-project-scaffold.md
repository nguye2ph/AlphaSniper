# Phase 1: Project Scaffold + Docker

## Overview
- **Priority**: Critical
- **Status**: completed
- **Description**: Bootstrap project structure, dependencies, Docker Compose, and dev tooling.

## Key Insights
- Use `uv` for dependency management (ultra-fast, 2026 standard)
- Docker Compose with 7 services: postgres, mongo, redis, api, collector, worker, beat
- TimescaleDB image optional — plain postgres:16 sufficient for MVP volume

## Requirements

### Functional
- pyproject.toml with all dependencies pinned
- Docker Compose with health checks for all infra services
- .env.example with all required environment variables
- Dockerfile for Python services
- Basic project package structure importable

### Non-functional
- `docker compose up -d` must bring all services healthy within 60s
- `uv sync` must install all deps without errors
- Python 3.12+ required

## Architecture
```
alpha-sniper/
├── pyproject.toml          # Dependencies (uv)
├── uv.lock                 # Lock file (auto-generated)
├── Dockerfile              # Python service image
├── docker-compose.yml      # All services
├── .env.example            # Environment template
├── .gitignore
├── src/
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py       # pydantic-settings
│   │   └── database.py     # MongoDB + PostgreSQL connections
│   ├── collectors/
│   │   └── __init__.py
│   ├── parsers/
│   │   └── __init__.py
│   ├── api/
│   │   ├── __init__.py
│   │   └── main.py         # FastAPI app with lifespan
│   ├── jobs/
│   │   └── __init__.py
│   └── webapp/
│       └── .gitkeep
├── research/               # Already exists from brainstorm
├── plans/                  # Already exists
├── docs/
├── migrations/
├── tests/
│   └── __init__.py
└── scripts/
```

## Related Code Files
- **Create**: pyproject.toml, Dockerfile, docker-compose.yml, .env.example, .gitignore
- **Create**: src/core/config.py, src/core/database.py, src/api/main.py
- **Create**: All __init__.py files for package structure

## Implementation Steps

1. Initialize git repository
2. Create pyproject.toml with all dependencies from stack analysis
3. Create .env.example with all API keys and DB connection strings
4. Create .gitignore (Python + Docker + IDE)
5. Create Dockerfile (python:3.12-slim + uv)
6. Create docker-compose.yml (postgres, mongo, redis, api, collector, worker, beat)
7. Create src/ package structure with __init__.py files
8. Create src/core/config.py (pydantic-settings with all env vars)
9. Create src/core/database.py (MongoDB Beanie init + PostgreSQL async engine)
10. Create src/api/main.py (FastAPI app with lifespan, health check endpoint)
11. Run `uv sync` to generate uv.lock
12. Run `docker compose up -d` and verify all services healthy
13. Run `curl localhost:8000/health` to verify API responds

## Todo List
- [ ] git init
- [ ] pyproject.toml
- [ ] .env.example
- [ ] .gitignore
- [ ] Dockerfile
- [ ] docker-compose.yml
- [ ] src/ package structure
- [ ] src/core/config.py
- [ ] src/core/database.py
- [ ] src/api/main.py
- [ ] uv sync + verify
- [ ] docker compose up + verify

## Test Cases
- `uv sync --all-extras` completes without errors
- `docker compose up -d` all services reach "healthy" state
- `curl localhost:8000/health` returns `{"status": "ok"}`
- `docker compose exec mongo mongosh --eval "db.stats()"` succeeds
- `docker compose exec postgres psql -U alpha -d alpha_sniper -c "SELECT 1"` succeeds
- `docker compose exec redis redis-cli ping` returns PONG

## Verification Steps
1. `uv sync` — no dependency conflicts
2. `docker compose up -d` — all 7 services up
3. `docker compose ps` — all healthy
4. `curl localhost:8000/health` — 200 OK
5. `curl localhost:8000/docs` — Swagger UI loads

## Acceptance Criteria
- [ ] All Python imports resolve (no ModuleNotFoundError)
- [ ] Docker Compose brings up postgres, mongo, redis, api
- [ ] Health endpoint responds with 200
- [ ] .env.example documents all required variables
- [ ] pyproject.toml includes all production + dev dependencies

## Risk Assessment
- **uv version compatibility**: Pin uv version in Dockerfile
- **Docker image size**: Use slim base, multi-stage if needed
- **Port conflicts**: Document required ports (5432, 27017, 6379, 8000)

## Next Steps
- Phase 2: Database models + migrations
