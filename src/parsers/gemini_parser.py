"""Gemini AI parser — structured extraction of tickers, sentiment, category from headlines."""

import json

import structlog
from google import genai
from google.genai import types

from src.core.config import settings
from src.parsers.headline_parser import ParsedHeadline, parse_headline

logger = structlog.get_logger()

SYSTEM_PROMPT = """You are a financial news analyst. Extract structured data from stock news headlines.

For each headline, return a JSON object with:
- tickers: list of stock ticker symbols mentioned (e.g. ["AAPL", "TSLA"])
- sentiment: float from -1.0 (very bearish) to 1.0 (very bullish)
- sentiment_label: "bullish", "bearish", or "neutral"
- category: one of "earnings", "merger", "insider", "regulatory", "analyst", "legal", "product", "general"
- urgency: "high", "medium", or "low"

Be precise with ticker extraction. Only include actual stock tickers, not abbreviations.
If unsure about a ticker, omit it rather than guess."""


class GeminiParser:
    """Parse headlines using Google Gemini API with structured output."""

    def __init__(self):
        self.api_key = settings.gemini_api_key
        self.client = None
        self.model = "gemini-2.0-flash"

    def _ensure_client(self):
        """Lazy init the Gemini client."""
        if self.client is None:
            if not self.api_key:
                raise ValueError("GEMINI_API_KEY not set")
            self.client = genai.Client(api_key=self.api_key)

    async def parse_headline(self, headline: str) -> ParsedHeadline:
        """Parse a single headline. Falls back to rule-based on failure."""
        try:
            self._ensure_client()
            result = await self._call_gemini(headline)
            return result
        except Exception as e:
            logger.warning("gemini_fallback", error=str(e), headline=headline[:50])
            return parse_headline(headline)

    async def parse_batch(self, headlines: list[str]) -> list[ParsedHeadline]:
        """Parse multiple headlines in a single API call for efficiency."""
        if not headlines:
            return []

        try:
            self._ensure_client()
            return await self._call_gemini_batch(headlines)
        except Exception as e:
            logger.warning("gemini_batch_fallback", error=str(e), count=len(headlines))
            return [parse_headline(h) for h in headlines]

    async def _call_gemini(self, headline: str) -> ParsedHeadline:
        """Single headline Gemini API call."""
        prompt = f"Parse this stock news headline:\n\n\"{headline}\""

        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                response_mime_type="application/json",
                temperature=0.1,
            ),
        )

        return self._parse_response(response.text)

    async def _call_gemini_batch(self, headlines: list[str]) -> list[ParsedHeadline]:
        """Batch headlines in single API call."""
        numbered = "\n".join(f"{i+1}. \"{h}\"" for i, h in enumerate(headlines))
        prompt = f"Parse these {len(headlines)} stock news headlines. Return a JSON array of objects:\n\n{numbered}"

        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                response_mime_type="application/json",
                temperature=0.1,
            ),
        )

        try:
            items = json.loads(response.text)
            if isinstance(items, list):
                return [self._dict_to_parsed(item) for item in items]
            # Single object returned
            return [self._parse_response(response.text)]
        except (json.JSONDecodeError, KeyError) as e:
            logger.error("gemini_batch_parse_error", error=str(e))
            return [parse_headline(h) for h in headlines]

    def _parse_response(self, text: str) -> ParsedHeadline:
        """Convert Gemini JSON response to ParsedHeadline."""
        data = json.loads(text)
        return self._dict_to_parsed(data)

    def _dict_to_parsed(self, data: dict) -> ParsedHeadline:
        """Convert dict to ParsedHeadline with validation."""
        return ParsedHeadline(
            tickers=data.get("tickers", []),
            sentiment=max(-1.0, min(1.0, float(data.get("sentiment", 0.0)))),
            sentiment_label=data.get("sentiment_label", "neutral"),
            category=data.get("category", "general"),
        )
