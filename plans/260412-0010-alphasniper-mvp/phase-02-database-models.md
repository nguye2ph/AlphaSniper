# Phase 2: Database Models + Migrations

## Overview
- **Priority**: Critical
- **Status**: completed
- **Description**: Define MongoDB Beanie documents (raw zone) and PostgreSQL SQLAlchemy models (clean zone). Run Alembic migrations.

## Key Insights
- Two-zone design: MongoDB stores raw API responses, PostgreSQL stores parsed structured data
- Beanie ODM uses Pydantic v2 models — validation built-in
- SQLAlchemy 2.0 mapped_column style for type safety
- Dedup key: `source` + `source_id` combination (unique constraint)

## Requirements

### Functional
- MongoDB collections: `raw_articles`, `raw_tickers`
- PostgreSQL tables: `articles`, `tickers`, `sources`
- Alembic migration for initial schema
- Indexes for common query patterns (published_at, tickers, sentiment)

### Non-functional
- All DB operations async
- Bulk insert support for batch collection
- JSONB column for raw_data in PostgreSQL (backup)

## Related Code Files
- **Create**: `src/core/models/raw-article.py` (Beanie document)
- **Create**: `src/core/models/article.py` (SQLAlchemy model)
- **Create**: `src/core/models/ticker.py` (SQLAlchemy model)
- **Create**: `src/core/models/source.py` (SQLAlchemy model)
- **Create**: `src/core/models/__init__.py` (exports)
- **Create**: `src/core/schemas/article-schema.py` (Pydantic I/O)
- **Create**: `src/core/schemas/common-schema.py` (shared schemas)
- **Modify**: `src/core/database.py` (add Beanie init, Base declarative)
- **Create**: `migrations/` Alembic setup

## Implementation Steps

1. Create `src/core/models/` directory with __init__.py
2. Define Beanie document `RawArticle` in `raw-article.py`:
   - source, source_id, payload (dict), collected_at, is_processed
3. Define SQLAlchemy model `Article` in `article.py`:
   - id (UUID), source, source_id, headline, summary, url
   - published_at, tickers (ARRAY), sentiment (Float), sentiment_label
   - market_cap (Float nullable), category, raw_data (JSONB)
4. Define `Ticker` model in `ticker.py`:
   - symbol, name, exchange, market_cap, sector, is_active
5. Define `Source` model in `source.py`:
   - name, type (api/rss/websocket), base_url, is_active, last_collected_at
6. Create Pydantic schemas for API I/O in `src/core/schemas/`
7. Initialize Alembic: `alembic init migrations`
8. Configure alembic.ini to use async PostgreSQL
9. Generate initial migration: `alembic revision --autogenerate`
10. Run migration: `alembic upgrade head`
11. Test: insert sample data into both DBs

## Todo List
- [ ] Beanie RawArticle document
- [ ] SQLAlchemy Article model
- [ ] SQLAlchemy Ticker model
- [ ] SQLAlchemy Source model
- [ ] Pydantic I/O schemas
- [ ] Alembic setup + initial migration
- [ ] Database init in lifespan (Beanie + SQLAlchemy)
- [ ] Test insert/query both DBs

## Test Cases
- Insert RawArticle into MongoDB, query by source_id — found
- Insert Article into PostgreSQL, query by ticker — found
- Unique constraint on (source, source_id) prevents duplicates
- JSONB raw_data column stores and retrieves correctly
- Alembic migration up/down works cleanly
- Async session creates and commits without blocking

## Acceptance Criteria
- [ ] MongoDB `raw_articles` collection created with indexes
- [ ] PostgreSQL `articles`, `tickers`, `sources` tables created
- [ ] Alembic migration runs without errors
- [ ] All models importable from `src.core.models`
- [ ] Pydantic schemas validate sample data correctly

## Next Steps
- Phase 3: Finnhub collector (writes to raw_articles)
