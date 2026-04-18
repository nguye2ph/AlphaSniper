"""Cross-source deduplication: URL normalization (Redis) + headline similarity (Gemini batch LLM)."""

import json
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

import redis.asyncio as aioredis
import structlog
from google import genai
from google.genai import types

from src.core.config import settings

logger = structlog.get_logger()

URL_DEDUP_PREFIX = "dedup:urls"
URL_DEDUP_TTL = 48 * 3600  # 48 hours
HEADLINE_QUEUE_KEY = "dedup:headline_queue"

# Query params that carry meaningful identity (keep these, strip the rest)
_KEEP_PARAMS = {"symbol", "ticker", "id"}

HEADLINE_DEDUP_PROMPT = (
    "You are a news deduplication engine. "
    "Given a list of headlines, identify groups covering the same story.\n\n"
    'Headlines (JSON array of {{"headline": "...", "article_id": "..."}}):\n'
    "{headlines_json}\n\n"
    "Return a JSON array of groups. Each group is an array of article_ids for the same story.\n"
    'Only include groups with 2+ articles. If no duplicates, return [].\n'
    'Example: [["id1", "id2"], ["id3", "id4", "id5"]]'
)


def _normalize_url(url: str) -> str:
    """Strip non-essential query params, trailing slash, lowercase domain."""
    try:
        parsed = urlparse(url.strip())
        # Lowercase scheme + netloc
        scheme = parsed.scheme.lower()
        netloc = parsed.netloc.lower()
        # Strip trailing slash from path
        path = parsed.path.rstrip("/")
        # Keep only whitelisted query params
        qs = parse_qs(parsed.query, keep_blank_values=False)
        filtered_qs = {k: v for k, v in qs.items() if k.lower() in _KEEP_PARAMS}
        query = urlencode(sorted(filtered_qs.items()), doseq=True)
        return urlunparse((scheme, netloc, path, "", query, ""))
    except Exception:
        return url.lower().rstrip("/")


class CrossSourceDedup:
    """Two-layer cross-source deduplication: URL hash + LLM headline similarity."""

    def __init__(self, redis: aioredis.Redis):
        self.redis = redis
        self._gemini_client: genai.Client | None = None

    def _ensure_gemini(self) -> genai.Client:
        if self._gemini_client is None:
            if not settings.gemini_api_key:
                raise ValueError("GEMINI_API_KEY not configured")
            self._gemini_client = genai.Client(api_key=settings.gemini_api_key)
        return self._gemini_client

    async def is_url_duplicate(self, url: str, source: str) -> bool:
        """Layer 1: Normalize URL and check Redis SET. Returns True if duplicate.

        Marks the URL as seen on first encounter (atomic check-and-set).
        """
        if not url:
            return False
        normalized = _normalize_url(url)
        key = f"{URL_DEDUP_PREFIX}:{normalized}"
        # SET NX — returns True if newly set (not duplicate), None if already exists
        result = await self.redis.set(key, source, ex=URL_DEDUP_TTL, nx=True)
        is_new = result is not None
        if not is_new:
            logger.debug("cross_dedup_url_skip", url=url[:80], source=source)
        return not is_new

    async def queue_for_headline_dedup(self, headline: str, article_id: str) -> None:
        """Push headline + article_id to Redis LIST for batch LLM evaluation."""
        entry = json.dumps({"headline": headline, "article_id": article_id})
        await self.redis.rpush(HEADLINE_QUEUE_KEY, entry)

    async def run_batch_headline_dedup(self) -> list[list[str]]:
        """Layer 2: Pop all queued headlines, send to Gemini, return duplicate groups.

        Each group is a list of article_ids that cover the same story.
        Returns empty list if queue is empty or Gemini fails.
        """
        # Drain the queue atomically
        pipeline = self.redis.pipeline()
        await pipeline.lrange(HEADLINE_QUEUE_KEY, 0, -1)
        await pipeline.delete(HEADLINE_QUEUE_KEY)
        results = await pipeline.execute()
        raw_entries: list[bytes] = results[0]

        if not raw_entries:
            return []

        entries = []
        for raw in raw_entries:
            try:
                entries.append(json.loads(raw))
            except json.JSONDecodeError:
                continue

        logger.info("headline_dedup_batch", count=len(entries))

        try:
            client = self._ensure_gemini()
            headlines_json = json.dumps(entries, ensure_ascii=False)
            prompt = HEADLINE_DEDUP_PROMPT.format(headlines_json=headlines_json)

            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.1,
                ),
            )

            groups = json.loads(response.text)
            if not isinstance(groups, list):
                return []

            valid_groups = [g for g in groups if isinstance(g, list) and len(g) >= 2]
            logger.info("headline_dedup_groups_found", groups=len(valid_groups))
            return valid_groups

        except Exception as e:
            logger.warning("headline_dedup_llm_failed", error=str(e))
            return []
