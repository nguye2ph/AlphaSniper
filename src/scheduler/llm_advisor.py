"""LLM-based scheduling advisor — Gemini evaluates source metrics and recommends interval adjustments."""

import json
from typing import Literal

import structlog
from google import genai
from google.genai import types
from pydantic import BaseModel

from src.core.config import settings

logger = structlog.get_logger()

ADVISOR_PROMPT_TEMPLATE = (
    "You are a data pipeline scheduler advisor. "
    "Analyze source metrics and recommend frequency adjustments.\n\n"
    "Sources: {sources_json}\n\n"
    "Rules:\n"
    "- If ema > articles_per_poll_high -> consider 'decrease' interval (poll faster)\n"
    "- If ema < articles_per_poll_low or zero -> consider 'increase' interval (poll slower)\n"
    "- If rate_limit_errors > 0 -> consider 'increase' interval\n"
    "- Respect min_interval and max_interval bounds when setting new_interval\n"
    "- Only recommend if confidence > 0.8\n\n"
    "Output a JSON array (no markdown, raw JSON only):\n"
    '[{{"source": "name", "action": "increase|keep|decrease", '
    '"new_interval": N, "confidence": 0.0-1.0, "reason": "short reason"}}]'
)


class LLMRecommendation(BaseModel):
    """Scheduling recommendation from Gemini LLM advisor."""

    source: str
    action: Literal["increase", "keep", "decrease"]
    new_interval: int
    confidence: float  # 0.0-1.0
    reason: str


class LLMSchedulingAdvisor:
    """Calls Gemini with batched source metrics to get scheduling recommendations."""

    def __init__(self):
        self.client: genai.Client | None = None
        self.model = "gemini-2.0-flash"

    def _ensure_client(self) -> None:
        """Lazy-init Gemini client."""
        if self.client is None:
            if not settings.gemini_api_key:
                raise ValueError("GEMINI_API_KEY not configured")
            self.client = genai.Client(api_key=settings.gemini_api_key)

    async def get_recommendations(self, sources: list[dict]) -> list[LLMRecommendation]:
        """Call Gemini with all source metrics, return high-confidence recommendations.

        Args:
            sources: List of dicts with keys: name, ema, articles_per_poll_high,
                     articles_per_poll_low, current_interval, min_interval, max_interval,
                     rate_limit_errors, empty_responses_count

        Returns:
            Filtered list of recommendations with confidence > 0.8
        """
        if not sources:
            return []

        try:
            self._ensure_client()
            return await self._call_gemini(sources)
        except Exception as e:
            logger.warning("llm_advisor_failed", error=str(e))
            return []

    async def _call_gemini(self, sources: list[dict]) -> list[LLMRecommendation]:
        """Send batch request to Gemini and parse recommendations."""
        sources_json = json.dumps(sources, indent=2, default=str)
        prompt = ADVISOR_PROMPT_TEMPLATE.format(sources_json=sources_json)

        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.1,
            ),
        )

        try:
            items = json.loads(response.text)
            if not isinstance(items, list):
                logger.warning("llm_advisor_unexpected_format", type=type(items).__name__)
                return []

            recommendations = []
            for item in items:
                try:
                    rec = LLMRecommendation(**item)
                    if rec.confidence > 0.8:
                        recommendations.append(rec)
                except Exception as parse_err:
                    logger.warning("llm_advisor_item_parse_error", error=str(parse_err), item=item)

            logger.info(
                "llm_advisor_recommendations",
                total=len(items),
                high_confidence=len(recommendations),
            )
            return recommendations

        except (json.JSONDecodeError, KeyError) as e:
            logger.warning("llm_advisor_parse_error", error=str(e), response=response.text[:200])
            return []


# Module-level singleton
_advisor: LLMSchedulingAdvisor | None = None


def get_advisor() -> LLMSchedulingAdvisor:
    """Return shared advisor instance."""
    global _advisor
    if _advisor is None:
        _advisor = LLMSchedulingAdvisor()
    return _advisor


async def get_recommendations(sources: list[dict]) -> list[LLMRecommendation]:
    """Convenience function — calls shared advisor instance."""
    return await get_advisor().get_recommendations(sources)
