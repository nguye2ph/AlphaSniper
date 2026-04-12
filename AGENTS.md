# AGENTS.md - AlphaSniper Agent Definitions

## Overview
Specialized agents for the AlphaSniper stock news pipeline. Each agent has a specific domain and can be spawned via Claude Code's Agent tool.

---

## Data Collection Agents

### collector-agent
**Purpose:** Add, fix, or maintain data source collectors.
**When to spawn:**
- Adding a new data source (new API, RSS feed, etc.)
- Fixing broken collector (API format changed, auth expired)
- Optimizing collection frequency or rate limiting

**Context to provide:**
- Source API documentation URL
- Expected data format (JSON schema)
- Rate limits and authentication method
- Target files: `src/collectors/`

**Expected output:**
- Working collector module in `src/collectors/`
- Beanie document model if needed
- Taskiq task registration
- Tests in `tests/test-collectors/`

---

### parser-agent
**Purpose:** Improve AI parsing accuracy for news articles.
**When to spawn:**
- Parse errors or low accuracy on specific news types
- Adding new extraction fields (e.g., sector, analyst name)
- Switching AI provider or model
- Batch processing historical data

**Context to provide:**
- Sample articles that failed parsing
- Expected output format (Pydantic schema)
- AI model to use (Gemini API)
- Target files: `src/parsers/`

**Expected output:**
- Updated parser logic
- Validation tests with sample data
- Accuracy metrics

---

## Data Quality Agents

### data-quality-agent
**Purpose:** Validate data integrity, dedup accuracy, coverage gaps.
**When to spawn:**
- Scheduled daily review
- Suspected duplicate articles in clean DB
- Coverage gaps for specific tickers
- Source reliability degradation

**Context to provide:**
- Time range to analyze
- Specific tickers or sources of concern
- Database connection details (from .env)

**Expected output:**
- Data quality report in `plans/reports/`
- Identified issues with severity
- Recommended fixes

---

### schema-agent
**Purpose:** Evolve database schema, run migrations.
**When to spawn:**
- New data fields needed (MongoDB or PostgreSQL)
- Performance optimization (indexes, partitioning)
- Data model refactoring

**Context to provide:**
- Current schema (from CLAUDE.md or models/)
- New fields or changes needed
- Migration safety concerns

**Expected output:**
- Updated SQLAlchemy models
- Alembic migration file
- Updated Beanie documents if MongoDB changes
- Migration test

---

## Research Agents

### source-research-agent
**Purpose:** Find and evaluate new data sources.
**When to spawn:**
- Current sources have coverage gaps
- Need alternative/backup for existing source
- Exploring new data types (social media, SEC filings, etc.)

**Context to provide:**
- What data is missing (tickers, regions, types)
- Budget constraints
- Existing sources list (from CLAUDE.md)

**Expected output:**
- Research report in `research/source-evaluation/`
- API comparison table
- Integration feasibility assessment
- Sample responses

---

### api-test-agent
**Purpose:** Test API endpoints, validate response formats, measure latency.
**When to spawn:**
- Before integrating a new data source
- After API announces breaking changes
- Periodic validation of free tier limits

**Context to provide:**
- API documentation URL
- Endpoints to test
- Expected response format

**Expected output:**
- Live test results in `research/api-samples/`
- Response time measurements
- Free tier limit verification
- Data quality assessment

---

## Pipeline Agents

### pipeline-monitor-agent
**Purpose:** Monitor pipeline health, detect failures, alert on anomalies.
**When to spawn:**
- Pipeline seems stuck (no new articles)
- Error rates increasing
- Performance degradation

**Context to provide:**
- Time range of concern
- Specific service (collector, worker, API)
- Docker logs if available

**Expected output:**
- Diagnostic report
- Root cause identification
- Fix implementation or recommendation

---

## Agent Spawning Patterns

### Sequential Chain (Feature Development)
```
planner -> collector-agent -> parser-agent -> tester -> code-reviewer
```

### Parallel (Independent Research)
```
source-research-agent (Source A) | source-research-agent (Source B) | api-test-agent
```

### Reactive (Incident Response)
```
pipeline-monitor-agent -> debugger -> collector-agent (fix) -> tester
```

---

## Agent Communication

### Shared Context Paths
- **Research data**: `research/` directory
- **Reports**: `plans/reports/` directory
- **API samples**: `research/api-samples/`
- **Source evaluations**: `research/source-evaluation/`

### Handoff Protocol
1. Agent writes output to designated path
2. Agent returns summary with file paths
3. Next agent in chain reads those files for context
4. Each agent updates relevant docs if schema/architecture changes
