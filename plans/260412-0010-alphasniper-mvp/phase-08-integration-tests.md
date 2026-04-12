# Phase 8: Integration Tests + Polish

## Overview
- **Priority**: Medium
- **Status**: pending
- **Description**: End-to-end integration tests, error handling hardening, documentation updates, and production readiness checks.

## Related Code Files
- **Create**: `tests/test-collectors/test-finnhub.py`
- **Create**: `tests/test-collectors/test-marketaux.py`
- **Create**: `tests/test-collectors/test-sec-edgar.py`
- **Create**: `tests/test-parsers/test-headline-parser.py`
- **Create**: `tests/test-parsers/test-dedup.py`
- **Create**: `tests/test-api/test-articles-api.py`
- **Create**: `tests/test-integration/test-full-pipeline.py`
- **Modify**: `docs/` — update all project documentation

## Implementation Steps
1. Unit tests for each collector (mock API responses)
2. Unit tests for parsers (sample headlines)
3. Unit tests for API endpoints (test client)
4. Integration test: full pipeline (collect → dedup → parse → query)
5. Error handling review: all try/except blocks, retry logic
6. Logging review: structured JSON logs, log levels
7. Docker Compose production profile (no hot-reload, proper restart policies)
8. Update docs: project-overview-pdr, system-architecture, deployment-guide

## Todo List
- [ ] Collector unit tests (mocked)
- [ ] Parser unit tests
- [ ] API endpoint tests
- [ ] Full pipeline integration test
- [ ] Error handling audit
- [ ] Logging standardization
- [ ] Docker production profile
- [ ] Documentation update

## Test Cases
- Full pipeline: insert mock raw article → appears in PostgreSQL clean table
- API: query article inserted by pipeline → correct response
- Collector failure: API down → logs error, retries, doesn't crash
- Dedup: process same article twice → only 1 clean record
- Docker: `docker compose up` → all services healthy within 60s
- Health: `/health` reports status of all dependencies

## Acceptance Criteria
- [ ] >80% test coverage on src/
- [ ] All tests pass in CI (pytest exit 0)
- [ ] No unhandled exceptions in collector/worker logs
- [ ] Docker Compose production profile works
- [ ] docs/ updated with final architecture

## Success Criteria (MVP Complete)
- [ ] Collect 500+ unique articles/day from 3 sources
- [ ] < 10s latency Finnhub publish → MongoDB insert
- [ ] Zero duplicates in PostgreSQL
- [ ] FastAPI serves filtered queries correctly
- [ ] `docker compose up` → full system operational
