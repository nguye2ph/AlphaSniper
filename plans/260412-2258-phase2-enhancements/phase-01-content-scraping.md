# Phase 1: Content Scraping & AI Enrichment

## Context Links

- [Brainstorm — Part 3](../reports/brainstorm-260412-2258-ui-upgrade-discord.md)
- [Article Model](../../src/core/models/article.py)
- [Taskiq Jobs](../../src/jobs/taskiq_app.py)
- [Gemini Parser](../../src/parsers/gemini_parser.py)
- [Article Schema](../../src/core/schemas/article_schema.py)

## Overview

- **Priority**: P1
- **Status**: pending
- **Effort**: 4h
- **Description**: Scrape full article content from URLs, extract metadata, use Gemini to generate key_points. Expose in API + webapp.

## Key Insights

- `beautifulsoup4` + `lxml` already in pyproject.toml — no new deps needed for HTML parsing
- `httpx` already available for async HTTP
- Gemini `parse_batch` already handles batch calls — reuse for key_points extraction
- Current `Article` model has no content fields — needs Alembic migration
- Some URLs will 403/paywall/timeout — must handle gracefully

## Requirements

### Functional
- Scrape article body text from URL for unscraped articles
- Extract metadata: image_url, author, publish_date
- Generate 3-5 key_points bullets via Gemini API
- Display content preview + key_points in webapp article card
- API returns content + key_points in ArticleResponse

### Non-Functional
- Rate limit: max 1 request/sec to avoid IP blocks
- Skip gracefully on 403/404/timeout (mark content_scraped=True, content=None)
- Batch Gemini calls (10-20 articles per API call) to minimize cost

## Architecture

```
PostgreSQL articles (content_scraped=False)
  → Taskiq job: scrape_unscraped_articles(batch=20)
    → httpx GET article URL
    → BeautifulSoup: extract <article>/<main> body, image_url, author
    → Collect batch of content texts
    → Gemini API: extract key_points from content (batch)
    → UPDATE articles SET content, key_points, image_url, author, content_scraped=True
```

## Related Code Files

### Modify
- `src/core/models/article.py` — add content, key_points, image_url, author, content_scraped columns
- `src/core/schemas/article_schema.py` — add fields to ArticleResponse
- `src/jobs/taskiq_app.py` — register scrape task + add to scheduler
- `src/webapp/types/index.ts` — add content, key_points, image_url, author fields to Article
- `src/webapp/components/feed/article-card.tsx` — show content preview + key_points

### Create
- `alembic/versions/xxx_add_content_columns.py` — migration for new columns
- `src/parsers/content_scraper.py` — fetch_article_content(), extract_metadata()
- `src/jobs/scrape_content_tasks.py` — scrape_unscraped_articles() Taskiq task

## Implementation Steps

### Step 1: Alembic Migration (15min)

1. Generate migration: `uv run alembic revision --autogenerate -m "add_content_columns"`
2. Add columns to articles table:
   ```sql
   content TEXT DEFAULT NULL
   key_points JSONB DEFAULT NULL
   image_url TEXT DEFAULT NULL
   author TEXT DEFAULT NULL
   content_scraped BOOLEAN DEFAULT FALSE NOT NULL
   ```
3. Add index: `ix_article_content_scraped` on `content_scraped`
4. Run: `uv run alembic upgrade head`

### Step 2: Update Article Model (15min)

1. Add to `Article` class in `src/core/models/article.py`:
   - `content: Mapped[str | None]` — TEXT, nullable
   - `key_points: Mapped[dict | None]` — JSONB, nullable (stores list of strings)
   - `image_url: Mapped[str | None]` — TEXT, nullable
   - `author: Mapped[str | None]` — String(255), nullable
   - `content_scraped: Mapped[bool]` — Boolean, default=False
2. Add index `ix_article_content_scraped` to `__table_args__`

### Step 3: Content Scraper Module (1h)

Create `src/parsers/content_scraper.py` (<200 lines):

1. `async def fetch_article_content(url: str) -> ContentResult | None`
   - httpx GET with 10s timeout, User-Agent header
   - Return None on 403/404/timeout
   - Parse HTML with BeautifulSoup
2. `def extract_body(soup: BeautifulSoup) -> str`
   - Try `<article>` tag first
   - Fallback: `<main>` tag
   - Fallback: `<body>` stripped of `<nav>`, `<footer>`, `<header>`, `<script>`, `<style>`
   - Strip HTML tags, normalize whitespace
   - Limit to 5000 chars
3. `def extract_metadata(soup: BeautifulSoup) -> dict`
   - image_url: `<meta property="og:image">` or first `<img>` in article
   - author: `<meta name="author">` or `<span class="author">`
   - publish_date: `<meta property="article:published_time">` or `<time>`
4. `ContentResult` dataclass: body, image_url, author

### Step 4: Scrape Taskiq Job (1h)

Create `src/jobs/scrape_content_tasks.py` (<200 lines):

1. `@broker.task() async def scrape_unscraped_articles(batch_size: int = 20)`
   - Query PostgreSQL: `SELECT * FROM articles WHERE content_scraped = FALSE ORDER BY published_at DESC LIMIT batch_size`
   - For each article:
     - `await asyncio.sleep(1.0)` — rate limit
     - Call `fetch_article_content(article.url)`
     - If success: store content + metadata
     - If fail: mark content_scraped=True, content=None
   - Collect successful content texts
   - Call `GeminiParser.extract_key_points_batch(contents)` (new method)
   - Batch UPDATE articles with content, key_points, image_url, author, content_scraped=True
   - Commit

2. Add to `taskiq_app.py`:
   - Import and register task
   - Add scheduled trigger (every 5 minutes)

### Step 5: Gemini Key Points Extraction (30min)

Add to `src/parsers/gemini_parser.py`:

1. New method `async def extract_key_points(self, content: str) -> list[str]`
   - System prompt: "Extract 3-5 key points as JSON array of strings"
   - Return list of bullet strings
2. New method `async def extract_key_points_batch(self, contents: list[str]) -> list[list[str]]`
   - Batch multiple contents in single API call
   - Truncate each content to 2000 chars before sending

### Step 6: Update API Schema (15min)

1. Add to `ArticleResponse` in `article_schema.py`:
   - `content: str | None = None`
   - `key_points: list[str] | None = None`
   - `image_url: str | None = None`
   - `author: str | None = None`

### Step 7: Update Webapp (45min)

1. Update `src/webapp/types/index.ts`:
   - Add `content`, `key_points`, `image_url`, `author` to Article interface
2. Update `src/webapp/components/feed/article-card.tsx`:
   - Show content preview (first 200 chars) in expanded view
   - Show key_points as bulleted list with colored dots
   - Show image thumbnail if image_url exists
   - Show author name

## Todo List

- [ ] Alembic migration for content columns
- [ ] Update Article SQLAlchemy model
- [ ] Create content_scraper.py module
- [ ] Create scrape_content_tasks.py Taskiq job
- [ ] Add key_points extraction to GeminiParser
- [ ] Update ArticleResponse schema
- [ ] Update Article TypeScript type
- [ ] Update article-card.tsx with content preview
- [ ] Register scrape task in taskiq_app.py scheduler

## Test Cases

- **Happy path**: URL returns HTML with `<article>` → content extracted, key_points generated
- **No article tag**: Falls back to `<main>` then `<body>` stripping nav/footer
- **403/paywall**: Returns None, article marked content_scraped=True with content=None
- **Timeout**: Same as 403 handling
- **Empty content**: Gemini returns empty key_points array
- **Batch processing**: 20 articles scraped, committed in single transaction

## Verification Steps

1. Run migration: `uv run alembic upgrade head`
2. Check DB: `psql -c "SELECT column_name FROM information_schema.columns WHERE table_name='articles'"`
3. Trigger job manually: `uv run python -c "from src.jobs.scrape_content_tasks import ..."`
4. Check API response includes content fields: `curl localhost:8200/api/articles/latest`
5. Verify webapp shows content preview in article card

## Acceptance Criteria

- [ ] Articles table has content, key_points, image_url, author, content_scraped columns
- [ ] Scraper fetches and stores content for accessible URLs
- [ ] Failed URLs marked content_scraped=True with null content
- [ ] Rate limit: max 1 req/sec
- [ ] API returns content + key_points
- [ ] Webapp displays content preview and key_points

## Success Criteria

- 60%+ of article URLs successfully scraped (non-paywalled)
- Key points generated for all scraped articles
- No IP blocks from rate limiting

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Paywalled URLs | Medium — no content for premium sources | Skip gracefully, mark as scraped |
| JS-rendered pages | Medium — empty content | httpx-first approach; Playwright fallback later |
| Gemini cost | Low — batch calls reduce API usage | Batch 10-20 contents per call |
| IP blocking | High — scraper blocked | 1 req/sec rate limit, User-Agent header |

## Security Considerations

- Sanitize scraped HTML before storing (strip scripts)
- Don't store cookies or session data from fetched pages
- Rate limit prevents abuse of external sites

## Next Steps

- Phase 2 (UI) depends on content/key_points fields being available
- Consider Playwright fallback for JS-rendered sites (future enhancement)
