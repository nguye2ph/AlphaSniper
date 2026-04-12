# Code Standards & Guidelines

## Language & Tools

- **Python**: 3.12+ required
- **Package Manager**: `uv` (fast, deterministic, replaces pip/poetry)
- **Type Hints**: Full type annotations (mypy strict mode)
- **Linter**: Ruff (formatting + linting in one)
- **Async**: asyncio for all I/O operations (DB, HTTP, WebSocket)

## File Organization

### Naming Conventions

- **Python files**: `snake_case.py` (e.g., `finnhub_ws.py`, `gemini_parser.py`)
- **Modules**: Organize by domain (collectors, parsers, api, core, jobs)
- **Classes**: `PascalCase` (e.g., `FinnhubCollector`, `GeminiParser`)
- **Functions**: `snake_case` (e.g., `extract_tickers()`, `parse_sentiment()`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `MAX_RETRIES`, `API_TIMEOUT_SEC`)

### File Size Limits

- **Max 200 lines per file** (including docstrings)
- Split large modules into focused sub-modules
- Use composition over inheritance
- Extract utility functions into `utils/` subdirectories

**Example refactoring:**
```
parsers/
  ├── __init__.py
  ├── base_parser.py        # Abstract base class
  ├── gemini_parser.py      # Gemini API calls
  ├── headline_parser.py    # Headline extraction
  ├── dedup.py              # Dedup logic
  └── utils/
      ├── sentiment.py      # Sentiment scoring
      └── ticker_extract.py # Ticker extraction helpers
```

## Async Patterns

### Database Operations

All DB calls must be async:

```python
# ✅ Correct
async def get_articles(ticker: str) -> list[Article]:
    async with get_session() as session:
        result = await session.execute(
            select(Article).where(Article.tickers.contains([ticker]))
        )
        return result.scalars().all()

# ❌ Wrong (blocking)
def get_articles(ticker: str) -> list[Article]:
    session = SessionLocal()
    return session.query(Article).filter(...).all()
```

### HTTP Calls

Use `httpx` with async context manager:

```python
# ✅ Correct
async def fetch_finnhub(url: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.get(url, timeout=10.0)
        response.raise_for_status()
        return response.json()

# ❌ Wrong (blocking)
import requests
response = requests.get(url)
```

### WebSocket Streams

Use `websockets` library with async generators:

```python
# ✅ Correct
async def stream_finnhub():
    async with websockets.connect(WS_URL) as ws:
        async for message in ws:
            yield json.loads(message)
```

## Validation & Configuration

### Pydantic v2 Models

All inputs/outputs use Pydantic models:

```python
from pydantic import BaseModel, Field, validator

class ArticleRequest(BaseModel):
    ticker: str = Field(..., min_length=1, max_length=5)
    limit: int = Field(default=10, ge=1, le=100)
    
    @field_validator('ticker')
    @classmethod
    def ticker_uppercase(cls, v: str) -> str:
        return v.upper()

class ArticleResponse(BaseModel):
    id: UUID
    headline: str
    sentiment: float = Field(ge=-1.0, le=1.0)
    tickers: list[str]
    
    model_config = ConfigDict(from_attributes=True)  # SQLAlchemy compat
```

### Configuration Management

All config via pydantic-settings + `.env`:

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    FINNHUB_API_KEY: str
    POSTGRES_URL: str
    MONGO_URL: str
    REDIS_URL: str = "redis://localhost:6379"
    API_PORT: int = 8200
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()  # Auto-loads from .env
```

**Never hardcode secrets.** Use `settings` object everywhere.

## Error Handling

### Retry Logic (Tenacity)

Use tenacity for API calls with exponential backoff:

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
async def call_gemini_api(text: str) -> dict:
    # Raises exception on failure, tenacity handles retry
    response = await client.post(GEMINI_URL, json={"text": text})
    response.raise_for_status()
    return response.json()
```

### Structured Logging (structlog)

All logging via structlog for JSON output:

```python
import structlog

logger = structlog.get_logger()

async def parse_article(article_id: str):
    try:
        logger.info("parsing_article_start", article_id=article_id)
        result = await gemini_parser.parse(article_id)
        logger.info("parsing_article_success", article_id=article_id)
        return result
    except Exception as e:
        logger.error("parsing_article_failed", article_id=article_id, error=str(e))
        raise
```

### Exception Handling

Catch exceptions at appropriate boundaries:

```python
# ✅ At API route level
@router.get("/articles")
async def list_articles(ticker: str) -> list[ArticleResponse]:
    try:
        articles = await db.get_articles_by_ticker(ticker)
        return articles
    except Exception as e:
        logger.error("list_articles_error", ticker=ticker, error=str(e))
        raise HTTPException(status_code=500, detail="Internal error")

# ❌ Too broad
try:
    await everything()
except:
    pass
```

## Testing Standards

### Unit Tests (pytest)

- Test async functions with `pytest-asyncio`
- Mock external APIs (Finnhub, Gemini, etc.)
- Test against running Docker services (integration tests)

```python
@pytest.mark.asyncio
async def test_extract_tickers():
    result = await extract_tickers("Apple and Tesla announced partnership")
    assert "AAPL" in result
    assert "TSLA" in result

@pytest.mark.asyncio
async def test_get_articles_by_ticker(test_db_session):
    # test_db_session fixture provides DB connection
    articles = await test_db_session.get_articles("AAPL")
    assert len(articles) > 0
```

### Running Tests

```bash
# All tests
uv run pytest tests -v --cov=src

# Specific test file
uv run pytest tests/test_parsers/test_gemini_parser.py -v

# With Docker services running
docker compose up -d postgres mongo redis
uv run pytest tests -v
```

## Code Quality Checklist

Before committing:

- [ ] All async functions use `async def` and `await`
- [ ] All external API calls wrapped in try-except + logging
- [ ] Pydantic models for all request/response boundaries
- [ ] No hardcoded secrets or API keys
- [ ] File size < 200 lines (split if needed)
- [ ] Type hints on all functions
- [ ] Docstrings on public functions
- [ ] Pass `ruff check . --fix` (linting)
- [ ] Pass `mypy src` (type checking)
- [ ] Pass `pytest tests -v` (tests)

## Documentation Standards

### Docstrings

Use Google-style docstrings:

```python
async def extract_tickers_and_sentiment(text: str) -> dict:
    """Extract ticker symbols and sentiment from article text using Gemini API.
    
    Args:
        text: Full article text to parse.
        
    Returns:
        Dictionary with:
            - tickers: list[str] (e.g., ["AAPL", "TSLA"])
            - sentiment: float (-1.0 to 1.0)
            - sentiment_label: str ("bullish", "neutral", "bearish")
            
    Raises:
        ValueError: If text is empty or exceeds 10k characters.
        APIError: If Gemini API call fails after 3 retries.
    """
```

### Code Comments

- Explain _why_, not _what_ (code shows what it does)
- Use for non-obvious logic or workarounds

```python
# ✅ Good
async def fetch_with_backoff(url: str) -> dict:
    # Finnhub rate limit is 60 req/min, so add jitter to avoid thundering herd
    await asyncio.sleep(random.uniform(0.5, 2.0))
    return await fetch(url)

# ❌ Bad
result = await fetch(url)  # Fetch the URL
```

## Dependency Management

### Adding Dependencies

```bash
uv add package_name              # Production
uv add --group dev pytest-asyncio  # Dev only
uv sync --all-extras             # Install all groups
```

### Pinning Versions

Let `uv` manage versions via `pyproject.toml`. Avoid manual version pinning unless necessary.

## Performance Considerations

- Use connection pooling for PostgreSQL/MongoDB
- Batch inserts when possible (100 articles at once)
- Index heavily-queried fields (ticker, published_at, source)
- Cache Redis dedup checks (TTL=7 days)
- Monitor memory usage in Taskiq workers
