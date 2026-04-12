# Deployment Guide

## Prerequisites

- **Docker**: 20.10+ with Docker Compose 2.0+
- **Python**: 3.12+ (for local development)
- **uv**: Latest version (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
- **API Keys**: Finnhub, MarketAux, Google Gemini (free tiers available)

## Environment Setup

### 1. Copy Environment Template

```bash
cp .env.example .env
```

### 2. Register for Free API Keys

| Service | URL | Free Tier | Required For |
|---------|-----|-----------|--------------|
| Finnhub | https://finnhub.io/register | 60 calls/min, 50 symbols | Real-time news stream |
| MarketAux | https://www.marketaux.com/register | 100 req/day | Secondary news |
| Google Gemini | https://ai.google.dev/tutorials/setup | Free tier (RPM limited) | Article parsing |

### 3. Edit `.env` with Your Keys

```bash
# .env
FINNHUB_API_KEY=your_key_here
MARKETAUX_API_KEY=your_key_here
GEMINI_API_KEY=your_key_here

# Database URLs (update if not using defaults)
POSTGRES_URL=postgresql+asyncpg://user:password@postgres:5432/alphasniper
MONGO_URL=mongodb://mongo:27017/alphasniper
REDIS_URL=redis://redis:6379

# API server
API_PORT=8200
API_HOST=0.0.0.0

# Logging
LOG_LEVEL=INFO
```

## Quick Start (Docker Compose)

### Start All Services

```bash
# Start all containers (postgres, mongo, redis, api, collector, worker, beat)
docker compose up -d

# Verify containers are running
docker compose ps

# Expected output:
# NAME           STATUS
# postgres       Up 2 minutes
# mongo          Up 2 minutes
# redis          Up 2 minutes
# api            Up 1 minute (port 8200)
# collector      Up 1 minute
# worker         Up 1 minute
# beat           Up 1 minute
```

### Check API Health

```bash
# Should return 200 OK
curl http://localhost:8200/health

# Get available articles
curl http://localhost:8200/articles?limit=5
```

### View Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f api
docker compose logs -f collector
docker compose logs -f worker
```

### Stop All Services

```bash
docker compose down
```

## Local Development (Without Docker API Service)

For faster iteration, run API locally while keeping services in Docker:

```bash
# 1. Start only database services
docker compose up -d postgres mongo redis

# 2. Install Python dependencies
uv sync --all-extras

# 3. Run API with hot-reload
uv run uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8200

# 4. In another terminal, run collector
uv run python -m src.collectors.finnhub_ws

# 5. In another terminal, run worker
uv run taskiq worker src.jobs.celery_app:broker --concurrency 8

# 6. In another terminal, run scheduler
uv run taskiq scheduler src.jobs.celery_app:broker
```

## Port Mapping

| Service | Port | Protocol | Access |
|---------|------|----------|--------|
| PostgreSQL | 5432 | TCP | Internal (localhost:5432) |
| MongoDB | 27017 | TCP | Internal (localhost:27017) |
| Redis | 6379 | TCP | Internal (localhost:6379) |
| FastAPI | 8200 | HTTP | http://localhost:8200 |

## Running Individual Components

### API Server Only

```bash
# With all databases running
docker compose up -d postgres mongo redis
uv run uvicorn src.api.main:app --port 8200
```

### Collector (Finnhub WebSocket)

```bash
# Pulls data from Finnhub and stores in MongoDB
uv run python -m src.collectors.finnhub_ws
```

### MarketAux Collector (Scheduled Task)

```bash
# Triggered by scheduler every 15 minutes
# No manual invocation needed; scheduler handles it
docker compose up beat
```

### SEC EDGAR Collector (Scheduled Task)

```bash
# Triggered by scheduler every 10 minutes
# No manual invocation needed; scheduler handles it
docker compose up beat
```

### Taskiq Workers

```bash
# Start worker pool (consumes parse tasks from Redis)
uv run taskiq worker src.jobs.celery_app:broker --concurrency 8

# Scale to N workers
docker compose up --scale worker=4
```

### Taskiq Scheduler (Beat)

```bash
# Runs scheduled tasks (MarketAux, SEC EDGAR collectors, cleanup)
uv run taskiq scheduler src.jobs.celery_app:broker
```

## Running Tests

### Unit & Integration Tests

```bash
# Ensure Docker services are running
docker compose up -d

# Run all tests
uv run pytest tests -v --cov=src

# Run specific test file
uv run pytest tests/test_parsers/test_gemini_parser.py -v

# Run with verbose output
uv run pytest tests -vv -s
```

### Test Coverage Report

```bash
uv run pytest tests --cov=src --cov-report=html
open htmlcov/index.html
```

## Database Management

### Run Migrations (PostgreSQL)

```bash
# Auto-generate new migration based on model changes
uv run alembic revision --autogenerate -m "add user preferences"

# Apply pending migrations
uv run alembic upgrade head

# Rollback one migration
uv run alembic downgrade -1
```

### View Database

```bash
# PostgreSQL
docker exec -it postgres psql -U alphasniper -d alphasniper -c "SELECT count(*) FROM articles;"

# MongoDB
docker exec -it mongo mongosh alphasniper --eval "db.raw_articles.countDocuments()"

# Redis
docker exec -it redis redis-cli DBSIZE
```

## Troubleshooting

### Issue: "Connection refused" on Port 8200

**Cause:** API not running or wrong port.

```bash
# Check if API is running
docker compose ps api

# If running in docker, check logs
docker compose logs api

# If running locally, ensure uvicorn is started
lsof -i :8200  # Show process on port 8200
```

### Issue: MongoDB Connection Error

**Cause:** MongoDB service not running or network issue.

```bash
# Restart MongoDB
docker compose restart mongo

# Check connection URL in .env
echo $MONGO_URL

# Test connection
docker exec -it mongo mongosh alphasniper
```

### Issue: "rate limit exceeded" (Finnhub)

**Cause:** Exceeded 60 calls/min free tier limit.

**Solution:** 
- Wait 60 seconds for rate limit to reset
- Upgrade to paid plan
- Reduce symbol list in config

### Issue: Gemini API Failures

**Cause:** Invalid API key or quota exceeded.

```bash
# Verify key is set
echo $GEMINI_API_KEY

# Check quota at https://ai.google.dev/tutorials/setup

# Retry manually
uv run pytest tests/test_parsers/test_gemini_parser.py -v
```

### Issue: Workers Not Processing Tasks

**Cause:** Taskiq queue empty or workers not running.

```bash
# Check Redis queue
docker exec -it redis redis-cli LLEN rpc_queue

# Restart workers
docker compose restart worker

# View worker logs
docker compose logs -f worker
```

### Issue: Disk Space (MongoDB/PostgreSQL)

**Cause:** Docker volumes filling up.

```bash
# Check volume usage
docker system df

# Clean up old containers/images
docker system prune -a

# Reinitialize databases (⚠️ deletes data)
docker compose down -v
docker compose up -d
```

## Production Deployment Checklist

- [ ] Set `LOG_LEVEL=WARNING` in production
- [ ] Use strong `POSTGRES_URL`, `MONGO_URL`, `REDIS_URL` (managed services)
- [ ] Enable HTTPS for API (reverse proxy with Nginx)
- [ ] Set up monitoring (Prometheus, DataDog)
- [ ] Configure backups for PostgreSQL and MongoDB
- [ ] Use separate API keys for dev/prod
- [ ] Run security audit: `pip audit`
- [ ] Set resource limits in Docker Compose
- [ ] Use managed services (AWS RDS, MongoDB Atlas, ElastiCache)

## Scaling

### Horizontal Scaling (Multiple Workers)

```bash
# Start 4 worker instances
docker compose up -d --scale worker=4
```

### Vertical Scaling (Increase Resources)

Edit `docker-compose.yml`:

```yaml
services:
  worker:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
```

### Load Testing

```bash
# Simple load test (10 concurrent requests, 100 total)
ab -n 100 -c 10 http://localhost:8200/articles

# Using wrk (if installed)
wrk -t4 -c10 -d30s http://localhost:8200/articles
```

## Monitoring & Logs

### View Structured Logs

```bash
# Collect all logs as JSON
docker compose logs --follow --timestamps | jq .
```

### Health Check

```bash
# API health
curl -s http://localhost:8200/health | jq .

# Database connectivity
docker compose exec api python -c "from src.core.database import get_session; print('OK')"
```

## Cleanup

```bash
# Stop all services
docker compose down

# Remove volumes (⚠️ deletes all data)
docker compose down -v

# Remove images too
docker compose down -v --rmi all
```
